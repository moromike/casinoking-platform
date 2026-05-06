from __future__ import annotations

import copy
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from app.modules.platform.admin_audit.service import record_audit_entry


def test_admin_audit_log_schema_is_in_place(db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'admin_audit_log'
            """
        )
        columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'admin_audit_log'
            """
        )
        indexes = {row["indexname"] for row in cursor.fetchall()}

    assert columns["admin_user_id"] == "NO"
    assert columns["action_kind"] == "NO"
    assert columns["resource_kind"] == "NO"
    assert columns["resource_id"] == "NO"
    assert columns["payload_json"] == "NO"
    assert columns["request_fingerprint"] == "NO"
    assert "idx_admin_audit_log_admin" in indexes
    assert "idx_admin_audit_log_resource" in indexes


def test_record_audit_entry_uses_supplied_cursor_transactionally(
    database_url,
    create_admin_user,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-service-admin")
    resource_id = f"tx-test-{uuid4().hex}"

    connection = psycopg.connect(database_url, row_factory=dict_row)
    try:
        with connection.cursor() as cursor:
            record_audit_entry(
                admin_user_id=str(admin_user["user_id"]),
                action_kind="title_config_publish",
                resource_kind="title",
                resource_id=resource_id,
                payload={"title_code": resource_id},
                request_fingerprint="a" * 64,
                cursor=cursor,
            )
            cursor.execute(
                """
                SELECT count(*) AS n
                FROM admin_audit_log
                WHERE resource_id = %s
                """,
                (resource_id,),
            )
            assert cursor.fetchone()["n"] == 1
        connection.rollback()
    finally:
        connection.close()

    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as verify:
        with verify.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*) AS n
                FROM admin_audit_log
                WHERE resource_id = %s
                """,
                (resource_id,),
            )
            assert cursor.fetchone()["n"] == 0


def test_title_config_publish_writes_operational_audit_log(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-publish-admin")
    title_code = f"mines_audit_{uuid4().hex[:8]}"

    try:
        duplicate_response = client.post(
            "/admin/games/titles/mines_classic/duplicate",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title_code": title_code,
                "display_name": "Mines Audit Variant",
                "site_code": "casinoking",
            },
        )
        assert duplicate_response.status_code == 200, duplicate_response.text

        config_response = client.get(
            f"/admin/games/titles/{title_code}/config",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert config_response.status_code == 200, config_response.text
        draft = copy.deepcopy(config_response.json()["data"]["draft"])
        draft["ui_labels"]["real"]["collect"] = "Collect audit marker"

        update_response = client.put(
            f"/admin/games/titles/{title_code}/config",
            headers=auth_headers(admin_user["access_token"]),
            json=draft,
        )
        assert update_response.status_code == 200, update_response.text

        publish_response = client.post(
            f"/admin/games/titles/{title_code}/config/publish",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert publish_response.status_code == 200, publish_response.text

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    action_kind,
                    resource_kind,
                    resource_id,
                    payload_json,
                    request_fingerprint
                FROM admin_audit_log
                WHERE admin_user_id = %s
                  AND action_kind = 'title_config_publish'
                  AND resource_kind = 'title'
                  AND resource_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (admin_user["user_id"], title_code),
            )
            audit_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT count(*) AS n
                FROM admin_actions
                WHERE admin_user_id = %s
                """,
                (admin_user["user_id"],),
            )
            financial_admin_actions_count = cursor.fetchone()["n"]

        assert audit_row is not None
        assert audit_row["action_kind"] == "title_config_publish"
        assert audit_row["resource_kind"] == "title"
        assert audit_row["resource_id"] == title_code
        assert len(audit_row["request_fingerprint"]) == 64

        payload = audit_row["payload_json"]
        assert payload["engine_code"] == "mines"
        assert payload["title_code"] == title_code
        assert "ui_labels" in payload["changed_fields"]
        assert "before" in payload
        assert "after" in payload
        assert financial_admin_actions_count == 0
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM admin_audit_log WHERE resource_id = %s",
                (title_code,),
            )
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
