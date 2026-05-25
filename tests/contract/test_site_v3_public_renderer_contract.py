from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"


def test_site_v3_public_renderer_has_public_only_boundaries() -> None:
    source_files = list((FRONTEND_V3 / "app").rglob("*.ts")) + list((FRONTEND_V3 / "app").rglob("*.tsx"))
    assert source_files, "frontend-v3 app source files must be tracked"

    combined_source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)

    assert "/admin/" not in combined_source
    assert "frontend-v2" not in combined_source
    assert "@/app/ui" not in combined_source
    assert "frontend/app" not in combined_source
    assert "/site-v3/sites/" in combined_source
    assert "/site/home" in combined_source
    assert "/games/library" in combined_source


def test_site_v3_public_renderer_dev_port_and_routes_are_locked() -> None:
    package_json = (FRONTEND_V3 / "package.json").read_text(encoding="utf-8")
    home_route = (FRONTEND_V3 / "app" / "page.tsx").read_text(encoding="utf-8")
    dynamic_route = (FRONTEND_V3 / "app" / "pages" / "[page_code]" / "page.tsx").read_text(encoding="utf-8")

    assert '"dev": "next dev -p 3001"' in package_json
    assert '"start": "next start -p 3001"' in package_json
    assert 'pageCode="home"' in home_route
    assert "SiteV3PublicPage" in dynamic_route


def test_site_v3_public_renderer_covers_all_mvp_modules() -> None:
    modules_dir = FRONTEND_V3 / "app" / "ui" / "modules"
    renderer_source = "\n".join(path.read_text(encoding="utf-8") for path in modules_dir.rglob("*.tsx"))

    expected_files = [
        "site-header.tsx",
        "hero-banner.tsx",
        "game-grid.tsx",
        "featured-game.tsx",
        "promo-band.tsx",
        "rich-text-safe.tsx",
        "site-footer.tsx",
        "module-renderer.tsx",
    ]
    for file_name in expected_files:
        assert (modules_dir / file_name).exists()

    assert "dangerouslySetInnerHTML" in renderer_source
    assert "resolvePublicAssetUrl" in renderer_source
