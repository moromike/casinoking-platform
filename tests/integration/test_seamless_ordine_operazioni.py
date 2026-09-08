"""POR-04 — il portafoglio esterno rifiuta operazioni fuori ordine."""

from __future__ import annotations

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


def _payload(
    *,
    user_id: str,
    game_session_id: str,
    tx_id: str,
    amount: str | None = None,
    is_win: bool | None = None,
    reserve_tx_id: str | None = None,
) -> dict[str, object]:
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
    return client.post(
        route,
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
            "Content-Type": "application/json",
        },
    )


def _open_reserve(client: Client, user_id: str) -> tuple[str, str]:
    game_session_id = str(uuid4())
    tx_id = f"ordine-reserve-{uuid4().hex}"
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(user_id=user_id, game_session_id=game_session_id, tx_id=tx_id, amount="10.00"),
    )
    assert response.status_code == 200, response.text
    return game_session_id, tx_id


def _assert_rejected_without_balance_change(response, before: str, after: str) -> None:
    assert 400 <= response.status_code < 500, response.text
    assert after == before, "L'operazione rifiutata ha modificato il saldo del giocatore"


def test_reserve_su_partita_gia_conclusa_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-reserve-closed")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-close-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            tx_id=f"ordine-reserve-after-close-{uuid4().hex}",
            amount="10.00",
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_doppia_commit_identica_restituisce_prima_risposta_e_muove_denaro_una_sola_volta(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-duplicate-commit")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    payload = _payload(
        user_id=user_id,
        game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"ordine-duplicate-commit-{uuid4().hex}",
        amount="25.00",
        is_win=True,
    )

    first = _post(client, "/seamless/wallet/commit", payload)
    assert first.status_code == 200, first.text
    balance_after_first = db_helpers.get_wallet_balance(user_id)
    second = _post(client, "/seamless/wallet/commit", payload)
    balance_after_second = db_helpers.get_wallet_balance(user_id)

    assert second.status_code == 200, second.text
    assert first.json()["already_exists"] is False
    assert second.json()["already_exists"] is True
    first_without_replay_flag = dict(first.json())
    second_without_replay_flag = dict(second.json())
    first_without_replay_flag.pop("already_exists")
    second_without_replay_flag.pop("already_exists")
    assert second_without_replay_flag == first_without_replay_flag
    assert balance_after_second == balance_after_first
    transactions = db_helpers.get_game_transactions(game_session_id)
    assert [tx["transaction_type"] for tx in transactions].count("win") == 1


def test_commit_stesso_tx_id_importo_diverso_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-amount-conflict")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    tx_id = f"ordine-same-tx-{uuid4().hex}"
    first = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="25.00", is_win=True),
    )
    assert first.status_code == 200, first.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="26.00", is_win=True),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_commit_ripetuta_divergente_non_aggiorna_importo_in_silenzio(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-silent-update")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    tx_id = f"ordine-silent-update-{uuid4().hex}"
    first = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="25.00", is_win=True),
    )
    assert first.status_code == 200, first.text
    before = db_helpers.get_wallet_balance(user_id)

    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="99.00", is_win=True),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)
    round_row = db_helpers.fetchone(
        "SELECT payout_amount FROM platform_rounds WHERE id = %s", (game_session_id,)
    )
    assert round_row is not None
    assert f"{round_row['payout_amount']:.6f}" == "25.000000"


def test_chiusura_in_perdita_su_partita_gia_conclusa_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-loss-after-close")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-win-before-loss-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-loss-after-close-{uuid4().hex}",
            amount="0.00",
            is_win=False,
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_conflitto_di_stato_risponde_4xx_mai_500(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-order-state-conflict")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-close-before-conflict-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-state-conflict-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)
