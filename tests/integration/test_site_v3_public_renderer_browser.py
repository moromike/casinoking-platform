from __future__ import annotations

import base64
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import httpx
import pytest

from app.core.config import settings
from app.modules.platform.site_v3.module_definitions import (
    create_custom_module_definition,
    publish_custom_module_definition,
)
from app.modules.platform.site_v3.service import publish_page, save_draft


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"
SITE_V3_URL = "http://localhost:3001"


@pytest.mark.integration
def test_site_v3_public_renderer_loads_published_page_without_admin_token(
    create_admin_user,
    create_published_mines_variant,
    db_connection,
) -> None:
    playwright_api = pytest.importorskip("playwright.sync_api")
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
            with playwright_api.sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    executable_path=chromium_executable,
                )
                try:
                    page = browser.new_page(viewport={"width": 1365, "height": 768})
                    page.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")

                    _wait_for_visible_text(page, "Site V3 Renderer Smoke")
                    _wait_for_visible_text(page, "Mines Site V3 Renderer Target")
                    assert page.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")

                    mobile = browser.new_page(viewport={"width": 390, "height": 844})
                    mobile.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")
                    _wait_for_visible_text(mobile, "Site V3 Renderer Smoke")
                    assert mobile.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")
                finally:
                    browser.close()
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


@pytest.mark.integration
def test_site_v3_public_renderer_loads_all_custom_renderer_templates(
    create_admin_user,
    create_published_mines_variant,
    db_connection,
) -> None:
    playwright_api = pytest.importorskip("playwright.sync_api")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin = create_admin_user(prefix="site-v3-custom-renderer-browser")
    title = create_published_mines_variant(
        title_code=f"mines_custom_matrix_{uuid4().hex[:8]}",
        display_name="Mines Custom Matrix Target",
    )
    suffix = uuid4().hex[:8]
    page_code = f"custom-renderers-{suffix}"
    asset_public_url = _write_custom_renderer_asset(suffix)
    definitions = _custom_renderer_definition_payloads(suffix)
    module_codes = [str(payload["module_code"]) for payload in definitions]

    try:
        for payload in definitions:
            create_custom_module_definition(
                site_code="casinoking",
                payload=payload,
                admin_user_id=str(admin["user_id"]),
            )
            publish_custom_module_definition(
                site_code="casinoking",
                module_code=str(payload["module_code"]),
                admin_user_id=str(admin["user_id"]),
            )

        save_draft(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            title="Custom renderer matrix",
            expected_draft_version=None,
            admin_user_id=str(admin["user_id"]),
            modules=_custom_renderer_modules(
                module_codes=module_codes,
                asset_public_url=asset_public_url,
                title_code=str(title["title_code"]),
            ),
        )
        publish_page(
            site_code="casinoking",
            page_code=page_code,
            locale="it",
            expected_draft_version=1,
            admin_user_id=str(admin["user_id"]),
        )

        with _ensure_site_v3_server():
            with playwright_api.sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    executable_path=chromium_executable,
                )
                try:
                    page = browser.new_page(viewport={"width": 1365, "height": 900})
                    page.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")

                    for expected_text in [
                        "Play image CTA",
                        "Custom game grid matrix",
                        "Mines Custom Matrix Target",
                        "Custom editorial panel",
                        "Custom rich text matrix",
                        "Featured custom card",
                    ]:
                        _wait_for_visible_text(page, expected_text)
                    assert page.locator(".site-v3-custom-image-banner img").count() == 1
                    assert page.locator(".site-v3-custom-editorial").count() >= 1
                    assert page.locator(".site-v3-rich-text").count() >= 1
                    assert page.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")

                    mobile = browser.new_page(viewport={"width": 390, "height": 844})
                    mobile.goto(f"{SITE_V3_URL}/pages/{page_code}", wait_until="networkidle")
                    _wait_for_visible_text(mobile, "Custom rich text matrix")
                    _wait_for_visible_text(mobile, "Mines Custom Matrix Target")
                    assert mobile.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")
                finally:
                    browser.close()
    finally:
        _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)
        _cleanup_custom_definitions(db_connection=db_connection, module_codes=module_codes)
        _cleanup_custom_renderer_asset(suffix)


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


def _find_chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        "/snap/bin/chromium",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _wait_for_visible_text(page, text: str) -> None:
    page.get_by_text(text).first.wait_for(timeout=20_000)


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


