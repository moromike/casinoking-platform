from __future__ import annotations

import copy
from dataclasses import replace
import os
from pathlib import Path
import time
from typing import Generator
from uuid import uuid4

import httpx
import jwt
import psycopg
from psycopg.rows import DictRow, dict_row
from psycopg.types.json import Jsonb
import pytest

import sys
import os
if os.environ.get("RUNNING_IN_DOCKER_WITHOUT_PLAYWRIGHT") == "1":
    from unittest.mock import MagicMock
    class MockPlaywright:
        sync_api = MagicMock()
        Page = MagicMock()
    sys.modules["playwright"] = MockPlaywright()
    sys.modules["playwright.sync_api"] = MockPlaywright.sync_api

from app.modules.auth.service import ensure_local_admin
from app.db import config as db_config_module
from app.db import connection as db_connection_module


type DbConnection = psycopg.Connection[DictRow]
type DbCursor = psycopg.Cursor[DictRow]



TITLE_CONFIG_GENERIC_COLUMNS = (
    "title_code",
    "rules_sections_json",
    "ui_labels_json",
    "bet_limits_json",
    "demo_labels_json",
    "theme_tokens_json",
    "draft_rules_sections_json",
    "draft_ui_labels_json",
    "draft_bet_limits_json",
    "draft_demo_labels_json",
    "draft_theme_tokens_json",
    "published_at",
    "updated_by_admin_user_id",
    "draft_updated_by_admin_user_id",
    "draft_updated_at",
    "created_at",
    "updated_at",
)

TITLE_CONFIG_GENERIC_JSON_COLUMNS = {
    "rules_sections_json",
    "ui_labels_json",
    "bet_limits_json",
    "demo_labels_json",
    "theme_tokens_json",
    "draft_rules_sections_json",
    "draft_ui_labels_json",
    "draft_bet_limits_json",
    "draft_demo_labels_json",
    "draft_theme_tokens_json",
}




@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("CASINOKING_API_BASE_URL", "http://localhost:8000/api/v1")


