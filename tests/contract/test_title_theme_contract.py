from __future__ import annotations

from uuid import uuid4

from psycopg.types.json import Jsonb


TITLE_CODE = "mines_classic"


def test_title_theme_returns_default_tokens(client, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE title_configs SET theme_tokens_json = NULL WHERE title_code = %s",
            (TITLE_CODE,),
        )

    response = client.get(f"/titles/{TITLE_CODE}/theme")

    assert response.status_code == 200, response.text
    assert response.headers["etag"]
    assert response.headers["cache-control"] == "public, max-age=60"
    payload = response.json()["data"]
    assert payload["title_code"] == TITLE_CODE
    assert payload["tokens"]["--ck-bg"] == "#09090f"
    assert payload["tokens"]["--ck-accent"] == "#56dc49"
    assert isinstance(payload["assets"], dict)
    assert payload["etag"] == response.headers["etag"]


def test_title_theme_applies_published_token_overrides(client, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = %s::jsonb
            WHERE title_code = %s
            """,
            (
                Jsonb(
                    {
                        "--ck-bg": "#101820",
                        "--ck-accent": "#f2aa4c",
                        "--ck-radius-cell": "12px",
                    }
                ),
                TITLE_CODE,
            ),
        )

    response = client.get(f"/titles/{TITLE_CODE}/theme")

    assert response.status_code == 200, response.text
    tokens = response.json()["data"]["tokens"]
    assert tokens["--ck-bg"] == "#101820"
    assert tokens["--ck-accent"] == "#f2aa4c"
    assert tokens["--ck-radius-cell"] == "12px"
    assert tokens["--ck-danger"] == "#ff764e"


def test_title_theme_returns_skin_separately_from_flat_tokens(client, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = %s::jsonb
            WHERE title_code = %s
            """,
            (
                Jsonb(
                    {
                        "--ck-bg": "#101820",
                        "skin": {
                            "title_render_mode": "image",
                            "button_density": "compact",
                            "button_radius": "rounded",
                            "button_style": "outlined",
                            "button_emphasis": "secondary",
                            "game_area_background_fit": "contain",
                            "game_area_background_position": "left",
                            "game_area_overlay": "strong",
                        },
                    }
                ),
                TITLE_CODE,
            ),
        )

    response = client.get(f"/titles/{TITLE_CODE}/theme")

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["tokens"]["--ck-bg"] == "#101820"
    assert "skin" not in payload["tokens"]
    assert payload["skin"] == {
        "title_render_mode": "image",
        "button_density": "compact",
        "button_radius": "rounded",
        "button_style": "outlined",
        "button_emphasis": "secondary",
        "game_area_background_fit": "contain",
        "game_area_background_position": "left",
        "game_area_overlay": "strong",
    }


def test_title_theme_rejects_unsupported_tokens(client, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = %s::jsonb
            WHERE title_code = %s
            """,
            (
                Jsonb({"--ck-unknown": "#ffffff"}),
                TITLE_CODE,
            ),
        )

    response = client.get(f"/titles/{TITLE_CODE}/theme")

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Unsupported theme token: --ck-unknown",
        },
    }


def test_title_theme_rejects_unsupported_skin_enum(client, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = %s::jsonb
            WHERE title_code = %s
            """,
            (
                Jsonb({"skin": {"game_area_overlay": "rgba(0,0,0,0.5)"}}),
                TITLE_CODE,
            ),
        )

    response = client.get(f"/titles/{TITLE_CODE}/theme")

    assert response.status_code == 422
    assert response.json()["error"]["message"] == (
        "Unsupported theme skin value for game_area_overlay: rgba(0,0,0,0.5)"
    )


