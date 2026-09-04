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
from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player
from app.api.responses import error_response
from app.db.connection import db_connection
from app.modules.games.manichino.exceptions import (
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


@router.post("/start")
def start_manichino_round(
    payload: StartRoundRequest,
    current_user: dict[str, object] = Depends(get_current_player),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    user_id = str(current_user["id"])
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
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
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
