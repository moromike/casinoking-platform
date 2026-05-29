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

from app.modules.auth.service import ensure_local_admin
from app.modules.games.mines.runtime import get_runtime_config
from app.db import config as db_config_module
from app.db import connection as db_connection_module


type DbConnection = psycopg.Connection[DictRow]


MINES_DEFAULT_TITLE_CODE = "mines_classic"

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

MINES_TITLE_CONFIG_COLUMNS = (
    "title_code",
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "published_board_assets_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_board_assets_json",
    "created_at",
    "updated_at",
)

MINES_TITLE_CONFIG_JSON_COLUMNS = {
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "published_board_assets_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_board_assets_json",
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
def v1_frontend_base_url() -> str:
    return os.getenv("CASINOKING_V1_FRONTEND_BASE_URL", "http://localhost:3002")


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


@pytest.fixture(scope="session", autouse=True)
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
def wait_for_v1_frontend(v1_frontend_base_url: str) -> None:
    deadline = time.time() + 90
    last_error: Exception | None = None
    admin_url = f"{v1_frontend_base_url.rstrip('/')}/admin"
    while time.time() < deadline:
        try:
            response = httpx.get(admin_url, timeout=5.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - retry loop
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"V1 frontend not ready in time: {last_error}")


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
def client(api_base_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=api_base_url, timeout=10.0) as session:
        yield session


@pytest.fixture
def db_connection(database_url: str) -> Generator[DbConnection, None, None]:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as conn:
        yield conn


@pytest.fixture(autouse=True)
def preserve_mines_backoffice_config(
    db_connection: DbConnection,
) -> Generator[None, None, None]:
    """Preserve and restore Mines backoffice config across tests.

    After Phase 3 the configuration lives in two tables: `title_configs` (engine
    agnostic) and `mines_title_configs` (engine specific). The legacy view
    `mines_backoffice_config` is read-only by design (no INSTEAD OF triggers),
    so writers must operate on the new tables directly.
    """

    with db_connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {", ".join(TITLE_CONFIG_GENERIC_COLUMNS)}
            FROM title_configs
            WHERE title_code = %s
            """,
            (MINES_DEFAULT_TITLE_CODE,),
        )
        generic_snapshot = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT {", ".join(MINES_TITLE_CONFIG_COLUMNS)}
            FROM mines_title_configs
            WHERE title_code = %s
            """,
            (MINES_DEFAULT_TITLE_CODE,),
        )
        engine_snapshot = cursor.fetchone()

    if generic_snapshot is None or engine_snapshot is None:
        baseline = _build_test_mines_backoffice_snapshot()
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO title_configs (
                    title_code,
                    rules_sections_json,
                    ui_labels_json,
                    published_at,
                    updated_at
                )
                VALUES (%s, %s::jsonb, %s::jsonb, NOW(), NOW())
                ON CONFLICT (title_code) DO NOTHING
                """,
                (
                    MINES_DEFAULT_TITLE_CODE,
                    Jsonb(baseline["rules_sections"]),
                    Jsonb(baseline["ui_labels"]),
                ),
            )
            cursor.execute(
                """
                INSERT INTO mines_title_configs (
                    title_code,
                    published_grid_sizes_json,
                    published_mine_counts_json,
                    default_mine_counts_json,
                    published_board_assets_json,
                    updated_at
                )
                VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (title_code) DO NOTHING
                """,
                (
                    MINES_DEFAULT_TITLE_CODE,
                    Jsonb(baseline["published_grid_sizes"]),
                    Jsonb(baseline["published_mine_counts"]),
                    Jsonb(baseline["default_mine_counts"]),
                    Jsonb(baseline["board_assets"]),
                ),
            )

    preserved_generic = copy.deepcopy(generic_snapshot) if generic_snapshot is not None else None
    preserved_engine = copy.deepcopy(engine_snapshot) if engine_snapshot is not None else None
    yield

    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM mines_title_configs WHERE title_code = %s",
            (MINES_DEFAULT_TITLE_CODE,),
        )
        cursor.execute(
            "DELETE FROM title_configs WHERE title_code = %s",
            (MINES_DEFAULT_TITLE_CODE,),
        )
        if preserved_generic is None or preserved_engine is None:
            return

        generic_values = [
            Jsonb(preserved_generic[column])
            if column in TITLE_CONFIG_GENERIC_JSON_COLUMNS and preserved_generic[column] is not None
            else preserved_generic[column]
            for column in TITLE_CONFIG_GENERIC_COLUMNS
        ]
        cursor.execute(
            f"""
            INSERT INTO title_configs ({", ".join(TITLE_CONFIG_GENERIC_COLUMNS)})
            VALUES ({", ".join(["%s"] * len(TITLE_CONFIG_GENERIC_COLUMNS))})
            """,
            generic_values,
        )

        engine_values = [
            Jsonb(preserved_engine[column])
            if column in MINES_TITLE_CONFIG_JSON_COLUMNS and preserved_engine[column] is not None
            else preserved_engine[column]
            for column in MINES_TITLE_CONFIG_COLUMNS
        ]
        cursor.execute(
            f"""
            INSERT INTO mines_title_configs ({", ".join(MINES_TITLE_CONFIG_COLUMNS)})
            VALUES ({", ".join(["%s"] * len(MINES_TITLE_CONFIG_COLUMNS))})
            """,
            engine_values,
        )


@pytest.fixture
def create_player(
    client: httpx.Client,
    site_access_password: str,
    db_connection: DbConnection,
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
        created_user_ids.append(str(payload["user_id"]))
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
    _cleanup_test_users(db_connection=db_connection, user_ids=created_user_ids)


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
) -> Generator[object, None, None]:
    created_user_ids: list[str] = []

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
        created_user_ids.append(str(bootstrap_data["user_id"]))
        login_payload = login_admin(
            email=str(admin_user["email"]),
            password=str(admin_user["password"]),
        )
        admin_user["access_token"] = login_payload["access_token"]
        return admin_user

    yield _create_admin_user
    _cleanup_test_users(db_connection=db_connection, user_ids=created_user_ids)


@pytest.fixture
def auth_headers(client: httpx.Client, db_connection: DbConnection):
    token_cache: dict[tuple[str, str, str, str], str | None] = {}
    created_title_codes: set[str] = set()
    implicit_title_code: str | None = None

    def _auth_headers(
        access_token: str,
        *,
        include_game_launch_token: bool = True,
        title_code: str | None = None,
        site_code: str = "casinoking",
        mode: str = "real",
    ) -> dict[str, str]:
        nonlocal implicit_title_code

        headers = {"Authorization": f"Bearer {access_token}"}
        if not include_game_launch_token:
            return headers

        resolved_title_code = title_code
        if resolved_title_code is None:
            if _decode_access_token_role(access_token) != "player":
                return headers
            if implicit_title_code is None:
                implicit_title_code = f"mines_auth_{uuid4().hex[:8]}"
                with db_connection.cursor() as cursor:
                    _upsert_published_mines_variant(
                        cursor=cursor,
                        title_code=implicit_title_code,
                        display_name="Mines Auth Header Variant",
                        site_code=site_code,
                        lobby_visibility="visible",
                        demo_enabled=True,
                        real_enabled=True,
                    )
                created_title_codes.add(implicit_title_code)
            resolved_title_code = implicit_title_code

        cache_key = (access_token, resolved_title_code, site_code, mode)
        # Mines operational endpoints require bearer + launch token in the monolite.
        if cache_key not in token_cache:
            issue_response = client.post(
                "/games/mines/launch-token",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "game_code": "mines",
                    "title_code": resolved_title_code,
                    "site_code": site_code,
                    "mode": mode,
                },
            )
            token_cache[cache_key] = (
                issue_response.json()["data"]["game_launch_token"]
                if issue_response.status_code == 200
                else None
            )

        game_launch_token = token_cache[cache_key]
        if game_launch_token:
            headers["X-Game-Launch-Token"] = game_launch_token
        return headers

    yield _auth_headers

    for title_code_to_cleanup in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code_to_cleanup,
        )


@pytest.fixture
def create_published_mines_variant(db_connection: DbConnection):
    created_title_codes: set[str] = set()

    def _create_published_mines_variant(
        *,
        title_code: str | None = None,
        display_name: str = "Mines Test Variant",
        site_code: str = "casinoking",
        lobby_visibility: str = "visible",
        demo_enabled: bool = True,
        real_enabled: bool = True,
        cleanup: bool = True,
    ) -> dict[str, object]:
        resolved_title_code = title_code or f"mines_test_{uuid4().hex[:8]}"
        with db_connection.cursor() as cursor:
            _upsert_published_mines_variant(
                cursor=cursor,
                title_code=resolved_title_code,
                display_name=display_name,
                site_code=site_code,
                lobby_visibility=lobby_visibility,
                demo_enabled=demo_enabled,
                real_enabled=real_enabled,
            )
        if cleanup:
            created_title_codes.add(resolved_title_code)
        return {
            "title_code": resolved_title_code,
            "site_code": site_code,
            "display_name": display_name,
        }

    yield _create_published_mines_variant

    for title_code in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code,
        )


@pytest.fixture
def track_mines_variant_cleanup(db_connection: DbConnection):
    created_title_codes: set[str] = set()

    def _track_mines_variant_cleanup(title_code: str) -> str:
        created_title_codes.add(title_code)
        return title_code

    yield _track_mines_variant_cleanup

    for title_code in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code,
        )


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

        def get_mine_positions(self, session_id: str) -> list[int]:
            row = self.fetchone(
                """
                SELECT mgr.mine_positions_json
                FROM platform_rounds pr
                JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                WHERE pr.id = %s
                """,
                (session_id,),
            )
            assert row is not None
            return list(row["mine_positions_json"])

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


def _upsert_published_mines_variant(
    *,
    cursor,
    title_code: str,
    display_name: str,
    site_code: str,
    lobby_visibility: str,
    demo_enabled: bool,
    real_enabled: bool,
) -> None:
    cursor.execute(
        """
        INSERT INTO game_titles (
            title_code,
            engine_code,
            display_name,
            status,
            is_master,
            source_title_code
        )
        SELECT
            %s,
            engine_code,
            %s,
            'active',
            false,
            title_code
        FROM game_titles
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET display_name = EXCLUDED.display_name,
            status = 'active',
            is_master = false,
            source_title_code = %s,
            updated_at = NOW()
        """,
        (title_code, display_name, MINES_DEFAULT_TITLE_CODE, MINES_DEFAULT_TITLE_CODE),
    )
    cursor.execute(
        """
        INSERT INTO site_titles (
            site_code,
            title_code,
            position,
            status,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            lobby_display_name,
            lobby_description,
            featured
        )
        VALUES (%s, %s, 999, 'active', %s, %s, %s, %s, 'Test publication variant', false)
        ON CONFLICT (site_code, title_code) DO UPDATE
        SET status = 'active',
            lobby_visibility = EXCLUDED.lobby_visibility,
            demo_enabled = EXCLUDED.demo_enabled,
            real_enabled = EXCLUDED.real_enabled,
            lobby_display_name = EXCLUDED.lobby_display_name,
            lobby_description = EXCLUDED.lobby_description,
            featured = EXCLUDED.featured,
            updated_at = NOW()
        """,
        (
            site_code,
            title_code,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            display_name,
        ),
    )
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_bet_limits_json,
            draft_demo_labels_json,
            draft_theme_tokens_json,
            published_at,
            updated_by_admin_user_id,
            draft_updated_by_admin_user_id,
            draft_updated_at
        )
        SELECT
            %s,
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_bet_limits_json,
            draft_demo_labels_json,
            draft_theme_tokens_json,
            COALESCE(published_at, NOW()),
            updated_by_admin_user_id,
            draft_updated_by_admin_user_id,
            COALESCE(draft_updated_at, NOW())
        FROM title_configs
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET rules_sections_json = EXCLUDED.rules_sections_json,
            ui_labels_json = EXCLUDED.ui_labels_json,
            bet_limits_json = EXCLUDED.bet_limits_json,
            demo_labels_json = EXCLUDED.demo_labels_json,
            theme_tokens_json = EXCLUDED.theme_tokens_json,
            draft_rules_sections_json = EXCLUDED.draft_rules_sections_json,
            draft_ui_labels_json = EXCLUDED.draft_ui_labels_json,
            draft_bet_limits_json = EXCLUDED.draft_bet_limits_json,
            draft_demo_labels_json = EXCLUDED.draft_demo_labels_json,
            draft_theme_tokens_json = EXCLUDED.draft_theme_tokens_json,
            published_at = EXCLUDED.published_at,
            updated_at = NOW()
        """,
        (title_code, MINES_DEFAULT_TITLE_CODE),
    )
    cursor.execute(
        """
        INSERT INTO mines_title_configs (
            title_code,
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json,
            published_board_assets_json,
            draft_grid_sizes_json,
            draft_mine_counts_json,
            draft_default_mine_counts_json,
            draft_board_assets_json
        )
        SELECT
            %s,
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json,
            published_board_assets_json,
            draft_grid_sizes_json,
            draft_mine_counts_json,
            draft_default_mine_counts_json,
            draft_board_assets_json
        FROM mines_title_configs
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET published_grid_sizes_json = EXCLUDED.published_grid_sizes_json,
            published_mine_counts_json = EXCLUDED.published_mine_counts_json,
            default_mine_counts_json = EXCLUDED.default_mine_counts_json,
            published_board_assets_json = EXCLUDED.published_board_assets_json,
            draft_grid_sizes_json = EXCLUDED.draft_grid_sizes_json,
            draft_mine_counts_json = EXCLUDED.draft_mine_counts_json,
            draft_default_mine_counts_json = EXCLUDED.draft_default_mine_counts_json,
            draft_board_assets_json = EXCLUDED.draft_board_assets_json,
            updated_at = NOW()
        """,
        (title_code, MINES_DEFAULT_TITLE_CODE),
    )


