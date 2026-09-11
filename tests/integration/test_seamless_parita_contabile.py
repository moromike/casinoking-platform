import pytest
from decimal import Decimal
import hmac
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4
from httpx import AsyncClient

# Uses manichino provider 'ck_collaudo'

def test_parita_contabile(db_helpers, db_connection, client, create_player):
    # Dobbiamo creare un giocatore e avere fondi
    user = create_player(prefix="seamless")
    
    # Prepariamo la richiesta Reserve
    reserve_payload = {
        "user_id": user["user_id"],
        "game_session_id": "a4fc741e-0c57-4632-8eff-9204556bc74f",
        "game_code": "manichino",
        "wallet_type": "cash",
        "tx_id": "tx_res_001",
        "amount": "10.0",
        # I quattro campi di protocollo diventano obbligatori con la proposta
        # "campi obbligatori": senza, questa richiesta riceverebbe 422 e il
        # collaudo di parita' - verde da ieri - diventerebbe rosso per un motivo
        # che non c'entra niente con la parita' contabile.
        "provider_code": "ck_collaudo",
        "currency": "CHIP",
        # ERA FISSO AL 7/09/2026, E DAL 10/09 CADE FUORI DALLA FINESTRA.
        # POR-03 introduce il controllo del momento (confine.py:76-110): un
        # timestamp scritto nel sorgente invecchia da solo e rende rosso un
        # collaudo verde, senza che nessuno abbia rotto niente. Ora e' l'ora
        # della corsa. Cio' che il collaudo PRETENDE non cambia di una virgola:
        # la parita' contabile e' verificata esattamente come prima.
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # ERA FISSO, E RENDEVA IL COLLAUDO NON RIPETIBILE. Con POR-03 il nonce
        # e' registrato: la prima corsa passava, la seconda trovava il nonce
        # gia' usato e diventava rossa. Un collaudo che passa una volta sola
        # non e' un collaudo. Trovato lanciando la suite due volte, non
        # rileggendola.
        "nonce": f"parita-reserve-{uuid4().hex}",
    }
    
    # Firma HMAC
    # get_provider_secret("ck_collaudo") -> vediamo come prenderlo, o lo fissiamo nel config?
    # default in test env is probably something known. Let's see auth_service.
    from app.modules.providers.auth import get_provider_secret
    secret = get_provider_secret("ck_collaudo")
    
    from tests.integration._firma_operazione import firma_operazione

    body_res = json.dumps(reserve_payload).encode()
    signature = firma_operazione(secret, "POST", "wallet.reserve.v1", body_res)

    res = client.post(
        "/seamless/wallet/reserve",
        content=body_res,
        headers={"x-provider-id": "ck_collaudo", "x-signature-hmac": signature, "Content-Type": "application/json"}
    )
    assert res.status_code == 200, res.text
    
    # Commit
    commit_payload = {
        "user_id": user["user_id"],
        "game_session_id": "a4fc741e-0c57-4632-8eff-9204556bc74f",
        "game_code": "manichino",
        "wallet_type": "cash",
        "tx_id": "tx_com_001",
        "amount": "25.0",
        "provider_code": "ck_collaudo",
        "currency": "CHIP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": f"parita-commit-{uuid4().hex}",
        # la trattenuta che questa chiusura chiude: e' il campo che impedisce
        # di farsi accreditare senza aver mai puntato.
        "reserve_tx_id": "tx_res_001",
        "is_win": True
    }
    body_com = json.dumps(commit_payload).encode()
    signature_com = firma_operazione(secret, "POST", "wallet.commit.v1", body_com)

    res_com = client.post(
        "/seamless/wallet/commit",
        content=body_com,
        headers={"x-provider-id": "ck_collaudo", "x-signature-hmac": signature_com, "Content-Type": "application/json"}
    )
    assert res_com.status_code == 200, res_com.text
    
    data = res_com.json()
    assert Decimal(data["balance_after"]) == Decimal("1015.00")
