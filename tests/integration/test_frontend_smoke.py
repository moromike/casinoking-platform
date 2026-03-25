from __future__ import annotations

import httpx


def test_frontend_homepage_renders_player_console(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    response = httpx.get(frontend_base_url, timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "Frontend base integrato con backend locale" in html
    assert "Area Player" in html
    assert "Area Admin" in html
    assert "25<!-- --> celle" in html
    assert "Mines via runtime ufficiale" in html
    assert "NaN" not in html


def test_frontend_admin_route_renders_backoffice(frontend_base_url: str) -> None:
    response = httpx.get(f"{frontend_base_url}/admin", timeout=10.0)

    assert response.status_code == 200
    html = response.text
    assert "Backoffice Admin" in html
    assert "Login admin" in html
    assert "Area Player" in html
    assert "Area Admin" in html
