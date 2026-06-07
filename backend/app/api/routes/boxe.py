from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player, require_admin_area
from app.api.responses import error_response
from app.modules.games.boxe import repository
from app.modules.games.boxe.service import (
    BoxeApiError,
    BoxeCursorError,
    BoxePlatformIdempotencyConflictError,
    BoxePlatformInsufficientBalanceError,
    BoxePlatformValidationError,
    DEFAULT_HISTORY_LIMIT,
    LATEST_ACCESS_SESSION_HISTORY_LIMIT,
    MAX_HISTORY_LIMIT,
    cashout_round,
    get_public_config,
    get_round_replay,
    get_round_replay_for_admin,
    get_session,
    list_latest_access_session_history_for_user,
    list_sessions,
    reveal_pick,
    start_round,
)
from app.modules.games.boxe.state_machine import BoxeStateTransitionError
from app.modules.platform.access_sessions.service import (
    AccessSessionNotFoundError,
    AccessSessionStateConflictError,
    AccessSessionValidationError,
    AccessSessionVoidedByOperatorError,
    ensure_access_session_active_for_round_start,
)
from app.modules.platform.game_launch.service import (
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    issue_game_launch_token,
    validate_game_launch_token,
)

router = APIRouter(prefix="/games/boxe", tags=["games-boxe"])


class StartRoundRequest(BaseModel):
    title_code: str
    rows: int
    difficulty: str
    bet_amount: str
    wallet_source: str
    client_seed: str | None = None
    table_session_id: str | None = None
    access_session_id: str | None = None


class RevealPickRequest(BaseModel):
    round_id: str
    row: int
    position: int


class CashoutRequest(BaseModel):
    round_id: str


class GameLaunchIssueRequest(BaseModel):
    game_code: str | None = None
    title_code: str | None = None
    site_code: str | None = None
    mode: str | None = None


@router.get("/config")
def boxe_config(
    title_code: str | None = Query(default=None),
    site_code: str | None = Query(default=None),
) -> dict[str, object] | object:
    try:
        return {
            "success": True,
            "data": get_public_config(title_code=title_code, site_code=site_code),
        }
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.post("/launch-token")
def issue_boxe_launch_token(
    payload: GameLaunchIssueRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    game_code = (payload.game_code or "boxe").strip().lower()
    if game_code != "boxe":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="BOXE launch endpoint can issue only BOXE launch tokens",
        )
    mode = (payload.mode or "real").strip().lower()
    if mode != "real":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="BOXE player launch tokens are available only for real mode",
        )

    try:
        result = issue_game_launch_token(
            player_id=str(current_user["id"]),
            role=str(current_user["role"]),
            game_code="boxe",
            title_code=payload.title_code,
            site_code=payload.site_code,
            mode="real",
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code,
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


def _resolve_boxe_actor(
    *,
    authorization: str | None,
    game_launch_token: str | None,
    allow_real_without_token: bool = False,
) -> dict[str, object] | object:
    if game_launch_token:
        try:
            launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
        except GameLaunchTokenValidationError as exc:
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="GAME_LAUNCH_TOKEN_INVALID",
                message=str(exc),
            )
        except GameLaunchTokenScopeError as exc:
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message=str(exc),
            )
        if launch_context["game_code"] != "boxe":
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game launch token scope is not valid for BOXE",
            )
        if launch_context["mode"] == "demo":
            return {
                "mode": "demo",
                "actor_id": str(launch_context["anonymous_id"]),
                "current_user": None,
                "launch_context": launch_context,
            }
        if not authorization:
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="UNAUTHORIZED",
                message="Authorization header is required",
            )
        current_user = get_current_player(authorization)
        if not isinstance(current_user, dict):
            return current_user
        if launch_context["player_id"] != str(current_user["id"]):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game launch token ownership is not valid",
            )
        return {
            "mode": "real",
            "actor_id": str(current_user["id"]),
            "current_user": current_user,
            "launch_context": launch_context,
        }

    if allow_real_without_token and authorization:
        current_user = get_current_player(authorization)
        if not isinstance(current_user, dict):
            return current_user
        return {
            "mode": "real",
            "actor_id": str(current_user["id"]),
            "current_user": current_user,
            "launch_context": None,
        }

    if allow_real_without_token:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authorization header is required",
        )
    return error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="GAME_LAUNCH_TOKEN_REQUIRED",
        message="X-Game-Launch-Token header is required",
    )


