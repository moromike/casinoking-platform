from __future__ import annotations

from uuid import uuid4


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


def test_mines_latest_access_sessions_groups_final_round_snapshots(
    client,
    create_authenticated_player,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-latest-access")
    title = create_published_mines_variant(
        title_code=f"mines_latest_access_{uuid4().hex[:8]}",
        real_enabled=True,
        demo_enabled=True,
    )
    title_code = str(title["title_code"])

    access_response = client.post(
        "/access-sessions",
        headers=auth_headers(
            player["access_token"],
            title_code=title_code,
        ),
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_response.status_code == 200, access_response.text
    access_session = access_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(
                player["access_token"],
                title_code=title_code,
            ),
            "Idempotency-Key": f"integration-latest-access-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": access_session["id"],
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    mine_cell = db_helpers.get_mine_positions(session_id)[0]
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(
            player["access_token"],
            title_code=title_code,
        ),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    active_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(
                player["access_token"],
                title_code=title_code,
            ),
            "Idempotency-Key": f"integration-latest-access-active-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": access_session["id"],
        },
    )
    assert active_start_response.status_code == 200, active_start_response.text
    active_session_id = active_start_response.json()["data"]["game_session_id"]

    latest_response = client.get(
        "/games/mines/access-sessions/latest",
        headers=auth_headers(
            player["access_token"],
            title_code=title_code,
        ),
    )
    assert latest_response.status_code == 200, latest_response.text
    payload = latest_response.json()

    assert payload["meta"]["limit"] == 3
    assert payload["meta"]["title_code"] == title_code
    assert len(payload["data"]) == 1
    latest_access_session = payload["data"][0]
    assert latest_access_session["id"] == access_session["id"]
    assert latest_access_session["title_code"] == title_code
    assert len(latest_access_session["rounds"]) == 1

    round_snapshot = latest_access_session["rounds"][0]
    assert round_snapshot["game_session_id"] == session_id
    assert round_snapshot["game_session_id"] != active_session_id
    assert round_snapshot["status"] == "lost"
    assert round_snapshot["mine_positions_available"] is True
    assert round_snapshot["mine_positions"] == [mine_cell]
    assert round_snapshot["replay_version"] == "mines-final-snapshot-v1"
    assert "steps" not in round_snapshot
