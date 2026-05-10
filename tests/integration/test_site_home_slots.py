from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4


def test_site_home_slots_schema_is_in_place(db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_home_slots'
            """
        )
        columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'site_home_slots'
            """
        )
        indexes = {row["indexname"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'site_assets'
            """
        )
        asset_columns = {row["column_name"]: row["is_nullable"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'site_assets'
            """
        )
        asset_indexes = {row["indexname"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = 'site_home_slots'
              AND kcu.column_name = 'media_asset_id'
            """
        )
        media_asset_foreign_table = cursor.fetchone()["foreign_table_name"]

    assert columns["site_code"] == "NO"
    assert columns["slot_key"] == "NO"
    assert columns["title"] == "NO"
    assert columns["cta_target_type"] == "NO"
    assert columns["cta_target_ref"] == "YES"
    assert columns["media_asset_id"] == "YES"
    assert columns["status"] == "NO"
    assert columns["created_by"] == "YES"
    assert columns["updated_by"] == "YES"
    assert "site_home_slots_site_slot_key_idx" in indexes
    assert "idx_site_home_slots_public" in indexes
    assert "idx_site_home_slots_media_asset" in indexes
    assert "idx_site_home_slots_target_ref" in indexes
    assert media_asset_foreign_table == "site_assets"
    assert asset_columns["site_code"] == "NO"
    assert asset_columns["asset_kind"] == "NO"
    assert asset_columns["public_url"] == "NO"
    assert asset_columns["checksum_sha256"] == "NO"
    assert asset_columns["status"] == "NO"
    assert "site_assets_checksum_per_site_kind_idx" in asset_indexes
    assert "idx_site_assets_site_kind_status" in asset_indexes


def test_admin_home_slot_crud_and_public_filtering_schedule_and_order(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-home-slots-admin")
    marker = f"cms2a-{uuid4().hex[:8]}"
    now = datetime.now(UTC)
    slot_keys = {
        "first": f"{marker}-first",
        "second": f"{marker}-second",
        "draft": f"{marker}-draft",
        "future": f"{marker}-future",
        "ended": f"{marker}-ended",
        "archived": f"{marker}-archived",
    }

    try:
        for key, payload in [
            (
                "second",
                {
                    "title": "Second visible slot",
                    "sort_order": 20,
                    "status": "published",
                    "starts_at": (now - timedelta(hours=1)).isoformat(),
                    "ends_at": (now + timedelta(days=1)).isoformat(),
                },
            ),
            (
                "first",
                {
                    "title": "First visible slot",
                    "sort_order": 10,
                    "status": "published",
                    "starts_at": (now - timedelta(hours=1)).isoformat(),
                    "ends_at": (now + timedelta(days=1)).isoformat(),
                },
            ),
            (
                "draft",
                {
                    "title": "Draft hidden slot",
                    "sort_order": 1,
                    "status": "draft",
                },
            ),
            (
                "future",
                {
                    "title": "Future hidden slot",
                    "sort_order": 2,
                    "status": "published",
                    "starts_at": (now + timedelta(days=1)).isoformat(),
                },
            ),
            (
                "ended",
                {
                    "title": "Ended hidden slot",
                    "sort_order": 3,
                    "status": "published",
                    "ends_at": (now - timedelta(minutes=1)).isoformat(),
                },
            ),
            (
                "archived",
                {
                    "title": "Archived hidden slot",
                    "sort_order": 4,
                    "status": "archived",
                },
            ),
        ]:
            response = client.post(
                "/admin/sites/casinoking/home-slots",
                headers=auth_headers(admin_user["access_token"]),
                json={"slot_key": slot_keys[key], **payload},
            )
            assert response.status_code == 200, response.text

        admin_list_response = client.get(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
        )
        assert admin_list_response.status_code == 200, admin_list_response.text
        admin_slots = [
            slot
            for slot in admin_list_response.json()["data"]["slots"]
            if slot["slot_key"] in set(slot_keys.values())
        ]
        assert {slot["slot_key"] for slot in admin_slots} == set(slot_keys.values())

        patch_response = client.patch(
            f"/admin/sites/casinoking/home-slots/{slot_keys['draft']}",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title": "Draft renamed",
                "subtitle": "Kept out of public because still draft",
            },
        )
        assert patch_response.status_code == 200, patch_response.text
        assert patch_response.json()["data"]["title"] == "Draft renamed"

        public_response = client.get("/site/home", params={"site_code": "casinoking"})
        assert public_response.status_code == 200, public_response.text
        public_slots = [
            slot
            for slot in public_response.json()["data"]["slots"]
            if slot["slot_key"] in set(slot_keys.values())
        ]

        assert [slot["slot_key"] for slot in public_slots] == [
            slot_keys["first"],
            slot_keys["second"],
        ]
        assert "created_by" not in public_slots[0]
        assert "updated_by" not in public_slots[0]
    finally:
        _cleanup_home_slots(db_connection=db_connection, slot_key_prefix=marker)


def test_home_slot_target_validation_uses_site_lobby_publication(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-home-target-admin")
    marker = f"cms2a-target-{uuid4().hex[:8]}"
    demo_title = create_published_mines_variant(
        title_code=f"mines_home_demo_{uuid4().hex[:8]}",
        display_name="Mines Home Demo Target",
        lobby_visibility="visible",
        demo_enabled=True,
        real_enabled=False,
    )
    hidden_title = create_published_mines_variant(
        title_code=f"mines_home_hidden_{uuid4().hex[:8]}",
        display_name="Mines Home Hidden Target",
        lobby_visibility="hidden",
        demo_enabled=True,
        real_enabled=True,
    )

    try:
        ok_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "slot_key": f"{marker}-ok",
                "title": "Demo target slot",
                "cta_label": "Play demo",
                "cta_target_type": "title_demo",
                "cta_target_ref": demo_title["title_code"],
                "status": "published",
            },
        )
        assert ok_response.status_code == 200, ok_response.text
        assert ok_response.json()["data"]["cta_target_ref"] == demo_title["title_code"]

        real_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "slot_key": f"{marker}-real-blocked",
                "title": "Real target blocked",
                "cta_target_type": "title_real",
                "cta_target_ref": demo_title["title_code"],
            },
        )
        assert real_response.status_code == 422
        assert real_response.json()["error"]["code"] == "VALIDATION_ERROR"

        hidden_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "slot_key": f"{marker}-hidden-blocked",
                "title": "Hidden target blocked",
                "cta_target_type": "title_demo",
                "cta_target_ref": hidden_title["title_code"],
            },
        )
        assert hidden_response.status_code == 422
        assert hidden_response.json()["error"]["code"] == "VALIDATION_ERROR"

        master_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "slot_key": f"{marker}-master-blocked",
                "title": "Master target blocked",
                "cta_target_type": "title_demo",
                "cta_target_ref": "mines_classic",
            },
        )
        assert master_response.status_code == 422
        assert master_response.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _cleanup_home_slots(db_connection=db_connection, slot_key_prefix=marker)


def test_home_slot_banner_asset_upload_select_public_render_and_delete(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-home-banner-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)
    marker = f"cms2d-banner-{uuid4().hex[:8]}"
    slot_key = f"{marker}-hero"
    uploaded_asset_id: str | None = None

    try:
        upload_response = client.post(
            "/admin/sites/casinoking/assets",
            headers=headers,
            data={"asset_kind": "homepage_banner"},
            files={"file": ("hero.png", _png_bytes(), "image/png")},
        )
        assert upload_response.status_code == 200, upload_response.text
        uploaded = upload_response.json()["data"]
        uploaded_asset_id = uploaded["id"]
        assert uploaded["site_code"] == "casinoking"
        assert uploaded["asset_kind"] == "homepage_banner"
        assert uploaded["mime"] == "image/png"
        assert uploaded["status"] == "active"
        assert uploaded["public_url"].startswith("/static/sites/casinoking/homepage_banner/")

        static_base_url = str(client.base_url).rstrip("/").removesuffix("/api/v1")
        static_response = client.get(f"{static_base_url}{uploaded['public_url']}")
        assert static_response.status_code == 200
        assert static_response.content == _png_bytes()

        list_response = client.get(
            "/admin/sites/casinoking/assets",
            headers=headers,
            params={"asset_kind": "homepage_banner"},
        )
        assert list_response.status_code == 200, list_response.text
        assert any(asset["id"] == uploaded_asset_id for asset in list_response.json()["data"])

        create_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=headers,
            json={
                "slot_key": slot_key,
                "title": "Hero with uploaded banner",
                "subtitle": "A published slot with site-owned media",
                "media_asset_id": uploaded_asset_id,
                "status": "published",
            },
        )
        assert create_response.status_code == 200, create_response.text
        created_slot = create_response.json()["data"]
        assert created_slot["media_asset_id"] == uploaded_asset_id

        public_response = client.get("/site/home", params={"site_code": "casinoking"})
        assert public_response.status_code == 200, public_response.text
        public_slot = next(
            slot
            for slot in public_response.json()["data"]["slots"]
            if slot["slot_key"] == slot_key
        )
        assert public_slot["media_asset_id"] == uploaded_asset_id
        assert public_slot["media_asset"]["public_url"] == uploaded["public_url"]

        upload_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="site_asset_upload",
            resource_kind="site_asset",
            resource_id=f"casinoking:{uploaded_asset_id}",
        )
        assert upload_audit_row is not None
        assert upload_audit_row["payload_json"]["asset"]["public_url"] == uploaded["public_url"]

        delete_response = client.delete(
            f"/admin/sites/casinoking/assets/{uploaded_asset_id}",
            headers=headers,
        )
        assert delete_response.status_code == 200, delete_response.text
        assert delete_response.json()["data"]["status"] == "deleted"

        admin_slots_response = client.get(
            "/admin/sites/casinoking/home-slots",
            headers=headers,
        )
        assert admin_slots_response.status_code == 200, admin_slots_response.text
        admin_slot = next(
            slot
            for slot in admin_slots_response.json()["data"]["slots"]
            if slot["slot_key"] == slot_key
        )
        assert admin_slot["media_asset_id"] is None
        assert admin_slot["media_asset"] is None

        delete_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="site_asset_delete",
            resource_kind="site_asset",
            resource_id=f"casinoking:{uploaded_asset_id}",
        )
        assert delete_audit_row is not None
    finally:
        _cleanup_home_slots(db_connection=db_connection, slot_key_prefix=marker)
        if uploaded_asset_id is not None:
            _cleanup_site_assets(db_connection=db_connection, asset_ids=[uploaded_asset_id])


def test_home_slot_publish_writes_operational_audit_without_financial_impact(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-home-audit-admin")
    marker = f"cms2a-audit-{uuid4().hex[:8]}"
    slot_key = f"{marker}-hero"
    resource_id = f"casinoking:{slot_key}"

    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT count(*) AS n FROM wallet_accounts")
            wallet_count_before = cursor.fetchone()["n"]
            cursor.execute("SELECT count(*) AS n FROM ledger_transactions")
            ledger_count_before = cursor.fetchone()["n"]
            cursor.execute("SELECT count(*) AS n FROM admin_actions")
            admin_actions_count_before = cursor.fetchone()["n"]

        create_response = client.post(
            "/admin/sites/casinoking/home-slots",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "slot_key": slot_key,
                "title": "Draft audit slot",
                "status": "draft",
            },
        )
        assert create_response.status_code == 200, create_response.text

        publish_response = client.patch(
            f"/admin/sites/casinoking/home-slots/{slot_key}",
            headers=auth_headers(admin_user["access_token"]),
            json={
                "title": "Published audit slot",
                "status": "published",
            },
        )
        assert publish_response.status_code == 200, publish_response.text

        update_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="site_home_slot_update",
            resource_kind="site_home_slot",
            resource_id=resource_id,
        )
        publish_audit_row = _fetch_latest_audit_row(
            db_connection=db_connection,
            admin_user_id=str(admin_user["user_id"]),
            action_kind="site_home_slot_publish",
            resource_kind="site_home_slot",
            resource_id=resource_id,
        )

        with db_connection.cursor() as cursor:
            cursor.execute("SELECT count(*) AS n FROM wallet_accounts")
            wallet_count_after = cursor.fetchone()["n"]
            cursor.execute("SELECT count(*) AS n FROM ledger_transactions")
            ledger_count_after = cursor.fetchone()["n"]
            cursor.execute("SELECT count(*) AS n FROM admin_actions")
            admin_actions_count_after = cursor.fetchone()["n"]

        assert update_audit_row is not None
        update_payload = update_audit_row["payload_json"]
        assert update_payload["site_code"] == "casinoking"
        assert update_payload["slot_key"] == slot_key
        assert "title" in update_payload["changed_fields"]
        assert "status" in update_payload["changed_fields"]
        assert update_payload["before"]["status"] == "draft"
        assert update_payload["after"]["status"] == "published"
        assert len(update_audit_row["request_fingerprint"]) == 64

        assert publish_audit_row is not None
        publish_payload = publish_audit_row["payload_json"]
        assert publish_payload["site_code"] == "casinoking"
        assert publish_payload["slot_key"] == slot_key
        assert publish_payload["after"]["status"] == "published"

        assert wallet_count_after == wallet_count_before
        assert ledger_count_after == ledger_count_before
        assert admin_actions_count_after == admin_actions_count_before
    finally:
        _cleanup_home_slots(db_connection=db_connection, slot_key_prefix=marker)


def _cleanup_home_slots(*, db_connection, slot_key_prefix: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM admin_audit_log
            WHERE resource_kind = 'site_home_slot'
              AND resource_id LIKE %s
            """,
            (f"casinoking:{slot_key_prefix}%",),
        )
        cursor.execute(
            """
            DELETE FROM site_home_slots
            WHERE site_code = 'casinoking'
              AND slot_key LIKE %s
            """,
            (f"{slot_key_prefix}%",),
        )


def _cleanup_site_assets(*, db_connection, asset_ids: list[str]) -> None:
    with db_connection.cursor() as cursor:
        for asset_id in asset_ids:
            cursor.execute(
                """
                UPDATE site_home_slots
                SET media_asset_id = NULL
                WHERE media_asset_id = %s
                """,
                (asset_id,),
            )
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE resource_kind = 'site_asset'
                  AND resource_id = %s
                """,
                (f"casinoking:{asset_id}",),
            )
            cursor.execute(
                """
                DELETE FROM site_assets
                WHERE id = %s
                """,
                (asset_id,),
            )


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


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
