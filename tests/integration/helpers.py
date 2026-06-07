from __future__ import annotations

from pathlib import Path

BOXE_SCHEMA_MIGRATION_PATHS = (
    Path("backend/migrations/sql/0039__boxe_session_tables.sql"),
    Path("backend/migrations/sql/0047__boxe_demo_session_id.sql"),
    Path("backend/migrations/sql/0048__boxe_drop_sessions.sql"),
)

HI_LO_SCHEMA_MIGRATION_PATHS = (
    Path("backend/migrations/sql/0043__hi_lo_round_tables.sql"),
)

SHARED_CONSTRAINTS_MIGRATION_PATH = Path(
    "backend/migrations/sql/0051__boxe_hilo_cancelled_status.sql"
)

BOXE_SCHEMA_DOWN_SQL = """
DROP TABLE IF EXISTS boxe_idempotency_keys;
DROP TABLE IF EXISTS boxe_picks;
DROP TABLE IF EXISTS boxe_rounds;
"""

HI_LO_SCHEMA_DOWN_SQL = """
DROP TABLE IF EXISTS hi_lo_idempotency_keys;
DROP TABLE IF EXISTS hi_lo_actions;
DROP TABLE IF EXISTS hi_lo_rounds;
"""

_BOXE_POST_MIGRATION_SQL = """
ALTER TABLE boxe_idempotency_keys
    DROP CONSTRAINT IF EXISTS boxe_idempotency_keys_player_id_fkey;
"""

_HI_LO_POST_MIGRATION_SQL = """
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_player_id_fkey;
ALTER TABLE hi_lo_idempotency_keys
    DROP CONSTRAINT IF EXISTS hi_lo_idempotency_keys_player_id_fkey;
"""


def apply_boxe_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in BOXE_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_BOXE_POST_MIGRATION_SQL)


def apply_hi_lo_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in HI_LO_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_HI_LO_POST_MIGRATION_SQL)


def apply_shared_constraints_migration(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(SHARED_CONSTRAINTS_MIGRATION_PATH.read_text(encoding="utf-8"))


def create_game_access_session(
    client,
    headers,
    *,
    game_code: str,
    title_code: str,
    site_code: str = "casinoking",
) -> str:
    """Create a game access session and return its id."""
    resp = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]
