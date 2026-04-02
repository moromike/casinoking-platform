from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import psycopg

from app.db.connection import db_connection

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations" / "sql"
MIGRATION_TABLE_NAME = "schema_migrations"
LEGACY_BASELINE_VERSION = 11
SPLIT_BASELINE_VERSION = 13
CURRENT_BASELINE_VERSION = 14
LEGACY_REQUIRED_TABLES = {
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
SPLIT_REQUIRED_TABLES = LEGACY_REQUIRED_TABLES | {
    "platform_rounds",
    "mines_game_rounds",
}
CURRENT_REQUIRED_TABLES = {
    "ledger_accounts",
    "wallet_accounts",
    "ledger_transactions",
    "ledger_entries",
    "users",
    "user_credentials",
    "password_reset_tokens",
    "admin_actions",
    "fairness_seed_rotations",
    "platform_rounds",
    "mines_game_rounds",
}
KNOWN_SCHEMA_TABLES = LEGACY_REQUIRED_TABLES | CURRENT_REQUIRED_TABLES
LEGACY_REQUIRED_SEQUENCES = {"game_sessions_nonce_seq"}
CURRENT_REQUIRED_SEQUENCES = {"mines_fairness_nonce_seq"}
KNOWN_SCHEMA_SEQUENCES = LEGACY_REQUIRED_SEQUENCES | CURRENT_REQUIRED_SEQUENCES


def apply_sql_migrations() -> dict[str, object]:
    migration_files = sorted(
        path for path in MIGRATIONS_DIR.glob("*.sql") if path.is_file()
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_migration_table(cursor)
            applied_names = _get_applied_migration_names(cursor)

            if not applied_names:
                inferred_version = _infer_existing_schema_version(cursor)
                if inferred_version is not None:
                    inferred_migrations = _migration_files_up_to_version(
                        migration_files,
                        inferred_version,
                    )
                    _record_existing_migrations(cursor, inferred_migrations)
                    applied_names = {path.name for path in inferred_migrations}

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
    return _infer_existing_schema_version(cursor) == LEGACY_BASELINE_VERSION


def _infer_existing_schema_version(cursor: psycopg.Cursor) -> int | None:
    found_tables = _get_public_tables(cursor, KNOWN_SCHEMA_TABLES)
    found_sequences = _get_public_sequences(cursor, KNOWN_SCHEMA_SEQUENCES)

    if found_tables == LEGACY_REQUIRED_TABLES and found_sequences == LEGACY_REQUIRED_SEQUENCES:
        return LEGACY_BASELINE_VERSION if _has_required_system_accounts(cursor) else None

    if found_tables == SPLIT_REQUIRED_TABLES and found_sequences == LEGACY_REQUIRED_SEQUENCES:
        return SPLIT_BASELINE_VERSION if _has_required_system_accounts(cursor) else None

    if found_tables == CURRENT_REQUIRED_TABLES and found_sequences == CURRENT_REQUIRED_SEQUENCES:
        return CURRENT_BASELINE_VERSION if _has_required_system_accounts(cursor) else None

    return None


def _get_public_tables(cursor: psycopg.Cursor, candidate_tables: set[str]) -> set[str]:
    if not candidate_tables:
        return set()

    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND table_name = ANY(%s)
        """,
        (list(candidate_tables),),
    )
    return {str(row["table_name"]) for row in cursor.fetchall()}


def _get_public_sequences(cursor: psycopg.Cursor, candidate_sequences: set[str]) -> set[str]:
    if not candidate_sequences:
        return set()

    cursor.execute(
        """
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
          AND sequence_name = ANY(%s)
        """,
        (list(candidate_sequences),),
    )
    return {str(row["sequence_name"]) for row in cursor.fetchall()}


def _has_required_system_accounts(cursor: psycopg.Cursor) -> bool:
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



def _migration_files_up_to_version(
    migration_files: list[Path],
    version: int,
) -> list[Path]:
    return [path for path in migration_files if _migration_version(path.name) <= version]


def _migration_version(migration_name: str) -> int:
    prefix, _, _ = migration_name.partition("__")
    return int(prefix)


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
