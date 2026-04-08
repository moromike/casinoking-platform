from datetime import UTC, datetime, timedelta
from uuid import uuid4


def test_create_access_session_and_attach_round_to_it(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-access-session-attach")

    create_response = client.post(
        "/access-sessions",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    assert create_response.status_code == 200
    access_session_payload = create_response.json()["data"]
    access_session_id = access_session_payload["id"]
    assert access_session_payload["game_code"] == "mines"
    assert access_session_payload["status"] == "active"
    assert access_session_payload["auto_cashout"] is None

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-access-session-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    round_row = db_helpers.fetchone(
        """
        SELECT access_session_id
        FROM platform_rounds
        WHERE id = %s
        """,
        (session_id,),
    )
    assert round_row is not None
    assert str(round_row["access_session_id"]) == access_session_id


def test_ping_expired_access_session_times_out_round_and_fails(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="integration-access-session-timeout-ping")

    create_response = client.post(
        "/access-sessions",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    access_session_id = create_response.json()["data"]["id"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-access-session-timeout-ping-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE game_access_sessions
            SET last_activity_at = %s
            WHERE id = %s
            """,
            (datetime.now(UTC) - timedelta(minutes=4), access_session_id),
        )

    ping_response = client.post(
        f"/access-sessions/{access_session_id}/ping",
        headers=auth_headers(player["access_token"]),
    )
    assert ping_response.status_code == 409
    assert ping_response.json() == {
        "success": False,
        "error": {
            "code": "GAME_STATE_CONFLICT",
            "message": "Access session timed out",
        },
    }

    access_session_row = db_helpers.fetchone(
        """
        SELECT status, ended_at
        FROM game_access_sessions
        WHERE id = %s
        """,
        (access_session_id,),
    )
    assert access_session_row is not None
    assert access_session_row["status"] == "timed_out"
    assert access_session_row["ended_at"] is not None

    round_row = db_helpers.fetchone(
        """
        SELECT status, payout_amount, closed_at
        FROM platform_rounds
        WHERE id = %s
        """,
        (session_id,),
    )
    assert round_row is not None
    assert round_row["status"] == "won"
    assert f"{round_row['payout_amount']:.6f}" == "5.000000"
    assert round_row["closed_at"] is not None
    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "1000.000000"
    assert [row["transaction_type"] for row in db_helpers.get_game_transactions(session_id)] == [
        "bet",
        "win",
    ]


def test_start_on_expired_access_session_auto_cashouts_active_round_and_blocks_new_round(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="integration-access-session-timeout-start")

    create_response = client.post(
        "/access-sessions",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    access_session_id = create_response.json()["data"]["id"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-access-session-timeout-start-first",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

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
    reveal_payload = reveal_response.json()["data"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE game_access_sessions
            SET last_activity_at = %s
            WHERE id = %s
            """,
            (datetime.now(UTC) - timedelta(minutes=4), access_session_id),
        )

    second_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-access-session-timeout-start-second",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert second_start_response.status_code == 409
    assert second_start_response.json() == {
        "success": False,
        "error": {
            "code": "GAME_STATE_CONFLICT",
            "message": "Access session timed out",
        },
    }

    round_row = db_helpers.fetchone(
        """
        SELECT status, payout_amount, closed_at
        FROM platform_rounds
        WHERE id = %s
        """,
        (session_id,),
    )
    assert round_row is not None
    assert round_row["status"] == "won"
    assert f"{round_row['payout_amount']:.6f}" == reveal_payload["potential_payout"]
    assert round_row["closed_at"] is not None

    access_session_row = db_helpers.fetchone(
        """
        SELECT status, ended_at
        FROM game_access_sessions
        WHERE id = %s
        """,
        (access_session_id,),
    )
    assert access_session_row is not None
    assert access_session_row["status"] == "timed_out"
    assert access_session_row["ended_at"] is not None
    assert [row["transaction_type"] for row in db_helpers.get_game_transactions(session_id)] == [
        "bet",
        "win",
    ]

