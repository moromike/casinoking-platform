from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "frontend" / "app" / "ui" / "site-v3-admin" / "site-v3-admin-builder.tsx"
PANEL = ROOT / "frontend" / "app" / "ui" / "site-v3-admin" / "site-v3-draft-preview-panel.tsx"
PUBLIC_PAGE = ROOT / "frontend-v3" / "app" / "ui" / "site-v3-public-page.tsx"
PREVIEW_ROUTE = ROOT / "frontend-v3" / "app" / "preview" / "[token]" / "page.tsx"
PREVIEW_LIB = ROOT / "frontend-v3" / "app" / "lib" / "preview.ts"
RENDER_HELPERS = ROOT / "frontend-v3" / "app" / "ui" / "site-v3-render-helpers.ts"


def test_site_v3_admin_preview_panel_is_mounted_on_page_bound_views() -> None:
    builder_source = BUILDER.read_text(encoding="utf-8")
    helper_source = (ROOT / "frontend" / "app" / "ui" / "site-v3-admin" / "site-v3-admin-helpers.ts").read_text(encoding="utf-8")

    assert "SiteV3DraftPreviewPanel" in builder_source
    assert "isPagePreviewView(currentView)" in builder_source
    assert "SiteV3PageActionBar" in builder_source
    assert "isPageActionBarView(currentView)" in builder_source
    for view in ("pageDetail", "composition", "moduleInstance", "validation"):
        assert f'view.kind === "{view}"' in helper_source
    for view in ("composition", "moduleInstance", "validation"):
        assert f'view.kind === "{view}"' in helper_source.split("function isPageActionBarView", maxsplit=1)[1]
    for excluded in ("pages", "modules", "moduleCategory", "moduleType", "overview", "siteSettings"):
        assert f'view.kind === "{excluded}"' not in helper_source.split("function isPagePreviewView", maxsplit=1)[1]


def test_site_v3_admin_preview_panel_is_collapsible_persistent_and_iframed() -> None:
    panel_source = PANEL.read_text(encoding="utf-8")

    assert "site_v3_preview_panel_expanded" in panel_source
    assert "site-v3-draft-preview-panel" in panel_source
    assert "iframe" in panel_source
    assert "sandbox=\"allow-same-origin allow-scripts allow-popups allow-forms\"" in panel_source
    assert "Open in new tab" in panel_source
    assert "Refresh preview" in panel_source
    assert "Save draft & refresh preview" not in panel_source
    assert "1000" in panel_source


def test_site_v3_public_preview_route_reuses_public_page_renderer() -> None:
    route_source = PREVIEW_ROUTE.read_text(encoding="utf-8")
    page_source = PUBLIC_PAGE.read_text(encoding="utf-8")
    preview_source = PREVIEW_LIB.read_text(encoding="utf-8")

    assert "SiteV3PublicPage" in route_source
    assert 'mode="preview"' in route_source
    assert "loadSiteV3Preview" in page_source
    assert "PreviewBanner" in page_source
    assert "mode?: \"published\" | \"preview\"" in page_source
    assert "/navigation?locale=" in preview_source
    assert "navigationResult.ok ? navigationResult.data : null" in preview_source
    assert "Preview token non valido" not in preview_source


def test_site_v3_public_renderer_preserves_composition_order_for_body_modules() -> None:
    helper_source = RENDER_HELPERS.read_text(encoding="utf-8")

    assert "function pinnedSlotOrder" in helper_source
    assert "slotKey === \"header\"" in helper_source
    assert "slotKey === \"footer\"" in helper_source
    assert "left.sort_order - right.sort_order" in helper_source
    assert "SLOT_ORDER.get(left.slot_key)" not in helper_source
