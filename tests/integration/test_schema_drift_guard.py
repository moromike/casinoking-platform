from __future__ import annotations


class TestSchemaDriftGuard:
    """Read-only guard: fail fast if a preceding test left schema degraded."""

    def test_boxe_constraint_includes_cancelled(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid) AS def
                FROM pg_constraint
                WHERE conname = 'boxe_rounds_closed_at_consistency_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint boxe_rounds_closed_at_consistency_check missing"
            assert "cancelled" in row["def"], f"Constraint missing cancelled: {row['def']}"

    def test_hi_lo_constraint_includes_cancelled(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid) AS def
                FROM pg_constraint
                WHERE conname = 'hi_lo_rounds_closed_at_consistency_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint hi_lo_rounds_closed_at_consistency_check missing"
            assert "cancelled" in row["def"], f"Constraint missing cancelled: {row['def']}"

    def test_boxe_outcome_includes_admin_force_close(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid) AS def
                FROM pg_constraint
                WHERE conname = 'boxe_rounds_outcome_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint boxe_rounds_outcome_check missing"
            assert "admin_force_close" in row["def"], f"Constraint missing admin_force_close: {row['def']}"

    def test_hi_lo_outcome_includes_admin_force_close(self, db_connection):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_get_constraintdef(oid) AS def
                FROM pg_constraint
                WHERE conname = 'hi_lo_rounds_outcome_check'
                """
            )
            row = cursor.fetchone()
            assert row is not None, "Constraint hi_lo_rounds_outcome_check missing"
            assert "admin_force_close" in row["def"], f"Constraint missing admin_force_close: {row['def']}"

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
