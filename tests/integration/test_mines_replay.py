from __future__ import annotations

from uuid import uuid4


def test_mines_replay_returns_closed_round_board_without_recalculating_outcome(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-replay")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-replay-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    mine_cell = db_helpers.get_mine_positions(session_id)[0]
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    replay_response = client.get(
        f"/games/mines/session/{session_id}/replay",
        headers=auth_headers(
            player["access_token"],
            include_game_launch_token=False,
        ),
    )
    assert replay_response.status_code == 200, replay_response.text
    replay = replay_response.json()["data"]

    assert replay["game_session_id"] == session_id
    assert replay["status"] == "lost"
    assert replay["grid_size"] == 9
    assert replay["mine_count"] == 1
    assert replay["bet_amount"] == "1.000000"
    assert replay["payout_amount"] == "0.000000"
    assert replay["board_reveal_available"] is True
    assert replay["mine_positions_available"] is True
    assert replay["mine_positions"] == [mine_cell]
    assert replay["final_revealed_cells"] == [mine_cell]
    assert replay["steps"] == [
        {
            "step_index": 1,
            "cell_index": mine_cell,
            "result": "mine",
            "safe_reveals_count": 0,
            "multiplier": "1.0000",
            "payout_amount": "0.000000",
        }
    ]
    assert replay["fairness"]["board_hash"]
    assert replay["fairness"]["user_verifiable"] is False


def test_mines_replay_hides_mine_positions_for_active_round(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-replay-active")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-replay-active-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    replay_response = client.get(
        f"/games/mines/session/{session_id}/replay",
        headers=auth_headers(
            player["access_token"],
            include_game_launch_token=False,
        ),
    )
    assert replay_response.status_code == 200, replay_response.text
    replay = replay_response.json()["data"]

    assert replay["status"] == "active"
    assert replay["board_reveal_available"] is False
    assert replay["mine_positions_available"] is False
    assert replay["mine_positions"] == []
    assert replay["final_revealed_cells"] == []
    assert replay["steps"] == []


def test_mines_replay_runtime_supports_demo_launch_token_without_exposing_active_board(
    client,
    create_published_mines_variant,
) -> None:
    title = create_published_mines_variant(
        title_code=f"mines_replay_demo_{uuid4().hex[:8]}",
        demo_enabled=True,
        real_enabled=True,
    )
    token_response = client.post("/demo/token")
    assert token_response.status_code == 200, token_response.text
    anonymous_token = token_response.json()["data"]["anonymous_token"]

    launch_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anonymous_token},
        json={"title_code": title["title_code"]},
    )
    assert launch_response.status_code == 200, launch_response.text
    launch_token = launch_response.json()["data"]["game_launch_token"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            "Idempotency-Key": f"integration-replay-demo-start-{uuid4().hex}",
            "X-Game-Launch-Token": launch_token,
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "demo",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    replay_response = client.get(
        f"/games/mines/session/{session_id}/replay",
        headers={"X-Game-Launch-Token": launch_token},
    )
    assert replay_response.status_code == 200, replay_response.text
    replay = replay_response.json()["data"]

    assert replay["mode"] == "demo"
    assert replay["wallet_type"] == "demo"
    assert replay["status"] == "active"
    assert replay["mine_positions_available"] is False
    assert replay["mine_positions"] == []


def test_mines_replay_admin_can_read_player_round_but_active_board_stays_hidden(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-mines-replay-admin-player")
    admin_user = create_admin_user(prefix="integration-mines-replay-admin")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-replay-admin-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    replay_response = client.get(
        f"/games/mines/admin/session/{session_id}/replay",
        headers=auth_headers(
            admin_user["access_token"],
            include_game_launch_token=False,
        ),
    )
    assert replay_response.status_code == 200, replay_response.text
    replay = replay_response.json()["data"]

    assert replay["game_session_id"] == session_id
    assert replay["status"] == "active"
    assert replay["admin_context"]["user_email"] == player["email"]
    assert replay["mine_positions_available"] is False
    assert replay["mine_positions"] == []


def test_mines_replay_rejects_other_players_round(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="integration-mines-replay-owner")
    other_player = create_authenticated_player(prefix="integration-mines-replay-other")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(owner["access_token"]),
            "Idempotency-Key": f"integration-replay-owner-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    replay_response = client.get(
        f"/games/mines/session/{session_id}/replay",
        headers=auth_headers(
            other_player["access_token"],
            include_game_launch_token=False,
        ),
    )

    assert replay_response.status_code == 403
    assert replay_response.json()["error"]["code"] == "FORBIDDEN"
