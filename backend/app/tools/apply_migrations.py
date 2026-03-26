from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import psycopg

from app.db.connection import db_connection

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations" / "sql"
MIGRATION_TABLE_NAME = "schema_migrations"


def apply_sql_migrations() -> dict[str, object]:
    migration_files = sorted(
        path for path in MIGRATIONS_DIR.glob("*.sql") if path.is_file()
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_migration_table(cursor)
            applied_names = _get_applied_migration_names(cursor)

            if not applied_names and _looks_like_legacy_initialized_schema(cursor):
                _record_existing_migrations(cursor, migration_files)
                applied_names = {path.name for path in migration_files}

            applied_now: list[str] = []
            skipped: list[str] = []

            for migration_path in migration_files:
                if migration_path.name in applied_names:
                    skipped.append(migration_path.name)
                    continue

                cursor.execute(migration_path.read_text(encoding="utf-8"))
                cursor.execute(
                    f"""
                    INSERT INTO {MIGRATION_TABLE_NAME} (
                        migration_name,
                        applied_at
                    )
                    VALUES (%s, %s)
                    """,
                    (migration_path.name, datetime.now(UTC)),
                )
                applied_now.append(migration_path.name)

    return {
        "applied": applied_now,
        "skipped": skipped,
        "total_known": len(migration_files),
    }


def _ensure_migration_table(cursor: psycopg.Cursor) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE_NAME} (
            migration_name varchar(255) PRIMARY KEY,
            applied_at timestamptz NOT NULL
        )
        """
    )


def _get_applied_migration_names(cursor: psycopg.Cursor) -> set[str]:
    cursor.execute(
        f"""
        SELECT migration_name
        FROM {MIGRATION_TABLE_NAME}
        """
    )
    return {str(row["migration_name"]) for row in cursor.fetchall()}


def _looks_like_legacy_initialized_schema(cursor: psycopg.Cursor) -> bool:
    required_tables = {
        "ledger_accounts",
        "wallet_accounts",
        "ledger_transactions",
        "ledger_entries",
        "users",
        "user_credentials",
        "password_reset_tokens",
        "game_sessions",
        "admin_actions",
        "fairness_seed_rotations",
    }

    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY(%s)
        """,
        (list(required_tables),),
    )
    found_tables = {str(row["table_name"]) for row in cursor.fetchall()}
    if found_tables != required_tables:
        return False

    cursor.execute(
        """
        SELECT COUNT(*) AS system_account_count
        FROM ledger_accounts
        WHERE account_code IN (
            'HOUSE_CASH',
            'HOUSE_BONUS',
            'PROMO_RESERVE',
            'GAME_PNL_MINES'
        )
        """
    )
    system_account_count = int(cursor.fetchone()["system_account_count"])
    return system_account_count == 4


def _record_existing_migrations(
    cursor: psycopg.Cursor,
    migration_files: list[Path],
) -> None:
    applied_at = datetime.now(UTC)
    cursor.executemany(
        f"""
        INSERT INTO {MIGRATION_TABLE_NAME} (
            migration_name,
            applied_at
        )
        VALUES (%s, %s)
        ON CONFLICT (migration_name) DO NOTHING
        """,
        [(migration_path.name, applied_at) for migration_path in migration_files],
    )


if __name__ == "__main__":
    result = apply_sql_migrations()
    print(
        "Applied SQL migrations:",
        ", ".join(result["applied"]) if result["applied"] else "none",
    )
    print(
        "Skipped SQL migrations:",
        ", ".join(result["skipped"]) if result["skipped"] else "none",
    )
