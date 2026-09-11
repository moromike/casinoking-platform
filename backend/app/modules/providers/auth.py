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

# 3bE — Token di operazione per rotta. La firma copre METODO\nTOKEN\nCORPO,
# non il percorso URL (che cambia con proxy, prefissi e alias). Il server
# verifica contro il token della rotta che ha RICEVUTO la richiesta, mai
# contro un token dichiarato dal client.
# I percorsi sono COMPLETI (prefisso /api/v1 incluso): il confronto e' esatto,
# non endswith. Un percorso che termina con lo stesso suffisso ma ha un
# prefisso diverso NON ottiene il token. (Revisione 3bE, 11/09/2026.)
TOKEN_OPERAZIONE_PER_ROTTA: dict[str, str] = {
    "/api/v1/seamless/wallet/reserve": "wallet.reserve.v1",
    "/api/v1/seamless/wallet/commit": "wallet.commit.v1",
    "/api/v1/seamless/wallet/rollback": "wallet.rollback.v1",
    "/api/v1/providers/launch/introspect": "launch.introspect.v1",
}


def token_da_percorso(percorso: str) -> str | None:
    """Risolve il token di operazione dal percorso della richiesta.

    Confronto esatto sul percorso completo (``request.url.path``). Torna
    ``None`` se il percorso non ha un token mappato.
    """
    return TOKEN_OPERAZIONE_PER_ROTTA.get(percorso)


def messaggio_firmato(metodo: str, token_operazione: str, corpo: bytes) -> bytes:
    """Il messaggio esatto che viene firmato: METODO\\nTOKEN\\nCORPO."""
    return f"{metodo}\n{token_operazione}\n".encode() + corpo


def identita_presunta(intestazione: str | None) -> str:
    """Chi dice di essere il chiamante, prima di qualunque verifica.

    Non e' un'autenticazione: e' solo la scelta della chiave con cui verificare.
    L'autenticazione la fa la firma.
    """
    # SOLO L'ASSENZA ATTIVA IL DEFAULT. FastAPI passa il default alla dipendenza
    # quando l'header manca, ma le passa "" quando l'header e' presente e vuoto.
    # Il 10/09/2026 `or` ha fatto divergere il confine dalla dipendenza: il primo
    # autenticava il presunto e prenotava il nonce, la seconda rifiutava "".
    return FORNITORE_PRESUNTO if intestazione is None else intestazione


def firma_valida(provider_id: str, messaggio: bytes, firma: str | None) -> bool:
    """La verifica HMAC sul messaggio firmato (METODO\\nTOKEN\\nCORPO).

    Il chiamante costruisce il messaggio con ``messaggio_firmato`` prima di
    passarlo qui. Senza FastAPI intorno, cosi' che possa usarla anche il
    confine PRIMA di scrivere qualunque cosa nel registro.
    """
    if not firma:
        return False
    secret = get_provider_secret(provider_id)
    if not secret:
        return False
    atteso = hmac.new(secret, messaggio, hashlib.sha256).hexdigest()
    return hmac.compare_digest(atteso, firma)


async def verify_provider_hmac(request: Request, x_provider_id: str = Header(default=FORNITORE_PRESUNTO), x_signature_hmac: str = Header(...)):
    secret = get_provider_secret(x_provider_id)
    if not secret:
        raise HTTPException(status_code=401, detail="Unknown provider")

    body = await request.body()
    token = token_da_percorso(request.url.path)
    if token is None:
        raise HTTPException(status_code=401, detail="Unknown route")
    msg = messaggio_firmato(request.method, token, body)
    expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, x_signature_hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    return x_provider_id
