from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


def _create_active_table_session_and_round(
    *,
    client,
    headers,
    bet_amount: str,
    grid_size: int = 9,
    mine_count: int = 1,
    table_budget_amount: str = "10.000000",
) -> dict[str, str]:
    """Create an access session, a table session, and start a round.

    Returns the created ids in a dict.
    """
    access_response = client.post(
        "/access-sessions",
        headers=headers,
        json={"game_code": "mines"},
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = access_response.json()["data"]["id"]

    table_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": table_budget_amount,
            "access_session_id": access_session_id,
        },
    )
    assert table_response.status_code == 200, table_response.text
    table_session_id = table_response.json()["data"]["id"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"cascade-close-start-{uuid4().hex}",
        },
        json={
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": bet_amount,
            "wallet_type": "cash",
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200, start_response.text
    game_session_id = start_response.json()["data"]["game_session_id"]

    return {
        "access_session_id": access_session_id,
        "table_session_id": table_session_id,
        "game_session_id": game_session_id,
    }


def test_close_access_session_cascades_to_table_session_with_no_reveals(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="cascade-no-reveals")
    headers = auth_headers(player["access_token"])

    ids = _create_active_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount="4.000000",
    )
    initial_balance = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))

    close_response = client.post(
        f"/access-sessions/{ids['access_session_id']}/close",
        headers=headers,
    )
    assert close_response.status_code == 200, close_response.text
    assert close_response.json()["data"]["status"] == "closed"

    # Round was auto-cashed (refund of bet, since safe_reveals=0).
    table_after = db_helpers.fetchone(
        """
        SELECT status, closed_reason, table_balance_amount, loss_reserved_amount, loss_consumed_amount
        FROM game_table_sessions
        WHERE id = %s
        """,
        (ids["table_session_id"],),
    )
    assert table_after is not None
    assert table_after["status"] == "closed"
    assert table_after["closed_reason"] == "access_session_closed"
    assert Decimal(table_after["table_balance_amount"]) == Decimal("10.000000")
    assert Decimal(table_after["loss_reserved_amount"]) == Decimal("0")
    assert Decimal(table_after["loss_consumed_amount"]) == Decimal("0")

    # Wallet balance was refunded the bet (we lost 4, then auto-cashout returns 4).
    final_balance = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    assert final_balance == initial_balance + Decimal("4.000000")
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")["drift"] == (
        "0.000000"
    )


def test_login_cleans_up_existing_active_sessions(
    client,
    create_authenticated_player,
    auth_headers,
    login_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="cascade-login")
    headers = auth_headers(player["access_token"])

    ids = _create_active_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount="3.000000",
    )

    # Re-login the same user.
    relogin_payload = login_player(
        email=str(player["email"]),
        password=str(player["password"]),
    )
    assert relogin_payload["access_token"]

    # All previous sessions are closed.
    access_after = db_helpers.fetchone(
        "SELECT status FROM game_access_sessions WHERE id = %s",
        (ids["access_session_id"],),
    )
    assert access_after is not None
    assert access_after["status"] == "closed"

    table_after = db_helpers.fetchone(
        "SELECT status, closed_reason FROM game_table_sessions WHERE id = %s",
        (ids["table_session_id"],),
    )
    assert table_after is not None
    assert table_after["status"] == "closed"
    assert table_after["closed_reason"] == "player_login_cleanup"


def test_logout_endpoint_closes_active_sessions(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="cascade-logout")
    headers = auth_headers(player["access_token"])

    ids = _create_active_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount="2.000000",
    )

    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200, logout_response.text
    assert logout_response.json()["data"]["reason"] == "player_logout"

    access_after = db_helpers.fetchone(
        "SELECT status FROM game_access_sessions WHERE id = %s",
        (ids["access_session_id"],),
    )
    assert access_after is not None
    assert access_after["status"] == "closed"

    table_after = db_helpers.fetchone(
        "SELECT status, closed_reason FROM game_table_sessions WHERE id = %s",
        (ids["table_session_id"],),
    )
    assert table_after is not None
    assert table_after["status"] == "closed"
    assert table_after["closed_reason"] == "player_logout"


def test_create_access_session_is_idempotent_when_active_exists(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="cascade-idempotent")
    headers = auth_headers(player["access_token"])

    first_response = client.post(
        "/access-sessions",
        headers=headers,
        json={"game_code": "mines"},
    )
    assert first_response.status_code == 200
    first_id = first_response.json()["data"]["id"]

    second_response = client.post(
        "/access-sessions",
        headers=headers,
        json={"game_code": "mines"},
    )
    assert second_response.status_code == 200
    second_id = second_response.json()["data"]["id"]

    assert first_id == second_id, (
        "create_access_session must be idempotent and reuse the active session "
        "to support page reload without killing the round"
    )


def test_creating_new_table_session_closes_orphan_table_sessions(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="cascade-orphan-ts")
    headers = auth_headers(player["access_token"])

    first_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
        },
    )
    assert first_response.status_code == 200
    first_id = first_response.json()["data"]["id"]

    second_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "20.000000",
        },
    )
    assert second_response.status_code == 200
    second_id = second_response.json()["data"]["id"]
    assert second_id != first_id

    first_after = db_helpers.fetchone(
        "SELECT status, closed_reason FROM game_table_sessions WHERE id = %s",
        (first_id,),
    )
    assert first_after is not None
    assert first_after["status"] == "closed"
    assert first_after["closed_reason"] == "replaced_by_new_session"

    second_after = db_helpers.fetchone(
        "SELECT status FROM game_table_sessions WHERE id = %s",
        (second_id,),
    )
    assert second_after is not None
    assert second_after["status"] == "active"
