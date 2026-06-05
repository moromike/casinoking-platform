from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player, require_admin_area
from app.api.responses import error_response
from app.modules.games.hi_lo import repository
from app.modules.games.hi_lo.round_gateway import (
    HiLoPlatformIdempotencyConflictError,
    HiLoPlatformInsufficientBalanceError,
    HiLoPlatformValidationError,
)
from app.modules.games.hi_lo.service import (
    DEFAULT_HISTORY_LIMIT,
    LATEST_ACCESS_SESSION_HISTORY_LIMIT,
    MAX_HISTORY_LIMIT,
    HiLoApiError,
    HiLoCursorError,
    cashout_round,
    get_active_round,
    get_public_config,
    get_round_replay,
    get_round_replay_for_admin,
    get_session,
    list_latest_access_session_history_for_user,
    list_sessions,
    predict_round,
    skip_round,
    start_round,
)
from app.modules.games.hi_lo.state_machine import HiLoStateTransitionError
from app.modules.platform.access_sessions.service import (
    AccessSessionNotFoundError,
    AccessSessionStateConflictError,
    AccessSessionValidationError,
    AccessSessionVoidedByOperatorError,
    ensure_access_session_active_for_round_start,
)
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
)
from app.modules.platform.game_launch.service import (
    GameLaunchTokenOwnershipError,
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    issue_game_launch_token,
    validate_game_launch_token,
    validate_required_game_launch_token_for_player,
)

router = APIRouter(prefix="/games/hi-lo", tags=["games-hi-lo"])


class StartRoundRequest(BaseModel):
    title_code: str
    bet_amount: str
    wallet_source: str
    client_seed: str | None = None
    table_session_id: str | None = None
    access_session_id: str | None = None


class PredictRequest(BaseModel):
    round_id: str
    action: str


class SkipRequest(BaseModel):
    round_id: str


class CashoutRequest(BaseModel):
    round_id: str


class GameLaunchIssueRequest(BaseModel):
    game_code: str | None = None
    title_code: str | None = None
    site_code: str | None = None
    mode: str | None = None


@router.get("/config")
def hi_lo_config(title_code: str | None = Query(default=None)) -> dict[str, object] | object:
    try:
        return {"success": True, "data": get_public_config(title_code=title_code)}
    except HiLoApiError as exc:
        return _hi_lo_error(exc)


@router.post("/launch-token")
def issue_hi_lo_launch_token(
    payload: GameLaunchIssueRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    game_code = (payload.game_code or "hi_lo").strip().lower()
    if game_code != "hi_lo":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="HI-LO launch endpoint can issue only HI-LO launch tokens",
        )
    mode = (payload.mode or "real").strip().lower()
    if mode != "real":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="HI-LO player launch tokens are available only for real mode",
        )

    try:
        result = issue_game_launch_token(
            player_id=str(current_user["id"]),
            role=str(current_user["role"]),
            game_code="hi_lo",
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


@router.post("/start")
def hi_lo_start(
    payload: StartRoundRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error

    is_demo = payload.wallet_source.strip().lower() == "demo"
    if is_demo and game_launch_token is not None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Demo rounds cannot have a launch token",
        )
    if is_demo and payload.access_session_id is not None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Demo rounds cannot have an access session",
        )
    launch_title_code = payload.title_code
    launch_site_code = "casinoking"
    if not is_demo:
        launch_context = _resolve_required_hi_lo_launch_context(
            game_launch_token=game_launch_token,
            player_id=str(current_user["id"]),
        )
        if not isinstance(launch_context, dict):
            return launch_context
        launch_title_code = str(launch_context["title_code"])
        launch_site_code = str(launch_context["site_code"])

    if not is_demo and payload.access_session_id is None:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Access session is required for real mode",
        )

    if payload.access_session_id is not None:
        try:
            ensure_access_session_active_for_round_start(
                user_id=str(current_user["id"]),
                access_session_id=payload.access_session_id,
                game_code="hi_lo",
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
            player_id=str(current_user["id"]),
            title_code=launch_title_code,
            site_code=launch_site_code,
            bet_amount=payload.bet_amount,
            wallet_source=payload.wallet_source,
            client_seed=payload.client_seed,
            idempotency_key=str(idempotency_key),
            table_session_id=payload.table_session_id,
            access_session_id=payload.access_session_id,
        )
    except Exception as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/predict")
