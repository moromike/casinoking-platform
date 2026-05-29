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


def test_site_v3_player_auth_handoff_preserves_return_to_across_v1_player_routes() -> None:
    login_page = (FRONTEND / "app" / "ui" / "player-login-page.tsx").read_text(encoding="utf-8")
    register_page = (FRONTEND / "app" / "ui" / "player-register-page.tsx").read_text(encoding="utf-8")
    account_page = (FRONTEND / "app" / "ui" / "player-account-page.tsx").read_text(encoding="utf-8")
    player_shell = (FRONTEND / "app" / "ui" / "player-shell.tsx").read_text(encoding="utf-8")
    site_v3_header = (FRONTEND_V3 / "app" / "ui" / "modules" / "site-header-auth-actions.tsx").read_text(
        encoding="utf-8",
    )

    assert 'resolveV1ReturnHref("/login", returnTo)' in site_v3_header
    assert 'resolveV1ReturnHref("/account", returnTo)' in site_v3_header
    assert 'params.get("return_to")' in login_page
    assert "preparePlayerAuthReturnHandoff" in login_page
    assert 'window.location.assign(returnTo)' in login_page
    assert 'withAuthReturnTo("/register", returnTo)' in login_page
    assert 'withAuthReturnTo("/login", returnTo)' in register_page
    assert '"return_to"' in account_page
    assert "sanitizeAuthReturnTo" in account_page
    assert 'withAuthReturnTo("/login", returnTo)' in account_page
    assert 'withAuthReturnTo("/register", returnTo)' in account_page
    assert 'window.location.assign(returnTo)' in player_shell


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
