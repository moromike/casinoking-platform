from __future__ import annotations

from uuid import uuid4

import pytest


def _demo_token(client) -> str:
    response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.40.0.{uuid4().int % 250 + 1}"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["anonymous_token"]


def _png_bytes_with_size(*, width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_game_library_exposes_visible_demo_variants_only(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-library-admin")
    player = create_authenticated_player(prefix="integration-library-player")
    title_code = f"mines_library_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Library Variant",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        upload_response = client.post(
            f"/admin/titles/{title_code}/assets",
            headers=auth_headers(admin_user["access_token"]),
            data={"asset_kind": "game_card"},
            files={
                "file": (
                    "game-card.png",
                    _png_bytes_with_size(width=512, height=512),
                    "image/png",
                )
            },
        )
        assert upload_response.status_code == 200, upload_response.text
        game_card_asset = upload_response.json()["data"]
        assert game_card_asset["asset_kind"] == "game_card"

        hidden_library_response = client.get("/games/library")
        assert hidden_library_response.status_code == 200
        hidden_titles = hidden_library_response.json()["data"]["titles"]
        assert all(title["title_code"] != title_code for title in hidden_titles)

        hidden_demo_token = _demo_token(client)
        hidden_demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": hidden_demo_token},
            json={"title_code": title_code},
        )
        assert hidden_demo_launch_response.status_code == 422
        assert hidden_demo_launch_response.json()["error"]["message"] == "Title is not visible in the player library"

        hidden_real_launch_response = client.post(
            "/games/mines/launch-token",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={"game_code": "mines", "title_code": title_code, "mode": "real"},
        )
        assert hidden_real_launch_response.status_code == 422
        assert hidden_real_launch_response.json()["error"]["message"] == "Title is not visible in the player library"

        publish_response = client.put(
            f"/admin/sites/casinoking/titles/{title_code}/publication",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "lobby_visibility": "visible",
                "demo_enabled": True,
                "real_enabled": False,
                "lobby_display_name": "Mines Library Demo",
                "lobby_description": "Demo library variant",
                "featured": True,
                "position": 7,
            },
        )
        assert publish_response.status_code == 200, publish_response.text
        publication = publish_response.json()["data"]["publication"]
        assert publication["lobby_visibility"] == "visible"
        assert publication["demo_enabled"] is True

        library_response = client.get("/games/library")
        assert library_response.status_code == 200
        titles = library_response.json()["data"]["titles"]
        library_title = next(title for title in titles if title["title_code"] == title_code)
        assert library_title["display_name"] == "Mines Library Demo"
        assert library_title["description"] == "Demo library variant"
        assert library_title["demo_enabled"] is True
        assert library_title["real_enabled"] is False
        assert library_title["featured"] is True
        assert library_title["game_card_asset"] == {
            "id": game_card_asset["id"],
            "asset_kind": "game_card",
            "public_url": game_card_asset["public_url"],
            "mime": "image/png",
            "byte_size": game_card_asset["byte_size"],
            "created_at": game_card_asset["created_at"],
        }

        demo_token = _demo_token(client)
        demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": demo_token},
            json={"title_code": title_code},
        )
        assert demo_launch_response.status_code == 200
        assert demo_launch_response.json()["data"]["title_code"] == title_code

        real_launch_response = client.post(
            "/games/mines/launch-token",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={"game_code": "mines", "title_code": title_code, "mode": "real"},
        )
        assert real_launch_response.status_code == 422
        assert real_launch_response.json()["error"]["message"] == "Real launch mode is not enabled for this title"

        config_response = client.get(f"/games/mines/config?title_code={title_code}")
        assert config_response.status_code == 200
        assert config_response.json()["data"]["title_code"] == title_code
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM mines_game_rounds WHERE title_code = %s AND demo_session_id IS NOT NULL", (title_code,))
            cursor.execute(
                """
                DELETE FROM demo_round_events
                WHERE demo_play_session_id IN (
                    SELECT id FROM demo_play_sessions WHERE title_code = %s
                )
                """,
                (title_code,),
            )
            cursor.execute("DELETE FROM demo_play_sessions WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_assets WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def test_real_only_variant_launch_respects_site_lobby_mode_flags(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-library-real-only-admin")
    player = create_authenticated_player(prefix="integration-library-real-only-player")
    title_code = f"mines_real_only_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Real Only Variant",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        publish_response = client.put(
            f"/admin/sites/casinoking/titles/{title_code}/publication",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "lobby_visibility": "visible",
                "demo_enabled": False,
                "real_enabled": True,
                "lobby_display_name": "Mines Real Only",
                "lobby_description": "Real-only library variant",
                "featured": False,
                "position": 8,
            },
        )
        assert publish_response.status_code == 200, publish_response.text

        real_launch_response = client.post(
            "/games/mines/launch-token",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={"game_code": "mines", "title_code": title_code, "mode": "real"},
        )
        assert real_launch_response.status_code == 200, real_launch_response.text
        assert real_launch_response.json()["data"]["title_code"] == title_code

        demo_token = _demo_token(client)
        demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": demo_token},
            json={"title_code": title_code},
        )
        assert demo_launch_response.status_code == 422
        assert demo_launch_response.json()["error"]["message"] == "Demo launch mode is not enabled for this title"
    finally:
        _cleanup_mines_publication_variant(db_connection=db_connection, title_code=title_code)


