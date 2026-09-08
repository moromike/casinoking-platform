"""POR-01 / PRO-01 — ogni campo del protocollo e' indispensabile."""

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

# Questo e' l'elenco dichiarato dei campi che il collaudo esercita.  Se PRO-01
# cresce, aggiornare PROTOCOL_REQUIRED_FIELDS prima di aggiungere il caso: il
# test sottostante impedisce di dimenticare la nuova prova.
EXERCISED_REQUIRED_FIELDS = frozenset(
    {
        "user_id",
        "game_session_id",
        "provider_code",
        "currency",
        "game_code",
        "wallet_type",
        "tx_id",
        "timestamp",
        "nonce",
        "reserve_tx_id",
    }
)
PROTOCOL_REQUIRED_FIELDS = frozenset(
    {
        "user_id",
        "game_session_id",
        "provider_code",
        "currency",
        "game_code",
        "wallet_type",
        "tx_id",
        "timestamp",
        "nonce",
        "reserve_tx_id",
    }
)
RESERVE_REQUIRED_FIELDS = PROTOCOL_REQUIRED_FIELDS - {"reserve_tx_id"}


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


def _open_reserve(client: Client, user_id: str) -> tuple[str, str]:
    game_session_id = str(uuid4())
    reserve_tx_id = f"required-field-reserve-{uuid4().hex}"
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


def test_elenco_campi_esercitati_copre_tutto_pro_01() -> None:
    assert EXERCISED_REQUIRED_FIELDS == PROTOCOL_REQUIRED_FIELDS, (
        "PRO-01 contiene campi obbligatori non esercitati: "
        f"{sorted(PROTOCOL_REQUIRED_FIELDS - EXERCISED_REQUIRED_FIELDS)}"
    )


@pytest.mark.parametrize("missing_field", sorted(RESERVE_REQUIRED_FIELDS))
def test_reserve_rifiuta_ogni_campo_pro_01_assente_senza_muovere_saldo(
    missing_field, client, create_player, db_helpers
) -> None:
    player = create_player(prefix=f"seamless-required-reserve-{missing_field}")
    user_id = str(player["user_id"])
    payload = _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"missing-{missing_field}-{uuid4().hex}",
        amount="10.00",
    )
    del payload[missing_field]

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", payload)
    after = db_helpers.get_wallet_balance(user_id)

    assert 400 <= response.status_code < 500, response.text
    assert after == before, f"Reserve senza {missing_field} ha modificato il saldo"


def test_commit_rifiuta_reserve_tx_id_assente_senza_muovere_saldo(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-required-commit")
    user_id = str(player["user_id"])
    game_session_id, _reserve_tx_id = _open_reserve(client, user_id)
    payload = _payload(
        user_id=user_id,
        game_session_id=game_session_id,
        tx_id=f"missing-reserve-tx-id-commit-{uuid4().hex}",
        amount="25.00",
        is_win=True,
    )

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/commit", payload)
    after = db_helpers.get_wallet_balance(user_id)

    assert 400 <= response.status_code < 500, response.text
    assert after == before, "Commit senza reserve_tx_id ha modificato il saldo"


def test_rollback_rifiuta_reserve_tx_id_assente_senza_muovere_saldo(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-required-rollback")
    user_id = str(player["user_id"])
    game_session_id, _reserve_tx_id = _open_reserve(client, user_id)
    payload = _payload(
        user_id=user_id,
        game_session_id=game_session_id,
        tx_id=f"missing-reserve-tx-id-rollback-{uuid4().hex}",
    )

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/rollback", payload)
    after = db_helpers.get_wallet_balance(user_id)

    assert 400 <= response.status_code < 500, response.text
    assert after == before, "Rollback senza reserve_tx_id ha modificato il saldo"