@router.post("/start")
def boxe_start(
    payload: StartRoundRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    is_demo = payload.wallet_source.strip().lower() == "demo"
    if is_demo and not game_launch_token and authorization:
        # Retro-compat: demo via Bearer token (legacy /auth/demo path)
        current_user = get_current_player(authorization)
        if not isinstance(current_user, dict):
            return current_user
        actor_context = {
            "mode": "demo",
            "actor_id": str(current_user["id"]),
            "current_user": current_user,
            "launch_context": None,
        }
    else:
        actor_context = _resolve_boxe_actor(
            authorization=authorization,
            game_launch_token=game_launch_token,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error

    launch_context = actor_context["launch_context"]
    launch_title_code = (
        str(launch_context["title_code"])
        if isinstance(launch_context, dict)
        else payload.title_code
    )
    launch_site_code = (
        str(launch_context["site_code"])
        if isinstance(launch_context, dict)
        else "casinoking"
    )
    if is_demo and actor_context["mode"] == "real" and game_launch_token is not None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Real launch tokens cannot start demo rounds",
        )
    if is_demo and payload.access_session_id is not None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Demo rounds cannot have an access session",
        )
    if not is_demo and payload.access_session_id is None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Access session is required for real mode",
        )

    current_user = actor_context.get("current_user")
    if payload.access_session_id is not None and current_user is not None:
        try:
            ensure_access_session_active_for_round_start(
                user_id=str(current_user["id"]),
                access_session_id=payload.access_session_id,
                game_code="boxe",
                title_code=launch_title_code,
                site_code=launch_site_code,
            )
        except AccessSessionValidationError as exc:
            return error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message=str(exc),
            )
        except AccessSessionNotFoundError as exc:
            return error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                code="RESOURCE_NOT_FOUND",
                message=str(exc),
            )
        except AccessSessionVoidedByOperatorError as exc:
            return error_response(
                status_code=status.HTTP_409_CONFLICT,
                code="SESSION_VOIDED_BY_OPERATOR",
                message=str(exc),
            )
        except AccessSessionStateConflictError as exc:
            return error_response(
                status_code=status.HTTP_409_CONFLICT,
                code="GAME_STATE_CONFLICT",
                message=str(exc),
            )

    try:
        result = start_round(
            player_id=str(actor_context["actor_id"]),
            title_code=launch_title_code,
            site_code=launch_site_code,
            rows=payload.rows,
            difficulty=payload.difficulty,
            bet_amount=payload.bet_amount,
            wallet_source=payload.wallet_source,
            client_seed=payload.client_seed,
            idempotency_key=str(idempotency_key),
            table_session_id=payload.table_session_id,
            access_session_id=payload.access_session_id,
        )
    except (
        BoxeApiError,
        BoxePlatformIdempotencyConflictError,
        BoxePlatformInsufficientBalanceError,
        BoxePlatformValidationError,
        repository.BoxeIdempotencyConflict,
    ) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/reveal")
