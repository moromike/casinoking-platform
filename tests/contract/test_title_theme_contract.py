from __future__ import annotations

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
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET theme_tokens_json = NULL, draft_theme_tokens_json = NULL
            WHERE title_code = %s
            """,
            (TITLE_CODE,),
        )

    admin_user = create_admin_user(prefix="contract-title-theme-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)

    draft_response = client.put(
        f"/admin/titles/{TITLE_CODE}/theme",
        headers=headers,
        json={
            "tokens": {
                "--ck-bg": "#111827",
                "--ck-accent": "#22c55e",
            }
        },
    )

    assert draft_response.status_code == 200, draft_response.text
    draft_payload = draft_response.json()["data"]
    assert draft_payload["draft"]["tokens"]["--ck-bg"] == "#111827"
    assert draft_payload["published"]["tokens"]["--ck-bg"] == "#09090f"
    assert draft_payload["has_unpublished_changes"] is True

    public_before_publish = client.get(f"/titles/{TITLE_CODE}/theme")
    assert public_before_publish.status_code == 200
    assert public_before_publish.json()["data"]["tokens"]["--ck-bg"] == "#09090f"

    publish_response = client.post(
        f"/admin/titles/{TITLE_CODE}/theme/publish",
        headers=headers,
    )

    assert publish_response.status_code == 200, publish_response.text
    published_payload = publish_response.json()["data"]
    assert published_payload["published"]["tokens"]["--ck-bg"] == "#111827"
    assert published_payload["draft"]["tokens"]["--ck-bg"] == "#111827"
    assert published_payload["has_unpublished_changes"] is False

    public_after_publish = client.get(f"/titles/{TITLE_CODE}/theme")
    assert public_after_publish.status_code == 200
    assert public_after_publish.json()["data"]["tokens"]["--ck-bg"] == "#111827"


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
