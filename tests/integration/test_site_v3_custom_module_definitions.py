from __future__ import annotations

from uuid import uuid4


def test_site_v3_custom_module_definition_schema_is_in_place(db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_v3_module_definitions'
            """
        )
        definition_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_v3_module_definition_versions'
            """
        )
        version_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename IN ('site_v3_module_definitions', 'site_v3_module_definition_versions')
            """
        )
        indexes = {row["indexname"] for row in cursor.fetchall()}

    assert definition_columns["module_code"] == "NO"
    assert definition_columns["draft_field_schema_json"] == "NO"
    assert definition_columns["published_version"] == "YES"
    assert version_columns["definition_id"] == "NO"
    assert version_columns["field_schema_json"] == "NO"
    assert "idx_site_v3_module_definitions_site_module" in indexes
    assert "idx_site_v3_module_definition_versions_definition_version" in indexes


def test_site_v3_custom_module_definition_create_publish_archive_flow(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-module-def-admin")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    module_code = f"custom_test_{uuid4().hex[:8]}"

    try:
        create_response = client.post(
            "/admin/site-v3/sites/casinoking/module-definitions",
            headers=headers,
            json=_definition_payload(module_code=module_code),
        )
        assert create_response.status_code == 200, create_response.text
        created = create_response.json()["data"]["definition"]
        assert created["module_code"] == module_code
        assert created["status"] == "draft"
        assert created["published_version"] is None

        list_response = client.get(
            "/admin/site-v3/sites/casinoking/module-definitions",
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        module_codes = {definition["module_code"] for definition in list_response.json()["data"]["definitions"]}
        assert module_code in module_codes

        update_response = client.put(
            f"/admin/site-v3/sites/casinoking/module-definitions/{module_code}/draft",
            headers=headers,
            json={
                **_definition_payload(module_code=module_code),
                "label": "Custom test banner updated",
                "field_schema_json": [
                    {
                        "key": "headline",
                        "label": "Headline",
                        "type": "string",
                        "group": "content",
                        "required": True,
                        "max_length": 120,
                    },
                    {
                        "key": "media",
                        "label": "Media",
                        "type": "asset_ref",
                        "group": "assets",
                    },
                    {
                        "key": "cta_url",
                        "label": "CTA URL",
                        "type": "url",
                        "group": "links",
                    },
                ],
                "default_config_json": {
                    "headline": "",
                    "media": {},
                    "cta_url": "",
                },
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()["data"]["definition"]
        assert updated["label"] == "Custom test banner updated"
        assert updated["draft_schema_version"] == 2
        assert updated["field_schema_json"][2]["type"] == "url"

        publish_response = client.post(
            f"/admin/site-v3/sites/casinoking/module-definitions/{module_code}/publish",
            headers=headers,
        )
        assert publish_response.status_code == 200, publish_response.text
        published = publish_response.json()["data"]
        assert published["definition"]["status"] == "published"
        assert published["definition"]["published_version"] == 1
        assert published["version"]["version"] == 1
        assert published["version"]["schema_version"] == 2
        assert published["version"]["label"] == "Custom test banner updated"
        assert published["version"]["field_schema_json"][0]["key"] == "headline"

        archive_response = client.post(
            f"/admin/site-v3/sites/casinoking/module-definitions/{module_code}/archive",
            headers=headers,
        )
        assert archive_response.status_code == 200, archive_response.text
        assert archive_response.json()["data"]["definition"]["status"] == "archived"

        action_kinds = _fetch_definition_audit_actions(
            db_connection=db_connection,
            admin_user_id=str(admin["user_id"]),
            resource_id=f"casinoking:{module_code}",
        )
        assert {
            "site_v3.module_definition_create",
            "site_v3.module_definition_update_draft",
            "site_v3.module_definition_publish",
            "site_v3.module_definition_archive",
        }.issubset(action_kinds)
    finally:
        _cleanup_definition(db_connection=db_connection, module_code=module_code)


def test_site_v3_custom_module_definition_validation_blocks_reserved_or_unsafe_codes(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin = create_admin_user(prefix="site-v3-module-def-validation")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)

    invalid_prefix = client.post(
        "/admin/site-v3/sites/casinoking/module-definitions",
        headers=headers,
        json=_definition_payload(module_code="hero_banner"),
    )
    assert invalid_prefix.status_code == 422, invalid_prefix.text
    assert invalid_prefix.json()["error"]["code"] == "SITEV3.MODULE_DEFINITION.INVALID"
    assert _issue_codes(invalid_prefix.json()["error"]["details"]) == {"SITEV3.MODULE_DEFINITION.INVALID_CODE"}

    invalid_field_type = client.post(
        "/admin/site-v3/sites/casinoking/module-definitions",
        headers=headers,
        json={
            **_definition_payload(module_code=f"custom_bad_{uuid4().hex[:8]}"),
            "field_schema_json": [
                {
                    "key": "script",
                    "label": "Script",
                    "type": "javascript",
                    "group": "content",
                }
            ],
        },
    )
    assert invalid_field_type.status_code == 422, invalid_field_type.text
    assert "SITEV3.MODULE_DEFINITION.INVALID_FIELD_TYPE" in _issue_codes(
        invalid_field_type.json()["error"]["details"]
    )


def test_site_v3_custom_module_definition_mount_preview_and_publish_snapshot(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin = create_admin_user(prefix="site-v3-module-def-mount")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    module_code = f"custom_mount_{uuid4().hex[:8]}"
    page_code = f"custom-page-{uuid4().hex[:8]}"

    try:
        create_response = client.post(
            "/admin/site-v3/sites/casinoking/module-definitions",
            headers=headers,
            json=_definition_payload(module_code=module_code),
        )
        assert create_response.status_code == 200, create_response.text

        publish_definition_response = client.post(
            f"/admin/site-v3/sites/casinoking/module-definitions/{module_code}/publish",
            headers=headers,
        )
        assert publish_definition_response.status_code == 200, publish_definition_response.text
        assert publish_definition_response.json()["data"]["definition"]["published_version"] == 1

        draft_response = client.put(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
            headers=headers,
            json={
                "locale": "it",
                "title": "Custom module page",
                "modules": [
                    {
                        "module_code": "global_header",
                        "slot_key": "header",
                        "sort_order": 0,
                        "config_json": {"brand_label": "CasinoKing"},
                    },
                    {
                        "module_code": module_code,
                        "schema_version": 1,
                        "slot_key": "hero",
                        "sort_order": 1,
                        "config_json": {
                            "headline": "Custom mounted banner",
                            "media": {"public_url": "/static/sites/casinoking/custom-banner.webp"},
                        },
                    },
                    {
                        "module_code": "global_footer",
                        "slot_key": "footer",
                        "sort_order": 2,
                        "config_json": {"legal_text": "18+"},
                    },
                ],
            },
        )
        assert draft_response.status_code == 200, draft_response.text

        token_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft-preview-token?locale=it",
            headers=headers,
        )
        assert token_response.status_code == 200, token_response.text
        preview_response = client.get(
            f"/site-v3/sites/casinoking/pages/{page_code}/preview-draft?locale=it",
            headers={"X-Draft-Preview-Token": token_response.json()["data"]["token"]},
        )
        assert preview_response.status_code == 200, preview_response.text
        preview_module = _find_module(preview_response.json()["data"]["modules"], module_code)
        assert preview_module["definition_snapshot"]["renderer_template"] == "image_banner"

        validate_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/validate",
            headers=headers,
            json={
                "locale": "it",
                "title": "Custom module page",
                "modules": draft_response.json()["data"]["modules"],
            },
        )
        assert validate_response.status_code == 200, validate_response.text
        assert validate_response.json()["data"]["status"] == "valid"

        publish_page_response = client.post(
            f"/admin/site-v3/sites/casinoking/pages/{page_code}/publish",
            headers=headers,
            json={"locale": "it", "expected_draft_version": 1},
        )
        assert publish_page_response.status_code == 200, publish_page_response.text
        snapshot_module = _find_module(
            publish_page_response.json()["data"]["version"]["snapshot_json"]["modules"],
            module_code,
        )
        assert snapshot_module["definition_snapshot"]["definition_version"] == 1
        assert snapshot_module["definition_snapshot"]["field_schema_json"][0]["key"] == "headline"

        public_response = client.get(f"/site-v3/sites/casinoking/pages/{page_code}")
        assert public_response.status_code == 200, public_response.text
        public_module = _find_module(public_response.json()["data"]["modules"], module_code)
        assert public_module["schema_version"] == 1
        assert public_module["definition_snapshot"]["module_code"] == module_code
        assert public_module["definition_snapshot"]["default_config_json"]["headline"] == ""
        assert "created_by" not in public_response.text
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)
        _cleanup_definition(db_connection=db_connection, module_code=module_code)


def _definition_payload(*, module_code: str) -> dict[str, object]:
    return {
        "module_code": module_code,
        "label": "Custom test banner",
        "category": "hero",
        "renderer_template": "image_banner",
        "field_schema_json": [
            {
                "key": "headline",
                "label": "Headline",
                "type": "string",
                "group": "content",
                "required": True,
                "max_length": 120,
            },
            {
                "key": "media",
                "label": "Media",
                "type": "asset_ref",
                "group": "assets",
            },
        ],
        "default_config_json": {
            "headline": "",
            "media": {},
        },
    }


def _issue_codes(details: dict[str, object]) -> set[str]:
    return {
        str(issue["code"])
        for issue in details.get("issues", [])
        if isinstance(issue, dict)
    }


def _fetch_definition_audit_actions(
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
              AND resource_kind = 'site_v3_module_definition'
              AND resource_id = %s
            """,
            (admin_user_id, resource_id),
        )
        rows = cursor.fetchall()
    assert all(row["payload_json"]["source"] == "site_v3" for row in rows)
    return {row["action_kind"] for row in rows}


def _cleanup_definition(*, db_connection, module_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_kind = 'site_v3_module_definition'
              AND resource_id = %s
            """,
            (f"casinoking:{module_code}",),
        )
        cursor.execute(
            """
            DELETE FROM site_v3_module_definitions
            WHERE site_code = 'casinoking'
              AND module_code = %s
            """,
            (module_code,),
        )


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


def _find_module(modules: list[dict[str, object]], module_code: str) -> dict[str, object]:
    for module in modules:
        if module["module_code"] == module_code:
            return module
    raise AssertionError(f"Module {module_code} not found")
