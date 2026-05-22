from __future__ import annotations

from typing import Generator
from uuid import uuid4

import pytest


def _build_backoffice_payload() -> dict[str, object]:
    return {
        "rules_sections": {
            "ways_to_win": "<p>Pick at least one diamond, then collect.</p>",
            "payout_display": "<p>The highlighted multiplier is the payout available right now.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Authenticated players can inspect completed hands from account history.</p>",
        },
        "published_grid_sizes": [9, 16],
        "published_mine_counts": {
            "9": [1, 3, 5],
            "16": [1, 5, 8],
        },
        "default_mine_counts": {
            "9": 3,
            "16": 5,
        },
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
                "bet": "Place bet",
                "bet_loading": "Placing bet...",
                "collect": "Collect win",
                "collect_loading": "Collecting win...",
                "home": "Return home",
                "fullscreen": "Go fullscreen",
                "game_info": "Open game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }


@pytest.fixture
def secondary_mines_title(db_connection) -> Generator[str, None, None]:
    """Create a second Mines Title for isolation tests; clean it up afterwards."""

    title_code = "mines_book_of_ra"
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_titles (title_code, engine_code, display_name, status)
            VALUES (%s, 'mines', 'Mines Book of Ra', 'active')
            ON CONFLICT (title_code) DO NOTHING
            """,
            (title_code,),
        )
        cursor.execute(
            """
            INSERT INTO site_titles (site_code, title_code, position, status)
            VALUES ('casinoking', %s, 1, 'active')
            ON CONFLICT (site_code, title_code) DO NOTHING
            """,
            (title_code,),
        )

    yield title_code

    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM mines_title_configs WHERE title_code = %s",
            (title_code,),
        )
        cursor.execute(
            "DELETE FROM title_configs WHERE title_code = %s",
            (title_code,),
        )
        cursor.execute(
            "DELETE FROM site_titles WHERE title_code = %s",
            (title_code,),
        )
        cursor.execute(
            "DELETE FROM game_titles WHERE title_code = %s",
            (title_code,),
        )


def test_phase3_schema_is_in_place(db_connection) -> None:
    """Migration 0025 leaves the new tables and the read-only view in place."""

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                'title_configs',
                'mines_title_configs',
                'mines_backoffice_config',
                'mines_backoffice_config_legacy'
              )
            ORDER BY table_name
            """
        )
        rows = list(cursor.fetchall())

    table_types = {row["table_name"]: row["table_type"] for row in rows}
    assert table_types.get("title_configs") == "BASE TABLE"
    assert table_types.get("mines_title_configs") == "BASE TABLE"
    assert table_types.get("mines_backoffice_config_legacy") == "BASE TABLE"
    assert table_types.get("mines_backoffice_config") == "VIEW"


def test_legacy_view_returns_same_payload_as_new_tables(db_connection) -> None:
    """The compatibility view JOINs the two new tables and matches their data."""

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                tc.rules_sections_json,
                tc.ui_labels_json,
                mtc.published_grid_sizes_json,
                mtc.published_mine_counts_json
            FROM title_configs tc
            JOIN mines_title_configs mtc ON mtc.title_code = tc.title_code
            WHERE tc.title_code = 'mines_classic'
            """
        )
        joined = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                rules_sections_json,
                ui_labels_json,
                published_grid_sizes_json,
                published_mine_counts_json
            FROM mines_backoffice_config
            """
        )
        view_row = cursor.fetchone()

    assert joined is not None
    assert view_row is not None
    assert view_row["rules_sections_json"] == joined["rules_sections_json"]
    assert view_row["ui_labels_json"] == joined["ui_labels_json"]
    assert view_row["published_grid_sizes_json"] == joined["published_grid_sizes_json"]
    assert view_row["published_mine_counts_json"] == joined["published_mine_counts_json"]