def hi_lo_predict(
    payload: PredictRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = predict_round(
            player_id=str(current_user["id"]),
            round_id=payload.round_id,
            action=payload.action,
            idempotency_key=str(idempotency_key),
        )
    except Exception as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/skip")
def hi_lo_skip(
    payload: SkipRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    key_error = _require_idempotency_key(idempotency_key)
    if key_error is not None:
        return key_error
    try:
        result = skip_round(
            player_id=str(current_user["id"]),
            round_id=payload.round_id,
            idempotency_key=str(idempotency_key),
        )
    except Exception as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.post("/cashout")
def hi_lo_cashout(
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
    except Exception as exc:
        return _map_exception(exc)
    return {"success": True, "data": result.response}


@router.get("/session/{session_id}")
def hi_lo_session(
    session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        return {"success": True, "data": get_session(player_id=str(current_user["id"]), session_id=session_id)}
    except HiLoApiError as exc:
        return _hi_lo_error(exc)


@router.get("/active-round")
def hi_lo_active_round(
    title_code: str = Query(default="hilo001", min_length=1),
    wallet_source: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        return {
            "success": True,
            "data": get_active_round(
                player_id=str(current_user["id"]),
                title_code=title_code,
                wallet_source=wallet_source,
            ),
        }
    except HiLoApiError as exc:
        return _hi_lo_error(exc)


@router.get("/round/{round_id}/replay")
def hi_lo_replay(
    round_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        return {"success": True, "data": get_round_replay(player_id=str(current_user["id"]), round_id=round_id)}
    except HiLoApiError as exc:
        return _hi_lo_error(exc)


@router.get("/admin/round/{round_id}/replay")
def hi_lo_admin_replay(
    round_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    try:
        return {"success": True, "data": get_round_replay_for_admin(round_id=round_id)}
    except HiLoApiError as exc:
        return _hi_lo_error(exc)


@router.get("/sessions")
def hi_lo_sessions(
    limit: int = Query(default=DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    try:
        page = list_sessions(player_id=str(current_user["id"]), limit=limit, cursor=cursor)
    except HiLoCursorError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except HiLoApiError as exc:
        return _hi_lo_error(exc)
    return {
        "success": True,
        "data": page["items"],
        "meta": {
            "next_cursor": page["next_cursor"],
            "limit": page["limit"],
        },
    }


@router.get("/access-sessions/latest")
def list_latest_hi_lo_access_sessions(
    title_code: str | None = Query(default=None),
    site_code: str | None = Query(default=None),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    token_error = _reject_non_real_history_launch_token(
        game_launch_token=game_launch_token,
        game_code="hi_lo",
        player_id=str(current_user["id"]),
    )
    if token_error is not None:
        return token_error

    resolved_title_code = title_code or "hilo001"
    resolved_site_code = site_code or "casinoking"
    try:
        sessions = list_latest_access_session_history_for_user(
            user_id=str(current_user["id"]),
            title_code=resolved_title_code,
            site_code=resolved_site_code,
        )
    except HiLoApiError as exc:
        return _hi_lo_error(exc)

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


def _resolve_required_hi_lo_launch_context(
    *,
    game_launch_token: str | None,
    player_id: str,
) -> dict[str, object] | object:
    if not game_launch_token:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )

    try:
        launch_context = validate_required_game_launch_token_for_player(
            game_launch_token=game_launch_token,
            player_id=player_id,
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_INVALID",
            message=str(exc),
        )
    except (GameLaunchTokenOwnershipError, GameLaunchTokenScopeError) as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    if launch_context["game_code"] != "hi_lo":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token scope is not valid for HI-LO",
        )
    if launch_context["mode"] != "real":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="HI-LO start accepts only real launch tokens",
        )
    return launch_context


def _map_exception(exc: Exception) -> object:
    if isinstance(exc, HiLoApiError):
        return _hi_lo_error(exc)
    if isinstance(exc, repository.HiLoIdempotencyConflict):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, DemoWalletIdempotencyConflictError):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, HiLoPlatformIdempotencyConflictError):
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, (HiLoPlatformInsufficientBalanceError, DemoWalletInsufficientBalanceError)):
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    if isinstance(exc, (HiLoPlatformValidationError, DemoWalletValidationError, ValueError)):
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    if isinstance(exc, HiLoStateTransitionError):
        code = "ROUND_ALREADY_CLOSED" if "terminal" in exc.reason else "ACTION_NOT_ALLOWED"
        status_code = status.HTTP_409_CONFLICT if code == "ROUND_ALREADY_CLOSED" else status.HTTP_422_UNPROCESSABLE_ENTITY
        return error_response(status_code=status_code, code=code, message=str(exc))
    if isinstance(exc, KeyError):
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROUND_NOT_FOUND",
            message=str(exc),
        )
    raise exc


def _hi_lo_error(exc: HiLoApiError) -> object:
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )
