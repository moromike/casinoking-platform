from __future__ import annotations

import copy
from datetime import UTC, datetime
import json
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


def test_admin_audit_log_endpoint_lists_filters_and_paginates(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-list-admin")
    other_admin_user = create_admin_user(prefix="integration-audit-list-other-admin")
    marker = f"audit-list-{uuid4().hex}"
    event_ids = [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000004",
    ]

    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM admin_audit_log WHERE id = ANY(%s::uuid[])",
                (event_ids,),
            )
            cursor.executemany(
                """
                INSERT INTO admin_audit_log (
                    id,
                    admin_user_id,
                    action_kind,
                    resource_kind,
                    resource_id,
                    payload_json,
                    request_fingerprint,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                [
                    (
                        event_ids[0],
                        admin_user["user_id"],
                        "title_config_publish",
                        "title",
                        f"{marker}-old",
                        json.dumps({"marker": marker, "sequence": 1}),
                        "1" * 64,
                        datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
                    ),
                    (
                        event_ids[1],
                        admin_user["user_id"],
                        "title_config_publish",
                        "title",
                        f"{marker}-second",
                        json.dumps({"marker": marker, "sequence": 2}),
                        "2" * 64,
                        datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
                    ),
                    (
                        event_ids[2],
                        admin_user["user_id"],
                        "title_config_publish",
                        "title",
                        f"{marker}-third",
                        json.dumps({"marker": marker, "sequence": 3}),
                        "3" * 64,
                        datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
                    ),
                    (
                        event_ids[3],
                        other_admin_user["user_id"],
                        "theme_publish",
                        "title",
                        f"{marker}-other-admin",
                        json.dumps({"marker": marker, "sequence": 4}),
                        "4" * 64,
                        datetime(2026, 1, 3, 10, 0, tzinfo=UTC),
                    ),
                ],
            )

        page_one_response = client.get(
            "/admin/audit-log",
            headers=auth_headers(admin_user["access_token"]),
            params={
                "action_kind": "title_config_publish",
                "resource_kind": "title",
                "admin_user_id": str(admin_user["user_id"]),
                "date_from": "2026-01-01",
                "date_to": "2026-01-02",
                "page": "1",
                "limit": "2",
            },
        )
        assert page_one_response.status_code == 200, page_one_response.text
        page_one_payload = page_one_response.json()["data"]

        assert page_one_payload["pagination"] == {
            "page": 1,
            "limit": 2,
            "total_items": 3,
            "total_pages": 2,
        }
        assert [event["id"] for event in page_one_payload["events"]] == [
            event_ids[2],
            event_ids[1],
        ]
        assert page_one_payload["events"][0] == {
            "id": event_ids[2],
            "admin_user_id": str(admin_user["user_id"]),
            "action_kind": "title_config_publish",
            "resource_kind": "title",
            "resource_id": f"{marker}-third",
            "payload_json": {"marker": marker, "sequence": 3},
            "request_fingerprint": "3" * 64,
            "created_at": "2026-01-02T10:00:00+00:00",
        }

        page_two_response = client.get(
            "/admin/audit-log",
            headers=auth_headers(admin_user["access_token"]),
            params={
                "action_kind": "title_config_publish",
                "resource_kind": "title",
                "admin_user_id": str(admin_user["user_id"]),
                "date_from": "2026-01-01",
                "date_to": "2026-01-02",
                "page": "2",
                "limit": "2",
            },
        )
        assert page_two_response.status_code == 200, page_two_response.text
        page_two_payload = page_two_response.json()["data"]
        assert page_two_payload["pagination"]["page"] == 2
        assert [event["id"] for event in page_two_payload["events"]] == [event_ids[0]]

        resource_response = client.get(
            "/admin/audit-log",
            headers=auth_headers(admin_user["access_token"]),
            params={"resource_id": f"{marker}-other-admin"},
        )
        assert resource_response.status_code == 200, resource_response.text
        resource_payload = resource_response.json()["data"]
        assert resource_payload["pagination"]["total_items"] == 1
        assert resource_payload["events"][0]["admin_user_id"] == str(other_admin_user["user_id"])
        assert resource_payload["events"][0]["action_kind"] == "theme_publish"
    finally:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM admin_audit_log WHERE id = ANY(%s::uuid[])",
                (event_ids,),
            )


def test_admin_audit_log_endpoint_returns_validation_error_for_bad_query(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-list-validation-admin")

    invalid_limit_response = client.get(
        "/admin/audit-log",
        headers=auth_headers(admin_user["access_token"]),
        params={"limit": "101"},
    )
    assert invalid_limit_response.status_code == 422
    assert invalid_limit_response.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid_date_response = client.get(
        "/admin/audit-log",
        headers=auth_headers(admin_user["access_token"]),
        params={"date_from": "not-a-date"},
    )
    assert invalid_date_response.status_code == 422
    assert invalid_date_response.json()["error"]["code"] == "VALIDATION_ERROR"


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

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*) AS n
                FROM admin_audit_log
                WHERE admin_user_id = %s
                  AND action_kind = 'title_config_publish'
                  AND resource_kind = 'title'
                  AND resource_id = %s
                """,
                (admin_user["user_id"], title_code),
            )
            assert cursor.fetchone()["n"] == 0

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


def test_lobby_publication_change_writes_operational_audit_log(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-lobby-admin")
    title_code = f"mines_audit_lobby_{uuid4().hex[:8]}"
    resource_id = f"casinoking:{title_code}"

    try:
        _duplicate_mines_variant(
            client=client,
            auth_headers=auth_headers,
            admin_user=admin_user,
            title_code=title_code,
            display_name="Mines Audit Lobby Variant",
        )

        publication_response = client.put(
            f"/admin/sites/casinoking/titles/{title_code}/publication",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "lobby_visibility": "visible",
                "demo_enabled": True,
                "real_enabled": False,
                "lobby_display_name": "Mines Audit Lobby",
                "lobby_description": "Audit lobby variant",
                "featured": True,
                "position": 11,
            },
        )
        assert publication_response.status_code == 200, publication_response.text

        audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="lobby_publication_change",
            resource_kind="site_title",
            resource_id=resource_id,
        )

        assert audit_row is not None
        payload = audit_row["payload_json"]
        assert payload["site_code"] == "casinoking"
        assert payload["title_code"] == title_code
        assert "lobby_visibility" in payload["changed_fields"]
        assert payload["before"]["lobby_visibility"] == "hidden"
        assert payload["after"]["lobby_visibility"] == "visible"
        assert payload["after"]["demo_enabled"] is True
        assert len(audit_row["request_fingerprint"]) == 64
    finally:
        _cleanup_mines_variant(db_connection=db_connection, title_code=title_code)


def test_theme_publish_writes_operational_audit_log(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-theme-admin")
    title_code = f"mines_audit_theme_{uuid4().hex[:8]}"

    try:
        _duplicate_mines_variant(
            client=client,
            auth_headers=auth_headers,
            admin_user=admin_user,
            title_code=title_code,
            display_name="Mines Audit Theme Variant",
        )

        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE title_configs SET theme_tokens_json = '{}'::jsonb WHERE title_code = %s",
                (title_code,),
            )

        draft_response = client.put(
            f"/admin/titles/{title_code}/theme",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "tokens": {
                    "--ck-bg": "#111827",
                    "--ck-accent": "#22c55e",
                }
            },
        )
        assert draft_response.status_code == 200, draft_response.text

        publish_response = client.post(
            f"/admin/titles/{title_code}/theme/publish",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert publish_response.status_code == 200, publish_response.text

        audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="theme_publish",
            resource_kind="title",
            resource_id=title_code,
        )

        assert audit_row is not None
        payload = audit_row["payload_json"]
        assert payload["title_code"] == title_code
        assert "--ck-bg" in payload["changed_token_keys"]
        assert payload["before"]["tokens"]["--ck-bg"] == "#09090f"
        assert payload["after"]["tokens"]["--ck-bg"] == "#111827"
        assert len(audit_row["request_fingerprint"]) == 64
    finally:
        _cleanup_mines_variant(db_connection=db_connection, title_code=title_code)


def test_title_asset_upload_and_delete_write_operational_audit_log(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-audit-asset-admin")
    title_code = f"mines_audit_asset_{uuid4().hex[:8]}"
    resource_id = f"{title_code}:symbol_safe"

    try:
        _duplicate_mines_variant(
            client=client,
            auth_headers=auth_headers,
            admin_user=admin_user,
            title_code=title_code,
            display_name="Mines Audit Asset Variant",
        )

        upload_response = client.post(
            f"/admin/titles/{title_code}/assets",
            headers=auth_headers(admin_user["access_token"]),
            data={"asset_kind": "symbol_safe"},
            files={"file": ("safe.png", _png_bytes(), "image/png")},
        )
        assert upload_response.status_code == 200, upload_response.text
        uploaded_asset = upload_response.json()["data"]

        delete_response = client.delete(
            f"/admin/titles/{title_code}/assets/symbol_safe",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert delete_response.status_code == 200, delete_response.text

        upload_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="title_asset_upload",
            resource_kind="title_asset",
            resource_id=resource_id,
        )
        delete_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="title_asset_delete",
            resource_kind="title_asset",
            resource_id=resource_id,
        )

        assert upload_audit_row is not None
        upload_payload = upload_audit_row["payload_json"]
        assert upload_payload["title_code"] == title_code
        assert upload_payload["asset_kind"] == "symbol_safe"
        assert upload_payload["before"]["active_assets"] == []
        assert upload_payload["after"]["active_asset"]["id"] == uploaded_asset["id"]
        assert upload_payload["after"]["active_asset"]["checksum_sha256"] == uploaded_asset["checksum_sha256"]

        assert delete_audit_row is not None
        delete_payload = delete_audit_row["payload_json"]
        assert delete_payload["title_code"] == title_code
        assert delete_payload["asset_kind"] == "symbol_safe"
        assert delete_payload["before"]["active_asset"]["id"] == uploaded_asset["id"]
        assert delete_payload["before"]["active_asset"]["status"] == "active"
        assert delete_payload["after"]["deleted_asset"]["status"] == "deleted"
        assert len(delete_audit_row["request_fingerprint"]) == 64
    finally:
        _cleanup_mines_variant(db_connection=db_connection, title_code=title_code)


def _duplicate_mines_variant(
    *,
    client,
    auth_headers,
    admin_user: dict[str, object],
    title_code: str,
    display_name: str,
) -> None:
    response = client.post(
        "/admin/games/titles/mines_classic/duplicate",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "title_code": title_code,
            "display_name": display_name,
            "site_code": "casinoking",
        },
    )
    assert response.status_code == 200, response.text


def _fetch_latest_audit_row(
    *,
    db_connection,
    admin_user_id: str,
    action_kind: str,
    resource_kind: str,
    resource_id: str,
) -> dict[str, object] | None:
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
              AND action_kind = %s
              AND resource_kind = %s
              AND resource_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (admin_user_id, action_kind, resource_kind, resource_id),
        )
        return cursor.fetchone()


def _cleanup_mines_variant(*, db_connection, title_code: str) -> None:
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
        cursor.execute("DELETE FROM title_assets WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
