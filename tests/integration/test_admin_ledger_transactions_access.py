from __future__ import annotations
import pytest

from uuid import uuid4


def _issue_manichino_launch_token(client, headers: dict[str, str]) -> str:
    """La cavia passa dalla stessa porta di lancio comune dei giochi reali."""
    response = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["game_launch_token"])


def test_admin_ledger_transactions_match_database_transaction_count(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-ledger-admin")
    player = create_authenticated_player(prefix="integration-ledger-player")

    headers = auth_headers(player["access_token"])
    game_launch_token = _issue_manichino_launch_token(client, headers)

    # MAN-03: prima questa prova apriva un round di Mines per far comparire una
    # scrittura "bet" nel registro. Ma cio' che verifica e' l'elenco admin delle
    # transazioni, e Mines era solo il mezzo per muovere l'euro: ora il mezzo e'
    # il manichino, e le asserzioni sono le stesse. La sessione d'accesso, che
    # Mines esigeva, qui non serve: la start del manichino la accetta facoltativa.
    start_response = client.post(
        "/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"integration-ledger-admin-start-{uuid4().hex}",
        },
        json={
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200

    response = client.get(
        "/ledger/transactions",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert response.status_code == 200
    payload = response.json()["data"]

    db_count = db_helpers.fetchone(
        """
        SELECT COUNT(*) AS transaction_count
        FROM ledger_transactions
        """,
        (),
    )
    assert db_count is not None
    assert len(payload) == db_count["transaction_count"]

    player_rows = [
        row for row in payload if row["transaction_type"] == "signup_credit"
    ]
    assert any(row["id"] == player["bootstrap_transaction_id"] for row in player_rows)
    assert any(row["transaction_type"] == "bet" for row in payload)
