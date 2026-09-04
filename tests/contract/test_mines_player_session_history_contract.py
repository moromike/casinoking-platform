from __future__ import annotations

from uuid import uuid4


def test_mines_recent_sessions_list_exposes_access_session_metadata(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-history-access-session")
    headers = auth_headers(owner["access_token"])
    validate_response = client.post(
        "/games/mines/launch/validate",
        json={"game_launch_token": headers["X-Game-Launch-Token"]},
    )
    assert validate_response.status_code == 200
    launch_context = validate_response.json()["data"]

    create_response = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "title_code": launch_context["title_code"],
            "site_code": launch_context["site_code"],
        },
    )
    assert create_response.status_code == 200
    access_session = create_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"owner-history-access-session-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
            "access_session_id": access_session["id"],
        },
    )
    assert start_response.status_code == 200

    list_response = client.get(
        "/games/mines/sessions",
        headers=auth_headers(owner["access_token"]),
    )

    assert list_response.status_code == 200
    first_entry = list_response.json()["data"][0]
    assert first_entry["access_session_id"] == access_session["id"]
    assert first_entry["access_session"]["id"] == access_session["id"]
    assert first_entry["access_session"]["game_code"] == "mines"
    assert first_entry["access_session"]["status"] == "active"
    assert first_entry["access_session"]["started_at"] == access_session["started_at"]
    assert isinstance(first_entry["access_session"]["last_activity_at"], str)
    assert first_entry["access_session"]["last_activity_at"] >= access_session["last_activity_at"]
    assert first_entry["access_session"]["ended_at"] is None


from tests.integration.helpers import create_game_access_session


def test_mines_recent_sessions_list_is_scoped_to_current_player(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-history-owner")
    other = create_authenticated_player(prefix="contract-history-other")

    owner_headers = auth_headers(owner["access_token"])
    owner_title_code = auth_headers.implicit_title_code() or "mines_auth_default"
    owner_access_session_id = create_game_access_session(
        client, owner_headers, game_code="mines", title_code=owner_title_code
    )

    owner_session_ids: list[str] = []
    for index in range(2):
        start_response = client.post(
            "/games/mines/start",
            headers={
                **owner_headers,
                "Idempotency-Key": f"owner-history-start-{index}-{uuid4().hex}",
            },
            json={
                "grid_size": 25,
                "mine_count": 3,
                "bet_amount": "2.000000",
                "wallet_type": "cash",
                "access_session_id": owner_access_session_id,
            },
        )
        assert start_response.status_code == 200
        owner_session_ids.append(start_response.json()["data"]["game_session_id"])

    other_headers = auth_headers(other["access_token"])
    other_title_code = auth_headers.implicit_title_code() or "mines_auth_default"
    other_access_session_id = create_game_access_session(
        client, other_headers, game_code="mines", title_code=other_title_code
    )

    other_start_response = client.post(
        "/games/mines/start",
        headers={
            **other_headers,
            "Idempotency-Key": f"other-history-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": other_access_session_id,
        },
    )
    assert other_start_response.status_code == 200
    other_session_id = other_start_response.json()["data"]["game_session_id"]

    list_response = client.get(
        "/games/mines/sessions",
        headers=auth_headers(owner["access_token"]),
    )

    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert len(payload) >= 2

    returned_ids = [entry["game_session_id"] for entry in payload]
    assert returned_ids[:2] == list(reversed(owner_session_ids))
    assert other_session_id not in returned_ids

    first_entry = payload[0]
    assert first_entry["status"] == "active"
    assert first_entry["grid_size"] == 25
    assert first_entry["mine_count"] == 3
    assert first_entry["bet_amount"] == "2.000000"
    assert first_entry["wallet_type"] == "cash"
    assert first_entry["safe_reveals_count"] == 0
    assert first_entry["revealed_cells_count"] == 0
    assert first_entry["multiplier_current"] == "1.0000"
    assert first_entry["potential_payout"] == "2.000000"
    assert first_entry["access_session_id"] == owner_access_session_id
    assert first_entry["access_session"] is not None
    assert first_entry["access_session"]["id"] == owner_access_session_id
    assert isinstance(first_entry["created_at"], str)
    assert first_entry["closed_at"] is None
    assert "revealed_cells" not in first_entry
    assert "mine_positions" not in first_entry
    assert "mine_positions_json" not in first_entry
    assert "rng_material" not in first_entry

