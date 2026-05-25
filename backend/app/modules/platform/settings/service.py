from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.api.errors import ERROR_REGISTRY
from app.core.config import settings
from app.modules.platform.access_sessions.service import (
    ACCESS_SESSION_TIMEOUT,
    ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
)
from app.modules.platform.game_codes import ALLOWED_GAME_CODES
from app.modules.platform.table_sessions.service import (
    TABLE_SESSION_DEFAULT_CHIPS,
    TABLE_SESSION_MAX_CHIPS,
)


SourceOfTruth = str
Visibility = str
RiskClass = str
RestartRequired = str
AuditRequired = str
MaskingRule = str

VISIBILITIES = {"hidden", "masked", "read_only", "editable_future"}
RESTART_VALUES = {"yes", "no", "unknown"}
AUDIT_VALUES = {"yes", "no", "future"}
MASKING_RULES = {"none", "full", "partial", "count_only", "hash_only"}
RISK_CLASSES = {"low", "medium", "high", "critical"}
SOURCES = {"env", "code", "db", "registry", "title_config", "document", "derived"}
STATUSES = {"ok", "gap", "pending"}


@dataclass(frozen=True)
class SettingsDescriptor:
    key: str
    label: str
    source_of_truth: SourceOfTruth
    owner: str
    visibility: Visibility
    risk_class: RiskClass
    environment_scope: str
    restart_required: RestartRequired
    audit_required: AuditRequired
    editable_now: bool
    masking_rule: MaskingRule
    evidence: str
    category: str
    status: str = "ok"
    notes: tuple[str, ...] = ()
    editable_when: str | None = None
    value_reader: Callable[[], object | None] | None = None


@dataclass(frozen=True)
class GapRisk:
    key: str
    severity: str
    impact: str
    mvp_mitigation: str
    long_term_mitigation: str
    follow_up_wp: str
    evidence: str


REPO_ROOT = Path(__file__).resolve().parents[5]


GAP_RISKS: tuple[GapRisk, ...] = (
    GapRisk(
        key="site_access.client_default",
        severity="critical",
        impact="A client-side default access password can leak an access-control secret and normalize unsafe registration behavior.",
        mvp_mitigation="Expose this row as a critical gap only. Do not fix the registration flow in this WP.",
        long_term_mitigation="Remove client-side default access password and move registration to a temporary-token or server-mediated flow.",
        follow_up_wp="WP-FRONTEND-SECRET-AUDIT",
        evidence="frontend/app/ui/player-register-page.tsx:13",
    ),
    GapRisk(
        key="health.ready_db_redis",
        severity="high",
        impact="/ready can report ready while DB or Redis dependencies are unavailable, producing false operational health.",
        mvp_mitigation="Expose the dependency-readiness limitation as a high gap. Keep /ready behavior unchanged in this WP.",
        long_term_mitigation="Add DB and Redis dependency pings to readiness and surface degraded dependency states.",
        follow_up_wp="WP-HEALTH-READINESS-DB-REDIS",
        evidence="backend/app/api/routes/health.py:17-27",
    ),
    GapRisk(
        key="auth.rbac_fallback",
        severity="critical",
        impact="Treating an admin without profile as superadmin can become privilege escalation if profile creation drifts.",
        mvp_mitigation="Expose this as a critical gap and make the Settings endpoint require an explicit superadmin profile.",
        long_term_mitigation="Remove the compatibility fallback and require explicit admin_profiles rows for admin authorization.",
        follow_up_wp="WP-AUTH-RBAC-EXPLICIT-PROFILE",
        evidence="backend/app/api/dependencies.py:89-99",
    ),
    GapRisk(
        key="cms_v2_lab.admin_token_in_query",
        severity="high",
        impact="Passing an admin token through URL query can expose it through browser history, referrers, logs, or screenshots.",
        mvp_mitigation="Expose this row as a high gap. Do not change CMS v2 lab handoff in this WP.",
        long_term_mitigation="Move the lab handoff to postMessage, a one-time server token, or an httpOnly cookie flow.",
        follow_up_wp="WP-CMS-V2-LAB-TOKEN-HANDOFF",
        evidence="frontend/app/ui/admin-shell-panel.tsx:81",
    ),
)


