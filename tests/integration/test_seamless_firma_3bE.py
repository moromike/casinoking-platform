"""3bE — Firma per operazione: cross-route, body-only e metodo diverso.

Collaudi che inchiodano le tre proprieta' nuove della firma per operazione:
1. Una firma valida per reserve non e' valida per commit (cross-route → 401).
2. Una firma calcolata solo sul corpo (vecchio schema) viene rifiutata (→ 401).
3. Un metodo HTTP diverso da quello firmato viene rifiutato (→ 401).

Revisione 3bE giro 1 (11/09/2026): ogni collaudo PRIMA dimostra che la firma
giusta per la rotta e il metodo giusti viene ACCETTATA (2xx), POI che la
variante sbagliata e' 401. Senza il controllo positivo, un 401 potrebbe
mascherare un errore di configurazione.

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

ROTTA_RESERVE = "/seamless/wallet/reserve"
ROTTA_COMMIT = "/seamless/wallet/commit"


# --- 0. unit: endswith rimosso, confronto esatto ---


def test_token_da_percorso_rifiuta_prefisso_diverso() -> None:
    """Un percorso che termina con /seamless/wallet/reserve ma ha un prefisso
    diverso NON deve ottenere il token. Inchioda la rimozione di endswith."""
    from app.core.config import settings
    from app.modules.providers.auth import token_da_percorso

    prefisso = settings.api_v1_prefix.rstrip("/")
    assert token_da_percorso("/altro/api/seamless/wallet/reserve") is None
    assert token_da_percorso("/seamless/wallet/reserve") is None
    assert token_da_percorso(f"{prefisso}/seamless/wallet/reserve") == "wallet.reserve.v1"


def test_confine_senza_token_non_ricade_su_corpo() -> None:
    """Se il percorso non ha un token, il confine NON deve verificare la
    firma sul solo corpo. Inchioda la rimozione del ramo else: msg = corpo."""
    import inspect
    from app.api.v1.seamless.confine import RottaDelConfine

    sorgente = inspect.getsource(RottaDelConfine.get_route_handler)
    assert "msg = corpo" not in sorgente, (
        "Il confine ha ancora il ramo 'msg = corpo' per rotte senza token"
    )


def _payload_reserve(user_id: str, *, tx_id: str | None = None) -> dict:
    return {
        "user_id": user_id,
        "game_session_id": str(uuid4()),
        "provider_code": PROVIDER_CODE,
        "currency": "CHIP",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": tx_id or f"3bE-{uuid4().hex}",
        "amount": "10.00",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
    }


def _payload_commit(user_id: str, *, reserve_tx_id: str) -> dict:
    return {
        "user_id": user_id,
        "game_session_id": str(uuid4()),
        "provider_code": PROVIDER_CODE,
        "currency": "CHIP",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": f"3bE-c-{uuid4().hex}",
        "amount": "10.00",
        "is_win": True,
        "reserve_tx_id": reserve_tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
    }


def _firma_vecchia(secret: bytes, body: bytes) -> str:
    """Firma del SOLO corpo (schema pre-3bE, deve essere rifiutata)."""
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def _firma_corretta(secret: bytes, metodo: str, token: str, body: bytes) -> str:
    """Firma corretta: METODO\\nTOKEN\\nCORPO."""
    msg = f"{metodo}\n{token}\n".encode() + body
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def _post_firmato(client: Client, rotta: str, body: bytes, firma: str) -> int:
    """Invia una richiesta POST con la firma data e torna il codice HTTP."""
    response = client.post(
        rotta,
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": firma,
            "Content-Type": "application/json",
        },
    )
    return response.status_code


# --- 1. cross-route: firma di reserve riusata su commit → 401 ---


def test_firma_valida_reserve_accettata(client, create_player) -> None:
    """CONTROLLO POSITIVO: la firma giusta per reserve viene accettata."""
    player = create_player(prefix="3bE-ok-reserve")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    firma = _firma_corretta(secret, "POST", "wallet.reserve.v1", body)
    codice = _post_firmato(client, ROTTA_RESERVE, body, firma)
    assert codice == 200, f"positivo reserve: atteso 200, ottenuto {codice}"


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
    firma_reserve = _firma_corretta(secret, "POST", "wallet.reserve.v1", body)

    # La stessa firma, mandata a commit: il server deve rifiutare per la
    # firma (401), non per lo schema (422).
    codice = _post_firmato(client, ROTTA_COMMIT, body, firma_reserve)
    assert codice == 401, (
        f"cross-route: atteso 401, ottenuto {codice}"
    )


# --- 2. firma solo-corpo (vecchio schema) → 401 ---


def test_firma_solo_corpo_e_401(client, create_player) -> None:
    """Una firma calcolata solo sul corpo (pre-3bE) non e' piu' accettata.

    CONTROLLO POSITIVO: prima si verifica che la firma giusta passa (200),
    poi che la firma solo-corpo viene rifiutata (401).
    """
    player = create_player(prefix="3bE-bodyonly")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    # POSITIVO: firma corretta accettata
    firma_ok = _firma_corretta(secret, "POST", "wallet.reserve.v1", body)
    codice_ok = _post_firmato(client, ROTTA_RESERVE, body, firma_ok)
    assert codice_ok == 200, f"positivo body-only: atteso 200, ottenuto {codice_ok}"

    # NEGATIVO: firma solo-corpo rifiutata
    # Nuovo payload (nonce e tx_id diversi per evitare anti-rigioco)
    payload2 = _payload_reserve(str(player["user_id"]))
    body2 = json.dumps(payload2, separators=(",", ":")).encode()
    firma_vecchia = _firma_vecchia(secret, body2)

    codice = _post_firmato(client, ROTTA_RESERVE, body2, firma_vecchia)
    assert codice == 401, (
        f"body-only: atteso 401, ottenuto {codice}"
    )


# --- 3. metodo diverso da quello firmato → 401 ---


def test_metodo_diverso_da_quello_firmato_e_401(
    client, create_player
) -> None:
    """Una firma calcolata con GET, mandata come POST, deve essere 401.

    CONTROLLO POSITIVO: prima si verifica che la firma con POST passa (200),
    poi che la firma con GET viene rifiutata (401).
    """
    player = create_player(prefix="3bE-method")
    payload = _payload_reserve(str(player["user_id"]))
    body = json.dumps(payload, separators=(",", ":")).encode()

    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None

    # POSITIVO: firma con POST accettata
    firma_post = _firma_corretta(secret, "POST", "wallet.reserve.v1", body)
    codice_ok = _post_firmato(client, ROTTA_RESERVE, body, firma_post)
    assert codice_ok == 200, f"positivo metodo: atteso 200, ottenuto {codice_ok}"

    # NEGATIVO: firma con GET invece di POST
    # Nuovo payload per evitare anti-rigioco
    payload2 = _payload_reserve(str(player["user_id"]))
    body2 = json.dumps(payload2, separators=(",", ":")).encode()
    firma_get = _firma_corretta(secret, "GET", "wallet.reserve.v1", body2)

    codice = _post_firmato(client, ROTTA_RESERVE, body2, firma_get)
    assert codice == 401, (
        f"wrong method: atteso 401, ottenuto {codice}"
    )


# --- 4. giro 2: confine rifiuta 401 su rotta non mappata ---


def test_confine_rotta_non_mappata_rifiuta_401() -> None:
    """Una rotta del confine NON mappata riceve 401 e l'handler non gira.

    Giro 2 (11/09/2026): sul codice 2d633be il confine delegava all'handler
    quando token_op era None. Un bypass totale della firma per rotte non
    mappate. Visto ROSSO: l'handler veniva eseguito e tornava 200.
    """
    from fastapi import FastAPI, APIRouter
    from fastapi.testclient import TestClient
    from app.api.v1.seamless.confine import RottaDelConfine

    handler_eseguito = False

    app = FastAPI()
    router = APIRouter(route_class=RottaDelConfine)

    @router.post("/prova-non-mappata")
    async def rotta_di_prova() -> dict:
        nonlocal handler_eseguito
        handler_eseguito = True
        return {"esito": "handler raggiunto"}

    app.include_router(router)
    tc = TestClient(app, raise_server_exceptions=False)

    risposta = tc.post(
        "/prova-non-mappata",
        json={"campo": "valore"},
        headers={
            "x-provider-id": "m-and-m-games",
            "x-signature-hmac": "firma-inventata",
        },
    )
    assert risposta.status_code == 401, (
        f"rotta non mappata: atteso 401, ottenuto {risposta.status_code}"
    )
    assert not handler_eseguito, (
        "L'handler e' stato eseguito nonostante la rotta non sia mappata"
    )


# --- 5. giro 2: mappa costruita dal prefisso di configurazione ---


def test_mappa_token_usa_prefisso_di_configurazione() -> None:
    """Le chiavi di TOKEN_OPERAZIONE_PER_ROTTA iniziano col prefisso configurato.

    Giro 2 (11/09/2026): la mappa aveva "/api/v1" hardcoded. Con un prefisso
    diverso (proxy, mount), request.url.path non avrebbe mai combaciato con
    le chiavi, e ogni rotta legittima avrebbe perso il token (401 o bypass).
    """
    from app.core.config import settings
    from app.modules.providers.auth import TOKEN_OPERAZIONE_PER_ROTTA

    prefisso_atteso = settings.api_v1_prefix.rstrip("/")
    for chiave in TOKEN_OPERAZIONE_PER_ROTTA:
        assert chiave.startswith(prefisso_atteso + "/"), (
            f"La chiave {chiave!r} non inizia col prefisso configurato "
            f"{prefisso_atteso!r}: la mappa e' hardcoded, non segue la config."
        )
