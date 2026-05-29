from __future__ import annotations

from uuid import uuid4


def test_site_v3_schema_is_in_place(db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_v3_pages'
            """
        )
        page_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_v3_page_versions'
            """
        )
        version_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_v3_modules'
            """
        )
        module_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename IN ('site_v3_pages', 'site_v3_page_versions', 'site_v3_modules')
            """
        )
        indexes = {row["indexname"] for row in cursor.fetchall()}

    assert page_columns["site_code"] == "NO"
    assert page_columns["page_code"] == "NO"
    assert page_columns["locale"] == "NO"
    assert page_columns["draft_version"] == "NO"
    assert page_columns["published_version"] == "YES"
    assert version_columns["snapshot_json"] == "NO"
    assert version_columns["validation_json"] == "NO"
    assert module_columns["config_json"] == "NO"
    assert "idx_site_v3_pages_site_page_locale" in indexes
    assert "idx_site_v3_page_versions_page_version" in indexes
    assert "idx_site_v3_modules_page_slot_sort_order" in indexes


def test_site_v3_draft_publish_public_snapshot_and_audit_flow(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-admin")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    page_code = f"home-{uuid4().hex[:8]}"
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Target",
    )

    try:
        draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Site V3 Draft",
                "modules": _valid_modules(title["title_code"]),
            },
        )
        assert draft_response.status_code == 200, draft_response.text
        draft_payload = draft_response.json()["data"]
        assert draft_payload["page"]["draft_version"] == 1

        public_draft_response = client.get(f"/site-v3/sites/casinoking/pages/{page_code}")
        assert public_draft_response.status_code == 404
        assert public_draft_response.json()["error"]["code"] == "SITEV3.PAGE.NOT_PUBLISHED"

        publish_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/publish",
            headers=headers,
            json={"locale": "it", "expected_draft_version": 1},
        )
        assert publish_response.status_code == 200, publish_response.text
        published = publish_response.json()["data"]
        assert published["page"]["status"] == "published"
        assert published["version"]["version"] == 1
        assert published["version"]["snapshot_json"]["title"] == "Site V3 Draft"

        public_response = client.get(f"/site-v3/sites/casinoking/pages/{page_code}")
        assert public_response.status_code == 200, public_response.text
        public_payload = public_response.json()["data"]
        assert public_payload["title"] == "Site V3 Draft"
        assert public_payload["published_version"] == 1
        assert "created_by" not in public_response.text
        assert "updated_by" not in public_response.text

        second_draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Site V3 Unpublished Draft",
                "expected_draft_version": 1,
                "modules": _valid_modules(title["title_code"]),
            },
        )
        assert second_draft_response.status_code == 200, second_draft_response.text
        assert second_draft_response.json()["data"]["page"]["draft_version"] == 2

        public_after_second_draft = client.get(f"/site-v3/sites/casinoking/pages/{page_code}")
        assert public_after_second_draft.status_code == 200
        assert public_after_second_draft.json()["data"]["title"] == "Site V3 Draft"

        versions_response = client.get(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/versions",
            headers=headers,
        )
        assert versions_response.status_code == 200, versions_response.text
        assert versions_response.json()["data"]["versions"][0]["version"] == 1

        archive_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/archive",
            headers=headers,
            json={"locale": "it"},
        )
        assert archive_response.status_code == 200, archive_response.text
        assert archive_response.json()["data"]["page"]["status"] == "archived"

        action_kinds = _fetch_site_v3_audit_actions(
            db_connection=db_connection,
            admin_user_id=str(admin["user_id"]),
            resource_id=f"casinoking:{page_code}:it",
        )
        assert {
            "site_v3.page_create",
            "site_v3.save_draft",
            "site_v3.publish",
            "site_v3.archive",
        }.issubset(action_kinds)
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def test_site_v3_validation_blocks_unknown_module_unknown_title_and_unsafe_html(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-validation-admin")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    page_code = f"validation-{uuid4().hex[:8]}"
    hidden_title = create_published_mines_variant(
        title_code=f"mines_site_v3_hidden_{uuid4().hex[:8]}",
        display_name="Mines Hidden Site V3 Target",
        lobby_visibility="hidden",
    )

    try:
        unknown_module_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/validate",
            headers=headers,
            json={
                "locale": "it",
                "title": "Validation Page",
                "modules": [
                    {
                        "module_code": "not_real",
                        "slot_key": "main",
                        "sort_order": 0,
                        "config_json": {},
                    }
                ],
            },
        )
        assert unknown_module_response.status_code == 200, unknown_module_response.text
        unknown_module_codes = _issue_codes(unknown_module_response.json()["data"])
        assert "SITEV3.VALIDATION.UNKNOWN_MODULE" in unknown_module_codes

        unsafe_html_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/validate",
            headers=headers,
            json={
                "locale": "it",
                "title": "Validation Page",
                "modules": [
                    {
                        "module_code": "rich_text_safe",
                        "slot_key": "main",
                        "sort_order": 0,
                        "config_json": {"html": "<p onclick=\"bad()\">Bad</p>"},
                    }
                ],
            },
        )
        assert unsafe_html_response.status_code == 200, unsafe_html_response.text
        unsafe_codes = _issue_codes(unsafe_html_response.json()["data"])
        assert "SITEV3.VALIDATION.UNSAFE_HTML" in unsafe_codes

        invalid_asset_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/validate",
            headers=headers,
            json={
                "locale": "it",
                "title": "Validation Page",
                "modules": [
                    {
                        "module_code": "hero_banner",
                        "slot_key": "hero",
                        "sort_order": 0,
                        "config_json": {
                            "headline": "Bad asset",
                            "media_asset_ref": {"public_url": "data:image/png;base64,abc"},
                        },
                    }
                ],
            },
        )
        assert invalid_asset_response.status_code == 200, invalid_asset_response.text
        invalid_asset_codes = _issue_codes(invalid_asset_response.json()["data"])
        assert "SITEV3.VALIDATION.INVALID_ASSET_URL" in invalid_asset_codes

        draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Invalid Publish Page",
                "modules": [
                    {
                        "module_code": "featured_game",
                        "slot_key": "main",
                        "sort_order": 0,
                        "config_json": {"title_code": hidden_title["title_code"]},
                    }
                ],
            },
        )
        assert draft_response.status_code == 200, draft_response.text

        publish_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/publish",
            headers=headers,
            json={"locale": "it", "expected_draft_version": 1},
        )
        assert publish_response.status_code == 422, publish_response.text
        error = publish_response.json()["error"]
        assert error["code"] == "SITEV3.PUBLISH.VALIDATION_FAILED"
        assert "SITEV3.VALIDATION.UNKNOWN_TITLE" in _issue_codes(error["details"])
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


