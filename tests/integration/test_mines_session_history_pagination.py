from __future__ import annotations


def test_mines_session_history_returns_pagination_meta_for_player(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-history-page")

    response = client.get(
        "/games/mines/sessions?limit=5",
        headers=auth_headers(
            player["access_token"],
            include_game_launch_token=False,
        ),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["data"] == []
    assert payload["meta"] == {
        "next_cursor": None,
        "limit": 5,
    }


def test_mines_session_history_rejects_invalid_cursor(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-history-bad-cursor")

    response = client.get(
        "/games/mines/sessions?cursor=not-a-cursor",
        headers=auth_headers(
            player["access_token"],
            include_game_launch_token=False,
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
