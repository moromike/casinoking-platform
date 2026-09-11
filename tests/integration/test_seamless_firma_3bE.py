"""3bE — Firma per operazione: cross-route, body-only e metodo diverso.

Collaudi che inchiodano le tre proprieta' nuove della firma per operazione:
1. Una firma valida per reserve non e' valida per commit (cross-route → 401).
2. Una firma calcolata solo sul corpo (vecchio schema) viene rifiutata (→ 401).
3. Un metodo HTTP diverso da quello firmato viene rifiutato (→ 401).

Scritti PRIMA del codice e visti ROSSI (missione 3bE, 11/09/2026).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret

pytestmark = [pytest.mark.integration]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload_reserve(user_id: str, *, tx_id: str | None = None) -> dict:
    return {
        "user_id": user_id,
        "game_session_id": str(uuid4()),
        "provider_code": PROVIDER_CODE,
        "currency": "CHIP",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": tx_id or f"3bE-xroute-{uuid4().hex}",
        "amount": "10.00",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
    }


def _firma_vecchia(secret: bytes, body: bytes) -> str:
    """Firma del SOLO corpo (schema pre-3bE, deve essere rifiutata)."""
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def _firma_operazione(secret: bytes, metodo: str, token: str, body: bytes) -> str:
    """Firma corretta: METODO\\nTOKEN\\nCORPO."""
    msg = f"{metodo}\n{token}\n".encode() + body
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


# --- 1. cross-route: firma di reserve riusata su commit → 401 ---


def test_firma_di_reserve_riusata_su_commit_e_401(
    client, create_player
) -> None:
    """La firma di una reserve valida, mandata a commit, deve essere 401.

    Non e' un problema di schema (il commit ha un suo schema che fallirebbe
    comunque), ma di FIRMA: il token di operazione e' diverso, quindi la
    firma non coincide e il server rifiuta prima di guardare il corpo.
    """
    player = create_player(prefix="3bE-crossroute")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    # Firma valida per reserve
    firma_reserve = _firma_operazione(secret, "POST", "wallet.reserve.v1", body)

    # La stessa firma, mandata a commit: il server deve rifiutare per la
    # firma (401), non per lo schema (422).
    response = client.post(
        "/seamless/wallet/commit",
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": firma_reserve,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401, (
        f"cross-route: atteso 401, ottenuto {response.status_code}: {response.text}"
    )


# --- 2. firma solo-corpo (vecchio schema) → 401 ---


def test_firma_solo_corpo_e_401(client, create_player) -> None:
    """Una firma calcolata solo sul corpo (pre-3bE) non e' piu' accettata.

    Nessuna doppia accettazione: il server verifica il nuovo formato e
    una firma vecchia produce un HMAC diverso, quindi 401.
    """
    player = create_player(prefix="3bE-bodyonly")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    firma_vecchia = _firma_vecchia(secret, body)

    response = client.post(
        "/seamless/wallet/reserve",
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": firma_vecchia,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401, (
        f"body-only: atteso 401, ottenuto {response.status_code}: {response.text}"
    )


# --- 3. metodo diverso da quello firmato → 401 ---


def test_metodo_diverso_da_quello_firmato_e_401(
    client, create_player
) -> None:
    """Una firma calcolata con GET, mandata come POST, deve essere 401.

    Il metodo fa parte del messaggio firmato: cambiarlo produce un HMAC
    diverso anche a parita' di token e corpo.
    """
    player = create_player(prefix="3bE-method")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    # Firma con GET invece di POST
    firma_get = _firma_operazione(secret, "GET", "wallet.reserve.v1", body)

    response = client.post(
        "/seamless/wallet/reserve",
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": firma_get,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401, (
        f"wrong method: atteso 401, ottenuto {response.status_code}: {response.text}"
    )
