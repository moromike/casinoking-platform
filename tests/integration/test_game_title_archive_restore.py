from __future__ import annotations

from uuid import uuid4


def test_admin_archives_title_neutralizes_home_cta_and_restore_is_hidden(
    client,
    create_admin_user,
    auth_headers,
    create_authenticated_player,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-archive-admin")
    player = create_authenticated_player(prefix="integration-title-archive-player")
    title = create_published_mines_variant(display_name="Archive Candidate")
    title_code = str(title["title_code"])
    slot_key = f"archive-{uuid4().hex[:8]}"
    admin_headers = auth_headers(str(admin_user["access_token"]), include_game_launch_token=False)

    try:
        create_slot_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=admin_headers,
            json={
                "slot_key": slot_key,
                "title": "Archive target banner",
                "cta_label": "Play",
                "cta_target_type": "title_demo",
                "cta_target_ref": title_code,
                "status": "published",
            },
        )
        assert create_slot_response.status_code == 200, create_slot_response.text

        archive_response = client.post(
            f"/admin/games/titles/{title_code}/archive",
            headers=admin_headers,
            json={"site_code": "casinoking", "reason": "integration cleanup"},
        )
        assert archive_response.status_code == 200, archive_response.text
        archived = archive_response.json()["data"]
        assert archived["status"] == "inactive"
        assert archived["is_archived"] is True
        assert archived["publication"]["site_title_status"] == "inactive"
        assert archived["publication"]["lobby_visibility"] == "hidden"
        assert archived["publication"]["demo_enabled"] is False
        assert archived["publication"]["real_enabled"] is False

        library_response = client.get("/games/library", params={"site_code": "casinoking"})
        assert library_response.status_code == 200, library_response.text
        assert title_code not in {title["title_code"] for title in library_response.json()["data"]["titles"]}

        launch_response = client.post(
            "/games/mines/launch-token",
            headers=auth_headers(str(player["access_token"]), include_game_launch_token=False),
            json={"game_code": "mines", "title_code": title_code, "site_code": "casinoking", "mode": "demo"},
        )
        assert launch_response.status_code == 422

        access_response = client.post(
            "/access-sessions",
            headers=auth_headers(str(player["access_token"]), include_game_launch_token=False),
            json={"game_code": "mines", "title_code": title_code, "site_code": "casinoking"},
        )
        assert access_response.status_code == 422
        assert access_response.json()["error"]["code"] == "VALIDATION_ERROR"

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cta_target_type, cta_target_ref
                FROM site_home_slots
                WHERE slot_key = %s
                """,
                (slot_key,),
            )
            slot = cursor.fetchone()
            assert slot == {"cta_target_type": "none", "cta_target_ref": None}

            cursor.execute(
                """
                SELECT payload_json
                FROM admin_audit_log
                WHERE resource_id = %s
                  AND action_kind = 'title_archive'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (title_code,),
            )
            audit_payload = cursor.fetchone()["payload_json"]
            assert audit_payload["homepage_cta_neutralized"][0]["slot_key"] == slot_key
            assert audit_payload["after"]["archived"] is True

        restore_response = client.post(
            f"/admin/games/titles/{title_code}/restore",
            headers=admin_headers,
            json={"site_code": "casinoking"},
        )
        assert restore_response.status_code == 200, restore_response.text
        restored = restore_response.json()["data"]
        assert restored["is_archived"] is False
        assert restored["status"] == "inactive"
        assert restored["publication"]["site_title_status"] == "inactive"
        assert restored["publication"]["lobby_visibility"] == "hidden"
        assert restored["publication"]["demo_enabled"] is False
        assert restored["publication"]["real_enabled"] is False

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload_json
                FROM admin_audit_log
                WHERE resource_id = %s
                  AND action_kind = 'title_restore'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (title_code,),
            )
            restore_audit_payload = cursor.fetchone()["payload_json"]
            assert restore_audit_payload["before"]["archived"] is True
            assert restore_audit_payload["after"]["archived"] is False
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM admin_audit_log WHERE resource_id = %s",
                (f"casinoking:{slot_key}",),
            )
            cursor.execute(
                "DELETE FROM site_home_slots WHERE site_code = 'casinoking' AND slot_key = %s",
                (slot_key,),
            )


def test_admin_cannot_archive_master_title(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-archive-master-admin")
    response = client.post(
        "/admin/games/titles/mines_classic/archive",
        headers=auth_headers(str(admin_user["access_token"]), include_game_launch_token=False),
        json={"site_code": "casinoking", "reason": "should fail"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_admin_can_create_test_variant_tag(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-test-tag-admin")
    title_code = f"mines_test_tag_{uuid4().hex[:8]}"

    try:
        response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(str(admin_user["access_token"]), include_game_launch_token=False),
            json={
                "title_code": title_code,
                "display_name": "Tagged Test Variant",
                "site_code": "casinoking",
                "is_test": True,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"]["is_test"] is True

        catalog_test_response = client.get(
            "/catalog/sites/casinoking/titles",
            params={"status": "all", "test": "only"},
        )
        assert catalog_test_response.status_code == 200, catalog_test_response.text
        assert title_code in {
            title["title_code"] for title in catalog_test_response.json()["data"]["titles"]
        }

        update_response = client.put(
            f"/admin/games/titles/{title_code}/profile",
            headers=auth_headers(str(admin_user["access_token"]), include_game_launch_token=False),
            json={
                "display_name": "Tagged Regular Variant",
                "site_code": "casinoking",
                "is_test": False,
            },
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["data"]["is_test"] is False

        catalog_exclude_response = client.get(
            "/catalog/sites/casinoking/titles",
            params={"status": "all", "test": "exclude"},
        )
        assert catalog_exclude_response.status_code == 200, catalog_exclude_response.text
        assert title_code in {
            title["title_code"] for title in catalog_exclude_response.json()["data"]["titles"]
        }
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM admin_audit_log WHERE resource_id = %s", (title_code,))
            cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def test_admin_archive_is_blocked_by_active_access_session(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-title-archive-block-admin")
    title = create_published_mines_variant(display_name="Blocked Archive Candidate")
    title_code = str(title["title_code"])
    session_id = str(uuid4())

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_access_sessions (
                id,
                user_id,
                game_code,
                status,
                title_code,
                site_code
            )
            VALUES (%s, %s, 'mines', 'active', %s, 'casinoking')
            """,
            (session_id, str(admin_user["user_id"]), title_code),
        )

    try:
        response = client.post(
            f"/admin/games/titles/{title_code}/archive",
            headers=auth_headers(str(admin_user["access_token"]), include_game_launch_token=False),
            json={"site_code": "casinoking", "reason": "should fail"},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "TITLE_ARCHIVE_BLOCKED"
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM game_access_sessions WHERE id = %s", (session_id,))
