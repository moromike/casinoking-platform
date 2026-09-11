"""3bE — Firma per operazione: helper centralizzato per i collaudi.

Il messaggio firmato e' ``METODO \\n TOKEN-OPERAZIONE \\n CORPO``.
Il token di operazione e' dichiarato per rotta, e il server verifica contro
il token della rotta che ha RICEVUTO la richiesta.

La mappa canonical vive in ``auth.py`` (TOKEN_OPERAZIONE_PER_ROTTA); questo
modulo la riesporta e aggiunge le funzioni di comodita' per i collaudi.

Revisione 3bE giro 1 (11/09/2026): la risoluzione del token dalla rotta sta
qui e fa ``assert token is not None``. I file migrati la usano invece di
ripeterla.
"""

from __future__ import annotations

import hashlib
import hmac

from app.core.config import settings
from app.modules.providers.auth import (
    TOKEN_OPERAZIONE_PER_ROTTA,
    messaggio_firmato,
    token_da_percorso as _token_da_percorso_server,
)

__all__ = [
    "TOKEN_OPERAZIONE_PER_ROTTA",
    "messaggio_firmato",
    "token_da_percorso",
    "firma_operazione",
    "intestazioni_firmate",
]


def token_da_percorso(rotta: str) -> str:
    """Risolve il token di operazione per i collaudi.

    Accetta sia il percorso corto (``/seamless/wallet/reserve``) sia quello
    completo (``/api/v1/seamless/wallet/reserve``). Aggiunge il prefisso
    dall'impostazione di piattaforma, poi delega alla funzione del server.

    Solleva ``AssertionError`` se la rotta non ha un token mappato: un token
    ``None`` produrrebbe una firma silenziosamente sbagliata, mascherando un
    errore del collaudo come un 401 del server.
    """
    prefisso = settings.api_v1_prefix.rstrip("/")
    percorso = rotta if rotta.startswith(prefisso) else f"{prefisso}{rotta}"
    token = _token_da_percorso_server(percorso)
    assert token is not None, (
        f"Nessun token di operazione per la rotta {rotta!r} "
        f"(percorso completo: {percorso!r})"
    )
    return token


def firma_operazione(
    secret: bytes, metodo: str, token_operazione: str, corpo: bytes
) -> str:
    """Calcola l'HMAC-SHA256 del messaggio firmato."""
    msg = messaggio_firmato(metodo, token_operazione, corpo)
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def intestazioni_firmate(
    provider_id: str,
    secret: bytes,
    metodo: str,
    token_operazione: str,
    corpo: bytes,
) -> dict[str, str]:
    """Le tre intestazioni che il fornitore manda con ogni richiesta."""
    return {
        "x-provider-id": provider_id,
        "x-signature-hmac": firma_operazione(
            secret, metodo, token_operazione, corpo
        ),
        "Content-Type": "application/json",
    }
