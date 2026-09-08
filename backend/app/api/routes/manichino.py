"""Rotte del manichino: due endpoint contabili, nessuna rotta anonima.

PERCHE' ESISTONO: i test della piattaforma chiamano queste rotte per produrre
transazioni vere e verificare contabilita', sessioni e registro. Le regole di
autenticazione sono quelle delle rotte di Mines: bearer obbligatorio,
Idempotency-Key obbligatoria, nessun cammino anonimo.

PERCHE' LA REGISTRAZIONE E' CONDIZIONALE: questo modulo e' incluso in
`app/api/router.py` solo quando `manichino_attivo()` e' vera; in produzione
queste rotte non esistono proprio (404).
"""

from decimal import Decimal

import psycopg
from fastapi import APIRouter, Body, Depends, Header, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player, get_current_player_allow_suspended
from app.api.responses import error_response
from app.db.connection import db_connection
from app.modules.games.manichino.exceptions import (
    ManichinoSessionVoidedByOperatorError,
    ManichinoGameStateConflictError,
    ManichinoIdempotencyConflictError,
    ManichinoInsufficientBalanceError,
    ManichinoValidationError,
)
from app.modules.games.manichino.round_gateway import (
    is_open_round_idempotency_violation,
)
from app.modules.games.manichino.service import (
    apri_round,
    build_start_request_fingerprint,
    chiudi_round,
    get_open_round_by_idempotency_key,
)
from app.modules.platform.game_launch.service import (
    GameLaunchTokenOwnershipError,
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    issue_game_launch_token,
    validate_required_game_launch_token_for_player,
)
from app.modules.platform.manichino_flag import (
    GAME_CODE_MANICHINO,
    TITLE_CODE_MANICHINO_TEST,
)

router = APIRouter(prefix="/games/manichino", tags=["games-manichino"])


class StartRoundRequest(BaseModel):
    bet_amount: str
    wallet_type: str
    title_code: str | None = None
    access_session_id: str | None = None
    table_session_id: str | None = None


class SettleRoundRequest(BaseModel):
    game_session_id: str
    esito: str
    payout_amount: str | None = None


class ManichinoLaunchIssueRequest(BaseModel):
    title_code: str = TITLE_CODE_MANICHINO_TEST
    site_code: str = "casinoking"