SETTINGS_DESCRIPTORS: tuple[SettingsDescriptor, ...] = (
    SettingsDescriptor(
        key="app.name",
        label="Application name",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="low",
        environment_scope="all",
        restart_required="yes",
        audit_required="no",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:12",
        category="Environment",
        value_reader=lambda: settings.app_name,
    ),
    SettingsDescriptor(
        key="app.version",
        label="Application version",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="low",
        environment_scope="all",
        restart_required="yes",
        audit_required="no",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:13",
        category="Environment",
        value_reader=lambda: settings.app_version,
    ),
    SettingsDescriptor(
        key="app.env",
        label="Application environment",
        source_of_truth="env",
        owner="infra",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:14",
        category="Environment",
        value_reader=lambda: settings.app_env,
    ),
    SettingsDescriptor(
        key="api.v1_prefix",
        label="API v1 prefix",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:15",
        category="Environment",
        value_reader=lambda: settings.api_v1_prefix,
    ),
    SettingsDescriptor(
        key="database.url",
        label="Database URL",
        source_of_truth="env",
        owner="infra/security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:16",
        category="Security-sensitive values",
        value_reader=lambda: settings.database_url,
    ),
    SettingsDescriptor(
        key="redis.url",
        label="Redis URL",
        source_of_truth="env",
        owner="infra/security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:20",
        category="Security-sensitive values",
        value_reader=lambda: settings.redis_url,
    ),
    SettingsDescriptor(
        key="jwt.secret",
        label="JWT secret",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:21",
        category="Security-sensitive values",
        value_reader=lambda: settings.jwt_secret,
    ),
    SettingsDescriptor(
        key="jwt.access_ttl_minutes",
        label="JWT access TTL minutes",
        source_of_truth="env",
        owner="security",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:25",
        category="Security-sensitive values",
        value_reader=lambda: settings.jwt_access_token_ttl_minutes,
    ),
    SettingsDescriptor(
        key="game_launch.token_ttl_minutes",
        label="Game launch token TTL minutes",
        source_of_truth="env",
        owner="security/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:28",
        category="Security-sensitive values",
        value_reader=lambda: settings.game_launch_token_ttl_minutes,
    ),
    SettingsDescriptor(
        key="game_launch.signing_key",
        label="Game launch signing key",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:5.1",
        category="Security-sensitive values",
        status="pending",
        notes=("No separate signing key is implemented yet; launch tokens currently depend on the JWT secret path.",),
    ),
    SettingsDescriptor(
        key="site_access.password",
        label="Site access password",
        source_of_truth="env",
        owner="security",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:31",
        category="Security-sensitive values",
        value_reader=lambda: settings.site_access_password,
    ),
    SettingsDescriptor(
        key="site_access.client_default",
        label="Client default site access password",
        source_of_truth="code",
        owner="security",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/ui/player-register-page.tsx:13",
        category="Gap risk write-up",
        status="gap",
        notes=("Frontend contains a hardcoded access password default; value intentionally not surfaced.",),
        value_reader=lambda: "present",
    ),
    SettingsDescriptor(
        key="mines.server_seed",
        label="Mines server seed",
        source_of_truth="env",
        owner="security/fairness",
        visibility="hidden",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="yes",
        editable_now=False,
        masking_rule="full",
        evidence="backend/app/core/config.py:35",
        category="Security-sensitive values",
        value_reader=lambda: settings.mines_server_seed,
    ),
    SettingsDescriptor(
        key="cors.allowed_origins",
        label="CORS allowed origins",
        source_of_truth="env",
        owner="security/infra",
        visibility="masked",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="count_only",
        evidence="backend/app/core/config.py:39",
        category="Environment",
        value_reader=lambda: settings.cors_allowed_origins,
    ),
    SettingsDescriptor(
        key="assets.storage_root",
        label="Asset storage root",
        source_of_truth="env",
        owner="platform/infra",
        visibility="masked",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="partial",
        evidence="backend/app/core/config.py:45",
        category="Environment",
        value_reader=lambda: settings.asset_storage_root,
    ),
    SettingsDescriptor(
        key="assets.public_base_url",
        label="Asset public base URL",
        source_of_truth="env",
        owner="platform",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/core/config.py:48",
        category="Environment",
        value_reader=lambda: settings.asset_public_base_url,
    ),
    SettingsDescriptor(
        key="access_session.timeout",
        label="Access session timeout",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/access_sessions/service.py:23",
        category="Session/table/recovery policy",
        value_reader=lambda: _format_timedelta_minutes(ACCESS_SESSION_TIMEOUT),
    ),
    SettingsDescriptor(
        key="access_session.sweep_interval",
        label="Access session sweep interval seconds",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/main.py:17",
        category="Session/table/recovery policy",
        value_reader=lambda: "30",
    ),
    SettingsDescriptor(
        key="access_session.sweep_limit",
        label="Access session sweep limit",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/access_sessions/service.py:24",
        category="Session/table/recovery policy",
        value_reader=lambda: ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
    ),
    SettingsDescriptor(
        key="table_session.max_chips",
        label="Table session max chips",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/table_sessions/service.py:13",
        category="Session/table/recovery policy",
        value_reader=lambda: str(TABLE_SESSION_MAX_CHIPS),
    ),
    SettingsDescriptor(
        key="table_session.default_chips",
        label="Table session default chips",
        source_of_truth="code",
        owner="finance/platform",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/table_sessions/service.py:14",
        category="Session/table/recovery policy",
        value_reader=lambda: str(TABLE_SESSION_DEFAULT_CHIPS),
    ),
    SettingsDescriptor(
        key="demo.token_rate_limit",
        label="Demo token rate limit",
        source_of_truth="code",
        owner="platform/security",
        visibility="editable_future",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/routes/demo.py:27",
        category="Security-sensitive values",
        editable_when="After a rate-limit policy and audit trail are approved.",
        value_reader=lambda: "code constant",
    ),
    SettingsDescriptor(
        key="game_registry.backends",
        label="Backend game registry",
        source_of_truth="code",
        owner="platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/game_codes.py:1",
        category="Game registry health",
        value_reader=lambda: ", ".join(ALLOWED_GAME_CODES),
    ),
    SettingsDescriptor(
        key="catalog.publication_flags",
        label="Catalog publication flags",
        source_of_truth="db",
        owner="platform/product",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="no",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/platform/catalog/admin_title_service.py",
        category="Game registry health",
        status="pending",
        notes=("Settings MVP reports the capability, not live DB catalog health.",),
        value_reader=lambda: "catalog/site_titles",
    ),
    SettingsDescriptor(
        key="health.ready_db_redis",
        label="Readiness DB/Redis checks",
        source_of_truth="derived",
        owner="infra",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/routes/health.py:17-27",
        category="Gap risk write-up",
        status="gap",
        notes=("Current /ready confirms the app process only; DB/Redis dependency checks are not implemented.",),
        value_reader=lambda: "app-only readiness",
    ),
    SettingsDescriptor(
        key="auth.rbac_fallback",
        label="Admin RBAC missing-profile fallback",
        source_of_truth="code",
        owner="security",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/dependencies.py:89-99",
        category="Gap risk write-up",
        status="gap",
        notes=("Settings endpoint explicitly does not use this fallback.",),
        value_reader=lambda: "present outside Settings",
    ),
    SettingsDescriptor(
        key="cms_v2_lab.admin_token_in_query",
        label="CMS v2 lab admin token query",
        source_of_truth="code",
        owner="security/platform",
        visibility="read_only",
        risk_class="high",
        environment_scope="local",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/ui/admin-shell-panel.tsx:81",
        category="Gap risk write-up",
        status="gap",
        notes=("Admin token is passed in a query parameter for the lab surface; raw token is not surfaced here.",),
        value_reader=lambda: "present",
    ),
    SettingsDescriptor(
        key="error_registry.status",
        label="Error registry status",
        source_of_truth="code",
        owner="platform/support",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/api/errors.py:28",
        category="Error Matrix status",
        value_reader=lambda: f"{len(ERROR_REGISTRY)} CK codes",
    ),
    SettingsDescriptor(
        key="frontend.api_base_url",
        label="Frontend API base URL",
        source_of_truth="env",
        owner="infra",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="frontend/app/lib/api.ts:9",
        category="Environment",
        value_reader=lambda: "NEXT_PUBLIC_API_BASE_URL build-time",
    ),
    SettingsDescriptor(
        key="i18n.allowed_locales",
        label="Allowed game locales",
        source_of_truth="code",
        owner="product",
        visibility="read_only",
        risk_class="medium",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/boxe/i18n_manifest.py",
        category="Environment",
        value_reader=lambda: "it, en, de, es",
    ),
    SettingsDescriptor(
        key="mines.payout_runtime_path",
        label="Mines payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/mines/runtime.py:6",
        category="Finance/replay/retention status",
        value_reader=lambda: "docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json",
    ),
    SettingsDescriptor(
        key="boxe.payout_runtime_path",
        label="BOXE payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/boxe/math.py:9",
        category="Finance/replay/retention status",
        value_reader=lambda: "backend/app/modules/games/boxe/math.py",
    ),
    SettingsDescriptor(
        key="hi_lo.payout_runtime_path",
        label="HI-LO payout runtime path",
        source_of_truth="code",
        owner="finance",
        visibility="read_only",
        risk_class="critical",
        environment_scope="all",
        restart_required="yes",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="backend/app/modules/games/hi_lo/math.py:10",
        category="Finance/replay/retention status",
        value_reader=lambda: "backend/app/modules/games/hi_lo/math.py",
    ),
    SettingsDescriptor(
        key="finance.replay_retention",
        label="Finance replay retention",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:180",
        category="Finance/replay/retention status",
        value_reader=lambda: "online 30 days; cold storage TBD legal",
    ),
    SettingsDescriptor(
        key="replay.retention_online_days",
        label="Replay retention online days",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:180",
        category="Finance/replay/retention status",
        value_reader=lambda: "30",
    ),
    SettingsDescriptor(
        key="replay.retention_cold_storage",
        label="Replay retention cold storage",
        source_of_truth="document",
        owner="finance/legal",
        visibility="read_only",
        risk_class="high",
        environment_scope="all",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:181",
        category="Finance/replay/retention status",
        status="pending",
        notes=("Cold-storage duration is a legal decision, not an MVP runtime setting.",),
        value_reader=lambda: "TBD legal",
    ),
    SettingsDescriptor(
        key="crypto_wallet.enabled",
        label="Crypto wallet enabled",
        source_of_truth="document",
        owner="product",
        visibility="editable_future",
        risk_class="critical",
        environment_scope="production",
        restart_required="unknown",
        audit_required="future",
        editable_now=False,
        masking_rule="none",
        evidence="docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md:5.1",
        category="Finance/replay/retention status",
        status="pending",
        editable_when="After a dedicated production crypto wallet, compliance, ledger and custody plan.",
        value_reader=lambda: "future phase 2 production",
    ),
)