def test_mines_master_is_read_only_for_title_aware_mutations(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    """The Mines master can be read but not mutated from backoffice endpoints."""

    admin_user = create_admin_user(prefix="integration-title-config-master-admin")

    get_response = client.get(
        "/admin/games/titles/mines_classic/config",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert get_response.status_code == 200
    initial_payload = get_response.json()["data"]
    assert initial_payload["game_code"] == "mines"
    assert initial_payload["title_code"] == "mines_classic"
    assert "draft" in initial_payload
    assert "published" in initial_payload

    update_payload = _build_backoffice_payload()
    update_payload["ui_labels"]["real"]["collect"] = "Collect win title-aware marker"

    put_response = client.put(
        "/admin/games/titles/mines_classic/config",
        headers=auth_headers(admin_user["access_token"]),
        json=update_payload,
    )
    assert put_response.status_code == 422

    publish_response = client.post(
        "/admin/games/titles/mines_classic/config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 422


def test_legacy_endpoints_are_aliases_of_mines_classic(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    """Legacy /admin/games/mines/backoffice-config* still operate on mines_classic."""

    admin_user = create_admin_user(prefix="integration-title-config-legacy-admin")

    legacy_get = client.get(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
    )
    new_get = client.get(
        "/admin/games/titles/mines_classic/config",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert legacy_get.status_code == 200
    assert new_get.status_code == 200

    legacy_data = legacy_get.json()["data"]
    new_data = new_get.json()["data"]
    # The two endpoints must expose the same Title (only the `title_code` field
    # is added by the new endpoints).
    assert legacy_data["game_code"] == new_data["game_code"] == "mines"
    assert new_data["title_code"] == "mines_classic"
    assert legacy_data["published"] == new_data["published"]
    assert legacy_data["draft"] == new_data["draft"]

    legacy_put = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
        json=_build_backoffice_payload(),
    )
    assert legacy_put.status_code == 422


def test_second_mines_title_has_isolated_configuration(
    client,
    create_admin_user,
    auth_headers,
    secondary_mines_title,
    db_connection,
) -> None:
    """A different Title with the mines engine has its own config row."""

    admin_user = create_admin_user(prefix="integration-title-config-isolation-admin")
    title_code = secondary_mines_title

    seed_payload = _build_backoffice_payload()
    seed_payload["published_grid_sizes"] = [9]
    seed_payload["published_mine_counts"] = {"9": [1, 3, 5]}
    seed_payload["default_mine_counts"] = {"9": 5}
    seed_payload["ui_labels"]["real"]["bet"] = "Place bet (Book of Ra)"

    put_response = client.put(
        f"/admin/games/titles/{title_code}/config",
        headers=auth_headers(admin_user["access_token"]),
        json=seed_payload,
    )
    assert put_response.status_code == 200
    payload = put_response.json()["data"]
    assert payload["title_code"] == title_code
    assert payload["draft"]["published_grid_sizes"] == [9]
    assert payload["draft"]["ui_labels"]["real"]["bet"] == "Place bet (Book of Ra)"

    publish_response = client.post(
        f"/admin/games/titles/{title_code}/config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200

    # Verify mines_classic is not affected.
    classic_response = client.get(
        "/admin/games/titles/mines_classic/config",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert classic_response.status_code == 200
    classic_data = classic_response.json()["data"]
    assert classic_data["published"]["ui_labels"]["real"]["bet"] != "Place bet (Book of Ra)"
    assert classic_data["published"]["published_grid_sizes"] != [9]

    # The new Title must own its own row in both tables.
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT title_code FROM title_configs WHERE title_code = %s",
            (title_code,),
        )
        assert cursor.fetchone() is not None
        cursor.execute(
            "SELECT title_code FROM mines_title_configs WHERE title_code = %s",
            (title_code,),
        )
        assert cursor.fetchone() is not None


def test_admin_can_duplicate_mines_title_from_existing_title(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    """F7-B minimal slice: duplicate one Mines Title into isolated config rows."""

    admin_user = create_admin_user(prefix="integration-title-duplicate-admin")
    title_code = f"mines_variant_{uuid4().hex[:8]}"

    try:
        response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Variant",
                "site_code": "casinoking",
            },
        )

        assert response.status_code == 200
        duplicated_title = response.json()["data"]
        assert duplicated_title["title_code"] == title_code
        assert duplicated_title["engine_code"] == "mines"
        assert duplicated_title["site_title_status"] == "active"

        config_response = client.get(
            f"/admin/games/titles/{title_code}/config",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert config_response.status_code == 200
        config = config_response.json()["data"]
        assert config["title_code"] == title_code
        assert config["has_unpublished_changes"] is False
        assert config["published"]["published_grid_sizes"]
        assert config["draft"]["board_assets"] == {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        }

        catalog_response = client.get("/catalog/sites/casinoking/titles")
        assert catalog_response.status_code == 200
        catalog_titles = catalog_response.json()["data"]["titles"]
        assert any(title["title_code"] == title_code for title in catalog_titles)

        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT title_code FROM game_titles WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT title_code FROM site_titles WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT title_code FROM title_configs WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT title_code FROM mines_title_configs WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM mines_title_configs WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM title_configs WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM site_titles WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM game_titles WHERE title_code = %s",
                (title_code,),
            )


def test_admin_can_duplicate_boxe_title_from_existing_master(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-boxe-title-duplicate-admin")
    title_code = f"boxe_variant_{uuid4().hex[:8]}"

    try:
        response = client.post(
            "/admin/games/titles/boxe/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "BOXE Variant",
                "site_code": "casinoking",
                "is_test": True,
            },
        )

        assert response.status_code == 200, response.text
        duplicated_title = response.json()["data"]
        assert duplicated_title["title_code"] == title_code
        assert duplicated_title["engine_code"] == "boxe"
        assert duplicated_title["site_title_status"] == "active"
        assert duplicated_title["is_test"] is True

        config_response = client.get(
            f"/admin/games/boxe/config?title_code={title_code}",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert config_response.status_code == 200, config_response.text
        config = config_response.json()["data"]
        assert config["title_code"] == title_code
        assert config["has_unpublished_changes"] is False
        assert config["published"]["rows_enabled"] == [4, 5, 6, 7, 8]
        assert config["draft"]["difficulty_enabled"] == ["easy", "medium", "hard"]

        with db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT title_code FROM title_configs WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT title_code FROM boxe_admin_config WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT title_code FROM mines_title_configs WHERE title_code = %s",
                (title_code,),
            )
            assert cursor.fetchone() is None
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM boxe_admin_config WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM title_configs WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM site_titles WHERE title_code = %s",
                (title_code,),
            )
            cursor.execute(
                "DELETE FROM game_titles WHERE title_code = %s",
                (title_code,),
            )


def test_duplicate_mines_title_rejects_existing_title_code(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-duplicate-conflict-admin")
    response = client.post(
        "/admin/games/titles/mines_classic/duplicate",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "title_code": "mines_classic",
            "display_name": "Mines Classic Copy",
            "site_code": "casinoking",
        },
    )

    assert response.status_code == 409


def test_duplicate_mines_title_rejects_variant_source(
    client,
    create_admin_user,
    auth_headers,
    secondary_mines_title,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-duplicate-source-admin")
    response = client.post(
        f"/admin/games/titles/{secondary_mines_title}/duplicate",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "title_code": f"mines_variant_{uuid4().hex[:8]}",
            "display_name": "Mines Variant",
            "site_code": "casinoking",
        },
    )

    assert response.status_code == 422


def test_unknown_title_returns_404(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-config-unknown-admin")
    response = client.get(
        "/admin/games/titles/does-not-exist/config",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert response.status_code == 404


def test_first_write_on_empty_environment_creates_complete_rows(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
    secondary_mines_title,
) -> None:
    """CTO requirement: with empty title_configs/mines_title_configs the first
    PUT must populate both tables with valid defaults that satisfy the NOT NULL
    constraints, and a subsequent POST publish must succeed.
    """

    admin_user = create_admin_user(prefix="integration-title-config-empty-admin")

    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (secondary_mines_title,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (secondary_mines_title,))
        cursor.execute("SELECT count(*) AS n FROM title_configs WHERE title_code = %s", (secondary_mines_title,))
        assert cursor.fetchone()["n"] == 0
        cursor.execute(
            "SELECT count(*) AS n FROM mines_title_configs WHERE title_code = %s",
            (secondary_mines_title,),
        )
        assert cursor.fetchone()["n"] == 0

    put_response = client.put(
        f"/admin/games/titles/{secondary_mines_title}/config",
        headers=auth_headers(admin_user["access_token"]),
        json=_build_backoffice_payload(),
    )
    assert put_response.status_code == 200

    publish_response = client.post(
        f"/admin/games/titles/{secondary_mines_title}/config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200
    published = publish_response.json()["data"]["published"]
    assert published["published_grid_sizes"] == [9, 16]
    assert published["default_mine_counts"]["9"] == 3

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                rules_sections_json IS NOT NULL AS has_rules,
                ui_labels_json IS NOT NULL AS has_labels
            FROM title_configs
            WHERE title_code = %s
            """,
            (secondary_mines_title,),
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["has_rules"] is True
        assert row["has_labels"] is True

        cursor.execute(
            """
            SELECT
                published_grid_sizes_json IS NOT NULL AS has_grids,
                published_mine_counts_json IS NOT NULL AS has_counts,
                default_mine_counts_json IS NOT NULL AS has_defaults,
                published_board_assets_json IS NOT NULL AS has_assets
            FROM mines_title_configs
            WHERE title_code = %s
            """,
            (secondary_mines_title,),
        )
        engine_row = cursor.fetchone()
        assert engine_row is not None
        assert engine_row["has_grids"] is True
        assert engine_row["has_counts"] is True
        assert engine_row["has_defaults"] is True
        assert engine_row["has_assets"] is True
