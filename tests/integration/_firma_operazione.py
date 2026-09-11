"""3bE — Firma per operazione: helper centralizzato per i collaudi.

Il messaggio firmato e' ``METODO \\n TOKEN-OPERAZIONE \\n CORPO``.
Il token di operazione e' dichiarato per rotta, e il server verifica contro
il token della rotta che ha RICEVUTO la richiesta.

La mappa canonical vive in ``auth.py`` (TOKEN_OPERAZIONE_PER_ROTTA); questo
modulo la riesporta e aggiunge le funzioni di comodita' per i collaudi.
"""

from __future__ import annotations

import hashlib
import hmac

from app.modules.providers.auth import (
    TOKEN_OPERAZIONE_PER_ROTTA,
    messaggio_firmato,
    token_da_percorso,
)

__all__ = [
    "TOKEN_OPERAZIONE_PER_ROTTA",
    "messaggio_firmato",
    "token_da_percorso",
    "firma_operazione",
    "intestazioni_firmate",
]


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