def boxe_reveal(
    payload: RevealPickRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_boxe_actor(
        authorization=authorization,
        game_launch_token=game_launch_token,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = reveal_pick(
            player_id=str(actor_context["actor_id"]),
            round_id=payload.round_id,
            row=payload.row,
            position=payload.position,
            idempotency_key=str(idempotency_key),
        )
    except (
        BoxeApiError,
        BoxePlatformIdempotencyConflictError,
        BoxePlatformInsufficientBalanceError,
        BoxePlatformValidationError,
        BoxeStateTransitionError,
        repository.BoxeIdempotencyConflict,
        KeyError,
    ) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/cashout")
def boxe_cashout(
    payload: CashoutRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_boxe_actor(
        authorization=authorization,
        game_launch_token=game_launch_token,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = cashout_round(
            player_id=str(actor_context["actor_id"]),
            round_id=payload.round_id,
            idempotency_key=str(idempotency_key),
        )
    except (
        BoxeApiError,
        BoxePlatformIdempotencyConflictError,
        BoxePlatformInsufficientBalanceError,
        BoxePlatformValidationError,
        BoxeStateTransitionError,
        repository.BoxeIdempotencyConflict,
        KeyError,
    ) as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.get("/session/{session_id}")
def boxe_session(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_boxe_actor(
        authorization=authorization,
        game_launch_token=game_launch_token,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context
    try:
        return {"success": True, "data": get_session(player_id=str(actor_context["actor_id"]), session_id=session_id)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.get("/round/{round_id}/replay")
def boxe_replay(
    round_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_boxe_actor(
        authorization=authorization,
        game_launch_token=game_launch_token,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context
    try:
        return {"success": True, "data": get_round_replay(player_id=str(actor_context["actor_id"]), round_id=round_id)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.get("/admin/round/{round_id}/replay")
def boxe_admin_replay(
    round_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    try:
        return {"success": True, "data": get_round_replay_for_admin(round_id=round_id)}
    except BoxeApiError as exc:
        return _boxe_error(exc)


@router.get("/sessions")
def boxe_sessions(
    limit: int = Query(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
    cursor: str | None = Query(default=None),
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_boxe_actor(
        authorization=authorization,
        game_launch_token=game_launch_token,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context
    try:
        page = list_sessions(player_id=str(actor_context["actor_id"]), limit=limit, cursor=cursor)
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


@router.get("/access-sessions/latest")
def list_latest_boxe_access_sessions(
    title_code: str | None = Query(default=None),
    site_code: str | None = Query(default=None),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    token_error = _reject_non_real_history_launch_token(
        game_launch_token=game_launch_token,
        game_code="boxe",
        player_id=str(current_user["id"]),
    )
    if token_error is not None:
        return token_error

    resolved_title_code = title_code or "boxe001"
    resolved_site_code = site_code or "casinoking"
    try:
        sessions = list_latest_access_session_history_for_user(
            user_id=str(current_user["id"]),
            title_code=resolved_title_code,
            site_code=resolved_site_code,
        )
    except BoxeApiError as exc:
        return _boxe_error(exc)

    return {
        "success": True,
        "data": sessions,
        "meta": {
            "limit": LATEST_ACCESS_SESSION_HISTORY_LIMIT,
            "title_code": resolved_title_code,
            "site_code": resolved_site_code,
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


def _resolve_optional_boxe_launch_context(
    *,
    game_launch_token: str | None,
    player_id: str,
) -> dict[str, object] | object | None:
    if not game_launch_token:
        return None

    try:
        launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_INVALID",
            message=str(exc),
        )
    except GameLaunchTokenScopeError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    if launch_context["game_code"] != "boxe":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token scope is not valid for BOXE",
        )
    if launch_context["mode"] != "real":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="BOXE authenticated start accepts only real launch tokens",
        )
    if launch_context.get("player_id") != player_id:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token ownership is not valid",
        )
    return launch_context


def _reject_non_real_history_launch_token(
    *,
    game_launch_token: str | None,
    game_code: str,
    player_id: str,
) -> object | None:
    if not game_launch_token:
        return None

    try:
        launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_INVALID",
            message=str(exc),
        )
    except GameLaunchTokenScopeError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    if launch_context["game_code"] != game_code:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token scope is not valid for this history endpoint",
        )
    if launch_context["mode"] != "real":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Latest access session history is available only for real mode",
        )
    if launch_context.get("player_id") != player_id:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token ownership is not valid",
        )
    return None


def _map_exception(exc: Exception) -> object:
    if isinstance(exc, BoxeApiError):
        return _boxe_error(exc)
    if isinstance(exc, repository.BoxeIdempotencyConflict):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, BoxePlatformIdempotencyConflictError):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, BoxePlatformInsufficientBalanceError):
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    if isinstance(exc, BoxePlatformValidationError):
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
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
