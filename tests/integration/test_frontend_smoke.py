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
    assert 'href="/mines"' in html
    assert 'href="/account"' in html
    assert 'href="/login"' in html
    assert 'href="/register"' in html
    assert "NaN" not in html


@pytest.mark.parametrize(
    ("path", "expected_snippets"),
    [
        ("/mines", ("Mines", "Play Mines", "Login")),
        ("/account", ("Account", "Account recap", "Recent Mines rounds")),
        ("/admin", ("Backoffice Admin", "Operator workspace")),
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
