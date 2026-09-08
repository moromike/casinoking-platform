import pytest
from decimal import Decimal
import hmac
import hashlib
import json
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
        "timestamp": "2026-09-07T12:00:00Z",
        "nonce": "parita-reserve-001",
    }
    
    # Firma HMAC
    # get_provider_secret("ck_collaudo") -> vediamo come prenderlo, o lo fissiamo nel config?
    # default in test env is probably something known. Let's see auth_service.
    from app.modules.providers.auth import get_provider_secret
    secret = get_provider_secret("ck_collaudo")
    
    body_res = json.dumps(reserve_payload).encode()
    signature = hmac.new(secret, body_res, hashlib.sha256).hexdigest()
    
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
        "timestamp": "2026-09-07T12:00:05Z",
        "nonce": "parita-commit-001",
        # la trattenuta che questa chiusura chiude: e' il campo che impedisce
        # di farsi accreditare senza aver mai puntato.
        "reserve_tx_id": "tx_res_001",
        "is_win": True
    }
    body_com = json.dumps(commit_payload).encode()
    signature_com = hmac.new(secret, body_com, hashlib.sha256).hexdigest()
    
    res_com = client.post(
        "/seamless/wallet/commit",
        content=body_com,
        headers={"x-provider-id": "ck_collaudo", "x-signature-hmac": signature_com, "Content-Type": "application/json"}
    )
    assert res_com.status_code == 200, res_com.text
    
    data = res_com.json()
    assert Decimal(data["balance_after"]) == Decimal("1015.00")