CAPABILITY_MATRIX: tuple[dict[str, str], ...] = (
    {
        "capability": "Descriptor contract",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "read",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Code-backed read-only list with mandatory metadata.",
    },
    {
        "capability": "Backend read model superadmin-only",
        "db": "read admin_profiles",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "consume",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Requires explicit admin profile with is_superadmin true.",
    },
    {
        "capability": "Frontend Platform Settings UI",
        "db": "n/a",
        "backend": "consume",
        "api_payload": "parse",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "No editable inputs, no save, no publish.",
    },
    {
        "capability": "Game registry health",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Backend game_codes.py is MVP source of truth; adapters can be pending.",
    },
    {
        "capability": "Error Matrix placeholder",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "NEW",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "WP1 registry is present, so CK.* rows are surfaced read-only.",
    },
    {
        "capability": "Gap risk write-up doc",
        "db": "n/a",
        "backend": "NEW",
        "api_payload": "NEW",
        "admin_ui": "NEW",
        "player_ui": "n/a",
        "css": "n/a",
        "test": "NEW",
        "docs": "UPDATE",
        "status": "complete",
        "notes": "Four CTO-mandated gaps include severity and follow-up WP.",
    },
)


def build_platform_settings_inventory() -> dict[str, object]:
    validate_descriptor_contract()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "contract": {
            "required_fields": [
                "key",
                "label",
                "source_of_truth",
                "owner",
                "visibility",
                "risk_class",
                "environment_scope",
                "restart_required",
                "audit_required",
                "editable_now",
                "masking_rule",
                "evidence",
            ],
            "visibility_values": sorted(VISIBILITIES),
            "masking_rule_values": sorted(MASKING_RULES),
        },
        "summary": _build_summary(),
        "inventory": [_serialize_descriptor(descriptor) for descriptor in SETTINGS_DESCRIPTORS],
        "gap_risks": [_serialize_gap(gap) for gap in GAP_RISKS],
        "game_registry_health": build_game_registry_health(),
        "error_matrix": build_error_matrix(),
        "capability_matrix": list(CAPABILITY_MATRIX),
    }


