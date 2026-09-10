from __future__ import annotations
"""POR-05 — un provider sospeso non puo' piu' scrivere sul portafoglio."""


import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, amount: str | None = None,
             reserve_tx_id: str | None = None, is_win: bool | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id,
        "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE,
        "currency": "CHIP",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    if is_win is not None:
        payload["is_win"] = is_win
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return client.post(
        route,
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": signature,
            "Content-Type": "application/json",
        },
    )


def _set_provider_status(db_connection, status: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE game_providers SET status = %s WHERE provider_code = %s",
            (status, PROVIDER_CODE),
        )


def _open_reserve(client: Client, user_id: str, *, tx_id: str | None = None) -> tuple[str, str]:
    reserve_tx_id = tx_id or f"reserve-{uuid4().hex}"
    game_session_id = str(uuid4())
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            tx_id=reserve_tx_id,
            amount="10.00",
        ),
    )
    assert response.status_code == 200, response.text
    return game_session_id, reserve_tx_id


def test_fornitore_sospeso_reserve_rifiutata_saldo_invariato(
    client, create_player, db_connection, db_helpers
) -> None:
    player = create_player(prefix="seamless-provider-suspended-reserve")
    original_status = db_helpers.fetchone(
        "SELECT status FROM game_providers WHERE provider_code = %s", (PROVIDER_CODE,)
    )
    assert original_status is not None
    _set_provider_status(db_connection, "suspended")
    try:
        before = db_helpers.get_wallet_balance(str(player["user_id"]))
        response = _post(
            client,
            "/seamless/wallet/reserve",
            _payload(
                user_id=str(player["user_id"]),
                game_session_id=str(uuid4()),
                tx_id=f"suspended-reserve-{uuid4().hex}",
                amount="10.00",
            ),
        )
        after = db_helpers.get_wallet_balance(str(player["user_id"]))
        assert 400 <= response.status_code < 500, response.text
        assert after == before, "La reserve rifiutata ha modificato il saldo del giocatore"
    finally:
        _set_provider_status(db_connection, str(original_status["status"]))


def test_fornitore_sospeso_commit_rifiutato_saldo_invariato(
    client, create_player, db_connection, db_helpers
) -> None:
    player = create_player(prefix="seamless-provider-suspended-commit")
    original_status = db_helpers.fetchone(
        "SELECT status FROM game_providers WHERE provider_code = %s", (PROVIDER_CODE,)
    )
    assert original_status is not None
    try:
        _set_provider_status(db_connection, "active")
        game_session_id, reserve_tx_id = _open_reserve(client, str(player["user_id"]))
        _set_provider_status(db_connection, "suspended")
        before = db_helpers.get_wallet_balance(str(player["user_id"]))
        response = _post(
            client,
            "/seamless/wallet/commit",
            _payload(
                user_id=str(player["user_id"]),
                game_session_id=game_session_id,
                tx_id=f"suspended-commit-{uuid4().hex}",
                reserve_tx_id=reserve_tx_id,
                amount="25.00",
                is_win=True,
            ),
        )
        after = db_helpers.get_wallet_balance(str(player["user_id"]))
        assert 400 <= response.status_code < 500, response.text
        assert after == before, "Il commit rifiutato ha modificato il saldo del giocatore"
    finally:
        _set_provider_status(db_connection, str(original_status["status"]))


def test_fornitore_sospeso_rollback_rifiutato_saldo_invariato(
    client, create_player, db_connection, db_helpers
) -> None:
    player = create_player(prefix="seamless-provider-suspended-rollback")
    original_status = db_helpers.fetchone(
        "SELECT status FROM game_providers WHERE provider_code = %s", (PROVIDER_CODE,)
    )
    assert original_status is not None
    try:
        _set_provider_status(db_connection, "active")
        game_session_id, reserve_tx_id = _open_reserve(client, str(player["user_id"]))
        _set_provider_status(db_connection, "suspended")
        before = db_helpers.get_wallet_balance(str(player["user_id"]))
        response = _post(
            client,
            "/seamless/wallet/rollback",
            _payload(
                user_id=str(player["user_id"]),
                game_session_id=game_session_id,
                tx_id=f"suspended-rollback-{uuid4().hex}",
                reserve_tx_id=reserve_tx_id,
            ),
        )
        after = db_helpers.get_wallet_balance(str(player["user_id"]))
        assert 400 <= response.status_code < 500, response.text
        assert after == before, "Il rollback rifiutato ha modificato il saldo del giocatore"
    finally:
        _set_provider_status(db_connection, str(original_status["status"]))


def test_fornitore_riattivato_reserve_commit_rollback_passano(
    client, create_player, db_connection, db_helpers
) -> None:
    """Dopo la riattivazione le tre scritture tornano disponibili."""
    player = create_player(prefix="seamless-provider-reactivated")
    original_status = db_helpers.fetchone(
        "SELECT status FROM game_providers WHERE provider_code = %s", (PROVIDER_CODE,)
    )
    assert original_status is not None
    try:
        _set_provider_status(db_connection, "suspended")
        _set_provider_status(db_connection, "active")

        commit_session_id, commit_reserve_tx_id = _open_reserve(client, str(player["user_id"]))
        committed = _post(
            client,
            "/seamless/wallet/commit",
            _payload(
                user_id=str(player["user_id"]),
                game_session_id=commit_session_id,
                tx_id=f"reactivated-commit-{uuid4().hex}",
                reserve_tx_id=commit_reserve_tx_id,
                amount="25.00",
                is_win=True,
            ),
        )
        assert committed.status_code == 200, committed.text

        rollback_session_id, rollback_reserve_tx_id = _open_reserve(client, str(player["user_id"]))
        rolled_back = _post(
            client,
            "/seamless/wallet/rollback",
            _payload(
                user_id=str(player["user_id"]),
                game_session_id=rollback_session_id,
                tx_id=f"reactivated-rollback-{uuid4().hex}",
                reserve_tx_id=rollback_reserve_tx_id,
            ),
        )
        assert rolled_back.status_code == 200, rolled_back.text
    finally:
        _set_provider_status(db_connection, str(original_status["status"]))