def _cleanup_test_users(
    *,
    db_connection: DbConnection,
    user_ids: list[str],
) -> None:
    if not user_ids:
        return

    unique_user_ids = sorted(set(user_ids))
    with db_connection.transaction():
        with db_connection.cursor() as cursor:
            cursor.execute(
                "CREATE TEMP TABLE cleanup_users ON COMMIT DROP AS SELECT UNNEST(%s::uuid[]) AS id",
                (unique_user_ids,),
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
                CREATE TEMP TABLE cleanup_ledger_accounts ON COMMIT DROP AS
                SELECT id FROM ledger_accounts
                WHERE owner_user_id IN (SELECT id FROM cleanup_users)
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
                DELETE FROM demo_round_events
                WHERE demo_play_session_id IN (
                    SELECT id FROM demo_play_sessions
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                )
                """
            )
            cursor.execute(
                """
                DELETE FROM demo_mines_game_rounds
                WHERE demo_play_session_id IN (
                    SELECT id FROM demo_play_sessions
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                )
                """
            )
            cursor.execute(
                """
                DELETE FROM demo_play_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM mines_game_rounds
                WHERE user_id IN (SELECT id FROM cleanup_users)
                   OR platform_round_id IN (
                      SELECT id FROM platform_rounds
                      WHERE user_id IN (SELECT id FROM cleanup_users)
                   )
                """
            )
            cursor.execute("SELECT to_regclass('public.boxe_rounds') AS table_name")
            if cursor.fetchone()["table_name"] is not None:
                cursor.execute(
                    """
                    DELETE FROM boxe_rounds
                    WHERE player_id IN (SELECT id FROM cleanup_users)
                       OR platform_round_id IN (
                          SELECT id FROM platform_rounds
                          WHERE user_id IN (SELECT id FROM cleanup_users)
                       )
                    """
                )
            cursor.execute("SELECT to_regclass('public.boxe_sessions') AS table_name")
            if cursor.fetchone()["table_name"] is not None:
                cursor.execute(
                    """
                    DELETE FROM boxe_sessions
                    WHERE player_id IN (SELECT id FROM cleanup_users)
                    """
                )
            cursor.execute(
                """
                DELETE FROM platform_rounds
                WHERE user_id IN (SELECT id FROM cleanup_users)
                   OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                   OR start_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                   OR settlement_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                """
            )
            cursor.execute(
                """
                DELETE FROM game_table_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                   OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                   OR access_session_id IN (
                      SELECT id FROM game_access_sessions
                      WHERE user_id IN (SELECT id FROM cleanup_users)
                   )
                """
            )
            cursor.execute(
                """
                DELETE FROM game_access_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_actions
                WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                   OR target_user_id IN (SELECT id FROM cleanup_users)
                   OR ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                   OR resource_id IN (SELECT id::text FROM cleanup_users)
                """
            )
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
                UPDATE mines_backoffice_config_legacy
                SET updated_by_admin_user_id = NULL
                WHERE updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE mines_backoffice_config_legacy
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
            cursor.execute(
                """
                CREATE TEMP TABLE cleanup_orphan_titles ON COMMIT DROP AS
                SELECT gt.title_code
                FROM game_titles gt
                WHERE gt.title_code ~ '^(mines_test_|mines_auth_|statement_|integration_|contract_|browser_)'
                  AND NOT EXISTS (SELECT 1 FROM platform_rounds pr WHERE pr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM mines_game_rounds mgr WHERE mgr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM game_access_sessions gas WHERE gas.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM game_table_sessions gts WHERE gts.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM demo_play_sessions dps WHERE dps.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM demo_mines_game_rounds dmgr WHERE dmgr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM title_assets ta WHERE ta.title_code = gt.title_code)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE resource_id IN (SELECT title_code FROM cleanup_orphan_titles)
                   OR resource_id IN (
                      SELECT 'casinoking:' || title_code FROM cleanup_orphan_titles
                   )
                """
            )
            cursor.execute(
                """
                DELETE FROM mines_title_configs
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM title_configs
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM site_titles
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM game_titles
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                  AND NOT EXISTS (
                      SELECT 1 FROM game_access_sessions gas
                      WHERE gas.title_code = game_titles.title_code
                  )
                """
            )


def _cleanup_mines_variant_if_unreferenced(
    *,
    db_connection: DbConnection,
    title_code: str,
) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                EXISTS (SELECT 1 FROM platform_rounds WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM mines_game_rounds WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM game_access_sessions WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM game_table_sessions WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM demo_play_sessions WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM demo_mines_game_rounds WHERE title_code = %s)
                OR EXISTS (SELECT 1 FROM title_assets WHERE title_code = %s)
                AS has_refs
            """,
            (
                title_code,
                title_code,
                title_code,
                title_code,
                title_code,
                title_code,
                title_code,
            ),
        )
        if cursor.fetchone()["has_refs"] is True:
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE resource_id = %s
                   OR resource_id = %s
                   OR resource_id LIKE %s
                """,
                (title_code, f"casinoking:{title_code}", f"{title_code}:%"),
            )
            cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
            cursor.execute(
                """
                UPDATE game_titles
                SET status = 'inactive',
                    updated_at = NOW()
                WHERE title_code = %s
                """,
                (title_code,),
            )
            return

        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_id = %s
               OR resource_id = %s
               OR resource_id LIKE %s
            """,
            (title_code, f"casinoking:{title_code}", f"{title_code}:%"),
        )
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def _build_test_mines_backoffice_snapshot() -> dict[str, object]:
    runtime = get_runtime_config()
    published_grid_sizes = list(runtime["supported_grid_sizes"])
    published_mine_counts = {
        str(grid_size): _sample_test_mine_counts(runtime["supported_mine_counts"][str(grid_size)])
        for grid_size in published_grid_sizes
    }
    default_mine_counts = {
        str(grid_size): mine_counts[min(len(mine_counts) // 2, len(mine_counts) - 1)]
        for grid_size, mine_counts in (
            (grid_size, published_mine_counts[str(grid_size)]) for grid_size in published_grid_sizes
        )
    }
    return {
        "rules_sections": {
            "ways_to_win": "<p>Pick cells and avoid mines.</p>",
            "payout_display": "<p>The current payout is always shown.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Completed hands are visible in player history.</p>",
        },
        "published_grid_sizes": published_grid_sizes,
        "published_mine_counts": published_mine_counts,
        "default_mine_counts": default_mine_counts,
        "ui_labels": {
            "demo": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
            "real": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }


def _sample_test_mine_counts(values: list[int]) -> list[int]:
    if len(values) <= 5:
        return list(values)

    return list(values[:5])