def test_variant_profile_display_name_can_be_updated(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-profile-admin")
    title_code = f"mines_profile_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Profile Draft",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        update_response = client.put(
            f"/admin/games/titles/{title_code}/profile",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "display_name": "Mines Profile Renamed",
                "site_code": "casinoking",
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated_title = update_response.json()["data"]
        assert updated_title["display_name"] == "Mines Profile Renamed"
        assert updated_title["title_code"] == title_code

        catalog_response = client.get("/catalog/sites/casinoking/titles")
        assert catalog_response.status_code == 200
        catalog_title = next(
            title for title in catalog_response.json()["data"]["titles"] if title["title_code"] == title_code
        )
        assert catalog_title["display_name"] == "Mines Profile Renamed"
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def test_master_profile_cannot_be_updated(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-profile-master-admin")

    response = client.put(
        "/admin/games/titles/mines_classic/profile",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "display_name": "Mines Master Renamed",
            "site_code": "casinoking",
        },
    )

    assert response.status_code == 422


def test_master_cannot_be_published_to_player_library(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-library-master-admin")

    response = client.put(
        "/admin/sites/casinoking/titles/mines_classic/publication",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "lobby_visibility": "visible",
            "demo_enabled": True,
            "real_enabled": False,
            "position": 0,
        },
    )

    assert response.status_code == 422


def test_public_launch_rejects_master_with_stable_code(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-master-launch-player")

    demo_token = _demo_token(client)
    demo_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": demo_token},
        json={"title_code": "mines_classic"},
    )
    assert demo_response.status_code == 422
    assert demo_response.json()["error"]["code"] == "LAUNCH_REJECTED_MASTER"

    real_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
        json={"game_code": "mines", "title_code": "mines_classic", "mode": "real"},
    )
    assert real_response.status_code == 422
    assert real_response.json()["error"]["code"] == "LAUNCH_REJECTED_MASTER"


def test_public_launch_requires_explicit_title_code(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-title-required-player")

    demo_token = _demo_token(client)
    demo_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": demo_token},
        json={},
    )
    assert demo_response.status_code == 422
    assert demo_response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Title code is required",
    }

    real_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
        json={"game_code": "mines", "mode": "real"},
    )
    assert real_response.status_code == 422
    assert real_response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Title code is required",
    }


def test_admin_preview_token_launches_master_without_player_library_publication(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-preview-master")

    preview_response = client.post(
        "/admin/games/titles/mines_classic/preview-launch",
        headers=auth_headers(admin_user["access_token"], include_game_launch_token=False),
        json={"game_code": "mines", "site_code": "casinoking"},
    )
    assert preview_response.status_code == 200, preview_response.text
    preview_payload = preview_response.json()["data"]
    assert preview_payload["title_code"] == "mines_classic"
    assert preview_payload["mode"] == "demo"

    demo_token = _demo_token(client)
    demo_launch_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": demo_token},
        json={
            "title_code": "mines_classic",
            "preview_token": preview_payload["preview_token"],
        },
    )
    assert demo_launch_response.status_code == 200, demo_launch_response.text
    launch_payload = demo_launch_response.json()["data"]
    assert launch_payload["title_code"] == "mines_classic"
    assert launch_payload["mode"] == "demo"


