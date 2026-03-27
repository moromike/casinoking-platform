from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin, get_current_user
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
    MinesValidationError,
)
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
from app.modules.platform.game_launch.service import (
    GameLaunchTokenValidationError,
    issue_game_launch_token,
    validate_game_launch_token,
)

router = APIRouter(prefix="/games/mines", tags=["games-mines"])


class StartSessionRequest(BaseModel):
    grid_size: int
    mine_count: int
    bet_amount: str
    wallet_type: str


class RevealRequest(BaseModel):
    game_session_id: str
    cell_index: int


class CashoutRequest(BaseModel):
    game_session_id: str


class GameLaunchIssueRequest(BaseModel):
    game_code: str


class GameLaunchValidateRequest(BaseModel):
    game_launch_token: str


def _validate_optional_game_launch_token(
    *,
    game_launch_token: str | None,
    current_user: dict[str, object],
) -> dict[str, object] | None | object:
    if not game_launch_token:
        return None
    try:
        launch_context = validate_game_launch_token(
            game_launch_token=game_launch_token,
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    if launch_context["player_id"] != str(current_user["id"]):
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Game launch token ownership is not valid",
        )
    return launch_context


@router.get("/config")
def get_config() -> dict[str, object]:
    return {
        "success": True,
        "data": get_runtime_config(),
    }


@router.get("/fairness/current")
def get_current_fairness() -> dict[str, object]:
    return {
        "success": True,
        "data": get_current_fairness_config(),
    }


@router.get("/sessions")
def list_mines_sessions(
    current_user: dict[str, object] | object = Depends(get_current_user),
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
    current_user: dict[str, object] | object = Depends(get_current_user),
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
    launch_context = _validate_optional_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if launch_context is not None and not isinstance(launch_context, dict):
        return launch_context

    try:
        result = start_session(
            user_id=str(current_user["id"]),
            idempotency_key=idempotency_key,
            grid_size=payload.grid_size,
            mine_count=payload.mine_count,
            bet_amount=payload.bet_amount,
            wallet_type=payload.wallet_type,
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
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = issue_game_launch_token(
            player_id=str(current_user["id"]),
            role=str(current_user["role"]),
            game_code=payload.game_code,
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

    return {
        "success": True,
        "data": result,
    }


@router.post("/reveal")
def reveal_mines_cell(
    payload: RevealRequest,
    current_user: dict[str, object] | object = Depends(get_current_user),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _validate_optional_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if launch_context is not None and not isinstance(launch_context, dict):
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
    current_user: dict[str, object] | object = Depends(get_current_user),
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
    launch_context = _validate_optional_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if launch_context is not None and not isinstance(launch_context, dict):
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
    current_user: dict[str, object] | object = Depends(get_current_user),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _validate_optional_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if launch_context is not None and not isinstance(launch_context, dict):
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
    current_user: dict[str, object] | object = Depends(get_current_user),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user
    launch_context = _validate_optional_game_launch_token(
        game_launch_token=game_launch_token,
        current_user=current_user,
    )
    if launch_context is not None and not isinstance(launch_context, dict):
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
