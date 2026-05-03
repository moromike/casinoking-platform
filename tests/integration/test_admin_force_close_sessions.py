from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


def _create_active_table_session_and_round(
    *,
    client,
    auth_headers,
    player: dict[str, object],
    bet_amount: str = "5.000000",
    table_budget_amount: str = "20.000000",
) -> dict[str, str]:
    player_headers = auth_headers(str(player["access_token"]))

    access_response = client.post(
        "/access-sessions",
        headers=player_headers,
        json={"game_code": "mines"},
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = access_response.json()["data"]["id"]

    table_response = client.post(
        "/table-sessions",
        headers=player_headers,
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
            **player_headers,
            "Idempotency-Key": f"admin-force-close-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": bet_amount,
            "wallet_type": "cash",
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
        },
    )
    assert start_response.status_code == 200, start_response.text

    return {
        "access_session_id": access_session_id,
        "table_session_id": table_session_id,
        "game_session_id": start_response.json()["data"]["game_session_id"],
    }


def _force_close_player_sessions(
    *,
    client,
    auth_headers,
    admin: dict[str, object],
    player: dict[str, object],
    reason: str = "integration force close",
):
    return client.post(
        f"/admin/users/{player['user_id']}/sessions/force-close",
        headers=auth_headers(str(admin["access_token"])),
        json={
            "game_code": "mines",
            "reason": reason,
        },
    )


