from __future__ import annotations

import pytest
import httpx


def test_frontend_homepage_renders_player_lobby(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    response = httpx.get(frontend_base_url, timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "CasinoKing" in html
    assert "casino" in html.lower()
    assert 'href="/login"' in html
    assert 'href="/register"' in html
    assert 'href="/mines"' in html
    assert "Mines" in html
    assert "Guest access" not in html
    assert "Player lobby connected to the local backend" not in html
    assert "Login o Demo" not in html
    assert "Runtime loading" not in html
    assert "NaN" not in html


@pytest.mark.parametrize(
    ("path", "expected_snippets"),
    [
        ("/mines", ("Mines", "Grid size", "Game info", "Bet")),
        (
            "/account",
            ("Account", "Player account, wallets, and session history", "Guest access"),
        ),
        ("/admin", ("Login Backoffice", "Login admin")),
        ("/login", ("Sign in", "Password reset")),
        ("/register", ("Registration", "Create player")),
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


def test_register_route_hides_site_access_password_input(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/register", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "site access password" not in html.lower()


def test_mines_route_stays_isolated_from_player_and_backoffice_shells(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/mines", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "Mines" in html
    assert "Grid size" in html
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
    assert "Game info" in html
    assert "Bet" in html
    assert "Login Backoffice" not in html
    assert "Guest access" not in html


def test_frontend_favicon_route_is_served(
    frontend_base_url: str,
) -> None:
    response = httpx.get(f"{frontend_base_url}/favicon.ico", timeout=10.0)

    assert response.status_code == 200
