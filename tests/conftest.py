from __future__ import annotations

import copy
import os
from pathlib import Path
import time
from typing import Generator
from uuid import uuid4

import httpx
import psycopg
from psycopg.rows import DictRow, dict_row
from psycopg.types.json import Jsonb
import pytest

from app.modules.auth.service import ensure_local_admin
from app.modules.games.mines.runtime import get_runtime_config


type DbConnection = psycopg.Connection[DictRow]


MINES_BACKOFFICE_COLUMNS = (
    "game_code",
    "rules_sections_json",
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "ui_labels_json",
    "published_board_assets_json",
    "draft_rules_sections_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_ui_labels_json",
    "draft_board_assets_json",
    "updated_by_admin_user_id",
    "updated_at",
    "published_at",
    "draft_updated_by_admin_user_id",
    "draft_updated_at",
)

MINES_BACKOFFICE_JSON_COLUMNS = {
    "rules_sections_json",
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "ui_labels_json",
    "published_board_assets_json",
    "draft_rules_sections_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_ui_labels_json",
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
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                game_code,
                rules_sections_json,
                published_grid_sizes_json,
                published_mine_counts_json,
                default_mine_counts_json,
                ui_labels_json,
                published_board_assets_json,
                draft_rules_sections_json,
                draft_grid_sizes_json,
                draft_mine_counts_json,
                draft_default_mine_counts_json,
                draft_ui_labels_json,
                draft_board_assets_json,
                updated_by_admin_user_id,
                updated_at,
                published_at,
                draft_updated_by_admin_user_id,
                draft_updated_at
            FROM mines_backoffice_config
            WHERE game_code = 'mines'
            """
        )
        snapshot = cursor.fetchone()

    if snapshot is None:
        baseline_snapshot = _build_test_mines_backoffice_snapshot()
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO mines_backoffice_config (
                    game_code,
                    rules_sections_json,
                    published_grid_sizes_json,
                    published_mine_counts_json,
                    default_mine_counts_json,
                    ui_labels_json,
                    published_board_assets_json,
                    updated_at,
                    published_at
                )
                VALUES (
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    %s::jsonb,
                    %s::jsonb,
                    %s::jsonb,
                    %s::jsonb,
                    NOW(),
                    NOW()
                )
                """,
                (
                    "mines",
                    Jsonb(baseline_snapshot["rules_sections"]),
                    Jsonb(baseline_snapshot["published_grid_sizes"]),
                    Jsonb(baseline_snapshot["published_mine_counts"]),
                    Jsonb(baseline_snapshot["default_mine_counts"]),
                    Jsonb(baseline_snapshot["ui_labels"]),
                    Jsonb(baseline_snapshot["board_assets"]),
                ),
            )

    preserved_snapshot = copy.deepcopy(snapshot) if snapshot is not None else None
    yield

    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM mines_backoffice_config WHERE game_code = 'mines'")
        if preserved_snapshot is None:
            return

        values = [
            Jsonb(preserved_snapshot[column])
            if column in MINES_BACKOFFICE_JSON_COLUMNS and preserved_snapshot[column] is not None
            else preserved_snapshot[column]
            for column in MINES_BACKOFFICE_COLUMNS
        ]
        cursor.execute(
            f"""
            INSERT INTO mines_backoffice_config ({", ".join(MINES_BACKOFFICE_COLUMNS)})
            VALUES ({", ".join(["%s"] * len(MINES_BACKOFFICE_COLUMNS))})
            """,
            values,
        )


@pytest.fixture
def create_player(client: httpx.Client, site_access_password: str):
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

    return _create_player


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
def create_admin_user(login_admin):
    def _create_admin_user(prefix: str = "admin") -> dict[str, object]:
        email = f"{prefix}-{uuid4().hex[:12]}@example.com"
        password = f"StrongPass-{uuid4().hex[:12]}"
        bootstrap_data = ensure_local_admin(email=email, password=password)
        admin_user = {
            "email": email,
            "password": password,
            "user_id": bootstrap_data["user_id"],
        }
        login_payload = login_admin(
            email=str(admin_user["email"]),
            password=str(admin_user["password"]),
        )
        admin_user["access_token"] = login_payload["access_token"]
        return admin_user

    return _create_admin_user


@pytest.fixture
def auth_headers(client: httpx.Client):
    token_cache: dict[str, str | None] = {}

    def _auth_headers(
        access_token: str,
        *,
        include_game_launch_token: bool = True,
    ) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {access_token}"}
        if not include_game_launch_token:
            return headers

        # Mines operational endpoints require bearer + launch token in the monolite.
        if access_token not in token_cache:
            issue_response = client.post(
                "/games/mines/launch-token",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"game_code": "mines"},
            )
            token_cache[access_token] = (
                issue_response.json()["data"]["game_launch_token"]
                if issue_response.status_code == 200
                else None
            )

        game_launch_token = token_cache[access_token]
        if game_launch_token:
            headers["X-Game-Launch-Token"] = game_launch_token
        return headers

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
