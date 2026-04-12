from fastapi import APIRouter, Depends, Header, Query, Request, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin, require_admin_area
from app.api.responses import error_response
from app.modules.auth.service import (
    AuthConflictError,
    AuthForbiddenError,
    AuthInvalidCredentialsError,
    AuthValidationError,
    authenticate_user,
)
from app.modules.games.mines.backoffice_config import (
    MinesBackofficeValidationError,
    get_admin_backoffice_config,
    publish_admin_backoffice_config,
    update_admin_backoffice_draft,
)
from app.modules.admin.service import (
    AdminIdempotencyConflictError,
    AdminInsufficientBalanceError,
    AdminNotFoundError,
    AdminValidationError,
    change_admin_password,
    create_admin_user,
    create_bonus_grant,
    create_wallet_adjustment,
    get_access_logs_for_admin,
    get_admin_profile,
    get_financial_session_detail,
    get_financial_sessions_report,
    get_ledger_report_for_admin,
    get_player_detail_for_admin,
    list_admins_for_superadmin,
    list_users_for_admin,
    reset_admin_password_for_superadmin,
    reset_player_password_for_admin,
    suspend_user_for_admin,
    update_admin_last_login,
    update_admin_profile,
)
from app.modules.platform.access_logs import record_access_log

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminAdjustmentRequest(BaseModel):
    wallet_type: str
    direction: str
    amount: str
    reason: str


class BonusGrantRequest(BaseModel):
    amount: str
    reason: str


class ModeUiLabelsRequest(BaseModel):
    bet: str
    bet_loading: str
    collect: str
    collect_loading: str
    home: str
    fullscreen: str
    game_info: str


class BoardAssetsRequest(BaseModel):
    safe_icon_data_url: str | None = None
    mine_icon_data_url: str | None = None


class MinesBackofficeConfigRequest(BaseModel):
    rules_sections: dict[str, str]
    published_grid_sizes: list[int]
    published_mine_counts: dict[str, list[int]]
    default_mine_counts: dict[str, int]
    ui_labels: dict[str, ModeUiLabelsRequest]
    board_assets: BoardAssetsRequest


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CreateAdminRequest(BaseModel):
    email: str
    password: str
    is_superadmin: bool = False
    areas: list[str] = []


class UpdateAdminProfileRequest(BaseModel):
    is_superadmin: bool
    areas: list[str]


class FinancialSessionEventResponse(BaseModel):
    ledger_transaction_id: str
    platform_round_id: str
    timestamp: str
    transaction_type: str
    wallet_type: str
    bank_credit: str
    bank_debit: str
    delta: str
    game_enrichment: str


class FinancialSessionSummaryResponse(BaseModel):
    session_id: str
    is_legacy: bool
    user_id: str
    user_email: str
    game_code: str
    started_at: str
    ended_at: str
    status: str
    total_transactions: int
    bank_total_credit: str
    bank_total_debit: str
    bank_delta: str


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int


class PageTotals(BaseModel):
    bank_delta: str


class FinancialSessionsReportResponse(BaseModel):
    sessions: list[FinancialSessionSummaryResponse]
    pagination: PaginationMeta
    page_totals: PageTotals
    summary: dict[str, str]


class FinancialSessionDetailResponse(BaseModel):
    session_id: str
    is_legacy: bool
    user_id: str
    user_email: str
    game_code: str
    started_at: str
    ended_at: str
    status: str
    bank_total_credit: str
    bank_total_debit: str
    bank_delta: str
    events: list[FinancialSessionEventResponse]


# ─── Auth endpoints ────────────────────────────────────────────────────────────

@router.post("/auth/login")
def login_admin(payload: AdminLoginRequest, request: Request) -> dict[str, object] | object:
    try:
        result = authenticate_user(
            email=payload.email,
            password=payload.password,
            required_role="admin",
        )
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthInvalidCredentialsError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except AuthForbiddenError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    update_admin_last_login(admin_id=str(result["user_id"]))
    record_access_log(
        user_id=str(result["user_id"]),
        user_email=str(result["email"]),
        user_role="admin",
        ip_address=ip,
    )
    return {
        "success": True,
        "data": result,
    }


