import hmac
import hashlib
from fastapi import Request, HTTPException, Header, Depends
from .registry import get_provider_secret

# IL FORNITORE PRESUNTO QUANDO L'INTESTAZIONE MANCA.
# Sta qui, in una costante sola, perche' il 10/09/2026 e' costato un buco:
# i controlli del confine (POR-03) leggevano l'intestazione per conto loro e, se
# mancava, lasciavano passare la richiesta senza verificare niente — mentre QUESTA
# funzione le assegnava comunque questo default e la autenticava. Bastava omettere
# l'intestazione per saltare identita', momento e anti-rigioco.
# Due punti che risolvono la stessa identita' in modi diversi sono un buco che
# aspetta: da qui in avanti la risolve una funzione sola.
FORNITORE_PRESUNTO = "m-and-m-games"


def identita_presunta(intestazione: str | None) -> str:
    """Chi dice di essere il chiamante, prima di qualunque verifica.

    Non e' un'autenticazione: e' solo la scelta della chiave con cui verificare.
    L'autenticazione la fa la firma.
    """
    return intestazione or FORNITORE_PRESUNTO


def firma_valida(provider_id: str, corpo: bytes, firma: str | None) -> bool:
    """La verifica HMAC, senza FastAPI intorno, cosi' che possa usarla anche il
    confine PRIMA di scrivere qualunque cosa nel registro."""
    if not firma:
        return False
    secret = get_provider_secret(provider_id)
    if not secret:
        return False
    atteso = hmac.new(secret, corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(atteso, firma)


async def verify_provider_hmac(request: Request, x_provider_id: str = Header(default=FORNITORE_PRESUNTO), x_signature_hmac: str = Header(...)):
    secret = get_provider_secret(x_provider_id)
    if not secret:
        raise HTTPException(status_code=401, detail="Unknown provider")
        
    body = await request.body()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected, x_signature_hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")
        
    return x_provider_id
