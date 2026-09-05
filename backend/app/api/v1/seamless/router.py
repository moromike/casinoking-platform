"""Seamless Wallet — ABBOZZO NON COLLEGATO AL LIBRO MASTRO.

ATTENZIONE, LEGGERE PRIMA DI USARE QUESTI ENDPOINT.

Queste rotte **non toccano nessun conto**. Non chiamano il ledger, non leggono un
saldo, non conoscono nemmeno il giocatore: il corpo della richiesta contiene solo
`tx_id` e un importo, quindi non e' definito di chi siano i soldi. Fino al
4/09/2026 rispondevano `balance_after: 100.0` fisso con un `# TODO` accanto, mentre
un rapporto di consegna dichiarava che il provider "preleva e versa soldi veri".
Il client firmava davvero, ma dall'altro capo non succedeva niente.

Perche' allora esistono ancora: la firma HMAC in ingresso (PLAT-12) e' vera e va
tenuta viva, ed e' l'unico pezzo della Fase 4 che regge. Completare il collegamento
al ledger — con il giocatore nel corpo della richiesta e una difesa contro il
rinvio della stessa richiesta firmata — e' lavoro dello sviluppo giochi, non di
questa bonifica.

Perche' sono SPENTE per difetto: un abbozzo che risponde "success" e' peggio di una
rotta assente, perche' chi lo prova conclude che funziona. Si accendono solo
dichiarandolo, e mai in produzione.
"""

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from decimal import Decimal

from app.core.config import settings
from app.modules.providers.auth import verify_provider_hmac

router = APIRouter(prefix="/seamless", tags=["Seamless Wallet (abbozzo)"])


def abbozzo_consentito() -> None:
    """Rifiuta la chiamata se l'abbozzo non e' stato acceso di proposito."""
    if settings.app_env in ("production", "prod"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Seamless Wallet e' un abbozzo che non tocca nessun conto: "
                "non e' utilizzabile in produzione."
            ),
        )
    if os.environ.get("SEAMLESS_STUB_ATTIVO", "").lower() not in ("1", "true", "si"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Seamless Wallet e' un abbozzo e non movimenta denaro. Per usarlo in "
                "sviluppo serve SEAMLESS_STUB_ATTIVO=1, cosi' nessuno lo scambia per "
                "un portafoglio funzionante."
            ),
        )


class ReserveRequest(BaseModel):
    tx_id: str
    amount: Decimal


class CommitRequest(BaseModel):
    tx_id: str
    amount: Decimal
    is_win: bool


class RollbackRequest(BaseModel):
    tx_id: str


_DIPENDENZE = [Depends(verify_provider_hmac), Depends(abbozzo_consentito)]


@router.post("/wallet/reserve", dependencies=_DIPENDENZE)
def reserve_funds(req: ReserveRequest) -> dict:
    # ABBOZZO: nessun conto viene toccato. Impegno aperto per il collegamento reale.
    return {"status": "abbozzo", "nessun_conto_toccato": True, "tx_id": req.tx_id}


@router.post("/wallet/commit", dependencies=_DIPENDENZE)
def commit_funds(req: CommitRequest) -> dict:
    # ABBOZZO: nessun conto viene toccato.
    return {"status": "abbozzo", "nessun_conto_toccato": True, "tx_id": req.tx_id}


@router.post("/wallet/rollback", dependencies=_DIPENDENZE)
def rollback_funds(req: RollbackRequest) -> dict:
    # ABBOZZO: nessun conto viene toccato.
    return {"status": "abbozzo", "nessun_conto_toccato": True, "tx_id": req.tx_id}
