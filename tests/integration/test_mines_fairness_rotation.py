from __future__ import annotations


def test_admin_fairness_rotation_changes_active_seed_hash_and_new_sessions_use_it(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-fairness-rotate-admin")

    current_response = client.get("/games/mines/fairness/current")
    assert current_response.status_code == 200
    previous_hash = current_response.json()["data"]["active_server_seed_hash"]

    rotate_response = client.post(
        "/games/mines/fairness/rotate",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-fairness-rotate",
        },
    )
    assert rotate_response.status_code == 200
    rotate_payload = rotate_response.json()["data"]
    assert rotate_payload["game_code"] == "mines"
    assert rotate_payload["fairness_version"] == "seed_internal_v2"
    assert rotate_payload["previous_server_seed_hash"] == previous_hash
    assert len(rotate_payload["active_server_seed_hash"]) == 64
    assert rotate_payload["active_server_seed_hash"] != previous_hash

    duplicate_rotate_response = client.post(
        "/games/mines/fairness/rotate",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-fairness-rotate",
        },
    )
    assert duplicate_rotate_response.status_code == 200
    assert duplicate_rotate_response.json()["data"] == rotate_payload

    current_after_response = client.get("/games/mines/fairness/current")
    assert current_after_response.status_code == 200
    assert (
        current_after_response.json()["data"]["active_server_seed_hash"]
        == rotate_payload["active_server_seed_hash"]
    )

    player = create_authenticated_player(prefix="integration-fairness-rotate-player")
    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-fairness-rotate-start",
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

    fairness_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers=auth_headers(player["access_token"]),
    )
    assert fairness_response.status_code == 200
    assert (
        fairness_response.json()["data"]["server_seed_hash"]
        == rotate_payload["active_server_seed_hash"]
    )
