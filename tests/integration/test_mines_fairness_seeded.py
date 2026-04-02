from __future__ import annotations


def test_seeded_fairness_metadata_is_persisted_and_exposed(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-fairness-seeded")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-fairness-seeded-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    session_response = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_response.status_code == 200
    session_payload = session_response.json()["data"]
    assert session_payload["fairness_version"] == "seed_internal_v2"
    assert isinstance(session_payload["nonce"], int)
    assert len(session_payload["server_seed_hash"]) == 64
    assert len(session_payload["board_hash"]) == 64

    fairness_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers=auth_headers(player["access_token"]),
    )
    assert fairness_response.status_code == 200
    fairness_payload = fairness_response.json()["data"]
    assert fairness_payload["game_session_id"] == session_id
    assert fairness_payload["fairness_version"] == session_payload["fairness_version"]
    assert fairness_payload["nonce"] == session_payload["nonce"]
    assert fairness_payload["server_seed_hash"] == session_payload["server_seed_hash"]
    assert fairness_payload["board_hash"] == session_payload["board_hash"]
    assert fairness_payload["user_verifiable"] is False

    db_row = db_helpers.fetchone(
        """
        SELECT mgr.fairness_version, mgr.nonce, mgr.server_seed_hash, mgr.board_hash
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
        WHERE pr.id = %s
        """,
        (session_id,),
    )
    assert db_row is not None
    assert db_row["fairness_version"] == "seed_internal_v2"
    assert db_row["nonce"] == fairness_payload["nonce"]
    assert db_row["server_seed_hash"] == fairness_payload["server_seed_hash"]
    assert db_row["board_hash"] == fairness_payload["board_hash"]