def validate_descriptor_contract() -> None:
    keys: set[str] = set()
    for descriptor in SETTINGS_DESCRIPTORS:
        if descriptor.key in keys:
            raise ValueError(f"Duplicate platform settings descriptor key: {descriptor.key}")
        keys.add(descriptor.key)

        for field_name in (
            "key",
            "label",
            "source_of_truth",
            "owner",
            "visibility",
            "risk_class",
            "environment_scope",
            "restart_required",
            "audit_required",
            "masking_rule",
            "evidence",
            "category",
        ):
            if not getattr(descriptor, field_name):
                raise ValueError(f"{descriptor.key} is missing required field {field_name}")
        if descriptor.source_of_truth not in SOURCES:
            raise ValueError(f"{descriptor.key} has invalid source_of_truth")
        if descriptor.visibility not in VISIBILITIES:
            raise ValueError(f"{descriptor.key} has invalid visibility")
        if descriptor.risk_class not in RISK_CLASSES:
            raise ValueError(f"{descriptor.key} has invalid risk_class")
        if descriptor.restart_required not in RESTART_VALUES:
            raise ValueError(f"{descriptor.key} has invalid restart_required")
        if descriptor.audit_required not in AUDIT_VALUES:
            raise ValueError(f"{descriptor.key} has invalid audit_required")
        if descriptor.masking_rule not in MASKING_RULES:
            raise ValueError(f"{descriptor.key} has invalid masking_rule")
        if descriptor.status not in STATUSES:
            raise ValueError(f"{descriptor.key} has invalid status")
        if descriptor.editable_now is not False:
            raise ValueError(f"{descriptor.key} must not be editable in the MVP")
        if descriptor.visibility == "editable_future" and not descriptor.editable_when:
            raise ValueError(f"{descriptor.key} is editable_future without editable_when")


