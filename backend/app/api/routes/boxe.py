from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player
from app.api.responses import error_response
from app.modules.games.boxe import repository
from app.modules.games.boxe.service import (
    BoxeApiError,
    BoxeCursorError,
    DEFAULT_HISTORY_LIMIT,
    MAX_HISTORY_LIMIT,
    cashout_round,
    get_public_config,
    get_round_replay,
    get_session,
    list_sessions,
    reveal_pick,
    start_round,
)
from app.modules.games.boxe.state_machine import BoxeStateTransitionError

router = APIRouter(prefix="/games/boxe", tags=["games-boxe"])


class StartRoundRequest(BaseModel):
    title_code: str
    rows: int
    difficulty: str
    bet_amount: str
    wallet_source: str
    client_seed: str | None = None


class RevealPickRequest(BaseModel):
    round_id: str
    row: int
    position: int


class CashoutRequest(BaseModel):
    round_id: str


@router.get("/config")
def boxe_config(title_code: str | None = Query(default=None)) -> dict[str, object] | object:
    try:
        return {"success": True, "data": get_public_config(title_code=title_code)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.post("/start")
def boxe_start(
    payload: StartRoundRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = start_round(
            player_id=str(current_user["id"]),
            title_code=payload.title_code,
            rows=payload.rows,
            difficulty=payload.difficulty,
            bet_amount=payload.bet_amount,
            wallet_source=payload.wallet_source,
            client_seed=payload.client_seed,
            idempotency_key=str(idempotency_key),
        )
    except (BoxeApiError, repository.BoxeIdempotencyConflict) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/reveal")
def boxe_reveal(
    payload: RevealPickRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = reveal_pick(
            player_id=str(current_user["id"]),
            round_id=payload.round_id,
            row=payload.row,
            position=payload.position,
            idempotency_key=str(idempotency_key),
        )
    except (BoxeApiError, BoxeStateTransitionError, repository.BoxeIdempotencyConflict, KeyError) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/cashout")
def boxe_cashout(
    payload: CashoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = cashout_round(
            player_id=str(current_user["id"]),
            round_id=payload.round_id,
            idempotency_key=str(idempotency_key),
        )
    except (BoxeApiError, BoxeStateTransitionError, repository.BoxeIdempotencyConflict, KeyError) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.get("/session/{session_id}")
def boxe_session(
    session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        return {"success": True, "data": get_session(player_id=str(current_user["id"]), session_id=session_id)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.get("/round/{round_id}/replay")
def boxe_replay(
    round_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        return {"success": True, "data": get_round_replay(player_id=str(current_user["id"]), round_id=round_id)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.get("/sessions")
def boxe_sessions(
    limit: int = Query(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        page = list_sessions(player_id=str(current_user["id"]), limit=limit, cursor=cursor)
    except BoxeCursorError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except BoxeApiError as exc:
        return _boxe_error(exc)
    return {
        "success": True,
        "data": page["items"],
        "meta": {
            "next_cursor": page["next_cursor"],
            "limit": page["limit"],
        },
    }


def _require_idempotency_key(idempotency_key: str | None) -> object | None:
    if idempotency_key:
        return None
    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="IDEMPOTENCY_KEY_REQUIRED",
        message="Idempotency-Key header is required",
    )


def _map_exception(exc: Exception) -> object:
    if isinstance(exc, BoxeApiError):
        return _boxe_error(exc)
    if isinstance(exc, repository.BoxeIdempotencyConflict):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, BoxeStateTransitionError):
        code = "ROUND_ALREADY_CLOSED" if "terminal" in exc.reason else "CASHOUT_NOT_ALLOWED"
        status_code = status.HTTP_409_CONFLICT if code == "ROUND_ALREADY_CLOSED" else status.HTTP_422_UNPROCESSABLE_ENTITY
        return error_response(status_code=status_code, code=code, message=str(exc))
    if isinstance(exc, KeyError):
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROUND_NOT_FOUND",
            message=str(exc),
        )
    raise exc


def _boxe_error(exc: BoxeApiError) -> object:
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )
