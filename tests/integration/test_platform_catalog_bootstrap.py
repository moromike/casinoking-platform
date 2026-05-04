from __future__ import annotations

import pytest
from psycopg import errors


def test_platform_catalog_bootstrap_seed_and_migration_record(db_helpers):
    engine_row = db_helpers.fetchone(
        """
        SELECT engine_code, display_name, runtime_module, status
        FROM game_engines
        WHERE engine_code = %s
        """,
        ("mines",),
    )
    assert engine_row == {
        "engine_code": "mines",
        "display_name": "Mines",
        "runtime_module": "app.modules.games.mines",
        "status": "active",
    }

    title_row = db_helpers.fetchone(
        """
        SELECT title_code, engine_code, display_name, status
        FROM game_titles
        WHERE title_code = %s
        """,
        ("mines_classic",),
    )
    assert title_row == {
        "title_code": "mines_classic",
        "engine_code": "mines",
        "display_name": "Mines Classic",
        "status": "active",
    }

    site_row = db_helpers.fetchone(
        """
        SELECT site_code, display_name, base_url, status
        FROM sites
        WHERE site_code = %s
        """,
        ("casinoking",),
    )
    assert site_row == {
        "site_code": "casinoking",
        "display_name": "CasinoKing",
        "base_url": None,
        "status": "active",
    }

    site_title_row = db_helpers.fetchone(
        """
        SELECT site_code, title_code, position, status
        FROM site_titles
        WHERE site_code = %s
          AND title_code = %s
        """,
        ("casinoking", "mines_classic"),
    )
    assert site_title_row == {
        "site_code": "casinoking",
        "title_code": "mines_classic",
        "position": 0,
        "status": "active",
    }

    migration_row = db_helpers.fetchone(
        """
        SELECT migration_name
        FROM schema_migrations
        WHERE migration_name = %s
        """,
        ("0023__platform_catalog_bootstrap.sql",),
    )
    assert migration_row == {"migration_name": "0023__platform_catalog_bootstrap.sql"}


def test_platform_catalog_bootstrap_foreign_keys(db_connection):
    with pytest.raises(errors.ForeignKeyViolation):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO game_titles (
                    title_code,
                    engine_code,
                    display_name,
                    status
                )
                VALUES (%s, %s, %s, %s)
                """,
                ("invalid_missing_engine", "missing_engine", "Invalid", "active"),
            )
    db_connection.rollback()

    with pytest.raises(errors.ForeignKeyViolation):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO site_titles (
                    site_code,
                    title_code,
                    position,
                    status
                )
                VALUES (%s, %s, %s, %s)
                """,
                ("missing_site", "mines_classic", 0, "active"),
            )
    db_connection.rollback()

    with pytest.raises(errors.ForeignKeyViolation):
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO site_titles (
                    site_code,
                    title_code,
                    position,
                    status
                )
                VALUES (%s, %s, %s, %s)
                """,
                ("casinoking", "missing_title", 0, "active"),
            )
    db_connection.rollback()
