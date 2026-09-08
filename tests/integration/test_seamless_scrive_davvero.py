"""POR-06 — le risposte riuscite del seamless devono corrispondere al registro."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"
HOUSE_CASH_ACCOUNT = "HOUSE_CASH"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, amount: str | None = None,
             is_win: bool | None = None,
             reserve_tx_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id, "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE, "currency": "CHIP", "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE, "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if is_win is not None:
        payload["is_win"] = is_win
    # LA TRATTENUTA CHE LA CHIUSURA CHIUDE (POR-02): obbligatoria su commit e
    # rollback, assente sulla reserve, che non chiude niente.
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(route, content=body, headers={
        "x-provider-id": PROVIDER_CODE,
        "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
        "Content-Type": "application/json",
    })


def _assert_entries(db_helpers, transaction_id: str, expected: set[tuple[str, str, Decimal]]) -> None:
    actual = {
        (str(entry["account_code"]), str(entry["entry_side"]), Decimal(entry["amount"]))
        for entry in db_helpers.get_transaction_entries(transaction_id)
    }
    assert actual == expected


def _open_reserve(client: Client, user_id: str, amount: str = "10.00") -> tuple[str, str]:
    game_session_id = str(uuid4())
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=game_session_id,
        tx_id=f"scrive-reserve-{uuid4().hex}", amount=amount,
    ))
    assert response.status_code == 200, response.text
    return game_session_id, str(response.json()["tx_id"])


def test_reserve_riuscita_scrive_puntata_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-reserve")
    user_id = str(player["user_id"])
    game_session_id, _tx_id = _open_reserve(client, user_id)

    transactions = db_helpers.get_game_transactions(game_session_id)
    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction["transaction_type"] == "bet"
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(transaction["id"]), {
        (str(wallet_row["account_code"]), "debit", Decimal("10.00")),
        (HOUSE_CASH_ACCOUNT, "credit", Decimal("10.00")),
    })


def test_commit_vincita_riuscita_scrive_accredito_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-win")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"scrive-win-{uuid4().hex}", amount="25.00", is_win=True,
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    win = [tx for tx in transactions if tx["transaction_type"] == "win"]
    assert len(win) == 1
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(win[0]["id"]), {
        (HOUSE_CASH_ACCOUNT, "debit", Decimal("25.00")),
        (str(wallet_row["account_code"]), "credit", Decimal("25.00")),
    })


def test_commit_perdita_riuscita_conserva_la_sola_puntata_nel_registro(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-loss")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"scrive-loss-{uuid4().hex}", amount="0.00", is_win=False,
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    assert [tx["transaction_type"] for tx in transactions] == ["bet"]
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(transactions[0]["id"]), {
        (str(wallet_row["account_code"]), "debit", Decimal("10.00")),
        (HOUSE_CASH_ACCOUNT, "credit", Decimal("10.00")),
    })


def test_rollback_riuscito_scrive_rimborso_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-rollback")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=f"scrive-rollback-{uuid4().hex}",
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    rollback = [tx for tx in transactions if tx["transaction_type"] == "rollback"]
    assert len(rollback) == 1
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(rollback[0]["id"]), {
        (HOUSE_CASH_ACCOUNT, "debit", Decimal("10.00")),
        (str(wallet_row["account_code"]), "credit", Decimal("10.00")),
    })
