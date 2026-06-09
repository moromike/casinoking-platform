from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from app.modules.platform.site_v3.service import publish_page, save_draft


playwright = pytest.importorskip("playwright.sync_api")


def _find_chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _demo_token(client) -> str:
    response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.50.0.{uuid4().int % 250 + 1}"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["anonymous_token"]


def _boxe_library_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "site": {
                "site_code": "casinoking",
                "display_name": "CasinoKing",
                "status": "active",
            },
            "titles": [
                {
                    "title_code": "boxe001",
                    "engine_code": "boxe",
                    "engine_display_name": "BOXE",
                    "display_name": "BOXE",
                    "catalog_display_name": "BOXE",
                    "description": "Pick the safe boxes and collect.",
                    "demo_enabled": True,
                    "real_enabled": True,
                    "featured": True,
                    "position": 1,
                    "game_card_asset": {
                        "id": "boxe-card-asset",
                        "asset_kind": "game_card",
                        "public_url": "/static/games/boxe001/game_card/boxe.webp",
                        "mime": "image/webp",
                        "byte_size": 33000,
                        "created_at": "2026-05-18T00:00:00+00:00",
                    },
                }
            ],
        },
    }


def _home_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "site": {
                "site_code": "casinoking",
                "display_name": "CasinoKing",
                "status": "active",
            },
            "slots": [],
        },
    }


def _wallets_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": [
            {
                "wallet_type": "cash",
                "balance_snapshot": "125.00",
                "currency_code": "EUR",
            },
            {
                "wallet_type": "bonus",
                "balance_snapshot": "35.00",
                "currency_code": "EUR",
            },
        ],
    }


def _route_lobby_api(page) -> None:
    page.route(
        "**/api/v1/games/library*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_boxe_library_payload()),
        ),
    )
    page.route(
        "**/api/v1/site/home*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_home_payload()),
        ),
    )
    page.route(
        "**/api/v1/wallets",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_wallets_payload()),
        ),
    )


