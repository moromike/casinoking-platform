from __future__ import annotations


def test_register_creates_wallets_and_signup_ledger(
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-signup")

    user_row = db_helpers.fetchone(
        """
        SELECT email, role, status
        FROM users
        WHERE id = %s
        """,
        (player["user_id"],),
    )
    assert user_row == {
        "email": player["email"],
        "role": "player",
        "status": "active",
    }

    wallet_rows = db_helpers.fetchall(
        """
        SELECT wallet_type, balance_snapshot
        FROM wallet_accounts
        WHERE user_id = %s
        ORDER BY wallet_type
        """,
        (player["user_id"],),
    )
    assert [
        {
            "wallet_type": row["wallet_type"],
            "balance_snapshot": f"{row['balance_snapshot']:.6f}",
        }
        for row in wallet_rows
    ] == [
        {"wallet_type": "bonus", "balance_snapshot": "0.000000"},
        {"wallet_type": "cash", "balance_snapshot": "1000.000000"},
    ]

    transaction_rows = db_helpers.fetchall(
        """
        SELECT transaction_type, idempotency_key
        FROM ledger_transactions
        WHERE user_id = %s
        ORDER BY created_at
        """,
        (player["user_id"],),
    )
    assert transaction_rows == [
        {
            "transaction_type": "signup_credit",
            "idempotency_key": f"signup-{player['user_id']}",
        }
    ]


def test_mines_start_reveal_cashout_updates_wallet_and_ledger(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-win")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-win",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()["data"]
    session_id = start_payload["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200
    assert reveal_response.json()["data"]["result"] == "safe"

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-win",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200
    cashout_payload = cashout_response.json()["data"]
    assert cashout_payload["status"] == "won"

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "1000.114500"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]

    session_row = db_helpers.fetchone(
        """
        SELECT status, closed_at, safe_reveals_count
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] == "won"
    assert session_row["closed_at"] is not None
    assert session_row["safe_reveals_count"] == 1


def test_mines_loss_does_not_create_win_credit(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-loss")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-loss",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
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
    assert reveal_response.status_code == 200
    assert reveal_response.json()["data"] == {
        "game_session_id": session_id,
        "status": "lost",
        "result": "mine",
        "safe_reveals_count": 0,
    }

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    assert session_snapshot.json()["data"]["potential_payout"] == "0.000000"

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "999.000000"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet"]

    session_row = db_helpers.fetchone(
        """
        SELECT status, closed_at, safe_reveals_count
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] == "lost"
    assert session_row["closed_at"] is not None
    assert session_row["safe_reveals_count"] == 0


def test_password_reset_updates_credentials_and_consumes_token(
    client,
    create_player,
    login_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-password-reset")
    new_password = "StrongPass-PasswordReset"

    forgot_response = client.post(
        "/auth/password/forgot",
        json={"email": player["email"]},
    )
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["data"]["reset_token"]
    assert isinstance(reset_token, str)

    reset_response = client.post(
        "/auth/password/reset",
        json={
            "token": reset_token,
            "new_password": new_password,
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["data"] == {"password_reset": True}

    old_login_response = client.post(
        "/auth/login",
        json={
            "email": player["email"],
            "password": player["password"],
        },
    )
    assert old_login_response.status_code == 401

    new_login_payload = login_player(
        email=str(player["email"]),
        password=new_password,
    )
    assert new_login_payload["token_type"] == "bearer"

    token_rows = db_helpers.fetchall(
        """
        SELECT consumed_at
        FROM password_reset_tokens
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (player["user_id"],),
    )
    assert len(token_rows) == 1
    assert token_rows[0]["consumed_at"] is not None

    replay_response = client.post(
        "/auth/password/reset",
        json={
            "token": reset_token,
            "new_password": "StrongPass-PasswordReset-Replay",
        },
    )
    assert replay_response.status_code == 409
    assert replay_response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Reset token is not valid or expired",
        },
    }
