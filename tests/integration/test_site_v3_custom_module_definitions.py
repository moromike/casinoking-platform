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

        publish_response = client.post(
            f"/admin/site-v3/sites/casinoking/module-definitions/{module_code}/publish",
            headers=headers,
        )
        assert publish_response.status_code == 200, publish_response.text
        published = publish_response.json()["data"]
        assert published["definition"]["status"] == "published"
        assert published["definition"]["published_version"] == 1
        assert published["version"]["version"] == 1
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