def build_game_registry_health() -> list[dict[str, object]]:
    return [_build_game_health(game_code) for game_code in ALLOWED_GAME_CODES]


def build_error_matrix() -> dict[str, object]:
    codes = [
        {
            "code": definition.code,
            "http_status": definition.http_status,
            "message": definition.message,
            "retryable": definition.retryable,
            "log_level": definition.log_level,
        }
        for definition in sorted(ERROR_REGISTRY.values(), key=lambda item: item.code)
        if definition.code.startswith("CK.")
    ]
    return {
        "status": "available" if codes else "pending",
        "source": "backend/app/api/errors.py",
        "codes": codes,
        "notes": [] if codes else ["WP1 error registry not detected; placeholder only."],
    }


def _build_summary() -> dict[str, object]:
    total = len(SETTINGS_DESCRIPTORS)
    gaps = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.status == "gap")
    pending = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.status == "pending")
    hidden = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.visibility == "hidden")
    masked = sum(1 for descriptor in SETTINGS_DESCRIPTORS if descriptor.visibility == "masked")
    return {
        "total_descriptors": total,
        "gap_count": gaps,
        "pending_count": pending,
        "hidden_count": hidden,
        "masked_count": masked,
        "editable_now_count": 0,
    }


def _serialize_descriptor(descriptor: SettingsDescriptor) -> dict[str, object]:
    row: dict[str, object] = {
        "key": descriptor.key,
        "label": descriptor.label,
        "source_of_truth": descriptor.source_of_truth,
        "owner": descriptor.owner,
        "visibility": descriptor.visibility,
        "risk_class": descriptor.risk_class,
        "environment_scope": descriptor.environment_scope,
        "restart_required": descriptor.restart_required,
        "audit_required": descriptor.audit_required,
        "editable_now": descriptor.editable_now,
        "masking_rule": descriptor.masking_rule,
        "evidence": descriptor.evidence,
        "category": descriptor.category,
        "status": descriptor.status,
        "state": _build_state(descriptor),
        "notes": list(descriptor.notes),
    }
    if descriptor.editable_when:
        row["editable_when"] = descriptor.editable_when
    return row


def _build_state(descriptor: SettingsDescriptor) -> dict[str, object]:
    raw_value = _read_value(descriptor)
    configured = _is_configured(raw_value)
    state: dict[str, object] = {
        "status": descriptor.status,
        "configured": configured,
    }

    if descriptor.visibility == "hidden":
        return state

    if descriptor.visibility == "masked":
        state["display_value"] = _mask_value(raw_value, descriptor.masking_rule)
        return state

    if configured:
        state["display_value"] = _safe_display_value(raw_value)
    else:
        state["display_value"] = "missing"
    return state