def test_admin_preview_token_launches_hidden_variant_without_enabling_public_demo(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-preview-hidden")
    title_code = f"mines_preview_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"], include_game_launch_token=False),
            json={
                "title_code": title_code,
                "display_name": "Mines Hidden Preview",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        public_demo_token = _demo_token(client)
        public_demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": public_demo_token},
            json={"title_code": title_code},
        )
        assert public_demo_launch_response.status_code == 422
        assert (
            public_demo_launch_response.json()["error"]["message"]
            == "Title is not visible in the player library"
        )

        preview_response = client.post(
            f"/admin/games/titles/{title_code}/preview-launch",
            headers=auth_headers(admin_user["access_token"], include_game_launch_token=False),
            json={"game_code": "mines", "site_code": "casinoking"},
        )
        assert preview_response.status_code == 200, preview_response.text
        preview_payload = preview_response.json()["data"]

        demo_token = _demo_token(client)
        preview_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": demo_token},
            json={
                "title_code": title_code,
                "preview_token": preview_payload["preview_token"],
            },
        )
        assert preview_launch_response.status_code == 200, preview_launch_response.text
        assert preview_launch_response.json()["data"]["title_code"] == title_code
    finally:
        _cleanup_mines_publication_variant(db_connection=db_connection, title_code=title_code)


@pytest.mark.parametrize(
    "publication_payload",
    [
        {
            "lobby_visibility": "visible",
            "demo_enabled": False,
            "real_enabled": False,
            "position": 0,
        },
        {
            "lobby_visibility": "hidden",
            "demo_enabled": True,
            "real_enabled": False,
            "position": 0,
        },
        {
            "lobby_visibility": "hidden",
            "demo_enabled": False,
            "real_enabled": True,
            "position": 0,
        },
    ],
    ids=("visible", "demo", "real"),
)
def test_variant_with_missing_live_config_cannot_enable_lobby_publication(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
    publication_payload: dict[str, object],
) -> None:
    admin_user = create_admin_user(prefix="integration-library-config-block-admin")
    title_code = f"mines_cfg_block_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Missing Config Variant",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        _delete_title_live_config(db_connection=db_connection, title_code=title_code)

        publication_response = client.put(
            f"/admin/sites/casinoking/titles/{title_code}/publication",
            headers=auth_headers(admin_user["access_token"]),
            json=publication_payload,
        )

        assert publication_response.status_code == 422
        error = publication_response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert "published live config" in error["message"]

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT lobby_visibility, demo_enabled, real_enabled
                FROM site_titles
                WHERE site_code = 'casinoking'
                  AND title_code = %s
                """,
                (title_code,),
            )
            publication_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT count(*) AS n
                FROM admin_audit_log
                WHERE resource_id = %s
                  AND action_kind = 'lobby_publication_change'
                """,
                (f"casinoking:{title_code}",),
            )
            audit_count = cursor.fetchone()["n"]

        assert publication_row == {
            "lobby_visibility": "hidden",
            "demo_enabled": False,
            "real_enabled": False,
        }
        assert audit_count == 0
    finally:
        _cleanup_mines_publication_variant(db_connection=db_connection, title_code=title_code)


def test_variant_with_missing_live_config_can_be_hidden_and_modes_off(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-library-config-hide-admin")
    title_code = f"mines_cfg_hide_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Hidden Missing Config Variant",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        _delete_title_live_config(db_connection=db_connection, title_code=title_code)

        publication_response = client.put(
            f"/admin/sites/casinoking/titles/{title_code}/publication",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "lobby_visibility": "hidden",
                "demo_enabled": False,
                "real_enabled": False,
                "lobby_display_name": "Hidden Missing Config",
                "lobby_description": "Not exposed while config is missing",
                "featured": False,
                "position": 3,
            },
        )

        assert publication_response.status_code == 200, publication_response.text
        publication = publication_response.json()["data"]["publication"]
        assert publication["lobby_visibility"] == "hidden"
        assert publication["demo_enabled"] is False
        assert publication["real_enabled"] is False
        assert publication["lobby_display_name"] == "Hidden Missing Config"
    finally:
        _cleanup_mines_publication_variant(db_connection=db_connection, title_code=title_code)


def _delete_title_live_config(*, db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))


def _cleanup_mines_publication_variant(*, db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_id = %s
               OR resource_id = %s
               OR resource_id LIKE %s
            """,
            (title_code, f"casinoking:{title_code}", f"{title_code}:%"),
        )
        cursor.execute("DELETE FROM mines_game_rounds WHERE title_code = %s AND demo_session_id IS NOT NULL", (title_code,))
        cursor.execute(
            """
            DELETE FROM demo_round_events
            WHERE demo_play_session_id IN (
                SELECT id FROM demo_play_sessions WHERE title_code = %s
            )
            """,
            (title_code,),
        )
        cursor.execute("DELETE FROM demo_play_sessions WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))
