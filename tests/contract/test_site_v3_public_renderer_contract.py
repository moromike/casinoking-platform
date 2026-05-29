from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"


def test_site_v3_old_frontend_v2_lab_is_removed() -> None:
    assert not (ROOT / "frontend-v2").exists()


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
    assert "SITE_V3_API_INTERNAL_BASE_URL" in combined_source


def test_site_v3_public_renderer_dev_port_and_routes_are_locked() -> None:
    compose = (ROOT / "infra" / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "infra" / "docker" / "frontend-v3.Dockerfile").read_text(encoding="utf-8")
    package_json = (FRONTEND_V3 / "package.json").read_text(encoding="utf-8")
    layout = (FRONTEND_V3 / "app" / "layout.tsx").read_text(encoding="utf-8")
    home_route = (FRONTEND_V3 / "app" / "page.tsx").read_text(encoding="utf-8")
    dynamic_route = (FRONTEND_V3 / "app" / "pages" / "[page_code]" / "page.tsx").read_text(encoding="utf-8")

    assert "frontend-v3:" in compose
    assert "edge:" in compose
    assert "EDGE_PORT" in compose
    assert "FRONTEND_V3_PORT" in compose
    assert "NEXT_PUBLIC_V1_BASE_URL" in compose
    assert "SITE_V3_ASSET_PREFIX" in compose
    assert "SITE_V3_API_INTERNAL_BASE_URL" in compose
    assert "frontend_v3_node_modules" in compose
    assert "frontend-v3/package.json" in dockerfile
    assert '"dev": "next dev -p 3001"' in package_json
    assert '"start": "next start -p 3001"' in package_json
    assert '<html lang="en">' in layout
    assert 'pageCode="home"' in home_route
    assert "SiteV3PublicPage" in dynamic_route


def test_site_v3_public_renderer_keeps_v1_handoff_configurable() -> None:
    compose = (ROOT / "infra" / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    env_example = (ROOT / "infra" / "docker" / ".env.example").read_text(encoding="utf-8")
    render_helpers = (FRONTEND_V3 / "app" / "ui" / "site-v3-render-helpers.ts").read_text(
        encoding="utf-8",
    )

    assert "NEXT_PUBLIC_V1_BASE_URL: ${NEXT_PUBLIC_V1_BASE_URL:-http://localhost:3000}" in compose
    assert "NEXT_PUBLIC_V1_BASE_URL=http://localhost:3000" in env_example
    assert "NEXT_PUBLIC_SITE_V3_BASE_URL=http://localhost:3000" in env_example
    assert "process.env.NEXT_PUBLIC_V1_BASE_URL" in render_helpers
    assert "return_to" in render_helpers
    assert 'path: "/login" | "/account"' in render_helpers


def test_site_v3_public_edge_routes_root_to_v3_and_legacy_to_v1() -> None:
    compose = (ROOT / "infra" / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    edge_conf = (ROOT / "infra" / "docker" / "edge.conf").read_text(encoding="utf-8")
    next_config = (FRONTEND_V3 / "next.config.ts").read_text(encoding="utf-8")
    env_example = (ROOT / "infra" / "docker" / ".env.example").read_text(encoding="utf-8")

    assert "image: nginx:" in compose
    assert '"${EDGE_PORT:-3000}:80"' in compose
    assert '"${FRONTEND_PORT:-3002}:3000"' in compose
    assert "EDGE_PORT=3000" in env_example
    assert "FRONTEND_PORT=3002" in env_example
    assert "SITE_V3_PUBLIC_BASE_URL=http://localhost:3000" in env_example
    assert "assetPrefix" in next_config
    assert "SITE_V3_ASSET_PREFIX" in next_config
    assert "rewrites()" in next_config
    assert "location /site-v3-assets/_next/" in edge_conf
    assert "location / {" in edge_conf
    assert "proxy_pass http://casinoking_frontend_v3;" in edge_conf
    for legacy_path in ["login", "register", "account", "admin", "mines", "boxe", "hi-lo"]:
        assert f"location /{legacy_path}" in edge_conf


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


def test_site_v3_public_renderer_rejects_unsafe_asset_url_schemes() -> None:
    api_source = (FRONTEND_V3 / "app" / "lib" / "api.ts").read_text(encoding="utf-8")

    assert "/^(https?:|data:|blob:)/" not in api_source
    assert "assetUrl.startsWith" not in api_source
    assert 'return null;' in api_source
    assert 'normalized.startsWith("/static/")' in api_source
    assert 'normalized.startsWith("/uploads/")' in api_source


def test_site_v3_public_header_fallback_links_to_existing_sections() -> None:
    header_source = (FRONTEND_V3 / "app" / "ui" / "modules" / "site-header.tsx").read_text(encoding="utf-8")
    game_grid_source = (FRONTEND_V3 / "app" / "ui" / "modules" / "game-grid.tsx").read_text(encoding="utf-8")

    assert '{ label: "Games", url: "#games" }' in header_source
    assert '"#promos"' not in header_source
    assert 'id="games"' in game_grid_source