def _read_value(descriptor: SettingsDescriptor) -> object | None:
    if descriptor.value_reader is None:
        return None
    return descriptor.value_reader()


def _is_configured(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (tuple, list, set, dict)):
        return bool(value)
    return True


def _mask_value(value: object | None, masking_rule: str) -> str:
    if not _is_configured(value):
        return "missing"
    if masking_rule == "count_only":
        if isinstance(value, (tuple, list, set)):
            return f"{len(value)} entries configured"
        return "configured"
    if masking_rule == "partial":
        if isinstance(value, Path):
            return f".../{value.name}"
        raw = str(value)
        parsed = urlparse(raw)
        if parsed.hostname:
            return parsed.hostname
        if len(raw) <= 8:
            return "***"
        return f"{raw[:3]}...{raw[-3:]}"
    if masking_rule == "hash_only":
        return "hash hidden"
    return "configured"


def _safe_display_value(value: object | None) -> str:
    if value is None:
        return "missing"
    if isinstance(value, (tuple, list, set)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_timedelta_minutes(value: Any) -> str:
    total_seconds = int(value.total_seconds())
    minutes = total_seconds // 60
    return f"{minutes} minutes"


def _serialize_gap(gap: GapRisk) -> dict[str, str]:
    return {
        "key": gap.key,
        "severity": gap.severity,
        "impact": gap.impact,
        "mvp_mitigation": gap.mvp_mitigation,
        "long_term_mitigation": gap.long_term_mitigation,
        "follow_up_wp": gap.follow_up_wp,
        "evidence": gap.evidence,
    }


def _build_game_health(game_code: str) -> dict[str, object]:
    checks = {
        "backend": {
            "status": "present",
            "evidence": "backend/app/modules/platform/game_codes.py",
        },
        "frontend_player_registry": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/player-game-registry.ts",
            token=f"{game_code}:",
            evidence="frontend/app/ui/player-game-registry.ts",
        ),
        "title_editor_registry": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/title-editor/engine-editor-registry.ts",
            token=f"{game_code}:",
            evidence="frontend/app/ui/title-editor/engine-editor-registry.ts",
        ),
        "finance_replay_descriptor": _frontend_registry_check(
            path=REPO_ROOT / "frontend/app/ui/game-reporting-registry.tsx",
            token=f"{game_code}:",
            evidence="frontend/app/ui/game-reporting-registry.tsx",
            pending_note="WP3 finance/replay registry not detected in this workspace.",
        ),
        "error_namespace": _error_namespace_check(),
        "smoke_status": {
            "status": "pending",
            "evidence": "manual smoke not tracked by Settings MVP",
            "notes": ["No per-game smoke status feed exists yet."],
        },
    }
    aggregate_status = "present"
    for check in checks.values():
        if check["status"] == "gap":
            aggregate_status = "gap"
            break
        if check["status"] == "pending":
            aggregate_status = "pending"
    return {
        "game_code": game_code,
        "source_of_truth": "backend/app/modules/platform/game_codes.py",
        "status": aggregate_status,
        "checks": checks,
    }


def _frontend_registry_check(
    *,
    path: Path,
    token: str,
    evidence: str,
    pending_note: str = "Adapter file not detected in this workspace.",
) -> dict[str, object]:
    if not path.exists():
        return {
            "status": "pending",
            "evidence": evidence,
            "notes": [pending_note],
        }
    source = path.read_text(encoding="utf-8")
    if token in source:
        return {
            "status": "present",
            "evidence": evidence,
            "notes": [],
        }
    return {
        "status": "gap",
        "evidence": evidence,
        "notes": [f"Missing adapter token {token}."],
    }


def _error_namespace_check() -> dict[str, object]:
    has_game_namespace = any(code.startswith("CK.GAME.") for code in ERROR_REGISTRY)
    if has_game_namespace:
        return {
            "status": "present",
            "evidence": "backend/app/api/errors.py",
            "notes": ["Shared CK.GAME namespace present; game-specific namespaces can be added later."],
        }
    return {
        "status": "pending",
        "evidence": "backend/app/api/errors.py",
        "notes": ["WP1 error namespace not detected."],
    }
