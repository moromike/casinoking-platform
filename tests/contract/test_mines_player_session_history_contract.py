from __future__ import annotations

from uuid import uuid4


def test_mines_recent_sessions_list_is_scoped_to_current_player(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-history-owner")
    other = create_authenticated_player(prefix="contract-history-other")

    owner_session_ids: list[str] = []
    for index in range(2):
        start_response = client.post(
            "/games/mines/start",
            headers={
                **auth_headers(owner["access_token"]),
                "Idempotency-Key": f"owner-history-start-{index}-{uuid4().hex}",
            },
            json={
                "grid_size": 25,
                "mine_count": 3,
                "bet_amount": "2.000000",
                "wallet_type": "cash",
            },
        )
        assert start_response.status_code == 200
        owner_session_ids.append(start_response.json()["data"]["game_session_id"])

    other_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(other["access_token"]),
            "Idempotency-Key": f"other-history-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
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
    assert isinstance(first_entry["created_at"], str)
    assert first_entry["closed_at"] is None
    assert "revealed_cells" not in first_entry
    assert "mine_positions" not in first_entry
    assert "mine_positions_json" not in first_entry
    assert "rng_material" not in first_entry

