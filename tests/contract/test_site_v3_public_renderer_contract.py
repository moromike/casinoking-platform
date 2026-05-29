from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"


def _edge_location_body(edge_conf: str, path: str) -> str:
    match = re.search(
        rf"location\s+(?:=\s+)?{re.escape(path)}\s*\{{(?P<body>.*?)\n\s*\}}",
        edge_conf,
        re.S,
    )
    assert match, f"edge location {path} must exist"
    return match.group("body")


def _is_public_v3_source(path: Path) -> bool:
    relative = path.relative_to(FRONTEND_V3 / "app")
    parts = relative.parts
    if parts[0] == "admin":
        return False
    if parts[:2] == ("ui", "site-v3-admin"):
        return False
    if parts[:2] in {
        ("ui", "audit"),
        ("ui", "games"),
        ("ui", "site"),
        ("ui", "title-editor"),
        ("ui", "boxe-backoffice"),
        ("ui", "hi-lo-backoffice"),
        ("ui", "mines-backoffice"),
    }:
        return False
    if parts[0] == "ui" and path.name in {
        "access-log.tsx",
        "admin-finance-panel.tsx",
        "admin-management.tsx",
        "admin-my-space.tsx",
        "admin-platform-settings-panel.tsx",
        "admin-shell-panel.tsx",
        "casinoking-console.tsx",
        "game-reporting-registry.tsx",
        "player-admin-panel.tsx",
        "player-game-registry.ts",
    }:
        return False
    if parts == ("ui", "admin-site-v3-page.tsx"):
        return False
    if parts in {
        ("ui", "admin-games-page.tsx"),
        ("ui", "platform-catalog-panel.tsx"),
    }:
        return False
    if parts == ("lib", "admin-storage.ts"):
        return False
    if parts == ("lib", "title-code.ts"):
        return False
    return True


def test_site_v3_old_frontend_v2_lab_is_removed() -> None:
    assert not (ROOT / "frontend-v2").exists()


def test_site_v3_public_renderer_has_public_only_boundaries() -> None:
    source_files = [
        path
        for path in list((FRONTEND_V3 / "app").rglob("*.ts")) + list((FRONTEND_V3 / "app").rglob("*.tsx"))
        if _is_public_v3_source(path)
    ]
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
    assert 'path: "/login" | "/register" | "/account"' in render_helpers
    assert "resolvePlayerReturnHref" in render_helpers
    assert 'return `${path}?${params.toString()}`' in render_helpers
    assert "pointsToAccount" in (FRONTEND_V3 / "app" / "ui" / "modules" / "account-aware-link.tsx").read_text(encoding="utf-8")


def test_site_v3_public_edge_routes_root_player_shell_and_game_shell_to_v3() -> None:
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
    for v3_path in ["login", "register", "account", "admin", "admin/site-v3", "admin/games", "runtime/mines", "runtime/boxe", "runtime/hi-lo", "mines", "boxe", "hi-lo"]:
        assert f"location /{v3_path}" in edge_conf
    assert edge_conf.index("location /admin/site-v3") < edge_conf.index("location /admin {")
    assert edge_conf.index("location /admin/games") < edge_conf.index("location /admin {")
    assert "location /legacy-games/mines" not in edge_conf
    assert "location /legacy-games/boxe" not in edge_conf
    assert "location /legacy-games/hi-lo" not in edge_conf
    for v3_path in ["/login", "/register", "/account", "/admin", "/admin/site-v3", "/admin/games", "/runtime/mines", "/runtime/boxe", "/runtime/hi-lo", "/mines", "/boxe", "/hi-lo"]:
        location_block = _edge_location_body(edge_conf, v3_path)
        assert "proxy_pass http://casinoking_frontend_v3;" in location_block