@router.get("/auth/me")
def get_current_admin_me(
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    """Return the current admin's profile including is_superadmin and areas."""
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": {
            "id": str(current_admin["id"]),
            "email": current_admin["email"],
            "role": current_admin["role"],
            "status": current_admin["status"],
            "is_superadmin": current_admin.get("is_superadmin", True),
            "areas": current_admin.get("areas", []),
        },
    }


@router.post("/auth/password/change")
def change_current_admin_password(
    payload: AdminChangePasswordRequest,
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = change_admin_password(
            admin_id=str(current_admin["id"]),
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthInvalidCredentialsError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except AuthForbiddenError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


# ─── Admin management (superadmin only) ────────────────────────────────────────

@router.post("/admins")
def create_new_admin(
    payload: CreateAdminRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("superadmin")),
) -> dict[str, object] | object:
    """Create a new admin user. Requires superadmin."""
    if not isinstance(current_admin, dict):
        return current_admin

    # Extra guard: only superadmin can create admins
    if not current_admin.get("is_superadmin", False):
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only superadmin can create new admin accounts",
        )

    try:
        result = create_admin_user(
            email=payload.email,
            password=payload.password,
            is_superadmin=payload.is_superadmin,
            areas=payload.areas,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.put("/admins/{target_admin_id}/profile")
def update_admin_profile_endpoint(
    target_admin_id: str,
    payload: UpdateAdminProfileRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("superadmin")),
) -> dict[str, object] | object:
    """Update is_superadmin and areas for an admin. Requires superadmin."""
    if not isinstance(current_admin, dict):
        return current_admin

    if not current_admin.get("is_superadmin", False):
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only superadmin can update admin profiles",
        )

    try:
        result = update_admin_profile(
            user_id=target_admin_id,
            is_superadmin=payload.is_superadmin,
            areas=payload.areas,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/admins")
def list_admins(
    email: str | None = Query(default=None),
    current_admin: dict[str, object] | object = Depends(require_admin_area("superadmin")),
) -> dict[str, object] | object:
    """List all admin users. Only superadmin can access this."""
    if not isinstance(current_admin, dict):
        return current_admin

    if not current_admin.get("is_superadmin", False):
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only superadmin can list admins",
        )

    return {
        "success": True,
        "data": list_admins_for_superadmin(email_query=email),
    }


class AdminResetAdminPasswordRequest(BaseModel):
    new_password: str


