from __future__ import annotations

from uuid import uuid4


def test_wallets_require_bearer_token(client) -> None:
    response = client.get("/wallets")

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Missing or invalid bearer token",
        },
    }


def test_register_and_login_contract(client, site_access_password) -> None:
    email = f"contract-{uuid4().hex[:12]}@example.com"
    password = f"StrongPass-{uuid4().hex[:12]}"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "site_access_password": site_access_password,
        },
    )

    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["success"] is True
    assert register_payload["data"]["wallets"] == [
        {
            "wallet_type": "cash",
            "currency_code": "CHIP",
            "balance_snapshot": "1000.000000",
        },
        {
            "wallet_type": "bonus",
            "currency_code": "CHIP",
            "balance_snapshot": "0.000000",
        },
    ]

    duplicate_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "site_access_password": site_access_password,
        },
    )

    assert duplicate_response.status_code == 422
    assert duplicate_response.json()["error"]["code"] == "VALIDATION_ERROR"

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["success"] is True
    assert login_payload["data"]["token_type"] == "bearer"
    assert isinstance(login_payload["data"]["access_token"], str)


def test_demo_auth_contract(client) -> None:
    demo_response = client.post("/auth/demo")

    assert demo_response.status_code == 200
    demo_payload = demo_response.json()
    assert demo_payload["success"] is True
    assert demo_payload["data"]["email"].endswith("@casinoking.local")
    assert demo_payload["data"]["token_type"] == "bearer"
    assert isinstance(demo_payload["data"]["access_token"], str)
    assert demo_payload["data"]["wallets"] == [
        {
            "wallet_type": "cash",
            "currency_code": "CHIP",
            "balance_snapshot": "1000.000000",
        },
        {
            "wallet_type": "bonus",
            "currency_code": "CHIP",
            "balance_snapshot": "0.000000",
        },
    ]

    wallets_response = client.get(
        "/wallets",
        headers={
            "Authorization": f"Bearer {demo_payload['data']['access_token']}",
        },
    )
    assert wallets_response.status_code == 200
    wallet_types = {
        wallet["wallet_type"] for wallet in wallets_response.json()["data"]
    }
    assert wallet_types == {"cash", "bonus"}


def test_mines_game_launch_token_contract(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-game-launch")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )

    assert issue_response.status_code == 200
    issue_payload = issue_response.json()["data"]
    assert issue_payload["game_code"] == "mines"
    assert isinstance(issue_payload["game_launch_token"], str)
    assert isinstance(issue_payload["platform_session_id"], str)
    assert isinstance(issue_payload["play_session_id"], str)
    assert isinstance(issue_payload["game_play_session_id"], str)
    assert isinstance(issue_payload["expires_at"], str)

    validate_response = client.post(
        "/games/mines/launch/validate",
        json={"game_launch_token": issue_payload["game_launch_token"]},
    )

    assert validate_response.status_code == 200
    assert validate_response.json()["data"] == {
        "game_code": "mines",
        "player_id": str(player["user_id"]),
        "platform_session_id": issue_payload["platform_session_id"],
        "play_session_id": issue_payload["play_session_id"],
        "game_play_session_id": issue_payload["game_play_session_id"],
        "expires_at": validate_response.json()["data"]["expires_at"],
    }


def test_password_reset_contract(client, create_player) -> None:
    player = create_player(prefix="contract-password-reset")
    new_password = f"StrongPass-{uuid4().hex[:12]}"

    forgot_response = client.post(
        "/auth/password/forgot",
        json={"email": player["email"]},
    )

    assert forgot_response.status_code == 200
    forgot_payload = forgot_response.json()
    assert forgot_payload["success"] is True
    assert forgot_payload["data"]["request_accepted"] is True
    assert isinstance(forgot_payload["data"]["reset_token"], str)

    reset_response = client.post(
        "/auth/password/reset",
        json={
            "token": forgot_payload["data"]["reset_token"],
            "new_password": new_password,
        },
    )

    assert reset_response.status_code == 200
    assert reset_response.json() == {
        "success": True,
        "data": {"password_reset": True},
    }

    login_response = client.post(
        "/auth/login",
        json={
            "email": player["email"],
            "password": new_password,
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["data"]["token_type"] == "bearer"


def test_password_reset_unknown_email_is_accepted(client) -> None:
    response = client.post(
        "/auth/password/forgot",
        json={"email": f"missing-{uuid4().hex[:12]}@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {
            "request_accepted": True,
            "reset_token": None,
        },
    }


def test_mines_start_requires_idempotency_key(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-start")

    response = client.post(
        "/games/mines/start",
        headers=auth_headers(player["access_token"]),
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Idempotency-Key header is required",
        },
    }


def test_mines_session_is_owner_only(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-owner")
    other = create_authenticated_player(prefix="contract-other")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(owner["access_token"]),
            "Idempotency-Key": f"owner-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    forbidden_response = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(other["access_token"]),
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Game session ownership is not valid",
        },
    }


def test_mines_session_fairness_is_owner_only(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-owner-fairness")
    other = create_authenticated_player(prefix="contract-other-fairness")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(owner["access_token"]),
            "Idempotency-Key": f"owner-fairness-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    owner_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers=auth_headers(owner["access_token"]),
    )
    assert owner_response.status_code == 200
    owner_payload = owner_response.json()["data"]
    assert owner_payload["game_session_id"] == session_id
    assert owner_payload["fairness_version"] == "seed_internal_v2"
    assert isinstance(owner_payload["nonce"], int)
    assert len(owner_payload["server_seed_hash"]) == 64
    assert len(owner_payload["board_hash"]) == 64
    assert owner_payload["user_verifiable"] is False

    forbidden_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers=auth_headers(other["access_token"]),
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Game session ownership is not valid",
        },
    }


def test_mines_session_snapshot_omits_sensitive_board_fields_for_player(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-session-hidden-board")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"session-hidden-board-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
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

    assert session_payload["game_session_id"] == session_id
    assert "mine_positions" not in session_payload
    assert "mine_positions_json" not in session_payload
    assert "rng_material" not in session_payload
    assert "server_seed" not in session_payload
    assert "wallet_account_id" not in session_payload


def test_mines_session_fairness_payload_omits_secret_fields_for_player(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-fairness-hidden-secret")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"fairness-hidden-secret-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
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
    fairness_payload = fairness_response.json()["data"]

    assert fairness_payload["user_verifiable"] is False
    assert "server_seed" not in fairness_payload
    assert "rng_material" not in fairness_payload
    assert "mine_positions" not in fairness_payload
    assert "client_seed" not in fairness_payload


def test_ledger_transaction_detail_blocks_non_owner_players(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="contract-ledger-owner")
    other = create_authenticated_player(prefix="contract-ledger-other")

    owner_transactions_response = client.get(
        "/ledger/transactions",
        headers=auth_headers(owner["access_token"]),
    )
    assert owner_transactions_response.status_code == 200
    transaction_id = owner_transactions_response.json()["data"][0]["id"]

    forbidden_response = client.get(
        f"/ledger/transactions/{transaction_id}",
        headers=auth_headers(other["access_token"]),
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Transaction ownership is not valid",
        },
    }