def test_admin_force_close_voids_active_round_refunds_bet_and_is_idempotent(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="admin-force-close-player")
    admin = create_admin_user(prefix="admin-force-close-admin")
    ids = _create_active_table_session_and_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
    )
    player_headers = auth_headers(str(player["access_token"]))

    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(25) if index not in mine_positions)
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=player_headers,
        json={
            "game_session_id": ids["game_session_id"],
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "995.000000"

    force_response = _force_close_player_sessions(
        client=client,
        auth_headers=auth_headers,
        admin=admin,
        player=player,
    )
    assert force_response.status_code == 200, force_response.text
    payload = force_response.json()["data"]
    assert payload["closed_table_session_ids"] == [ids["table_session_id"]]
    assert payload["closed_access_session_ids"] == [ids["access_session_id"]]
    assert len(payload["voided_rounds"]) == 1
    assert payload["voided_rounds"][0]["round_id"] == ids["game_session_id"]
    assert payload["voided_rounds"][0]["bet_amount"] == "5.000000"

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "1000.000000"
    reconciliation = db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")
    assert reconciliation["balance_snapshot"] == "1000.000000"
    assert reconciliation["ledger_balance"] == "1000.000000"
    assert reconciliation["drift"] == "0.000000"

    table_after = db_helpers.fetchone(
        """
        SELECT
            status,
            closed_reason,
            table_balance_amount,
            loss_reserved_amount,
            loss_consumed_amount
        FROM game_table_sessions
        WHERE id = %s
        """,
        (ids["table_session_id"],),
    )
    assert table_after is not None
    assert table_after["status"] == "closed"
    assert table_after["closed_reason"] == "admin_voided"
    assert table_after["table_balance_amount"] == Decimal("20.000000")
    assert table_after["loss_reserved_amount"] == Decimal("0.000000")
    assert table_after["loss_consumed_amount"] == Decimal("0.000000")

    access_after = db_helpers.fetchone(
        "SELECT status, closed_reason FROM game_access_sessions WHERE id = %s",
        (ids["access_session_id"],),
    )
    assert access_after == {
        "status": "closed",
        "closed_reason": "admin_voided",
    }

    round_after = db_helpers.fetchone(
        """
        SELECT
            pr.status,
            pr.settlement_ledger_transaction_id,
            lt.transaction_type,
            aa.action_type,
            aa.amount
        FROM platform_rounds pr
        JOIN ledger_transactions lt ON lt.id = pr.settlement_ledger_transaction_id
        JOIN admin_actions aa ON aa.ledger_transaction_id = lt.id
        WHERE pr.id = %s
        """,
        (ids["game_session_id"],),
    )
    assert round_after is not None
    assert round_after["status"] == "cancelled"
    assert round_after["transaction_type"] == "void"
    assert round_after["action_type"] == "session_void"
    assert round_after["amount"] == Decimal("5.000000")

    void_entries = db_helpers.get_transaction_entries(
        str(round_after["settlement_ledger_transaction_id"])
    )
    assert {
        (entry["account_code"], entry["entry_side"], entry["amount"])
        for entry in void_entries
        if entry["account_code"] == "HOUSE_CASH"
    } == {("HOUSE_CASH", "debit", Decimal("5.000000"))}
    assert any(
        entry["account_code"].startswith("PLAYER_CASH_")
        and entry["entry_side"] == "credit"
        and entry["amount"] == Decimal("5.000000")
        for entry in void_entries
    )

    repeat_response = _force_close_player_sessions(
        client=client,
        auth_headers=auth_headers,
        admin=admin,
        player=player,
    )
    assert repeat_response.status_code == 200, repeat_response.text
    assert repeat_response.json()["data"]["voided_rounds"] == []

    rows_after_repeat = db_helpers.fetchall(
        """
        SELECT lt.id
        FROM ledger_transactions lt
        JOIN admin_actions aa ON aa.ledger_transaction_id = lt.id
        WHERE aa.target_user_id = %s
          AND aa.action_type = 'session_void'
          AND lt.transaction_type = 'void'
        """,
        (player["user_id"],),
    )
    assert len(rows_after_repeat) == 1


def test_admin_force_close_surfaces_voided_error_to_player_and_financial_report(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="admin-force-close-overlay")
    admin = create_admin_user(prefix="admin-force-close-overlay-admin")
    ids = _create_active_table_session_and_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
    )
    player_headers = auth_headers(str(player["access_token"]))

    force_response = _force_close_player_sessions(
        client=client,
        auth_headers=auth_headers,
        admin=admin,
        player=player,
    )
    assert force_response.status_code == 200, force_response.text

    ping_response = client.post(
        f"/access-sessions/{ids['access_session_id']}/ping",
        headers=player_headers,
    )
    assert ping_response.status_code == 409
    assert ping_response.json()["error"]["code"] == "SESSION_VOIDED_BY_OPERATOR"

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=player_headers,
        json={
            "game_session_id": ids["game_session_id"],
            "cell_index": 0,
        },
    )
    assert reveal_response.status_code == 409
    assert reveal_response.json()["error"]["code"] == "SESSION_VOIDED_BY_OPERATOR"

    detail_response = client.get(
        f"/admin/reports/financial/sessions/{ids['access_session_id']}",
        headers=auth_headers(str(admin["access_token"])),
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()["data"]
    assert detail["bank_delta"] == "0.000000"
    assert [event["transaction_type"] for event in detail["events"]] == ["bet", "void"]
    assert detail["events"][0]["bank_credit"] == "5.000000"
    assert detail["events"][1]["bank_debit"] == "5.000000"
    assert "voided by operator" in detail["events"][1]["game_enrichment"]

    filtered_response = client.get(
        "/admin/reports/financial/sessions?transaction_type=void",
        headers=auth_headers(str(admin["access_token"])),
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered_sessions = filtered_response.json()["data"]["sessions"]
    assert any(
        session["session_id"] == ids["access_session_id"]
        and session["bank_delta"] == "0.000000"
        for session in filtered_sessions
    )


def test_admin_force_close_closes_settled_session_without_voiding_history(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="admin-force-close-settled")
    admin = create_admin_user(prefix="admin-force-close-settled-admin")
    ids = _create_active_table_session_and_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
    )
    player_headers = auth_headers(str(player["access_token"]))

    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(25) if index not in mine_positions)
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=player_headers,
        json={
            "game_session_id": ids["game_session_id"],
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text
    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **player_headers,
            "Idempotency-Key": f"admin-force-close-settled-cashout-{uuid4().hex}",
        },
        json={"game_session_id": ids["game_session_id"]},
    )
    assert cashout_response.status_code == 200, cashout_response.text

    force_response = _force_close_player_sessions(
        client=client,
        auth_headers=auth_headers,
        admin=admin,
        player=player,
    )
    assert force_response.status_code == 200, force_response.text
    assert force_response.json()["data"]["voided_rounds"] == []

    round_after = db_helpers.fetchone(
        """
        SELECT status
        FROM platform_rounds
        WHERE id = %s
        """,
        (ids["game_session_id"],),
    )
    assert round_after == {"status": "won"}

    void_rows = db_helpers.fetchall(
        """
        SELECT id
        FROM admin_actions
        WHERE target_user_id = %s
          AND action_type = 'session_void'
        """,
        (player["user_id"],),
    )
    assert void_rows == []


def test_admin_force_close_requires_finance_area(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="admin-force-close-forbidden-player")
    limited_admin = create_admin_user(prefix="admin-force-close-forbidden-admin")
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE admin_profiles
            SET is_superadmin = false,
                areas = ARRAY['end_user']
            WHERE user_id = %s
            """,
            (limited_admin["user_id"],),
        )

    response = _force_close_player_sessions(
        client=client,
        auth_headers=auth_headers,
        admin=limited_admin,
        player=player,
    )
    assert response.status_code == 403
