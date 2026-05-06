from __future__ import annotations

from uuid import uuid4


def test_game_library_exposes_visible_demo_variants_only(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-library-admin")
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

        hidden_library_response = client.get("/games/library")
        assert hidden_library_response.status_code == 200
        hidden_titles = hidden_library_response.json()["data"]["titles"]
        assert all(title["title_code"] != title_code for title in hidden_titles)

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

        demo_token_response = client.post("/demo/token")
        assert demo_token_response.status_code == 200
        demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": demo_token_response.json()["data"]["anonymous_token"]},
            json={"title_code": title_code},
        )
        assert demo_launch_response.status_code == 200
        assert demo_launch_response.json()["data"]["title_code"] == title_code

        config_response = client.get(f"/games/mines/config?title_code={title_code}")
        assert config_response.status_code == 200
        assert config_response.json()["data"]["title_code"] == title_code
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM demo_mines_game_rounds WHERE title_code = %s", (title_code,))
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