def test_site_v3_admin_rbac_uses_games_area_bridge(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-finance-admin")
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE admin_profiles
            SET is_superadmin = false,
                areas = ARRAY['finance']::text[]
            WHERE user_id = %s
            """,
            (admin["user_id"],),
        )

    response = client.get(
        "/admin/site-v3/sites/casinoking/pages",
        headers=auth_headers(admin["access_token"], include_game_launch_token=False),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "CK.AUTH.FORBIDDEN"


def _valid_modules(title_code: str) -> list[dict[str, object]]:
    return [
        {
            "module_code": "global_header",
            "slot_key": "header",
            "sort_order": 0,
            "config_json": {"brand_label": "CasinoKing"},
        },
        {
            "module_code": "hero_banner",
            "slot_key": "hero",
            "sort_order": 0,
            "config_json": {
                "headline": "Play now",
                "body": "A published hero",
                "cta_label": "Play demo",
                "cta_title_code": title_code,
            },
        },
        {
            "module_code": "game_grid",
            "slot_key": "games",
            "sort_order": 0,
            "config_json": {
                "heading": "Games",
                "title_codes": [title_code],
            },
        },
        {
            "module_code": "rich_text_safe",
            "slot_key": "content",
            "sort_order": 0,
            "config_json": {"html": "<p><strong>Safe</strong> content.</p>"},
        },
        {
            "module_code": "global_footer",
            "slot_key": "footer",
            "sort_order": 0,
            "config_json": {"legal_text": "18+ Play responsibly."},
        },
    ]


def _issue_codes(validation_json: dict[str, object]) -> set[str]:
    return {
        str(issue["code"])
        for issue in validation_json.get("issues", [])
        if isinstance(issue, dict)
    }


def _fetch_site_v3_audit_actions(
    *,
    db_connection,
    admin_user_id: str,
    resource_id: str,
) -> set[str]:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT action_kind, payload_json
            FROM admin_audit_log
            WHERE admin_user_id = %s
              AND resource_kind = 'site_v3_page'
              AND resource_id = %s
            """,
            (admin_user_id, resource_id),
        )
        rows = cursor.fetchall()
    assert all(row["payload_json"]["source"] == "site_v3" for row in rows)
    return {row["action_kind"] for row in rows}


def _cleanup_site_v3_page(*, db_connection, page_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_kind = 'site_v3_page'
              AND resource_id LIKE %s
            """,
            (f"casinoking:{page_code}:%",),
        )
        cursor.execute(
            """
            DELETE FROM site_v3_pages
            WHERE site_code = 'casinoking'
              AND page_code = %s
            """,
            (page_code,),
        )