def test_title_theme_returns_404_for_unknown_title(client) -> None:
    response = client.get("/titles/missing_title/theme")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_admin_title_theme_draft_publish_contract(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    variant_title_code = _create_mines_variant(db_connection, "theme")
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = NULL, draft_theme_tokens_json = NULL
            WHERE title_code = %s
            """,
            (variant_title_code,),
        )

    admin_user = create_admin_user(prefix="contract-title-theme-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)

    try:
        draft_response = client.put(
            f"/admin/titles/{variant_title_code}/theme",
            headers=headers,
            json={
                "tokens": {
                    "--ck-bg": "#111827",
                    "--ck-accent": "#22c55e",
                    "skin": {
                        "title_render_mode": "image",
                        "button_density": "large",
                        "button_radius": "rounded",
                        "button_style": "raised",
                        "button_emphasis": "primary",
                        "game_area_background_fit": "cover",
                        "game_area_background_position": "right",
                        "game_area_overlay": "medium",
                    },
                }
            },
        )

        assert draft_response.status_code == 200, draft_response.text
        draft_payload = draft_response.json()["data"]
        assert draft_payload["draft"]["tokens"]["--ck-bg"] == "#111827"
        assert draft_payload["draft"]["skin"]["title_render_mode"] == "image"
        assert draft_payload["draft"]["skin"]["game_area_background_position"] == "right"
        assert draft_payload["published"]["tokens"]["--ck-bg"] == "#09090f"
        assert draft_payload["published"]["skin"] is None
        assert draft_payload["has_unpublished_changes"] is True

        public_before_publish = client.get(f"/titles/{variant_title_code}/theme")
        assert public_before_publish.status_code == 200
        assert public_before_publish.json()["data"]["tokens"]["--ck-bg"] == "#09090f"
        assert "skin" not in public_before_publish.json()["data"]

        publish_response = client.post(
            f"/admin/titles/{variant_title_code}/theme/publish",
            headers=headers,
        )

        assert publish_response.status_code == 200, publish_response.text
        published_payload = publish_response.json()["data"]
        assert published_payload["published"]["tokens"]["--ck-bg"] == "#111827"
        assert published_payload["draft"]["tokens"]["--ck-bg"] == "#111827"
        assert published_payload["published"]["skin"]["title_render_mode"] == "image"
        assert published_payload["has_unpublished_changes"] is False

        public_after_publish = client.get(f"/titles/{variant_title_code}/theme")
        assert public_after_publish.status_code == 200
        assert public_after_publish.json()["data"]["tokens"]["--ck-bg"] == "#111827"
        assert public_after_publish.json()["data"]["skin"]["game_area_background_position"] == "right"
    finally:
        _delete_mines_variant(db_connection, variant_title_code)


def test_admin_title_theme_publish_blocks_low_contrast(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    variant_title_code = _create_mines_variant(db_connection, "low_contrast")
    admin_user = create_admin_user(prefix="contract-title-theme-contrast-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)

    try:
        draft_response = client.put(
            f"/admin/titles/{variant_title_code}/theme",
            headers=headers,
            json={
                "tokens": {
                    "--ck-bg": "#111111",
                    "--ck-surface": "#111111",
                    "--ck-surface-strong": "#111111",
                    "--ck-fg": "#121212",
                    "--ck-muted": "#121212",
                    "--ck-accent": "#121212",
                }
            },
        )
        assert draft_response.status_code == 200, draft_response.text

        publish_response = client.post(
            f"/admin/titles/{variant_title_code}/theme/publish",
            headers=headers,
        )

        assert publish_response.status_code == 422
        assert publish_response.json()["error"]["message"].startswith(
            "Theme contrast is too low"
        )
    finally:
        _delete_mines_variant(db_connection, variant_title_code)


def test_admin_title_theme_rejects_master_mutation(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-title-theme-master-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)

    draft_response = client.put(
        f"/admin/titles/{TITLE_CODE}/theme",
        headers=headers,
        json={"tokens": {"--ck-bg": "#111827"}},
    )
    assert draft_response.status_code == 422

    publish_response = client.post(
        f"/admin/titles/{TITLE_CODE}/theme/publish",
        headers=headers,
    )
    assert publish_response.status_code == 422


def test_admin_title_theme_rejects_player_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-title-theme-player")

    response = client.get(
        f"/admin/titles/{TITLE_CODE}/theme",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def _create_mines_variant(db_connection, suffix: str) -> str:
    title_code = f"mines_contract_{suffix}_{uuid4().hex[:8]}"
    with db_connection.cursor() as cursor:
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
            VALUES (%s, 'mines', 'Mines Contract Variant', 'active', false, %s)
            """,
            (title_code, TITLE_CODE),
        )
        cursor.execute(
            """
            INSERT INTO site_titles (site_code, title_code, position, status)
            VALUES ('casinoking', %s, 99, 'active')
            """,
            (title_code,),
        )
        cursor.execute(
            """
            INSERT INTO title_configs (
                title_code,
                rules_sections_json,
                ui_labels_json,
                theme_tokens_json,
                draft_rules_sections_json,
                draft_ui_labels_json,
                draft_theme_tokens_json
            )
            SELECT
                %s,
                rules_sections_json,
                ui_labels_json,
                NULL,
                rules_sections_json,
                ui_labels_json,
                NULL
            FROM title_configs
            WHERE title_code = %s
            """,
            (title_code, TITLE_CODE),
        )
    return title_code


def _delete_mines_variant(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))