@router.post("/admins/{target_admin_id}/password-reset")
def reset_admin_password(
    target_admin_id: str,
    payload: AdminResetAdminPasswordRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("superadmin")),
) -> dict[str, object] | object:
    """Force-reset another admin's password. Only superadmin."""
    if not isinstance(current_admin, dict):
        return current_admin

    if not current_admin.get("is_superadmin", False):
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only superadmin can reset admin passwords",
        )

    try:
        result = reset_admin_password_for_superadmin(
            superadmin_id=str(current_admin["id"]),
            target_admin_id=target_admin_id,
            new_password=payload.new_password,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


# ─── User management (End-User area) ──────────────────────────────────────────

@router.get("/users")
def list_users(
    email: str | None = Query(default=None),
    current_admin: dict[str, object] | object = Depends(require_admin_area("end_user")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": list_users_for_admin(email_query=email),
    }


@router.post("/users/{target_user_id}/suspend")
def suspend_user(
    target_user_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("end_user")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = suspend_user_for_admin(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/users/{target_user_id}")
def get_user_detail(
    target_user_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("end_user")),
) -> dict[str, object] | object:
    """Return full detail of a single player, including PII fields."""
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = get_player_detail_for_admin(player_id=target_user_id)
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


class AdminResetPlayerPasswordRequest(BaseModel):
    new_password: str


@router.post("/users/{target_user_id}/password-reset")
def reset_player_password(
    target_user_id: str,
    payload: AdminResetPlayerPasswordRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("end_user")),
) -> dict[str, object] | object:
    """Force-reset a player's password without requiring the old one."""
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = reset_player_password_for_admin(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
            new_password=payload.new_password,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


# ─── Access logs ──────────────────────────────────────────────────────────────

@router.get("/access-logs")
def get_access_logs(
    role: str | None = Query(default=None),
    email: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50),
    current_admin: dict[str, object] | object = Depends(require_admin_area("end_user")),
) -> dict[str, object] | object:
    """Return paginated access logs. Admin logs visible only to superadmin."""
    if not isinstance(current_admin, dict):
        return current_admin

    # Non-superadmin can only see player logs
    effective_role = role
    if not current_admin.get("is_superadmin", False):
        effective_role = "player"

    result = get_access_logs_for_admin(
        user_role=effective_role,
        email_query=email,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    return {
        "success": True,
        "data": result,
    }


# ─── Finance area ──────────────────────────────────────────────────────────────

@router.get("/reports/ledger")
def get_ledger_report(
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": get_ledger_report_for_admin(),
    }


@router.get("/reports/financial/sessions")
def get_financial_sessions(
    user_id: str | None = Query(default=None),
    email: str | None = Query(default=None),
    email_query: str | None = Query(default=None),
    wallet_type: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50),
    transaction_type: str | None = Query(default=None),
    min_delta: str | None = Query(default=None),
    max_delta: str | None = Query(default=None),
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = get_financial_sessions_report(
            user_id=user_id,
            email_query=email_query if email_query is not None else email,
            wallet_type=wallet_type,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
            transaction_type=transaction_type,
            min_delta=min_delta,
            max_delta=max_delta,
        )
        FinancialSessionsReportResponse.model_validate(result)
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/reports/financial/sessions/{session_id}")
def get_financial_session(
    session_id: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = get_financial_session_detail(session_id=session_id)
        FinancialSessionDetailResponse.model_validate(result)
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/users/{target_user_id}/adjustments")
def create_adjustment(
    target_user_id: str,
    payload: AdminAdjustmentRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
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
        result = create_wallet_adjustment(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
            idempotency_key=idempotency_key,
            wallet_type=payload.wallet_type,
            direction=payload.direction,
            amount=payload.amount,
            reason=payload.reason,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AdminInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except AdminIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/users/{target_user_id}/bonus-grants")
def create_bonus(
    target_user_id: str,
    payload: BonusGrantRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("finance")),
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
        result = create_bonus_grant(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
            idempotency_key=idempotency_key,
            amount=payload.amount,
            reason=payload.reason,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AdminInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except AdminIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


# ─── Mines backoffice (Mines area) ────────────────────────────────────────────

@router.get("/games/mines/backoffice-config")
def get_mines_backoffice_config(
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": get_admin_backoffice_config(),
    }


@router.put("/games/mines/backoffice-config")
def put_mines_backoffice_config(
    payload: MinesBackofficeConfigRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = update_admin_backoffice_draft(
            admin_user_id=str(current_admin["id"]),
            rules_sections=payload.rules_sections,
            published_grid_sizes=payload.published_grid_sizes,
            published_mine_counts=payload.published_mine_counts,
            default_mine_counts=payload.default_mine_counts,
            ui_labels={
                mode: labels.model_dump()
                for mode, labels in payload.ui_labels.items()
            },
            board_assets=payload.board_assets.model_dump(),
        )
    except MinesBackofficeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/games/mines/backoffice-config/publish")
def publish_mines_backoffice_config(
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = publish_admin_backoffice_config(
            admin_user_id=str(current_admin["id"]),
        )
    except MinesBackofficeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }
