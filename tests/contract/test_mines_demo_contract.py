from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]

from uuid import uuid4




def _issue_demo_auth_token(client) -> tuple[str, str]:
    auth_response = client.post(
        "/auth/demo",
        headers={"X-Forwarded-For": f"10.20.1.{uuid4().int % 250 + 1}"},
    )
    assert auth_response.status_code == 200, auth_response.text
    data = auth_response.json()["data"]
    return data["access_token"], data["user_id"]


def _user_table_count(db_helpers, mines_db_helpers, table_name: str, user_id: str) -> int:
    row = db_helpers.fetchone(f"SELECT COUNT(*) AS count FROM {table_name} WHERE user_id = %s", (user_id,))
    assert row is not None
    return int(row["count"])


def _request_table_count(db_helpers, table_name: str, idempotency_key: str) -> int:
    """Conteggio per CHIAVE DI IDEMPOTENZA della richiesta, non per utente.

    Il conteggio per user_id non vede una scrittura errata con user_id nullo o
    attribuito a un altro utente; la chiave di idempotenza e' unica per
    richiesta, quindi intercetta qualunque riga finanziaria scritta per colpa
    di QUELLA richiesta, ovunque sia stata attribuita. Non e' un conteggio
    globale: non e' influenzato dalle esecuzioni parallele.
    """
    row = db_helpers.fetchone(
        f"SELECT COUNT(*) AS count FROM {table_name} WHERE idempotency_key = %s",
        (idempotency_key,),
    )
    assert row is not None
    return int(row["count"])


def _reference_table_count(db_helpers, table_name: str, reference_id: str) -> int:
    """Conteggio per riferimento alla sessione demo della richiesta."""
    row = db_helpers.fetchone(
        f"SELECT COUNT(*) AS count FROM {table_name} WHERE reference_id = %s",
        (reference_id,),
    )
    assert row is not None
    return int(row["count"])


def test_mines_demo_start_no_platform_rounds_write(
    client,
    db_helpers, mines_db_helpers,
    create_published_mines_variant,
) -> None:
    published_title = create_published_mines_variant(
        display_name="Mines Demo Contract Start Variant",
    )
    demo_token, user_id = _issue_demo_auth_token(client)
    demo_headers = {"Authorization": f"Bearer {demo_token}"}
    platform_rounds_before = _user_table_count(db_helpers, mines_db_helpers, "platform_rounds", user_id)
    ledger_transactions_before = _user_table_count(db_helpers, mines_db_helpers, "ledger_transactions", user_id)

    start_idempotency_key = f"demo-start-{uuid4().hex}"
    start_response = client.post(
        "/games/mines/start",
        headers={
            **demo_headers,
            "Idempotency-Key": start_idempotency_key,
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
    assert _user_table_count(db_helpers, mines_db_helpers, "platform_rounds", user_id) == platform_rounds_before
    assert _user_table_count(db_helpers, mines_db_helpers, "ledger_transactions", user_id) == ledger_transactions_before
    # Correlato alla richiesta: nessuna riga finanziaria, per NESSUN utente,
    # puo' portare la chiave di idempotenza di questo start demo.
    assert _request_table_count(db_helpers, "ledger_transactions", start_idempotency_key) == 0
    assert _request_table_count(db_helpers, "platform_rounds", start_idempotency_key) == 0


def test_mines_demo_full_round_cashout_no_ledger_write(
    client,
    db_helpers, mines_db_helpers,
    create_published_mines_variant,
) -> None:
    published_title = create_published_mines_variant(
        display_name="Mines Demo Contract Cashout Variant",
    )
    demo_token, user_id = _issue_demo_auth_token(client)
    demo_headers = {"Authorization": f"Bearer {demo_token}"}
    platform_rounds_before = _user_table_count(db_helpers, mines_db_helpers, "platform_rounds", user_id)
    ledger_transactions_before = _user_table_count(db_helpers, mines_db_helpers, "ledger_transactions", user_id)

    start_idempotency_key = f"demo-full-start-{uuid4().hex}"
    start_response = client.post(
        "/games/mines/start",
        headers={
            **demo_headers,
            "Idempotency-Key": start_idempotency_key,
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

    # SIC-08: open rounds do not persist mine positions; the helper
    # recomputes them from seed+nonce+params when they are not stored.
    mine_positions = set(mines_db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=demo_headers,
        json={"game_session_id": session_id, "cell_index": safe_cell, "wallet_source": "demo"},
    )
    assert reveal_response.status_code == 200, reveal_response.text
    assert reveal_response.json()["data"]["result"] == "safe"

    cashout_idempotency_key = f"demo-full-cashout-{uuid4().hex}"
    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **demo_headers,
            "Idempotency-Key": cashout_idempotency_key,
        },
        json={"game_session_id": session_id, "wallet_source": "demo"},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    cashout_payload = cashout_response.json()["data"]
    assert cashout_payload["mode"] == "demo"
    assert cashout_payload["ledger_transaction_id"] is None
    assert cashout_payload["mine_positions"] == sorted(mine_positions)

    assert _user_table_count(db_helpers, mines_db_helpers, "platform_rounds", user_id) == platform_rounds_before
    count_after = _user_table_count(db_helpers, mines_db_helpers, "ledger_transactions", user_id)
    if count_after != ledger_transactions_before:
        rows = db_helpers.fetchall("SELECT id, transaction_type, reference_type FROM ledger_transactions ORDER BY created_at DESC LIMIT 5", ())
        print("LEAKED TRANSACTIONS:", rows)
    assert count_after == ledger_transactions_before
    # Correlato alla richiesta e alla sessione demo: nessuna riga finanziaria,
    # per NESSUN utente, puo' portare le chiavi di idempotenza di questo giro
    # demo ne' riferirsi alla sua sessione.
    assert _request_table_count(db_helpers, "ledger_transactions", start_idempotency_key) == 0
    assert _request_table_count(db_helpers, "ledger_transactions", cashout_idempotency_key) == 0
    assert _request_table_count(db_helpers, "platform_rounds", start_idempotency_key) == 0
    assert _request_table_count(db_helpers, "platform_rounds", cashout_idempotency_key) == 0
    assert _reference_table_count(db_helpers, "ledger_transactions", session_id) == 0
