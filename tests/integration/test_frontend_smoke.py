from __future__ import annotations

import os
from pathlib import Path

import pytest
import httpx


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_edge_homepage_renders_site_v3(
    public_edge_base_url: str,
    wait_for_public_edge,
) -> None:
    del wait_for_public_edge

    response = httpx.get(public_edge_base_url, timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "site-v3-page" in html
    assert "site-v3-main" in html
    assert "CasinoKing" in html
    assert "/site-v3-assets/_next/" in html
    assert "Page not published" not in html
    assert "frontend-v2" not in html
    assert "NaN" not in html


def test_v1_frontend_direct_homepage_still_serves_legacy_player_lobby(
    v1_frontend_base_url: str,
    wait_for_v1_frontend,
) -> None:
    del wait_for_v1_frontend

    response = httpx.get(v1_frontend_base_url, timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "CasinoKing" in html
    assert 'href="/login"' in html
    assert 'href="/register"' in html
    assert 'href="/mines"' in html
    assert "Mines" in html
    assert "site-v3-page" not in html
    assert "Runtime loading" not in html
    assert "NaN" not in html


def test_site_v3_frontend_homepage_route_is_served(
    site_v3_frontend_base_url: str,
    wait_for_site_v3_frontend,
) -> None:
    del wait_for_site_v3_frontend

    response = httpx.get(site_v3_frontend_base_url, timeout=10.0)

    assert response.status_code == 200
    html = response.text
    public_site_v3_base_url = os.getenv("CASINOKING_PUBLIC_SITE_V3_BASE_URL", "http://localhost:3000").rstrip("/")
    encoded_site_v3_base_url = public_site_v3_base_url.replace(":", "%3A").replace("/", "%2F")
    assert "site-v3-page" in html
    assert 'href="/login?return_to=' in html
    assert encoded_site_v3_base_url in html
    assert "admin_access_token" not in html
    assert "frontend-v2" not in html


def test_site_v3_frontend_home_route_alias_is_served(
    site_v3_frontend_base_url: str,
) -> None:
    response = httpx.get(f"{site_v3_frontend_base_url}/pages/home", timeout=10.0)

    assert response.status_code == 200
    assert "site-v3-page" in response.text


# This HTTP smoke verifies that route shells are served. Hydrated client UI
# controls are covered by the Playwright browser smokes.
@pytest.mark.parametrize(
    ("path", "expected_snippets"),
    [
        ("/mines", ("Mines",)),
        (
            "/account",
            ("Account", "Saldo", "dettagli account.", "Guest access"),
        ),
        ("/admin", ("Admin", "Backoffice")),
        ("/admin/games", ("Admin", "Backoffice")),
        ("/admin/games/mines", ("Admin", "Backoffice")),
        ("/admin/games/mines/titles/mines_classic", ("Admin", "Backoffice")),
        ("/login", ("Sign in", "Hai dimenticato la password?")),
        ("/register", ("Registration", "Checking current player session.")),
    ],
)
def test_frontend_subroutes_render_dedicated_shell(
    frontend_base_url: str,
    path: str,
    expected_snippets: tuple[str, ...],
) -> None:
    response = httpx.get(f"{frontend_base_url}{path}", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "CasinoKing" in html
    for snippet in expected_snippets:
        assert snippet in html

    if path == "/login":
        assert "Password reset" not in html


def test_register_route_does_not_embed_site_access_password_default(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/register", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "change-me" not in html
    assert "Checking current player session." in html

    register_source = (REPO_ROOT / "frontend-v3/app/ui/player-register-page.tsx").read_text()
    assert "accessCodeLabel" in register_source
    assert "hasPlayerAuthSnapshot" in register_source


@pytest.mark.parametrize("path", ["/login", "/register", "/account"])
def test_v1_direct_player_routes_redirect_to_site_v3(
    v1_frontend_base_url: str,
    wait_for_v1_frontend,
    path: str,
) -> None:
    del wait_for_v1_frontend

    response = httpx.get(
        f"{v1_frontend_base_url}{path}?return_to=%2Fgames&locale=it",
        timeout=10.0,
        follow_redirects=False,
    )

    assert response.status_code in {307, 308}
    location = response.headers["location"]
    assert location.startswith(f"http://localhost:3000{path}")
    assert "return_to=%2Fgames" in location
    assert "locale=it" in location


def test_mines_route_stays_isolated_from_player_and_backoffice_shells(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/mines", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "Mines" in html
    assert "Login Backoffice" not in html
    assert "Guest access" not in html
    assert "Create player" not in html


def test_mines_embed_route_renders_standalone_surface(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/mines?embed=1", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "Mines" in html
    assert "Login Backoffice" not in html
    assert "Guest access" not in html


def test_frontend_favicon_route_is_served(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/favicon.ico", timeout=10.0)

    assert response.status_code == 200
