from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin, get_current_player, require_admin_area
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
    cashout_demo_session,
    demo_session_exists,
    DEFAULT_SESSION_HISTORY_LIMIT,
    get_demo_session_fairness_for_anonymous,
    get_demo_session_for_anonymous,
    get_demo_session_replay_for_anonymous,
    list_latest_access_session_history_for_user,
    list_session_history_page_for_user,
    MAX_SESSION_HISTORY_LIMIT,
    MinesSessionCursorError,
    get_session_replay_for_admin,
    get_session_replay_for_user,
    get_session_fairness_for_user,
    get_session_for_user,
    reveal_demo_cell,
    reveal_cell,
    session_belongs_to_user,
    session_exists,
    start_demo_session,
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
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_published_title_for_launch,
)
from app.modules.platform.catalog.title_locale_service import (
    flatten_locale_rule_sections,
    TitleLocaleNotFoundError,
    TitleLocaleValidationError,
    resolve_title_locale_bundle,
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
    wallet_source: str | None = None


class CashoutRequest(BaseModel):
    game_session_id: str
    wallet_source: str | None = None


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


def _resolve_actor_and_launch_context(
    *,
    game_launch_token: str | None,
    authorization: str | None,
    allow_real_without_token: bool = False,
) -> dict[str, object] | object:
    if not game_launch_token:
        # NEW (B1): real players can use reveal/cashout without launch token.
        # Authorization is still required; ownership is enforced by service layer.
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
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )

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

    if launch_context["mode"] == "demo":
        return {
            "mode": "demo",
            "actor_id": str(launch_context["anonymous_id"]),
            "current_user": None,
            "launch_context": launch_context,
        }

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


@router.get("/config")
def get_config(
    title_code: str | None = Query(default=None),
    site_code: str | None = Query(default=None),
) -> dict[str, object] | object:
    resolved_title_code = title_code or "mines_classic"
    resolved_site_code = site_code or "casinoking"
    try:
        title = get_published_title_for_launch(
            site_code=resolved_site_code,
            title_code=resolved_title_code,
        )
    except CatalogNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except CatalogValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    if title["engine_code"] != "mines":
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Title engine is not valid for Mines config",
        )
    runtime_config = get_runtime_config()
    presentation_config = get_public_backoffice_config(
        title_code=resolved_title_code,
    )
    try:
        locale_bundle = resolve_title_locale_bundle(
            title_code=resolved_title_code,
        )
        presentation_config["i18n"] = locale_bundle
        presentation_config["rules_sections"] = flatten_locale_rule_sections(
            locale_bundle.get("rules_sections", {}),
        )
    except TitleLocaleNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except TitleLocaleValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    runtime_config["presentation_config"] = presentation_config
    runtime_config["title_code"] = resolved_title_code
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
    limit: int = Query(
        default=DEFAULT_SESSION_HISTORY_LIMIT,
        ge=1,
        le=MAX_SESSION_HISTORY_LIMIT,
    ),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        page = list_session_history_page_for_user(
            user_id=str(current_user["id"]),
            limit=limit,
            cursor=cursor,
        )
    except MinesSessionCursorError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": page["items"],
        "meta": {
            "next_cursor": page["next_cursor"],
            "limit": page["limit"],
        },
    }


