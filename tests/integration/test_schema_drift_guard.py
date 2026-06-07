from __future__ import annotations

import pytest


@pytest.fixture(scope="module", autouse=True)
def boxe_and_hi_lo_schema(database_url: str):
    from tests.integration.helpers import (
        BOXE_SCHEMA_DOWN_SQL,
        HI_LO_SCHEMA_DOWN_SQL,
        apply_boxe_schema_migrations,
        apply_hi_lo_schema_migrations,
        apply_shared_constraints_migration,
    )
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(BOXE_SCHEMA_DOWN_SQL)
            cursor.execute(HI_LO_SCHEMA_DOWN_SQL)
        apply_boxe_schema_migrations(connection)
        apply_hi_lo_schema_migrations(connection)
        apply_shared_constraints_migration(connection)
        yield


class TestSchemaDriftGuard:
    """Fail fast if canonical migrations are not applied in test fixtures."""

    def test_boxe_constraint_includes_cancelled(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'boxe_rounds_closed_at_consistency_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint boxe_rounds_closed_at_consistency_check missing"
            assert "cancelled" in row["pg_get_constraintdef"], f"Constraint missing cancelled: {row['pg_get_constraintdef']}"

    def test_hi_lo_constraint_includes_cancelled(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'hi_lo_rounds_closed_at_consistency_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint hi_lo_rounds_closed_at_consistency_check missing"
            assert "cancelled" in row["pg_get_constraintdef"], f"Constraint missing cancelled: {row['pg_get_constraintdef']}"

    def test_boxe_outcome_includes_admin_force_close(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'boxe_rounds_outcome_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint boxe_rounds_outcome_check missing"
            assert "admin_force_close" in row["pg_get_constraintdef"], f"Constraint missing admin_force_close: {row['pg_get_constraintdef']}"

    def test_hi_lo_outcome_includes_admin_force_close(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conname = 'hi_lo_rounds_outcome_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint hi_lo_rounds_outcome_check missing"
            assert "admin_force_close" in row["pg_get_constraintdef"], f"Constraint missing admin_force_close: {row['pg_get_constraintdef']}"

    def test_forbidden_fk_absent(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT conname FROM pg_constraint
                WHERE conname IN (
                    'boxe_idempotency_keys_player_id_fkey',
                    'hi_lo_rounds_player_id_fkey',
                    'hi_lo_idempotency_keys_player_id_fkey'
                )
                """
            )
            rows = cursor.fetchall()
            assert rows == [], f"Forbidden FK constraints found: {[r[0] for r in rows]}"