def _custom_renderer_definition_payloads(suffix: str) -> list[dict[str, object]]:
    return [
        {
            "module_code": f"custom_matrix_image_{suffix}",
            "label": "Matrix image banner",
            "category": "hero",
            "renderer_template": "image_banner",
            "field_schema_json": [
                {"key": "headline", "label": "Headline", "type": "string", "group": "content"},
                {"key": "media", "label": "Media", "type": "asset_ref", "group": "assets", "required": True},
                {"key": "cta_label", "label": "CTA label", "type": "string", "group": "links"},
                {"key": "cta_url", "label": "CTA URL", "type": "url", "group": "links"},
                {"key": "show_cta", "label": "Show CTA", "type": "boolean", "group": "links"},
            ],
            "default_config_json": {"headline": "", "media": {}, "cta_label": "", "cta_url": "", "show_cta": True},
        },
        {
            "module_code": f"custom_matrix_grid_{suffix}",
            "label": "Matrix game grid",
            "category": "catalog",
            "renderer_template": "game_grid",
            "field_schema_json": [
                {"key": "heading", "label": "Heading", "type": "string", "group": "content", "required": True},
                {
                    "key": "title_codes",
                    "label": "Game titles",
                    "type": "title_code_list",
                    "group": "catalog",
                    "required": True,
                    "max_items": 8,
                },
            ],
            "default_config_json": {"heading": "", "title_codes": []},
        },
        {
            "module_code": f"custom_matrix_editorial_{suffix}",
            "label": "Matrix editorial",
            "category": "promo",
            "renderer_template": "editorial_panel",
            "field_schema_json": [
                {"key": "headline", "label": "Headline", "type": "string", "group": "content", "required": True},
                {"key": "body", "label": "Body", "type": "string", "group": "content"},
                {"key": "media", "label": "Media", "type": "asset_ref", "group": "assets"},
                {"key": "cta_label", "label": "CTA label", "type": "string", "group": "links"},
                {"key": "cta_url", "label": "CTA URL", "type": "url", "group": "links"},
            ],
            "default_config_json": {"headline": "", "body": "", "media": {}, "cta_label": "", "cta_url": ""},
        },
        {
            "module_code": f"custom_matrix_rich_{suffix}",
            "label": "Matrix rich text",
            "category": "text_legal",
            "renderer_template": "rich_text",
            "field_schema_json": [
                {"key": "html", "label": "HTML", "type": "html", "group": "rules", "required": True},
            ],
            "default_config_json": {"html": ""},
        },
        {
            "module_code": f"custom_matrix_feature_{suffix}",
            "label": "Matrix feature card",
            "category": "catalog",
            "renderer_template": "feature_card",
            "field_schema_json": [
                {"key": "title_code", "label": "Game title", "type": "title_code", "group": "catalog", "required": True},
                {"key": "headline", "label": "Headline", "type": "string", "group": "content"},
                {"key": "body", "label": "Body", "type": "string", "group": "content"},
                {"key": "cta_label", "label": "CTA label", "type": "string", "group": "links"},
            ],
            "default_config_json": {"title_code": "", "headline": "", "body": "", "cta_label": ""},
        },
    ]


def _custom_renderer_modules(
    *,
    module_codes: list[str],
    asset_public_url: str,
    title_code: str,
) -> list[dict[str, object]]:
    image_code, grid_code, editorial_code, rich_code, feature_code = module_codes
    return [
        {
            "module_code": "global_header",
            "slot_key": "header",
            "sort_order": 0,
            "config_json": {"brand_label": "CasinoKing", "nav_items": [{"label": "Games", "url": "/"}]},
        },
        {
            "module_code": image_code,
            "schema_version": 1,
            "slot_key": "hero",
            "sort_order": 0,
            "config_json": {
                "headline": "Custom image banner matrix",
                "media": {"public_url": asset_public_url},
                "cta_label": "Play image CTA",
                "cta_url": "/login",
                "show_cta": True,
            },
        },
        {
            "module_code": grid_code,
            "schema_version": 1,
            "slot_key": "games",
            "sort_order": 0,
            "config_json": {
                "heading": "Custom game grid matrix",
                "title_codes": [title_code],
            },
        },
        {
            "module_code": editorial_code,
            "schema_version": 1,
            "slot_key": "promo",
            "sort_order": 0,
            "config_json": {
                "headline": "Custom editorial panel",
                "body": "Editorial text authored through a custom schema.",
                "media": {"public_url": asset_public_url},
                "cta_label": "Read editorial",
                "cta_url": "/account",
            },
        },
        {
            "module_code": rich_code,
            "schema_version": 1,
            "slot_key": "content",
            "sort_order": 1,
            "config_json": {"html": "<p><strong>Custom rich text matrix</strong> content.</p>"},
        },
        {
            "module_code": feature_code,
            "schema_version": 1,
            "slot_key": "games",
            "sort_order": 1,
            "config_json": {
                "title_code": title_code,
                "headline": "Featured custom card",
                "body": "Feature card backed by a custom definition.",
                "cta_label": "Start feature",
            },
        },
        {
            "module_code": "global_footer",
            "slot_key": "footer",
            "sort_order": 0,
            "config_json": {"legal_text": "18+ Play responsibly."},
        },
    ]


def _write_custom_renderer_asset(suffix: str) -> str:
    asset_dir = settings.asset_storage_root / f"site_v3_custom_matrix_{suffix}" / "banner"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "matrix.png").write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lF78ywAAAABJRU5ErkJggg=="
        )
    )
    return f"/static/games/site_v3_custom_matrix_{suffix}/banner/matrix.png"


def _cleanup_custom_renderer_asset(suffix: str) -> None:
    shutil.rmtree(settings.asset_storage_root / f"site_v3_custom_matrix_{suffix}", ignore_errors=True)


def _cleanup_custom_definitions(*, db_connection, module_codes: list[str]) -> None:
    with db_connection.cursor() as cursor:
        for module_code in module_codes:
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