@router.get("/access-sessions/latest")
def list_latest_mines_access_sessions(
    title_code: str | None = Query(default=None),
    site_code: str | None = Query(default=None),
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    actor_context = _resolve_actor_and_launch_context(
        game_launch_token=game_launch_token,
        authorization=authorization,
        allow_real_without_token=True,
    )
    if not isinstance(actor_context, dict):
        return actor_context

    if actor_context["mode"] != "real":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Latest access session history is available only for authenticated players",
        )

    current_user = actor_context["current_user"]
    assert isinstance(current_user, dict)
    launch_context = actor_context.get("launch_context")
    resolved_title_code = (
        str(launch_context["title_code"])
        if launch_context
        else (title_code or "mines_classic")
    )
    resolved_site_code = (
        str(launch_context["site_code"])
        if launch_context
        else (site_code or "casinoking")
    )
    sessions = list_latest_access_session_history_for_user(
        user_id=str(current_user["id"]),
        title_code=resolved_title_code,
        site_code=resolved_site_code,
    )

    return {
        "success": True,
        "data": sessions,
        "meta": {
            "limit": 3,
            "title_code": resolved_title_code,
            "site_code": resolved_site_code,
        },
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )
    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
        )
        if not isinstance(actor_context, dict):
            return actor_context
        launch_context = actor_context["launch_context"]

        if actor_context["mode"] == "demo":
            if payload.access_session_id is not None:
                return error_response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="VALIDATION_ERROR",
                    message="Demo rounds cannot have an access session",
                )
            try:
                result = start_demo_session(
                    user_id=str(actor_context["actor_id"]),
                    idempotency_key=idempotency_key,
                    grid_size=payload.grid_size,
                    mine_count=payload.mine_count,
                    bet_amount=payload.bet_amount,
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

        if payload.access_session_id is None:
            return error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="Access session is required for real mode",
            )
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

    # Token-less path (B3): bearer + wallet_type discriminates demo vs real
    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if payload.wallet_type == "demo":
        if payload.access_session_id is not None:
            return error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="Demo rounds cannot have an access session",
            )
        try:
            result = start_demo_session(
                user_id=str(current_user["id"]),
                idempotency_key=idempotency_key,
                grid_size=payload.grid_size,
                mine_count=payload.mine_count,
                bet_amount=payload.bet_amount,
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

    return error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="GAME_LAUNCH_TOKEN_REQUIRED",
        message="X-Game-Launch-Token header is required for real mode",
    )


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
            code=exc.code,
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context

        if actor_context["mode"] == "demo":
            try:
                result = reveal_demo_cell(
                    user_id=str(actor_context["actor_id"]),
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
                if demo_session_exists(payload.game_session_id):
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

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

    # Token-less path (B3): bearer + wallet_source discriminates demo vs real
    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if payload.wallet_source == "demo":
        try:
            result = reveal_demo_cell(
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
            if demo_session_exists(payload.game_session_id):
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
) -> dict[str, object] | object:
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )

    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context

        if actor_context["mode"] == "demo":
            try:
                result = cashout_demo_session(
                    user_id=str(actor_context["actor_id"]),
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

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

    # Token-less path (B3): bearer + wallet_source discriminates demo vs real
    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="Idempotency-Key header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if payload.wallet_source == "demo":
        try:
            result = cashout_demo_session(
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


@router.get("/session/{session_id}/replay")
def get_mines_session_replay(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    wallet_source: str | None = Query(default=None),
) -> dict[str, object] | object:
    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context

        if actor_context["mode"] == "demo":
            result = get_demo_session_replay_for_anonymous(
                user_id=str(actor_context["actor_id"]),
                session_id=session_id,
            )
            if result is None:
                if demo_session_exists(session_id):
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

        result = get_session_replay_for_user(
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

    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if wallet_source == "demo":
        result = get_demo_session_replay_for_anonymous(
            user_id=str(current_user["id"]),
            session_id=session_id,
        )
        if result is None:
            if demo_session_exists(session_id):
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

    result = get_session_replay_for_user(
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


@router.get("/admin/session/{session_id}/replay")
def get_mines_session_replay_for_admin(
    session_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    result = get_session_replay_for_admin(session_id=session_id)
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


@router.get("/session/{session_id}")
def get_mines_session(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    wallet_source: str | None = Query(default=None),
) -> dict[str, object] | object:
    if not game_launch_token and authorization:
        current_admin = get_current_admin(authorization)
        if isinstance(current_admin, dict):
            return _get_mines_session_for_admin(
                current_admin=current_admin,
                session_id=session_id,
            )

    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context

        if actor_context["mode"] == "demo":
            result = get_demo_session_for_anonymous(
                user_id=str(actor_context["actor_id"]),
                session_id=session_id,
            )
            if result is None:
                if demo_session_exists(session_id):
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

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

    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if wallet_source == "demo":
        result = get_demo_session_for_anonymous(
            user_id=str(current_user["id"]),
            session_id=session_id,
        )
        if result is None:
            if demo_session_exists(session_id):
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


def _get_mines_session_for_admin(
    *,
    current_admin: dict[str, object],
    session_id: str,
) -> dict[str, object] | object:
    result = get_session_for_user(
        user_id=str(current_admin["id"]),
        viewer_role="admin",
        session_id=session_id,
    )
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


@router.get("/session/{session_id}/fairness")
def get_mines_session_fairness(
    session_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token"),
    wallet_source: str | None = Query(default=None),
) -> dict[str, object] | object:
    if game_launch_token:
        actor_context = _resolve_actor_and_launch_context(
            game_launch_token=game_launch_token,
            authorization=authorization,
            allow_real_without_token=True,
        )
        if not isinstance(actor_context, dict):
            return actor_context

        if actor_context["mode"] == "demo":
            result = get_demo_session_fairness_for_anonymous(
                user_id=str(actor_context["actor_id"]),
                session_id=session_id,
            )
            if result is None:
                if demo_session_exists(session_id):
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

        current_user = actor_context["current_user"]
        assert isinstance(current_user, dict)

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

    if not authorization:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="GAME_LAUNCH_TOKEN_REQUIRED",
            message="X-Game-Launch-Token header is required",
        )
    current_user = get_current_player(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if wallet_source == "demo":
        result = get_demo_session_fairness_for_anonymous(
            user_id=str(current_user["id"]),
            session_id=session_id,
        )
        if result is None:
            if demo_session_exists(session_id):
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
