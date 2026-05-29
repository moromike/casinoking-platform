from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
FRONTEND_V3 = ROOT / "frontend-v3"


def test_player_auth_return_targets_are_sanitized_and_whitelisted() -> None:
    auth_return = (FRONTEND / "app" / "lib" / "auth-return.ts").read_text(encoding="utf-8")

    assert "export function sanitizeAuthReturnTo" in auth_return
    assert 'value.startsWith("/") && !value.startsWith("//")' in auth_return
    assert "allowedAuthReturnOrigins().has(url.origin)" in auth_return
    assert "NEXT_PUBLIC_SITE_V3_BASE_URL" in auth_return
    assert "http://localhost:3000" in auth_return
    assert "http://localhost:3001" in auth_return
    assert "export function withAuthReturnTo" in auth_return


def test_site_v3_player_shell_owns_auth_routes_and_preserves_return_to() -> None:
    v1_redirect_helper = (FRONTEND / "app" / "lib" / "site-v3-redirect.ts").read_text(encoding="utf-8")
    v1_root_route = (FRONTEND / "app" / "(player)" / "page.tsx").read_text(encoding="utf-8")
    v1_login_route = (FRONTEND / "app" / "login" / "page.tsx").read_text(encoding="utf-8")
    v1_register_route = (FRONTEND / "app" / "register" / "page.tsx").read_text(encoding="utf-8")
    v1_account_route = (FRONTEND / "app" / "account" / "page.tsx").read_text(encoding="utf-8")
    site_v3_header = (FRONTEND_V3 / "app" / "ui" / "modules" / "site-header-auth-actions.tsx").read_text(
        encoding="utf-8",
    )
    site_v3_login_page = (FRONTEND_V3 / "app" / "ui" / "player-login-page.tsx").read_text(encoding="utf-8")
    site_v3_register_page = (FRONTEND_V3 / "app" / "ui" / "player-register-page.tsx").read_text(encoding="utf-8")
    site_v3_account_page = (FRONTEND_V3 / "app" / "ui" / "player-account-page.tsx").read_text(encoding="utf-8")
    site_v3_player_shell = (FRONTEND_V3 / "app" / "ui" / "player-shell.tsx").read_text(encoding="utf-8")

    assert 'resolvePlayerReturnHref("/login", returnTo)' in site_v3_header
    assert 'resolvePlayerReturnHref("/account", returnTo)' in site_v3_header
    assert (FRONTEND_V3 / "app" / "login" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "register" / "page.tsx").exists()
    assert (FRONTEND_V3 / "app" / "account" / "page.tsx").exists()
    assert 'params.get("return_to")' in site_v3_login_page
    assert 'window.location.assign(returnTo)' in site_v3_login_page
    assert 'withAuthReturnTo("/register", returnTo)' in site_v3_login_page
    assert 'withAuthReturnTo("/login", returnTo)' in site_v3_register_page
    assert '"return_to"' in site_v3_account_page
    assert "sanitizeAuthReturnTo" in site_v3_account_page
    assert 'withAuthReturnTo("/login", returnTo)' in site_v3_account_page
    assert 'withAuthReturnTo("/register", returnTo)' in site_v3_account_page
    assert 'window.location.assign(returnTo)' in site_v3_player_shell

    # V1 direct public/player routes are not a second player product anymore.
    # They preserve query parameters and hand off ownership to Site V3.
    assert "process.env.NEXT_PUBLIC_SITE_V3_BASE_URL" in v1_redirect_helper
    assert 'const DEFAULT_SITE_V3_BASE_URL = "http://localhost:3000"' in v1_redirect_helper
    assert "appendSearchParams(target.searchParams, searchParams)" in v1_redirect_helper
    assert "redirect(target.toString())" in v1_redirect_helper
    assert 'redirectToSiteV3("/login", (await searchParams) ?? {})' in v1_login_route
    assert 'redirectToSiteV3("/register", (await searchParams) ?? {})' in v1_register_route
    assert 'redirectToSiteV3("/account", (await searchParams) ?? {})' in v1_account_route
    assert 'redirect("/admin")' in v1_root_route
    assert not (FRONTEND / "app" / "(player)" / "layout.tsx").exists()
    assert "PlayerLobbyPage" not in v1_root_route
    for route_source in [v1_login_route, v1_register_route, v1_account_route]:
        assert "PlayerShell" not in route_source
        assert "PlayerLoginPage" not in route_source
        assert "PlayerRegisterPage" not in route_source
        assert "PlayerAccountPage" not in route_source


def test_cross_origin_player_auth_handoff_is_scoped_and_short_lived() -> None:
    v1_auth_storage = (FRONTEND / "app" / "lib" / "auth-storage.ts").read_text(encoding="utf-8")
    v3_player_auth = (FRONTEND_V3 / "app" / "lib" / "player-auth.ts").read_text(encoding="utf-8")
    v3_bridge = (FRONTEND_V3 / "app" / "ui" / "player-auth-bridge.tsx").read_text(encoding="utf-8")

    assert "target_origin: target.origin" in v1_auth_storage
    assert "issued_at: Date.now()" in v1_auth_storage
    assert "window.name = JSON.stringify" in v1_auth_storage
    assert "PLAYER_AUTH_HANDOFF_MAX_AGE_MS = 2 * 60 * 1000" in v3_player_auth
    assert "parsed.target_origin !== window.location.origin" in v3_player_auth
    assert "window.name = \"\"" in v3_player_auth
    assert "consumePlayerAuthHandoff()" in v3_bridge


def test_site_v3_game_launch_handoff_returns_to_sanitized_public_site() -> None:
    render_helpers = (FRONTEND_V3 / "app" / "ui" / "site-v3-render-helpers.ts").read_text(encoding="utf-8")
    game_card = (FRONTEND_V3 / "app" / "ui" / "modules" / "game-card.tsx").read_text(encoding="utf-8")
    game_boot_request = (FRONTEND / "app" / "ui" / "game-runtime" / "game-boot-request.ts").read_text(
        encoding="utf-8",
    )
    mines_standalone = (FRONTEND / "app" / "ui" / "mines" / "mines-standalone.tsx").read_text(
        encoding="utf-8",
    )
    boxe_standalone = (FRONTEND / "app" / "ui" / "boxe" / "boxe-standalone.tsx").read_text(
        encoding="utf-8",
    )
    hilo_standalone = (FRONTEND / "app" / "ui" / "hi-lo" / "hi-lo-standalone.tsx").read_text(
        encoding="utf-8",
    )

    assert "appendReturnToParam(params, returnTo)" in render_helpers
    assert 'params.set("return_to", returnTo)' in render_helpers
    assert 'setReturnTo(window.location.href)' in game_card
    assert 'resolveGameHref(title, "demo", returnTo)' in game_card
    assert 'resolveGameHref(title, "real", returnTo)' in game_card
    assert 'resolveGameHref(title, "bonus", returnTo)' in game_card
    assert "returnTo: string | null" in game_boot_request
    assert 'sanitizeAuthReturnTo(searchParams.get("return_to"))' in game_boot_request
    assert "setReturnTo(bootRequest.returnTo)" in mines_standalone
    assert 'window.location.assign(returnTo ?? "/")' in mines_standalone
    assert 'window.location.assign(returnTo ?? "/")' in boxe_standalone
    assert 'window.location.assign(returnTo ?? "/")' in hilo_standalone
