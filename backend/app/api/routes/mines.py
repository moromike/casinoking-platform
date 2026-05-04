from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin, get_current_player
from app.api.responses import error_response
from app.modules.games.mines.fairness import (
    FairnessIdempotencyConflictError,
    get_current_fairness_config,
    rotate_active_fairness_seed,
    verify_session_fairness_for_admin,
)
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesSessionVoidedByOperatorError,
    MinesValidationError,
)
from app.modules.games.mines.backoffice_config import get_public_backoffice_config
from app.modules.games.mines.service import (
    cashout_session,
    list_recent_sessions_for_user,
    get_session_fairness_for_user,
    get_session_for_user,
    reveal_cell,
    session_belongs_to_user,
    session_exists,
    start_session,
)
from app.modules.games.mines.runtime import get_runtime_config
from app.modules.platform.access_sessions.service import (
    AccessSessionNotFoundError,
    AccessSessionStateConflictError,
    AccessSessionValidationError,
    AccessSessionVoidedByOperatorError,
    ensure_access_session_active_for_round_start,
)
from app.modules.platform.game_launch.service import (
    GameLaunchTokenOwnershipError,
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    issue_game_launch_token,
    validate_game_launch_token,
    validate_required_game_launch_token_for_player,
)

router = APIRouter(prefix="/games/mines", tags=["games-mines"])


class StartSessionRequest(BaseModel):
    grid_size: int
    mine_count: int
    bet_amount: str
    wallet_type: str
    access_session_id: str | None = None
    table_session_id: str | None = None


class RevealRequest(BaseModel):
    game_session_id: str
    cell_index: int


class CashoutRequest(BaseModel):
    game_session_id: str


class GameLaunchIssueRequest(BaseModel):
    game_code: str | None = None
    title_code: str | None = None
    site_code: str | None = None
    mode: str | None = None


class GameLaunchValidateRequest(BaseModel):
    game_launch_token: str


def _resolve_required_game_launch_token(
    *,
    game_launch_token: str | None,
    current_user: dict[str, object],
) -> dict[str, object] | object:
    try:
        return validate_required_game_launch_token_for_player(
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


@router.get("/config")
def get_config() -> dict[str, object]:
    runtime_config = get_runtime_config()
    runtime_config["presentation_config"] = get_public_backoffice_config()
    return {
        "success": True,
        "data": runtime_config,
    }


@router.get("/fairness/current")
def get_current_fairness() -> dict[str, object]:
    return {
        "success": True,
        "data": get_current_fairness_config(),
    }


@router.get("/sessions")
def list_mines_sessions(
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    return {
        "success": True,
        "data": list_recent_sessions_for_user(user_id=str(current_user["id"])),
    }


@router.post("/fairness/rotate")
def rotate_mines_fairness(
    current_admin: dict[str, object] | object = Depends(get_current_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )

    try:
        result = rotate_active_fairness_seed(
            admin_user_id=str(current_admin["id"]),
            idempotency_key=idempotency_key,
        )
    except FairnessIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/start")
def start_mines_session(
    payload: StartSessionRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    launch_context = _resolve_required_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context

    if payload.access_session_id is not None:
        try:
            ensure_access_session_active_for_round_start(
                user_id=str(current_user["id"]),
                access_session_id=payload.access_session_id,
                game_code=str(launch_context["game_code"]),
                title_code=str(launch_context["title_code"]),
                site_code=str(launch_context["site_code"]),
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
        result = start_session(
            user_id=str(current_user["id"]),
            idempotency_key=idempotency_key,
            grid_size=payload.grid_size,
            mine_count=payload.mine_count,
            bet_amount=payload.bet_amount,
            wallet_type=payload.wallet_type,
            access_session_id=payload.access_session_id,
            table_session_id=payload.table_session_id,
            title_code=str(launch_context["title_code"]),
            site_code=str(launch_context["site_code"]),
        )
    except MinesValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except MinesInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except MinesIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/launch-token")
def issue_mines_launch_token(
    payload: GameLaunchIssueRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = issue_game_launch_token(
            player_id=str(current_user["id"]),
            role=str(current_user["role"]),
            game_code=payload.game_code,
            title_code=payload.title_code,
            site_code=payload.site_code,
            mode=payload.mode,
        )
    except GameLaunchTokenValidationError as exc:
        status_code = (
            status.HTTP_501_NOT_IMPLEMENTED
            if "Demo launch mode is not available" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return error_response(
            status_code=status_code,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/launch/validate")
def validate_mines_launch_token(
    payload: GameLaunchValidateRequest,
) -> dict[str, object] | object:
    try:
        result = validate_game_launch_token(
            game_launch_token=payload.game_launch_token,
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except GameLaunchTokenScopeError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/reveal")
def reveal_mines_cell(
    payload: RevealRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _resolve_required_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context

    try:
        result = reveal_cell(
            user_id=str(current_user["id"]),
            session_id=payload.game_session_id,
            cell_index=payload.cell_index,
        )
    except MinesValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except MinesSessionVoidedByOperatorError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="SESSION_VOIDED_BY_OPERATOR",
            message=str(exc),
        )
    except MinesGameStateConflictError as exc:
        if session_exists(payload.game_session_id) and not session_belongs_to_user(
            session_id=payload.game_session_id,
            user_id=str(current_user["id"]),
        ):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game session ownership is not valid",
            )
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="GAME_STATE_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/cashout")
def cashout_mines_session(
    payload: CashoutRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    launch_context = _resolve_required_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context

    try:
        result = cashout_session(
            user_id=str(current_user["id"]),
            session_id=payload.game_session_id,
            idempotency_key=idempotency_key,
        )
    except MinesValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except MinesSessionVoidedByOperatorError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="SESSION_VOIDED_BY_OPERATOR",
            message=str(exc),
        )
    except MinesGameStateConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="GAME_STATE_CONFLICT",
            message=str(exc),
        )
    except MinesIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/session/{session_id}")
def get_mines_session(
    session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _resolve_required_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context

    result = get_session_for_user(
        user_id=str(current_user["id"]),
        viewer_role=str(current_user["role"]),
        session_id=session_id,
    )
    if result is None:
        if session_exists(session_id):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game session ownership is not valid",
            )
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Game session not found",
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/session/{session_id}/fairness")
def get_mines_session_fairness(
    session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _resolve_required_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if not isinstance(launch_context, dict):
        return launch_context

    result = get_session_fairness_for_user(
        user_id=str(current_user["id"]),
        session_id=session_id,
    )
    if result is None:
        if session_exists(session_id):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game session ownership is not valid",
            )
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Game session not found",
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/verify")
def verify_mines_session_fairness(
    session_id: str = Query(...),
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    result = verify_session_fairness_for_admin(session_id=session_id)
    if result is None:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Game session not found",
        )

    return {
        "success": True,
        "data": result,
    }
