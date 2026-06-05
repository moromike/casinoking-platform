from __future__ import annotations


def create_game_access_session(
    client,
    headers,
    *,
    game_code: str,
    title_code: str,
    site_code: str = "casinoking",
) -> str:
    """Create a game access session and return its id."""
    resp = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]
