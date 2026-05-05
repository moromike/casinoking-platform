from __future__ import annotations

from uuid import uuid4


def _issue_demo_launch_token(client) -> str:
    token_response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.20.1.{uuid4().int % 250 + 1}"},
    )
    assert token_response.status_code == 200, token_response.text
    anonymous_token = token_response.json()["data"]["anonymous_token"]
    launch_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anonymous_token},
        json={"title_code": "mines_classic"},
    )
    assert launch_response.status_code == 200, launch_response.text
    return launch_response.json()["data"]["game_launch_token"]


def _table_count(db_helpers, table_name: str) -> int:
    row = db_helpers.fetchone(f"SELECT COUNT(*) AS count FROM {table_name}", ())
    assert row is not None
    return int(row["count"])


def test_mines_demo_start_no_platform_rounds_write(client, db_helpers) -> None:
    platform_rounds_before = _table_count(db_helpers, "platform_rounds")
    ledger_transactions_before = _table_count(db_helpers, "ledger_transactions")
    game_launch_token = _issue_demo_launch_token(client)

    start_response = client.post(
        "/games/mines/start",
        headers={
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"demo-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "demo",
        },
    )

    assert start_response.status_code == 200, start_response.text
    payload = start_response.json()["data"]
    assert payload["mode"] == "demo"
    assert payload["wallet_balance_after"] == "95.000000"
    assert _table_count(db_helpers, "platform_rounds") == platform_rounds_before
    assert _table_count(db_helpers, "ledger_transactions") == ledger_transactions_before


def test_mines_demo_full_round_cashout_no_ledger_write(client, db_helpers) -> None:
    platform_rounds_before = _table_count(db_helpers, "platform_rounds")
    ledger_transactions_before = _table_count(db_helpers, "ledger_transactions")
    game_launch_token = _issue_demo_launch_token(client)

    start_response = client.post(
        "/games/mines/start",
        headers={
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"demo-full-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "demo",
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    row = db_helpers.fetchone(
        """
        SELECT mine_positions_json
        FROM demo_mines_game_rounds
        WHERE id = %s
        """,
        (session_id,),
    )
    assert row is not None
    mine_positions = set(row["mine_positions_json"])
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers={"X-Game-Launch-Token": game_launch_token},
        json={"game_session_id": session_id, "cell_index": safe_cell},
    )
    assert reveal_response.status_code == 200, reveal_response.text
    assert reveal_response.json()["data"]["result"] == "safe"

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"demo-full-cashout-{uuid4().hex}",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    cashout_payload = cashout_response.json()["data"]
    assert cashout_payload["mode"] == "demo"
    assert cashout_payload["ledger_transaction_id"] is None

    assert _table_count(db_helpers, "platform_rounds") == platform_rounds_before
    assert _table_count(db_helpers, "ledger_transactions") == ledger_transactions_before
