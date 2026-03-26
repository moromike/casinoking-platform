from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import httpx


def test_duplicate_start_same_idempotency_key_creates_one_session(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-start")
    headers = {
        "Authorization": f"Bearer {player['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": "concurrency-start-key",
    }
    payload = {
        "grid_size": 25,
        "mine_count": 3,
        "bet_amount": "4.000000",
        "wallet_type": "cash",
    }

    def do_start() -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post("/games/mines/start", headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: do_start(), range(2)))

    assert all(response.status_code == 200 for response in responses)
    session_ids = {response.json()["data"]["game_session_id"] for response in responses}
    assert len(session_ids) == 1

    rows = db_helpers.fetchall(
        """
        SELECT id
        FROM game_sessions
        WHERE user_id = %s
          AND idempotency_key = %s
        """,
        (player["user_id"], "concurrency-start-key"),
    )
    assert len(rows) == 1


def test_duplicate_reveal_same_cell_allows_only_one_success(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-reveal")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-reveal-start",
            },
            json={
                "grid_size": 25,
                "mine_count": 3,
                "bet_amount": "3.000000",
                "wallet_type": "cash",
            },
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    def do_reveal() -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/reveal",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "game_session_id": session_id,
                    "cell_index": safe_cell,
                },
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: do_reveal(), range(2)))

    status_codes = sorted(response.status_code for response in responses)
    assert status_codes == [200, 409]

    session_row = db_helpers.fetchone(
        """
        SELECT safe_reveals_count, revealed_cells_json
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row == {
        "safe_reveals_count": 1,
        "revealed_cells_json": [safe_cell],
    }


def test_double_cashout_same_session_only_one_win(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-cashout")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-cashout-start",
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

        mine_positions = set(db_helpers.get_mine_positions(session_id))
        safe_cell = next(index for index in range(25) if index not in mine_positions)
        reveal_response = client.post(
            "/games/mines/reveal",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={
                "game_session_id": session_id,
                "cell_index": safe_cell,
            },
        )
        assert reveal_response.status_code == 200

    def do_cashout(suffix: str) -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/cashout",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": f"concurrency-cashout-{suffix}",
                },
                json={"game_session_id": session_id},
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(do_cashout, ["a", "b"]))

    status_codes = sorted(response.status_code for response in responses)
    assert status_codes == [200, 409]

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]


def test_parallel_cashout_same_idempotency_key_returns_single_financial_effect(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-cashout-same-key")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-cashout-same-key-start",
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

        mine_positions = set(db_helpers.get_mine_positions(session_id))
        safe_cell = next(index for index in range(25) if index not in mine_positions)
        reveal_response = client.post(
            "/games/mines/reveal",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={
                "game_session_id": session_id,
                "cell_index": safe_cell,
            },
        )
        assert reveal_response.status_code == 200

    cashout_headers = {
        "Authorization": f"Bearer {player['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": "concurrency-cashout-same-key",
    }
    cashout_payload = {"game_session_id": session_id}
    barrier = Barrier(2)

    def do_cashout() -> httpx.Response:
        barrier.wait(timeout=5)
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/cashout",
                headers=cashout_headers,
                json=cashout_payload,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(do_cashout) for _ in range(2)]
        responses = [future.result() for future in futures]

    assert all(response.status_code == 200 for response in responses)
    response_data = [response.json()["data"] for response in responses]
    assert len({row["ledger_transaction_id"] for row in response_data}) == 1
    assert {row["status"] for row in response_data} == {"won"}
    assert len({row["payout_amount"] for row in response_data}) == 1
    assert len({row["wallet_balance_after"] for row in response_data}) == 1

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]
    assert (
        len(
            {
                row["idempotency_key"]
                for row in game_transactions
                if row["transaction_type"] == "win"
            }
        )
        == 1
    )
    assert db_helpers.get_wallet_balance(str(player["user_id"])) == response_data[0][
        "wallet_balance_after"
    ]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": response_data[0]["wallet_balance_after"],
        "ledger_balance": response_data[0]["wallet_balance_after"],
        "drift": "0.000000",
    }


def test_parallel_reveals_different_safe_cells_keep_state_coherent(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-reveal-different")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-reveal-different-start",
            },
            json={
                "grid_size": 25,
                "mine_count": 3,
                "bet_amount": "3.000000",
                "wallet_type": "cash",
            },
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cells = [index for index in range(25) if index not in mine_positions][:2]
    assert len(safe_cells) == 2

    def do_reveal(cell_index: int) -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/reveal",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "game_session_id": session_id,
                    "cell_index": cell_index,
                },
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(do_reveal, safe_cells))

    assert all(response.status_code == 200 for response in responses)
    assert {response.json()["data"]["result"] for response in responses} == {"safe"}

    session_row = db_helpers.fetchone(
        """
        SELECT safe_reveals_count, revealed_cells_json, status
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["safe_reveals_count"] == 2
    assert sorted(session_row["revealed_cells_json"]) == sorted(safe_cells)
    assert session_row["status"] == "active"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet"]


def test_parallel_safe_reveal_and_cashout_keep_session_and_ledger_coherent(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-reveal-cashout-safe")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-reveal-cashout-safe-start",
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

        mine_positions = set(db_helpers.get_mine_positions(session_id))
        safe_cells = [index for index in range(25) if index not in mine_positions][:2]
        assert len(safe_cells) == 2

        first_reveal_response = client.post(
            "/games/mines/reveal",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={
                "game_session_id": session_id,
                "cell_index": safe_cells[0],
            },
        )
        assert first_reveal_response.status_code == 200

    barrier = Barrier(2)

    def do_second_reveal() -> httpx.Response:
        barrier.wait(timeout=5)
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/reveal",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "game_session_id": session_id,
                    "cell_index": safe_cells[1],
                },
            )

    def do_cashout() -> httpx.Response:
        barrier.wait(timeout=5)
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/cashout",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": "concurrency-reveal-cashout-safe-cashout",
                },
                json={"game_session_id": session_id},
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        reveal_future = executor.submit(do_second_reveal)
        cashout_future = executor.submit(do_cashout)
        reveal_response = reveal_future.result()
        cashout_response = cashout_future.result()

    assert cashout_response.status_code == 200
    assert reveal_response.status_code in {200, 409}

    session_row = db_helpers.fetchone(
        """
        SELECT status, safe_reveals_count, revealed_cells_json, closed_at
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] == "won"
    assert session_row["closed_at"] is not None
    assert session_row["safe_reveals_count"] in {1, 2}
    assert safe_cells[0] in session_row["revealed_cells_json"]
    assert len(session_row["revealed_cells_json"]) == session_row["safe_reveals_count"]

    if reveal_response.status_code == 200:
        assert session_row["safe_reveals_count"] == 2
        assert sorted(session_row["revealed_cells_json"]) == sorted(safe_cells)
    else:
        assert session_row["safe_reveals_count"] == 1
        assert session_row["revealed_cells_json"] == [safe_cells[0]]

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")["drift"] == (
        "0.000000"
    )


def test_parallel_mine_reveal_and_cashout_produce_one_terminal_outcome(
    api_base_url,
    create_authenticated_player,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="concurrency-reveal-cashout-mine")
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        start_response = client.post(
            "/games/mines/start",
            headers={
                "Authorization": f"Bearer {player['access_token']}",
                "Idempotency-Key": "concurrency-reveal-cashout-mine-start",
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

        mine_positions = db_helpers.get_mine_positions(session_id)
        safe_cell = next(index for index in range(25) if index not in set(mine_positions))

        first_reveal_response = client.post(
            "/games/mines/reveal",
            headers={"Authorization": f"Bearer {player['access_token']}"},
            json={
                "game_session_id": session_id,
                "cell_index": safe_cell,
            },
        )
        assert first_reveal_response.status_code == 200

    barrier = Barrier(2)
    mine_cell = mine_positions[0]

    def do_mine_reveal() -> httpx.Response:
        barrier.wait(timeout=5)
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/reveal",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "game_session_id": session_id,
                    "cell_index": mine_cell,
                },
            )

    def do_cashout() -> httpx.Response:
        barrier.wait(timeout=5)
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                "/games/mines/cashout",
                headers={
                    "Authorization": f"Bearer {player['access_token']}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": "concurrency-reveal-cashout-mine-cashout",
                },
                json={"game_session_id": session_id},
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        reveal_future = executor.submit(do_mine_reveal)
        cashout_future = executor.submit(do_cashout)
        reveal_response = reveal_future.result()
        cashout_response = cashout_future.result()

    assert sorted([reveal_response.status_code, cashout_response.status_code]) in (
        [200, 409],
        [200, 200],
    )

    session_row = db_helpers.fetchone(
        """
        SELECT status, safe_reveals_count, revealed_cells_json, closed_at
        FROM game_sessions
        WHERE id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] in {"won", "lost"}
    assert session_row["closed_at"] is not None

    game_transactions = db_helpers.get_game_transactions(session_id)
    transaction_types = [row["transaction_type"] for row in game_transactions]

    if session_row["status"] == "won":
        assert cashout_response.status_code == 200
        assert reveal_response.status_code == 409
        assert transaction_types == ["bet", "win"]
        assert session_row["safe_reveals_count"] == 1
        assert session_row["revealed_cells_json"] == [safe_cell]
        assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
            "wallet_type": "cash",
            "balance_snapshot": "1000.114500",
            "ledger_balance": "1000.114500",
            "drift": "0.000000",
        }
    else:
        assert reveal_response.status_code == 200
        assert cashout_response.status_code == 409
        assert transaction_types == ["bet"]
        assert session_row["safe_reveals_count"] == 1
        assert sorted(session_row["revealed_cells_json"]) == sorted([safe_cell, mine_cell])
        assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
            "wallet_type": "cash",
            "balance_snapshot": "995.000000",
            "ledger_balance": "995.000000",
            "drift": "0.000000",
        }
