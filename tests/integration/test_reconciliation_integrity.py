from __future__ import annotations
import pytest

from uuid import uuid4


def test_signup_wallets_start_reconciled(
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-reconciliation-signup")

    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "1000.000000",
        "ledger_balance": "1000.000000",
        "drift": "0.000000",
    }
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "bonus") == {
        "wallet_type": "bonus",
        "balance_snapshot": "0.000000",
        "ledger_balance": "0.000000",
        "drift": "0.000000",
    }


def test_una_vincita_lascia_il_portafoglio_quadrato(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    """La quadratura dopo una vincita, SENZA dipendere da un gioco vero.

    MAN-03: prima questo test apriva una partita a Mines, scopriva una casella e
    incassava. Ma cio' che verifica e' l'ultima riga — che il portafoglio quadri —
    e Mines era solo il mezzo per far muovere l'euro. Ora il mezzo e' il manichino,
    e le asserzioni sono le stesse.

    In piu' il saldo atteso non dipende piu' dal moltiplicatore di Mines: la vincita
    la decidiamo noi, quindi 1000 - 5 + 5,568 e' aritmetica visibile invece che una
    costante da fidarsi.
    """
    player = create_authenticated_player(prefix="integration-reconciliation-manichino")
    headers = auth_headers(player["access_token"])

    start_response = client.post(
        "/games/manichino/start",
        headers={
            **headers,
            "Idempotency-Key": f"integration-reconciliation-start-{uuid4().hex}",
        },
        json={"bet_amount": "5.000000", "wallet_type": "cash"},
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    # La versione con Mines aveva un passo in piu' (scopri una casella) e quindi
    # un'asserzione in piu'. Invece di perderla, qui si verifica una cosa che quella
    # versione NON verificava: che la puntata sia stata davvero trattenuta prima
    # della chiusura. A round aperto il portafoglio deve gia' quadrare a 995.
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "995.000000",
        "ledger_balance": "995.000000",
        "drift": "0.000000",
    }

    settle_response = client.post(
        "/games/manichino/settle",
        headers={
            **headers,
            "Idempotency-Key": f"integration-reconciliation-settle-{uuid4().hex}",
        },
        json={
            "game_session_id": session_id,
            "esito": "vincita",
            "payout_amount": "5.568000",
        },
    )
    assert settle_response.status_code == 200, settle_response.text

    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "1000.568000",
        "ledger_balance": "1000.568000",
        "drift": "0.000000",
    }


def test_admin_bonus_grant_keeps_bonus_wallet_reconciled(
    client,
    create_admin_user,
    create_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-reconciliation-admin")
    target_user = create_player(prefix="integration-reconciliation-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/bonus-grants",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-reconciliation-bonus-grant",
        },
        json={
            "amount": "50.000000",
            "reason": "reconciliation_check",
        },
    )
    assert response.status_code == 200

    assert db_helpers.get_wallet_reconciliation(str(target_user["user_id"]), "bonus") == {
        "wallet_type": "bonus",
        "balance_snapshot": "50.000000",
        "ledger_balance": "50.000000",
        "drift": "0.000000",
    }
