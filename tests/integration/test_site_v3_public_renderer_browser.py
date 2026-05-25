from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import httpx
import pytest
from playwright.sync_api import sync_playwright

from app.modules.platform.site_v3.service import publish_page, save_draft
from tests.integration.test_mines_embed_browser_smoke import _find_chromium_executable


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"
SITE_V3_URL = "http://localhost:3001"


@pytest.mark.integration
def test_site_v3_public_renderer_loads_published_page_without_admin_token(
    create_admin_user,
    create_published_mines_variant,
    db_connection,
) -> None:
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin = create_admin_user(prefix="site-v3-public-renderer-admin")
    title = create_published_mines_variant(
        title_code=f"mines_site_v3_render_{uuid4().hex[:8]}",
        display_name="Mines Site V3 Renderer Target",
    )
    page_code = f"renderer-{uuid4().hex[:8]}"

    try:
        save_draft(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            title="Site V3 Renderer Smoke",
            expected_draft_version=None,
            admin_user_id=str(admin["user_id"]),
            modules=_renderer_modules(title["title_code"]),
        )
        publish_page(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            expected_draft_version=1,
            admin_user_id=str(admin["user_id"]),
        )

        with _ensure_site_v3_server():
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    executable_path=chromium_executable,
                )
                try:
                    page = browser.new_page(viewport={"width": 1365, "height": 768})
                    page.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")

                    page.get_by_text("Site V3 Renderer Smoke").wait_for(timeout=20_000)
                    page.get_by_text("Mines Site V3 Renderer Target").wait_for(timeout=20_000)
                    assert page.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")

                    mobile = browser.new_page(viewport={"width": 390, "height": 844})
                    mobile.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")
                    mobile.get_by_text("Site V3 Renderer Smoke").wait_for(timeout=20_000)
                    assert mobile.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")
                finally:
                    browser.close()
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


@contextmanager
def _ensure_site_v3_server():
    if _is_site_v3_ready():
        yield
        return

    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        pytest.skip("npm is not available to start frontend-v3.")

    env = os.environ.copy()
    env.setdefault("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000/api/v1")
    process = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=FRONTEND_V3,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("frontend-v3 dev server exited before becoming ready")
            if _is_site_v3_ready():
                yield
                return
            time.sleep(1)
        raise TimeoutError("frontend-v3 dev server did not become ready on :3001")
    finally:
        _stop_process_tree(process)


def _is_site_v3_ready() -> bool:
    try:
        response = httpx.get(SITE_V3_URL, timeout=2)
    except httpx.HTTPError:
        return False
    return response.status_code < 500 and "site-v3-page" in response.text


def _stop_process_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def _renderer_modules(title_code: str) -> list[dict[str, object]]:
    return [
        {
            "module_code": "global_header",
            "slot_key": "header",
            "sort_order": 0,
            "config_json": {
                "brand_label": "CasinoKing",
                "nav_items": [{"label": "Giochi", "url": "/"}],
                "login_label": "Login",
                "account_label": "Account",
            },
        },
        {
            "module_code": "hero_banner",
            "slot_key": "hero",
            "sort_order": 0,
            "config_json": {
                "headline": "Site V3 Renderer Smoke",
                "body": "Published-only public renderer.",
                "cta_label": "Gioca demo",
                "cta_title_code": title_code,
            },
        },
        {
            "module_code": "game_grid",
            "slot_key": "games",
            "sort_order": 0,
            "config_json": {
                "heading": "Giochi pubblicati",
                "title_codes": [title_code],
            },
        },
        {
            "module_code": "rich_text_safe",
            "slot_key": "content",
            "sort_order": 0,
            "config_json": {"html": "<p><strong>Safe</strong> public content.</p>"},
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
