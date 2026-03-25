from __future__ import annotations


def test_admin_can_verify_old_and_new_sessions_across_seed_rotation(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-fairness-verify-admin")

    player_before = create_authenticated_player(prefix="integration-fairness-verify-before")
    before_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player_before["access_token"]),
            "Idempotency-Key": "integration-fairness-verify-before-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert before_start_response.status_code == 200
    before_session_id = before_start_response.json()["data"]["game_session_id"]

    before_session_fairness_response = client.get(
        f"/games/mines/session/{before_session_id}/fairness",
        headers=auth_headers(player_before["access_token"]),
    )
    assert before_session_fairness_response.status_code == 200
    before_server_seed_hash = before_session_fairness_response.json()["data"][
        "server_seed_hash"
    ]

    rotate_response = client.post(
        "/games/mines/fairness/rotate",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-fairness-verify-rotate",
        },
    )
    assert rotate_response.status_code == 200
    rotated_hash = rotate_response.json()["data"]["active_server_seed_hash"]
    assert rotated_hash != before_server_seed_hash

    player_after = create_authenticated_player(prefix="integration-fairness-verify-after")
    after_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player_after["access_token"]),
            "Idempotency-Key": "integration-fairness-verify-after-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert after_start_response.status_code == 200
    after_session_id = after_start_response.json()["data"]["game_session_id"]

    after_session_fairness_response = client.get(
        f"/games/mines/session/{after_session_id}/fairness",
        headers=auth_headers(player_after["access_token"]),
    )
    assert after_session_fairness_response.status_code == 200
    after_server_seed_hash = after_session_fairness_response.json()["data"][
        "server_seed_hash"
    ]
    assert after_server_seed_hash == rotated_hash

    verify_before_response = client.get(
        "/games/mines/verify",
        params={"session_id": before_session_id},
        headers=auth_headers(admin_user["access_token"]),
    )
    assert verify_before_response.status_code == 200
    verify_before_payload = verify_before_response.json()["data"]
    assert verify_before_payload["game_session_id"] == before_session_id
    assert verify_before_payload["verified"] is True
    assert verify_before_payload["server_seed_hash_match"] is True
    assert verify_before_payload["board_hash_match"] is True
    assert verify_before_payload["mine_positions_match"] is True
    assert verify_before_payload["stored_server_seed_hash"] == before_server_seed_hash
    assert verify_before_payload["computed_server_seed_hash"] == before_server_seed_hash

    verify_after_response = client.get(
        "/games/mines/verify",
        params={"session_id": after_session_id},
        headers=auth_headers(admin_user["access_token"]),
    )
    assert verify_after_response.status_code == 200
    verify_after_payload = verify_after_response.json()["data"]
    assert verify_after_payload["game_session_id"] == after_session_id
    assert verify_after_payload["verified"] is True
    assert verify_after_payload["server_seed_hash_match"] is True
    assert verify_after_payload["board_hash_match"] is True
    assert verify_after_payload["mine_positions_match"] is True
    assert verify_after_payload["stored_server_seed_hash"] == after_server_seed_hash
    assert verify_after_payload["computed_server_seed_hash"] == after_server_seed_hash