@pytest.fixture(scope="session")
def database_url() -> str:
    project_env = _read_project_docker_env()
    docker_db_url = _build_local_database_url_from_env(project_env)
    return (
        os.getenv("CASINOKING_TEST_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or docker_db_url
        or "postgresql://casinoking:casinoking@localhost:5433/casinoking"
    )


@pytest.fixture(scope="session")
def site_access_password() -> str:
    return os.getenv("CASINOKING_SITE_ACCESS_PASSWORD", "change-me")


@pytest.fixture(scope="session")
def frontend_base_url() -> str:
    return os.getenv("CASINOKING_FRONTEND_BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def public_edge_base_url() -> str:
    return os.getenv("CASINOKING_PUBLIC_EDGE_BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def site_v3_frontend_base_url() -> str:
    return os.getenv("CASINOKING_SITE_V3_FRONTEND_BASE_URL", "http://localhost:3001")


def _read_project_docker_env() -> dict[str, str]:
    env_path = Path("infra/docker/.env")
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _build_local_database_url_from_env(env_values: dict[str, str]) -> str | None:
    database_url = env_values.get("CASINOKING_TEST_DATABASE_URL")
    if database_url:
        return database_url

    user = env_values.get("POSTGRES_USER")
    password = env_values.get("POSTGRES_PASSWORD")
    database = env_values.get("POSTGRES_DB")
    port = env_values.get("POSTGRES_PORT")
    if not all([user, password, database, port]):
        return None

    return f"postgresql://{user}:{password}@localhost:{port}/{database}"


@pytest.fixture(scope="session")
def wait_for_backend(api_base_url: str) -> None:
    deadline = time.time() + 30
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"{api_base_url}/health/ready", timeout=2.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Backend not ready in time: {last_error}")


@pytest.fixture(scope="session")
def wait_for_frontend(frontend_base_url: str) -> None:
    deadline = time.time() + 90
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(frontend_base_url, timeout=5.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Frontend not ready in time: {last_error}")


@pytest.fixture(scope="session")
def wait_for_public_edge(public_edge_base_url: str) -> None:
    deadline = time.time() + 90
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(public_edge_base_url, timeout=5.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Public edge not ready in time: {last_error}")


@pytest.fixture(scope="session")
def wait_for_site_v3_frontend(site_v3_frontend_base_url: str) -> None:
    deadline = time.time() + 90
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(site_v3_frontend_base_url, timeout=5.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Site V3 frontend not ready in time: {last_error}")


@pytest.fixture
def client(api_base_url: str, wait_for_backend: None) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=api_base_url, timeout=10.0) as session:
        yield session


@pytest.fixture
def db_connection(database_url: str) -> Generator[DbConnection, None, None]:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as conn:
        yield conn


# NON E' PIU' `autouse`, dal 10/09/2026 (PASSO 4A).
# Era la condizione di partenza di TUTTI i collaudi — compresi quelli di boxe, di
# hi-lo e quelli di pura matematica — e faceva pagare a ognuno la preparazione di UN
# gioco solo. Ora la chiede chi ne ha davvero bisogno, cioe' chi SCRIVE la
# configurazione di quel gioco e deve ritrovarla com'era.
# Chi la toglie di nuovo si riprenda anche questa frase: il punto non e' la
# velocita', e' che la radice della suite non deve conoscere un gioco.
@pytest.fixture
def preserve_site_bootstrap(
    db_connection: DbConnection,
) -> Generator[None, None, None]:
    """Preserve and restore the canonical site bootstrap row across tests."""
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT site_code, display_name, base_url, status
            FROM sites
            WHERE site_code = 'casinoking'
            """,
        )
        snapshot = cursor.fetchone()

    if snapshot is None:
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sites (site_code, display_name, base_url, status)
                VALUES ('casinoking', 'CasinoKing', NULL, 'active')
                ON CONFLICT (site_code) DO NOTHING
                """,
            )

    preserved = copy.deepcopy(snapshot) if snapshot is not None else None
    yield

    with db_connection.cursor() as cursor:
        if preserved is not None:
            cursor.execute(
                """
                INSERT INTO sites (site_code, display_name, base_url, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (site_code) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    base_url = EXCLUDED.base_url,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """,
                (
                    preserved["site_code"],
                    preserved["display_name"],
                    preserved["base_url"],
                    preserved["status"],
                ),
            )


@pytest.fixture
def create_player(
    client: httpx.Client,
    site_access_password: str,
    user_cleanup_coordinator: UserCleanupCoordinator,
) -> Generator[object, None, None]:
    created_user_ids: list[str] = []

    def _create_player(prefix: str = "player") -> dict[str, object]:
        email = f"{prefix}-{uuid4().hex[:12]}@example.com"
        password = f"StrongPass-{uuid4().hex[:12]}"
        first_name = f"{prefix.title()}First"
        last_name = f"{prefix.title()}Last"
        fiscal_code = f"FC{uuid4().hex[:14]}"[:16].upper()
        phone_number = f"+39{uuid4().int % 10**10:010d}"
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "site_access_password": site_access_password,
                "first_name": first_name,
                "last_name": last_name,
                "fiscal_code": fiscal_code,
                "phone_number": phone_number,
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        user_cleanup_coordinator.owned_user_ids.add(str(payload["user_id"]))
        return {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "fiscal_code": fiscal_code,
            "phone_number": phone_number,
            "user_id": payload["user_id"],
            "wallets": payload["wallets"],
            "bootstrap_transaction_id": payload["bootstrap_transaction_id"],
        }

    yield _create_player


@pytest.fixture
def login_player(client: httpx.Client):
    def _login_player(email: str, password: str) -> dict[str, str]:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()["data"]

    return _login_player


@pytest.fixture
def login_admin(client: httpx.Client):
    def _login_admin(email: str, password: str) -> dict[str, str]:
        response = client.post(
            "/admin/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()["data"]

    return _login_admin


@pytest.fixture
def create_authenticated_player(create_player, login_player):
    def _create_authenticated_player(prefix: str = "player") -> dict[str, object]:
        player = create_player(prefix=prefix)
        login_payload = login_player(
            email=str(player["email"]),
            password=str(player["password"]),
        )
        player["access_token"] = login_payload["access_token"]
        return player

    return _create_authenticated_player


@pytest.fixture
def create_admin_user(
    login_admin,
    db_connection: DbConnection,
    database_url: str,
    user_cleanup_coordinator: UserCleanupCoordinator,
) -> Generator[object, None, None]:
    def _create_admin_user(prefix: str = "admin") -> dict[str, object]:
        email = f"{prefix}-{uuid4().hex[:12]}@example.com"
        password = f"StrongPass-{uuid4().hex[:12]}"
        patched_db_config = replace(
            db_config_module.database_config,
            database_url=database_url,
        )
        db_config_module.database_config = patched_db_config
        db_connection_module.database_config = patched_db_config
        bootstrap_data = ensure_local_admin(email=email, password=password)
        admin_user = {
            "email": email,
            "password": password,
            "user_id": bootstrap_data["user_id"],
        }
        # La connessione dei collaudi e' autocommit: senza registrazione nel
        # coordinatore l'admin resterebbe nel database condiviso per sempre.
        user_cleanup_coordinator.owned_user_ids.add(str(bootstrap_data["user_id"]))
        login_payload = login_admin(
            email=str(admin_user["email"]),
            password=str(admin_user["password"]),
        )
        admin_user["access_token"] = login_payload["access_token"]
        return admin_user

    yield _create_admin_user


@pytest.fixture
def auth_headers():
    def _auth_headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}
    return _auth_headers

@pytest.fixture
def db_helpers(db_connection: DbConnection):
    class DBHelpers:
        def fetchone(self, query: str, params: tuple[object, ...]) -> dict[str, object] | None:
            with db_connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()

        def fetchall(self, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
            with db_connection.cursor() as cursor:
                cursor.execute(query, params)
                return list(cursor.fetchall())

        def get_wallet_balance(self, user_id: str, wallet_type: str = "cash") -> str:
            row = self.fetchone(
                """
                SELECT balance_snapshot
                FROM wallet_accounts
                WHERE user_id = %s
                  AND wallet_type = %s
                """,
                (user_id, wallet_type),
            )
            assert row is not None
            return f"{row['balance_snapshot']:.6f}"

        def get_game_transactions(self, session_id: str) -> list[dict[str, object]]:
            return self.fetchall(
                """
                SELECT id, transaction_type, idempotency_key
                FROM ledger_transactions
                WHERE reference_type = 'game_session'
                  AND reference_id = %s
                ORDER BY created_at
                """,
                (session_id,),
            )

        def get_transaction_entries(self, transaction_id: str) -> list[dict[str, object]]:
            return self.fetchall(
                """
                SELECT
                    la.account_code,
                    le.entry_side,
                    le.amount
                FROM ledger_entries le
                JOIN ledger_accounts la ON la.id = le.ledger_account_id
                WHERE le.transaction_id = %s
                ORDER BY le.created_at, le.id
                """,
                (transaction_id,),
            )

        def get_wallet_reconciliation(self, user_id: str, wallet_type: str) -> dict[str, object]:
            row = self.fetchone(
                """
                SELECT
                    wa.wallet_type,
                    wa.balance_snapshot,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN le.entry_side = 'credit' THEN le.amount
                                ELSE -le.amount
                            END
                        ),
                        0
                    ) AS ledger_balance,
                    wa.balance_snapshot - COALESCE(
                        SUM(
                            CASE
                                WHEN le.entry_side = 'credit' THEN le.amount
                                ELSE -le.amount
                            END
                        ),
                        0
                    ) AS drift
                FROM wallet_accounts wa
                JOIN ledger_accounts la ON la.id = wa.ledger_account_id
                LEFT JOIN ledger_entries le ON le.ledger_account_id = la.id
                WHERE wa.user_id = %s
                  AND wa.wallet_type = %s
                GROUP BY wa.wallet_type, wa.balance_snapshot
                """,
                (user_id, wallet_type),
            )
            assert row is not None
            return {
                "wallet_type": row["wallet_type"],
                "balance_snapshot": f"{row['balance_snapshot']:.6f}",
                "ledger_balance": f"{row['ledger_balance']:.6f}",
                "drift": f"{row['drift']:.6f}",
            }

    return DBHelpers()


def _decode_access_token_role(access_token: str) -> str | None:
    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        return None

    if payload.get("token_kind") != "access":
        return None
    role = payload.get("role")
    return role if isinstance(role, str) else None


_FILE_MARKERS: dict[str, str] = {
    # -- browser_smoke --
    "test_boxe_smoke.py": "browser_smoke",
    "test_boxe_lobby_launch.py": "browser_smoke",
    "test_frontend_smoke.py": "browser_smoke",
    "test_player_account_statement_browser_smoke.py": "browser_smoke",
    "test_site_v3_admin_builder_browser.py": "browser_smoke",
    "test_site_v3_player_handoff_browser.py": "browser_smoke",
    "test_site_v3_public_renderer_browser.py": "browser_smoke",
    # -- migration_schema --
    "test_apply_migrations.py": "migration_schema",
    "test_local_admin_bootstrap.py": "migration_schema",
    "test_platform_catalog_bootstrap.py": "migration_schema",
    "test_schema_drift_guard.py": "migration_schema",
    # -- visual (integration overlays) --
    "test_boxe_visual_regression.py": "visual",
    # -- money_admin --
    "test_account_wallet_movements.py": "money_admin",
    "test_admin_audit_log.py": "money_admin",
    "test_admin_bonus_and_adjustments.py": "money_admin",
    "test_admin_financial_reports.py": "money_admin",
    "test_admin_force_close_boxe_hi_lo.py": "money_admin",
    "test_admin_force_close_sessions.py": "money_admin",
    "test_admin_ledger_report.py": "money_admin",
    "test_admin_ledger_transactions_access.py": "money_admin",
    "test_admin_rbac.py": "money_admin",
    "test_admin_session_drilldown.py": "money_admin",
    "test_admin_suspend.py": "money_admin",
    "test_reconciliation_integrity.py": "money_admin",
    "test_wallet_detail_access.py": "money_admin",
    "test_finance_replay_metadata_contract.py": "money_admin",
    "test_ledger_admin_access.py": "money_admin",
    "test_wallet_detail_contract.py": "money_admin",
    "test_session_cascade_close.py": "money_admin",
    # -- catalog --
    "test_admin_assets_contract.py": "catalog",
    "test_admin_theme_editor_load_gate.py": "catalog",
    "test_asset_registry.py": "catalog",
    "test_boxe_admin_assets.py": "catalog",
    "test_boxe_admin_config.py": "catalog",
    "test_game_library_publication.py": "catalog",
    "test_game_title_archive_restore.py": "catalog",
    "test_hi_lo_admin_config.py": "catalog",
    "test_platform_settings_inventory.py": "catalog",
    "test_player_lobby_game_card_asset.py": "catalog",
    "test_site_home_slots.py": "catalog",
    "test_site_v3_admin_builder_contract.py": "catalog",
    "test_title_code_propagation.py": "catalog",
    "test_title_configs_split.py": "catalog",
    "test_title_editor_agnostic.py": "catalog",
    "test_title_editor_agnostic_frontend.py": "catalog",
    "test_title_theme_contract.py": "catalog",
}

def pytest_collection_modifyitems(config, items):  # noqa: D103
    for item in items:
        path = Path(item.fspath).as_posix()
        marker: str | None = None

        # 1. Directory-based defaults (works with absolute paths)
        if "/tests/unit/" in path:
            marker = "unit"
        elif "/tests/concurrency/" in path:
            marker = "concurrency"
        elif "/tests/stress/" in path:
            marker = "stress"
        elif "/tests/visual/" in path:
            marker = "visual"

        # 2. File-level overrides for contract/ and integration/
        file_name = Path(path).name
        if file_name in _FILE_MARKERS:
            marker = _FILE_MARKERS[file_name]

        # 3. Fallback: everything else in contract/ or integration/ -> api_service
        if marker is None and not list(item.iter_markers()) and (
            "/tests/contract/" in path or "/tests/integration/" in path
        ):
            marker = "api_service"

        if marker:
            item.add_marker(marker)


class UserCleanupCoordinator:
    def __init__(self):
        self.owned_user_ids: set[str] = set()
        self.owned_anonymous_ids: set[str] = set()
        self.owned_title_codes: set[str] = set()
        self.explicit_demo_session_ids: set[str] = set()
        self.domain_callbacks = []

    def register_domain_callback(self, cb):
        self.domain_callbacks.append(cb)


    def execute_cleanup(self, db_connection: DbConnection) -> None:
        """Esegue ORA la pulizia coordinata degli insiemi registrati.

        La fixture user_cleanup_coordinator la chiama in teardown; i collaudi che
        devono VERIFICARE la pulizia (test_teardown_full_graph) la chiamano a meta'
        prova e poi controllano con query che non resti nulla. E' idempotente: una
        seconda esecuzione sugli stessi insiemi non cancella piu' nulla.
        """
        if not self.owned_user_ids and not self.owned_anonymous_ids and not self.owned_title_codes and not self.explicit_demo_session_ids:
            return

        with db_connection.transaction():
            with db_connection.cursor() as cursor:
                cursor.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS cleanup_users ON COMMIT DROP AS SELECT UNNEST(%s::uuid[]) AS id",
                    (list(self.owned_user_ids),) if self.owned_user_ids else ([],)
                )
                cursor.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS cleanup_anon ON COMMIT DROP AS SELECT UNNEST(%s::uuid[]) AS id",
                    (list(self.owned_anonymous_ids),) if self.owned_anonymous_ids else ([],)
                )
                cursor.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS cleanup_titles ON COMMIT DROP AS SELECT UNNEST(%s::text[]) AS code",
                    (list(self.owned_title_codes),) if self.owned_title_codes else ([],)
                )
                cursor.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS cleanup_explicit_demo ON COMMIT DROP AS SELECT UNNEST(%s::uuid[]) AS id",
                    (list(self.explicit_demo_session_ids),) if self.explicit_demo_session_ids else ([],)
                )
                cursor.execute(
                    """
                    CREATE TEMP TABLE cleanup_wallet_accounts ON COMMIT DROP AS
                    SELECT id FROM wallet_accounts
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    CREATE TEMP TABLE cleanup_transactions ON COMMIT DROP AS
                    SELECT id FROM ledger_transactions
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    CREATE TEMP TABLE cleanup_ledger_accounts ON COMMIT DROP AS
                    SELECT id FROM ledger_accounts
                    WHERE owner_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
            
                # targeted_demo_session_ids
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_demo_session_ids ON COMMIT DROP AS
                    SELECT id FROM demo_play_sessions WHERE user_id IN (SELECT id FROM cleanup_users)
                    OR anonymous_id IN (SELECT id FROM cleanup_anon)
                    OR title_code IN (SELECT code FROM cleanup_titles)
                    OR id IN (SELECT id FROM cleanup_explicit_demo)
                    """
                )
            
                # targeted_platform_rounds
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_platform_rounds ON COMMIT DROP AS
                    SELECT id FROM platform_rounds WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )

                # targeted_access_sessions
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_access_sessions ON COMMIT DROP AS
                    SELECT id FROM game_access_sessions WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )

                # targeted_table_sessions
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_table_sessions ON COMMIT DROP AS
                    SELECT id FROM game_table_sessions WHERE user_id IN (SELECT id FROM cleanup_users)
                    OR access_session_id IN (SELECT id FROM targeted_access_sessions)
                    """
                )
            
                # Run domain callbacks first
                for cb in self.domain_callbacks:
                    cb(cursor)

                cursor.execute(
                    """
                    DELETE FROM admin_actions
                    WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                       OR target_user_id IN (SELECT id FROM cleanup_users)
                       OR ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                    """
                )
                # Admin audit log
                cursor.execute(
                    """
                    DELETE FROM admin_audit_log
                    WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                       OR resource_id IN (SELECT id::text FROM cleanup_users)
                    """
                )
            
                # Boxe & Hi-Lo Rounds
                cursor.execute("SELECT to_regclass('public.boxe_rounds') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute(
                        """
                        CREATE TEMP TABLE IF NOT EXISTS targeted_boxe_round_ids ON COMMIT DROP AS
                        SELECT id FROM boxe_rounds WHERE title_code IN (SELECT code FROM cleanup_titles)
                        OR player_id IN (SELECT id FROM cleanup_users)
                        OR player_id IN (SELECT id FROM cleanup_anon)
                        OR platform_round_id IN (SELECT id FROM targeted_platform_rounds)
                        OR access_session_id IN (SELECT id FROM targeted_access_sessions)
                        OR table_session_id IN (SELECT id FROM targeted_table_sessions)
                        OR demo_session_id IN (SELECT id FROM targeted_demo_session_ids)
                        """
                    )
                    cursor.execute("DELETE FROM boxe_picks WHERE round_id IN (SELECT id FROM targeted_boxe_round_ids)")
                    cursor.execute(
                        """
                        DELETE FROM boxe_idempotency_keys WHERE round_id IN (SELECT id FROM targeted_boxe_round_ids)
                        OR player_id IN (SELECT id FROM cleanup_users)
                        OR player_id IN (SELECT id FROM cleanup_anon)
                        """
                    )
                    cursor.execute("DELETE FROM boxe_rounds WHERE id IN (SELECT id FROM targeted_boxe_round_ids)")
            
                cursor.execute("SELECT to_regclass('public.hi_lo_rounds') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute(
                        """
                        CREATE TEMP TABLE IF NOT EXISTS targeted_hi_lo_round_ids ON COMMIT DROP AS
                        SELECT id FROM hi_lo_rounds WHERE title_code IN (SELECT code FROM cleanup_titles)
                        OR player_id IN (SELECT id FROM cleanup_users)
                        OR player_id IN (SELECT id FROM cleanup_anon)
                        OR platform_round_id IN (SELECT id FROM targeted_platform_rounds)
                        OR access_session_id IN (SELECT id FROM targeted_access_sessions)
                        OR table_session_id IN (SELECT id FROM targeted_table_sessions)
                        OR demo_session_id IN (SELECT id FROM targeted_demo_session_ids)
                        """
                    )
                    cursor.execute("DELETE FROM hi_lo_actions WHERE round_id IN (SELECT id FROM targeted_hi_lo_round_ids)")
                    cursor.execute(
                        """
                        DELETE FROM hi_lo_idempotency_keys WHERE round_id IN (SELECT id FROM targeted_hi_lo_round_ids)
                        OR player_id IN (SELECT id FROM cleanup_users)
                        OR player_id IN (SELECT id FROM cleanup_anon)
                        """
                    )
                    cursor.execute("DELETE FROM hi_lo_rounds WHERE id IN (SELECT id FROM targeted_hi_lo_round_ids)")

                # Core cleanups
                cursor.execute("DELETE FROM demo_round_events WHERE demo_play_session_id IN (SELECT id FROM targeted_demo_session_ids)")
                cursor.execute("DELETE FROM demo_play_sessions WHERE id IN (SELECT id FROM targeted_demo_session_ids)")
            


                cursor.execute(
                    """
                    DELETE FROM platform_rounds
                    WHERE id IN (SELECT id FROM targeted_platform_rounds)
                       OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                       OR start_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                       OR settlement_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM game_table_sessions
                    WHERE id IN (SELECT id FROM targeted_table_sessions)
                       OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM game_access_sessions
                    WHERE id IN (SELECT id FROM targeted_access_sessions)
                   
                    """
                )

                cursor.execute("UPDATE site_home_slots SET cta_target_ref = NULL WHERE cta_target_type = 'game' AND cta_target_ref IN (SELECT code FROM cleanup_titles)")
                cursor.execute("UPDATE site_assets SET uploaded_by_admin_user_id = NULL WHERE uploaded_by_admin_user_id IN (SELECT id FROM cleanup_users)")

                cursor.execute("UPDATE game_titles SET source_title_code = NULL WHERE source_title_code IN (SELECT code FROM cleanup_titles)")
                cursor.execute("DELETE FROM game_titles WHERE title_code IN (SELECT code FROM cleanup_titles)")
                cursor.execute(
                    """
                    UPDATE title_assets
                    SET uploaded_by_admin_user_id = NULL
                    WHERE uploaded_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE title_locale_maps
                    SET created_by_admin_user_id = NULL
                    WHERE created_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE title_locale_maps
                    SET published_by_admin_user_id = NULL
                    WHERE published_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE site_home_slots
                    SET created_by = NULL
                    WHERE created_by IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE site_home_slots
                    SET updated_by = NULL
                    WHERE updated_by IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE title_configs
                    SET updated_by_admin_user_id = NULL
                    WHERE updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE title_configs
                    SET draft_updated_by_admin_user_id = NULL
                    WHERE draft_updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    UPDATE fairness_seed_rotations
                    SET rotated_by_admin_user_id = NULL
                    WHERE rotated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM ledger_entries
                    WHERE transaction_id IN (SELECT id FROM cleanup_transactions)
                       OR ledger_account_id IN (SELECT id FROM cleanup_ledger_accounts)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM ledger_transactions
                    WHERE id IN (SELECT id FROM cleanup_transactions)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM wallet_accounts
                    WHERE id IN (SELECT id FROM cleanup_wallet_accounts)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM ledger_accounts
                    WHERE id IN (SELECT id FROM cleanup_ledger_accounts)
                    """
                )
                cursor.execute("SELECT to_regclass('public.site_v3_pages') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute("SELECT to_regclass('public.site_v3_module_definitions') AS table_name")
                    if cursor.fetchone()["table_name"] is not None:
                        cursor.execute(
                            """
                            DELETE FROM site_v3_module_definitions definition
                            WHERE definition.created_by IN (SELECT id FROM cleanup_users)
                               OR definition.updated_by IN (SELECT id FROM cleanup_users)
                               OR definition.published_by IN (SELECT id FROM cleanup_users)
                               OR definition.archived_by IN (SELECT id FROM cleanup_users)
                               OR EXISTS (
                                  SELECT 1
                                  FROM site_v3_module_definition_versions version
                                  WHERE version.definition_id = definition.id
                                    AND (
                                        version.created_by IN (SELECT id FROM cleanup_users)
                                        OR version.published_by IN (SELECT id FROM cleanup_users)
                                    )
                               )
                            """
                        )
                    cursor.execute(
                        """
                        DELETE FROM site_v3_pages page
                        WHERE page.created_by IN (SELECT id FROM cleanup_users)
                           OR page.updated_by IN (SELECT id FROM cleanup_users)
                           OR page.archived_by IN (SELECT id FROM cleanup_users)
                           OR EXISTS (
                              SELECT 1
                              FROM site_v3_page_versions version
                              WHERE version.page_id = page.id
                                AND (
                                    version.created_by IN (SELECT id FROM cleanup_users)
                                    OR version.published_by IN (SELECT id FROM cleanup_users)
                                )
                           )
                           OR EXISTS (
                              SELECT 1
                              FROM site_v3_modules module
                              WHERE module.page_id = page.id
                                AND (
                                    module.created_by IN (SELECT id FROM cleanup_users)
                                    OR module.updated_by IN (SELECT id FROM cleanup_users)
                                )
                           )
                        """
                    )
                cursor.execute(
                    """
                    DELETE FROM admin_profiles
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM access_logs
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM password_reset_tokens
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM user_credentials
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                    """
                )
                cursor.execute(
                    """
                    DELETE FROM users
                    WHERE id IN (SELECT id FROM cleanup_users)
                    """
                )



@pytest.fixture
def user_cleanup_coordinator(db_connection: DbConnection) -> Generator[UserCleanupCoordinator, None, None]:
    coordinator = UserCleanupCoordinator()
    yield coordinator
    coordinator.execute_cleanup(db_connection)