def test_site_v3_admin_root_is_owned_by_v3_with_legacy_redirect() -> None:
    edge_conf = (ROOT / "infra" / "docker" / "edge.conf").read_text(encoding="utf-8")
    v3_admin_route = (FRONTEND_V3 / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")
    v3_console = (FRONTEND_V3 / "app" / "ui" / "casinoking-console.tsx").read_text(encoding="utf-8")
    legacy_route = (ROOT / "frontend" / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")

    assert "proxy_pass http://casinoking_frontend_v3;" in _edge_location_body(edge_conf, "/admin")
    assert "CasinoKingConsole" in v3_admin_route
    assert "AdminFinancePanel" in v3_console
    assert "PlayerAdminPanel" in v3_console
    assert "AdminPlatformSettingsPanel" in v3_console
    assert "AdminAuditLog" in v3_console
    assert "AdminManagement" in v3_console
    assert "AdminMySpace" in v3_console
    assert "redirect(`${SITE_V3_BASE_URL}/admin`)" in legacy_route
    assert "CasinoKingConsole" not in legacy_route


def test_site_v3_admin_builder_route_is_owned_by_v3_with_legacy_redirect() -> None:
    edge_conf = (ROOT / "infra" / "docker" / "edge.conf").read_text(encoding="utf-8")
    v3_route = (FRONTEND_V3 / "app" / "admin" / "site-v3" / "page.tsx").read_text(encoding="utf-8")
    v3_shell = (FRONTEND_V3 / "app" / "ui" / "admin-site-v3-page.tsx").read_text(encoding="utf-8")
    v3_api = (FRONTEND_V3 / "app" / "lib" / "api.ts").read_text(encoding="utf-8")
    admin_api = (FRONTEND_V3 / "app" / "ui" / "site-v3-admin" / "site-v3-admin-api.ts").read_text(encoding="utf-8")
    legacy_route = (ROOT / "frontend" / "app" / "admin" / "site-v3" / "page.tsx").read_text(encoding="utf-8")

    assert "location /admin/site-v3" in edge_conf
    assert "proxy_pass http://casinoking_frontend_v3;" in _edge_location_body(edge_conf, "/admin/site-v3")
    assert edge_conf.index("location /admin/site-v3") < edge_conf.index("location /admin {")
    assert "AdminSiteV3Page" in v3_route
    assert "SiteV3AdminBuilder" in v3_shell
    assert '"/admin/auth/login"' in v3_shell
    assert '"/admin/auth/me"' in v3_shell
    assert "ADMIN_STORAGE_KEYS" in v3_shell
    assert "apiFormRequest" in v3_api
    assert "apiFormRequest" in admin_api
    assert "redirect(`${SITE_V3_BASE_URL}/admin/site-v3`)" in legacy_route
    assert "CasinoKingConsole" not in legacy_route
    assert "adminSiteV3Route" not in legacy_route


def test_site_v3_admin_games_routes_are_owned_by_v3_with_legacy_redirects() -> None:
    edge_conf = (ROOT / "infra" / "docker" / "edge.conf").read_text(encoding="utf-8")
    v3_admin_games_page = (FRONTEND_V3 / "app" / "ui" / "admin-games-page.tsx").read_text(encoding="utf-8")
    v3_api = (FRONTEND_V3 / "app" / "lib" / "api.ts").read_text(encoding="utf-8")
    legacy_pages = [
        ROOT / "frontend" / "app" / "admin" / "games" / "page.tsx",
        ROOT / "frontend" / "app" / "admin" / "games" / "[engine]" / "page.tsx",
        ROOT / "frontend" / "app" / "admin" / "games" / "[engine]" / "titles" / "[title_code]" / "page.tsx",
    ]

    assert "location /admin/games" in edge_conf
    assert "proxy_pass http://casinoking_frontend_v3;" in _edge_location_body(edge_conf, "/admin/games")
    assert edge_conf.index("location /admin/games") < edge_conf.index("location /admin {")
    assert (FRONTEND_V3 / "app" / "admin" / "games" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "admin" / "games" / "[engine]" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "admin" / "games" / "[engine]" / "titles" / "[title_code]" / "page.tsx").exists()
    assert "PlatformCatalogPanel" in v3_admin_games_page
    assert "TitleEditorShell" in v3_admin_games_page
    assert '"/admin/auth/login"' in v3_admin_games_page
    assert '"/admin/auth/me"' in v3_admin_games_page
    assert "/catalog/titles/" in v3_admin_games_page
    assert "/admin/games/titles/" in v3_admin_games_page
    assert "apiDeleteRequest" in v3_api
    for legacy_page in legacy_pages:
        source = legacy_page.read_text(encoding="utf-8")
        assert "redirect(" in source
        assert "SITE_V3_BASE_URL" in source
        assert "CasinoKingConsole" not in source


def test_site_v3_public_edge_allows_v1_only_for_static_residuals() -> None:
    edge_conf = (ROOT / "infra" / "docker" / "edge.conf").read_text(encoding="utf-8")
    location_blocks = re.findall(r"location\s+(?:=\s+)?(?P<path>[^\s{]+)\s*\{(?P<body>.*?)\n\s*\}", edge_conf, re.S)
    v1_paths = {
        path
        for path, body in location_blocks
        if "proxy_pass http://casinoking_frontend_v1" in body
    }

    assert v1_paths == {"/favicon.ico", "/_next/", "/game-assets/", "/brand/"}
    assert not any(path in v1_paths for path in {"/", "/login", "/register", "/account"})
    assert not any(path.startswith("/runtime/") for path in v1_paths)
    assert not any(path.startswith("/legacy-games/") for path in v1_paths)


def test_site_v3_public_renderer_owns_player_shell_routes_without_backend_changes() -> None:
    player_routes = ["login", "register", "account"]
    for route in player_routes:
        assert (FRONTEND_V3 / "app" / route / "page.tsx").exists()

    account_page = (FRONTEND_V3 / "app" / "ui" / "player-account-page.tsx").read_text(encoding="utf-8")
    login_page = (FRONTEND_V3 / "app" / "ui" / "player-login-page.tsx").read_text(encoding="utf-8")
    register_page = (FRONTEND_V3 / "app" / "ui" / "player-register-page.tsx").read_text(encoding="utf-8")
    register_route = (FRONTEND_V3 / "app" / "register" / "page.tsx").read_text(encoding="utf-8")
    registration_config = (FRONTEND_V3 / "app" / "ui" / "registration-form-config.ts").read_text(encoding="utf-8")

    assert 'apiRequest<LoginResponse>("/auth/login"' in login_page
    assert 'apiRequest<RegisterResponse>("/auth/register"' in register_page
    assert 'loadSiteV3Page({ siteCode, pageCode: "register", locale })' in register_route
    assert 'findFirstModule(result.page.modules, "system_registration_form")' in register_route
    assert "readRegistrationFormConfig" in register_route
    assert "postRegisterPath" in registration_config
    assert "requireDocumentImages" in registration_config
    assert "router.push(config.postRegisterPath)" in register_page
    assert "config.requireDocumentImages" in register_page
    assert 'apiRequest<PlayerProfile>("/auth/me"' in account_page
    assert 'apiRequest<Wallet[]>("/wallets"' in account_page
    assert "/account/statement-movements" in account_page
    assert '"/games/mines/sessions"' in account_page
    assert '"/games/boxe/sessions"' in account_page
    assert '"/games/hi-lo/sessions"' in account_page


def test_site_v3_public_renderer_owns_game_shell_routes_with_per_game_runtime_frame() -> None:
    game_frame = (FRONTEND_V3 / "app" / "ui" / "game-frame-page.tsx").read_text(encoding="utf-8")
    mines_route = (FRONTEND_V3 / "app" / "mines" / "page.tsx").read_text(encoding="utf-8")
    boxe_route = (FRONTEND_V3 / "app" / "boxe" / "page.tsx").read_text(encoding="utf-8")
    hi_lo_route = (FRONTEND_V3 / "app" / "hi-lo" / "page.tsx").read_text(encoding="utf-8")
    render_helpers = (FRONTEND_V3 / "app" / "ui" / "site-v3-render-helpers.ts").read_text(encoding="utf-8")

    for route in ["mines", "boxe", "hi-lo"]:
        assert (FRONTEND_V3 / "app" / route / "page.tsx").exists()

    assert "loadGameLibraryTitles" in (FRONTEND_V3 / "app" / "lib" / "api.ts").read_text(encoding="utf-8")
    assert (FRONTEND_V3 / "app" / "runtime" / "mines" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "runtime" / "boxe" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "runtime" / "hi-lo" / "page.tsx").exists()
    assert 'runtimePath: "/runtime/mines"' in mines_route
    assert 'runtimePath: "/runtime/boxe"' in boxe_route
    assert 'runtimePath: "/runtime/hi-lo"' in hi_lo_route
    assert 'return `${framePath}?${params.toString()}`' in game_frame
    assert 'params.set("embed", "1")' in game_frame
    assert 'params.set("embed_origin", origin)' in game_frame
    assert "GAME_EMBED_CLOSE_MESSAGE" in game_frame
    assert "GAME_EMBED_FULLSCREEN_STATE_MESSAGE" in game_frame
    assert "window.location.assign(returnTo)" in game_frame
    assert "SITE_V3_BASE_URL" in render_helpers
    assert 'return `${SITE_V3_BASE_URL}/${routeForEngine(title.engine_code)}?${params.toString()}`' in render_helpers


def test_site_v3_public_renderer_covers_all_mvp_modules() -> None:
    modules_dir = FRONTEND_V3 / "app" / "ui" / "modules"
    renderer_source = "\n".join(path.read_text(encoding="utf-8") for path in modules_dir.rglob("*.tsx"))

    expected_files = [
        "site-header.tsx",
        "hero-banner.tsx",
        "game-grid.tsx",
        "featured-game.tsx",
        "promo-band.tsx",
        "system-registration-form.tsx",
        "rich-text-safe.tsx",
        "site-footer.tsx",
        "module-renderer.tsx",
    ]
    for file_name in expected_files:
        assert (modules_dir / file_name).exists()

    assert "dangerouslySetInnerHTML" in renderer_source
    assert "resolvePublicAssetUrl" in renderer_source


def test_site_v3_public_renderer_supports_custom_snapshot_templates_without_public_definition_fetch() -> None:
    modules_dir = FRONTEND_V3 / "app" / "ui" / "modules"
    renderer_source = (modules_dir / "module-renderer.tsx").read_text(encoding="utf-8")
    custom_renderer_source = (modules_dir / "custom-module-renderer.tsx").read_text(encoding="utf-8")
    types_source = (FRONTEND_V3 / "app" / "lib" / "types.ts").read_text(encoding="utf-8")
    combined_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (FRONTEND_V3 / "app").rglob("*.ts*")
        if _is_public_v3_source(path)
    )

    assert "definition_snapshot" in types_source
    assert "SiteV3CustomDefinitionSnapshot" in types_source
    assert "module.module_code.startsWith(\"custom_\")" in renderer_source
    assert "CustomModuleRenderer" in renderer_source
    assert "without definition_snapshot" in custom_renderer_source
    assert "definition.module_code !== module.module_code" in custom_renderer_source
    for template in ["image_banner", "game_grid", "editorial_panel", "rich_text", "feature_card"]:
        assert f'case "{template}"' in custom_renderer_source
    assert "module-definitions" not in combined_source


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

    assert "readNavItems" not in header_source
    assert "<nav" not in header_source
    assert '{ label: "Games", url: "#games" }' not in header_source
    assert '"#promos"' not in header_source
    assert 'const sectionId = variant === "large4" ? "games-grid-dollar" : "games"' in game_grid_source
    assert "id={sectionId}" in game_grid_source
    assert "games-grid-dollar" in game_grid_source