@router.post("/launch-token")
def issue_manichino_launch_token(
    payload: ManichinoLaunchIssueRequest | None = Body(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    # PERCHE' E' SICURA: questo modulo e' incluso in `api/router.py` solo quando
    # `manichino_attivo()` e' vera, quindi in produzione la rotta non esiste (404).
    # Inoltre `issue_game_launch_token` rifiuta comunque il motore della cavia se
    # l'interruttore e' spento: sono due difese indipendenti, non una sola.
    if not isinstance(current_user, dict):
        return current_user

    request = payload or ManichinoLaunchIssueRequest()
    try:
        result = issue_game_launch_token(
            player_id=str(current_user["id"]),
            role=str(current_user["role"]),
            game_code=GAME_CODE_MANICHINO,
            title_code=request.title_code,
            site_code=request.site_code,
            mode="real",
        )
    except GameLaunchTokenValidationError as exc:
        status_code = (
            status.HTTP_501_NOT_IMPLEMENTED
            if "Demo launch mode is not available" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return error_response(
            status_code=status_code,
            code=exc.code,
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/start")
def start_manichino_round(
    payload: StartRoundRequest,
    current_user: dict[str, object] = Depends(get_current_player_allow_suspended),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    user_id = str(current_user["id"])
    launch_context = _resolve_required_manichino_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context
    if payload.wallet_type.strip().lower() == "demo":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="wallet_type demo is not supported for manichino",
        )
    requested_title_code = (
        payload.title_code.strip().lower()
        if payload.title_code is not None
        else TITLE_CODE_MANICHINO_TEST
    )
    if launch_context["title_code"] != requested_title_code:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token title code is not valid",
        )
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                result = apri_round(
                    cursor=cursor,
                    user_id=user_id,
                    bet_amount=payload.bet_amount,
                    wallet_type=payload.wallet_type,
                    idempotency_key=idempotency_key,
                    title_code=payload.title_code,
                    table_session_id=payload.table_session_id,
                    access_session_id=payload.access_session_id,
                )
    except ManichinoValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ManichinoInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except ManichinoIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    except psycopg.errors.UniqueViolation as exc:
        if not is_open_round_idempotency_violation(exc):
            raise
        # PERCHE' si rilegge invece di fallire: una start ripetuta con la
        # stessa chiave deve restituire il round gia' aperto (idempotenza),
        # non un errore — a patto che il payload sia lo stesso.
        expected_fingerprint = build_start_request_fingerprint(
            user_id=user_id,
            bet_amount=payload.bet_amount,
            wallet_type=payload.wallet_type,
            title_code=payload.title_code,
            table_session_id=payload.table_session_id,
            access_session_id=payload.access_session_id,
        )
        if expected_fingerprint is None:
            return error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="bet_amount is not valid",
            )
        replay = _replay_existing_round(
            user_id=user_id,
            idempotency_key=idempotency_key,
            request_fingerprint=expected_fingerprint,
        )
        if replay is None:
            return error_response(
                status_code=status.HTTP_409_CONFLICT,
                code="IDEMPOTENCY_CONFLICT",
                message="Idempotency key already used with a different payload",
            )
        return {
            "success": True,
            "data": replay,
        }

    return {
        "success": True,
        "data": result,
    }


@router.post("/settle")
def settle_manichino_round(
    payload: SettleRoundRequest,
    current_user: dict[str, object] = Depends(get_current_player),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    launch_context = _resolve_required_manichino_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                result = chiudi_round(
                    cursor=cursor,
                    user_id=str(current_user["id"]),
                    game_round_id=payload.game_session_id,
                    esito=payload.esito,
                    payout_amount=payload.payout_amount,
                    idempotency_key=idempotency_key,
                )
    except ManichinoValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ManichinoIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    except ManichinoSessionVoidedByOperatorError as exc:
        # PRIMA del conflitto generico: e' una sua sottoclasse, quindi invertendo
        # l'ordine questo ramo non verrebbe mai raggiunto.
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="SESSION_VOIDED_BY_OPERATOR",
            message=str(exc),
        )
    except ManichinoGameStateConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="GAME_STATE_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


def _resolve_required_manichino_launch_token(
    *,
    game_launch_token: str | None,
    current_user: dict[str, object],
) -> dict[str, object] | object:
    try:
        launch_context = validate_required_game_launch_token_for_player(
            game_launch_token=game_launch_token,
            player_id=str(current_user["id"]),
        )
    except GameLaunchTokenValidationError as exc:
        error_code = (
            "GAME_LAUNCH_TOKEN_REQUIRED"
            if not game_launch_token
            else "GAME_LAUNCH_TOKEN_INVALID"
        )
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=error_code,
            message=str(exc),
        )
    except GameLaunchTokenOwnershipError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )
    except GameLaunchTokenScopeError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    if launch_context["game_code"] != GAME_CODE_MANICHINO:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token game code is not valid",
        )
    return launch_context


def _replay_existing_round(
    *,
    user_id: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object] | None:
    """Risponde con il round gia' aperto da una start ripetuta.

    La transazione originale e' andata in rollback insieme alla violazione
    UNIQUE, quindi la rilettura avviene su una connessione nuova — lo stesso
    giro che Mines fa con il repository delle idempotenze. Se il fingerprint
    non combacia, la stessa chiave e' stata riusata con un payload diverso:
    None al chiamante, che risponde 409.
    """
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = get_open_round_by_idempotency_key(
                cursor=cursor,
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
    if row is None or row["request_fingerprint"] != request_fingerprint:
        return None
    return {
        "game_session_id": str(row["id"]),
        "status": "active",
        "bet_amount": f"{Decimal(row['bet_amount']):.6f}",
        "wallet_type": row["wallet_type"],
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "wallet_balance_after_start": f"{Decimal(row['wallet_balance_after_start']):.6f}",
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "table_session_id": (
            str(row["table_session_id"]) if row["table_session_id"] else None
        ),
        "already_exists": True,
    }