def test_boxe_catalog_seed_publication_demo_launch_and_master_block(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-boxe-lobby-admin")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)
    publication_snapshot = _snapshot_boxe_casinoking_publication(db_connection=db_connection)

    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT title_code, engine_code, is_master
                FROM game_titles
                WHERE title_code IN ('boxe', 'boxe001')
                ORDER BY title_code
                """
            )
            title_rows = cursor.fetchall()
        assert [
            (row["title_code"], row["engine_code"], row["is_master"])
            for row in title_rows
        ] == [
            ("boxe", "boxe", True),
            ("boxe001", "boxe", False),
        ]

        publish_response = client.put(
            "/admin/sites/casinoking/titles/boxe001/publication",
            headers=headers,
            json={
                "lobby_visibility": "visible",
                "demo_enabled": True,
                "real_enabled": True,
                "lobby_display_name": "BOXE",
                "lobby_description": "Pick safe boxes and collect.",
                "featured": True,
                "position": 3,
            },
        )
        assert publish_response.status_code == 200, publish_response.text

        library_response = client.get("/games/library")
        assert library_response.status_code == 200
        titles = library_response.json()["data"]["titles"]
        boxe_title = next(title for title in titles if title["title_code"] == "boxe001")
        assert boxe_title["engine_code"] == "boxe"
        assert boxe_title["display_name"] == "BOXE"
        assert boxe_title["demo_enabled"] is True
        assert boxe_title["real_enabled"] is True

        preview_response = client.post(
            "/admin/games/titles/boxe001/preview-launch",
            headers=headers,
            json={"game_code": "boxe", "site_code": "casinoking"},
        )
        assert preview_response.status_code == 200, preview_response.text
        preview_payload = preview_response.json()["data"]
        assert preview_payload["game_code"] == "boxe"
        assert preview_payload["title_code"] == "boxe001"

        demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": _demo_token(client)},
            json={"game_code": "boxe", "title_code": "boxe001", "site_code": "casinoking"},
        )
        assert demo_launch_response.status_code == 200, demo_launch_response.text
        demo_payload = demo_launch_response.json()["data"]
        assert demo_payload["game_code"] == "boxe"
        assert demo_payload["title_code"] == "boxe001"
        assert demo_payload["mode"] == "demo"

        master_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": _demo_token(client)},
            json={"game_code": "boxe", "title_code": "boxe", "site_code": "casinoking"},
        )
        assert master_launch_response.status_code == 422
        master_error = master_launch_response.json()["error"]
        assert master_error["code"] == "LAUNCH_REJECTED_MASTER"
        assert master_error["message"] == "Master titles cannot be launched publicly"
    finally:
        _restore_boxe_casinoking_publication(
            db_connection=db_connection,
            snapshot=publication_snapshot,
        )
        with db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM admin_audit_log WHERE resource_id = %s", ("boxe001",))


@pytest.mark.integration
def test_player_lobby_launch_cashier_routes_boxe_demo_real_and_bonus(
    frontend_base_url: str,
    wait_for_frontend,
    create_admin_user,
    db_connection,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin = create_admin_user(prefix="integration-boxe-lobby-v3")
    page_code = f"boxe-lobby-{uuid4().hex[:8]}"
    publication_snapshot = _snapshot_boxe_casinoking_publication(db_connection=db_connection)

    try:
        _publish_boxe_for_casinoking(db_connection=db_connection)
        save_draft(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            title="BOXE lobby route smoke",
            expected_draft_version=None,
            admin_user_id=str(admin["user_id"]),
            modules=_site_v3_boxe_modules(),
        )
        publish_page(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            expected_draft_version=1,
            admin_user_id=str(admin["user_id"]),
        )

        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=chromium_executable,
            )

            page = browser.new_page(viewport={"width": 1015, "height": 768})
            page.goto(f"{frontend_base_url}/pages/{page_code}", wait_until="networkidle")
            page.get_by_role("button", name="Open launch cashier for BOXE").wait_for()
            page.get_by_role("button", name="Open launch cashier for BOXE").click()
            page.get_by_role("dialog", name="BOXE").wait_for()
            assert page.get_by_text("Launch cashier").is_visible()
            assert page.get_by_text("Log in before using real balance.").is_visible()
            assert page.get_by_text("Log in before using bonus balance.").is_visible()
            page.locator(".player-lobby-cashier-option").nth(2).click()
            page.wait_for_url("**/boxe?*")
            assert "title_code=boxe001" in page.url
            assert "mode=demo" in page.url

            real_page = browser.new_page(viewport={"width": 1015, "height": 768})
            real_page.add_init_script(
                """
                window.localStorage.setItem('casinoking.access_token', 'boxe-lobby-token');
                window.localStorage.setItem('casinoking.email', 'boxe-lobby@example.test');
                """
            )
            real_page.goto(f"{frontend_base_url}/pages/{page_code}", wait_until="networkidle")
            real_page.get_by_role("button", name="Open launch cashier for BOXE").click()
            real_page.get_by_role("dialog", name="BOXE").wait_for()
            playwright.expect(real_page.locator(".player-lobby-cashier-option").nth(0)).to_be_enabled()
            real_page.locator(".player-lobby-cashier-option").nth(0).click()
            real_page.wait_for_url("**/boxe?*")
            assert "title_code=boxe001" in real_page.url
            assert "mode=real" in real_page.url
            assert "wallet_source=real" in real_page.url

            bonus_page = browser.new_page(viewport={"width": 1015, "height": 768})
            bonus_page.add_init_script(
                """
                window.localStorage.setItem('casinoking.access_token', 'boxe-lobby-token');
                window.localStorage.setItem('casinoking.email', 'boxe-lobby@example.test');
                """
            )
            bonus_page.goto(f"{frontend_base_url}/pages/{page_code}", wait_until="networkidle")
            bonus_page.get_by_role("button", name="Open launch cashier for BOXE").click()
            bonus_page.get_by_role("dialog", name="BOXE").wait_for()
            playwright.expect(bonus_page.locator(".player-lobby-cashier-option").nth(1)).to_be_enabled()
            bonus_page.locator(".player-lobby-cashier-option").nth(1).click()
            bonus_page.wait_for_url("**/boxe?*")
            assert "title_code=boxe001" in bonus_page.url
            assert "mode=real_bonus" in bonus_page.url
            assert "wallet_source=bonus" in bonus_page.url

            browser.close()
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)
        _restore_boxe_casinoking_publication(
            db_connection=db_connection,
            snapshot=publication_snapshot,
        )


def _publish_boxe_for_casinoking(*, db_connection) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE site_titles
            SET
                lobby_visibility = 'visible',
                demo_enabled = true,
                real_enabled = true,
                featured = true,
                lobby_display_name = 'BOXE',
                lobby_description = 'Pick safe boxes and collect.',
                position = 3,
                updated_at = NOW()
            WHERE site_code = 'casinoking'
              AND title_code = 'boxe001'
            """
        )


def _snapshot_boxe_casinoking_publication(*, db_connection) -> dict[str, object] | None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                lobby_visibility,
                demo_enabled,
                real_enabled,
                featured,
                lobby_display_name,
                lobby_description,
                position
            FROM site_titles
            WHERE site_code = 'casinoking'
              AND title_code = 'boxe001'
            """
        )
        row = cursor.fetchone()
    return dict(row) if row is not None else None


def _restore_boxe_casinoking_publication(
    *,
    db_connection,
    snapshot: dict[str, object] | None,
) -> None:
    if snapshot is None:
        return

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE site_titles
            SET
                lobby_visibility = %s,
                demo_enabled = %s,
                real_enabled = %s,
                featured = %s,
                lobby_display_name = %s,
                lobby_description = %s,
                position = %s,
                updated_at = NOW()
            WHERE site_code = 'casinoking'
              AND title_code = 'boxe001'
            """,
            (
                snapshot["lobby_visibility"],
                snapshot["demo_enabled"],
                snapshot["real_enabled"],
                snapshot["featured"],
                snapshot["lobby_display_name"],
                snapshot["lobby_description"],
                snapshot["position"],
            ),
        )


def _site_v3_boxe_modules() -> list[dict[str, object]]:
    return [
        {
            "module_code": "global_header",
            "slot_key": "header",
            "sort_order": 0,
            "config_json": {"brand_label": "CasinoKing"},
        },
        {
            "module_code": "game_grid",
            "slot_key": "games",
            "sort_order": 0,
            "config_json": {
                "heading": "BOXE launch smoke",
                "title_codes": ["boxe001"],
            },
        },
        {
            "module_code": "global_footer",
            "slot_key": "footer",
            "sort_order": 0,
            "config_json": {"legal_text": "18+ Play responsibly."},
        },
    ]


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
