import os
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.modules.providers.auth import verify_provider_hmac
from app.db.connection import db_connection
from app.modules.platform.rounds.service import (
    open_game_round,
    settle_game_round_win,
    settle_game_round_loss,
    rollback_game_round,
    PlatformRoundInsufficientBalanceError,
    PlatformRoundIdempotencyConflictError,
    PlatformRoundNotFoundError,
    PlatformRoundCurrencyMismatchError,
    PlatformRoundAmountBelowMinimumError,
    PlatformRoundAmountAboveMaximumError,
    PlatformRoundStateConflictError,
    PlatformRoundGameCodeInvalidError,
    PlatformRoundIdempotencyKeyTooLongError,
    PlatformRoundReserveTransactionMismatchError,
)
from app.modules.platform.catalog.service import CatalogNotFoundError, CatalogProviderSuspendedError
from app.modules.platform.table_sessions.service import (
    TableSessionInsufficientBalanceError,
    TableSessionLimitExceededError,
)
from app.api.errors import build_error_payload
from app.api.v1.seamless.errors import translate_seamless_error

router = APIRouter(prefix="/seamless", tags=["Seamless Wallet"])

def fuori_produzione() -> None:
    """Blocca le rotte del portafoglio fornitore in produzione.

    PERCHE' RESTA, ORA CHE LE ROTTE SONO VERE: prima proteggeva da un abbozzo
    che rispondeva "success" senza toccare niente. Ora protegge dal contrario —
    tre rotte che muovono denaro vero con una chiave condivisa, mentre gli
    impegni POR-02 (accredito senza trattenuta), POR-03 (firma legata a momento
    e rotta), POR-05 (fornitore sospeso) e POR-07 (controlli di casa) NON sono
    ancora implementati. Finche' mancano, chi ha la chiave puo' farsi accreditare
    quello che vuole: la porta resta chiusa in produzione.
    """
    if settings.app_env in ("production", "prod"):
        raise HTTPException(
            status_code=503,
            detail="Seamless Wallet non e' abilitato in produzione.",
        )

# I CAMPI DEL PROTOCOLLO, DICHIARATI UNA VOLTA SOLA (PRO-01).
# Fino al 7/09/2026 currency, provider_code, timestamp e nonce NON ESISTEVANO in
# questi modelli: una richiesta che li ometteva veniva accettata, perche' pydantic
# non puo' pretendere un campo che nessuno ha dichiarato. Non era un controllo
# debole, era un controllo assente. Lo hanno dimostrato i collaudi di
# test_seamless_campi_obbligatori.py, non una lettura del codice.
class _RichiestaSeamless(BaseModel):
    """Cio' che OGNI richiesta esterna deve portare. Nessun campo ha un default:
    un default trasformerebbe un dato mancante in un dato inventato, e su un
    percorso che muove denaro un dato inventato e' peggio di un errore."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    game_session_id: str
    game_code: str
    wallet_type: str
    tx_id: str
    # provider_code viaggia DENTRO la richiesta, non solo nell'intestazione:
    # l'intestazione sceglie la chiave con cui verificare, ma l'identita' che vale
    # e' quella firmata. Se non coincidono si rifiuta (POR-03).
    provider_code: str
    # la valuta non si desume dal conto: una valuta diversa si RIFIUTA, non si
    # converte, ed e' fuori scope convertirla.
    currency: str
    # senza momento la richiesta non invecchia mai: una intercettata oggi resta
    # valida per sempre.
    timestamp: str
    # su cui vive l'anti-rigioco. Distinto da tx_id, che e' l'anti-doppione.
    nonce: str

class ReserveRequest(_RichiestaSeamless):
    amount: Decimal

class CommitRequest(_RichiestaSeamless):
    amount: Decimal
    is_win: bool
    # LA TRATTENUTA CHE QUESTA CHIUSURA CHIUDE (POR-02).
    # Senza, "accredita mille euro" e' una richiesta valida per chiunque abbia la
    # chiave del fornitore: la chiave diventa una stampante di denaro. E' il campo
    # che lega la chiusura alla trattenuta, e la piattaforma lo confronta con
    # quello conservato sulla partita.
    reserve_tx_id: str

class RollbackRequest(_RichiestaSeamless):
    # obbligatorio anche qui: un annullamento che non dice QUALE trattenuta sta
    # annullando oggi risponde "riuscito" e muove i soldi. Provato sul campo.
    reserve_tx_id: str

# PERCHE' LA GUARDIA E' QUI E NON NELLE SINGOLE ROTTE: cosi' una rotta nuova
# aggiunta domani la eredita senza che nessuno debba ricordarsene.
# L'HMAC non si ripete: ogni rotta lo prende gia' con Depends(verify_provider_hmac)
# nella propria firma, perche' le serve il provider_code che ne esce.
_DIPENDENZE = [Depends(fuori_produzione)]

_SEAMLESS_DOMAIN_ERRORS = (
    PlatformRoundInsufficientBalanceError,
    PlatformRoundIdempotencyConflictError,
    PlatformRoundNotFoundError,
    PlatformRoundCurrencyMismatchError,
    PlatformRoundAmountBelowMinimumError,
    PlatformRoundAmountAboveMaximumError,
    PlatformRoundStateConflictError,
    PlatformRoundGameCodeInvalidError,
    PlatformRoundIdempotencyKeyTooLongError,
    PlatformRoundReserveTransactionMismatchError,
    CatalogNotFoundError,
    CatalogProviderSuspendedError,
    TableSessionInsufficientBalanceError,
    TableSessionLimitExceededError,
)


def _raise_translated_seamless_error(
    exc: Exception, translation: tuple[int, str] | None
) -> None:
    if translation is None:
        raise exc
    status_code, code = translation
    raise HTTPException(status_code=status_code, detail=build_error_payload(code=code))

@router.post("/wallet/reserve", dependencies=_DIPENDENZE)
def reserve_funds(req: ReserveRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
    idempotency_key = f"{provider_code}:reserve:{req.tx_id}"
    
    with db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT provider_code FROM game_engines WHERE engine_code = %s", (req.game_code,))
                row = cursor.fetchone()
                if not row or row["provider_code"] != provider_code:
                    raise HTTPException(status_code=403, detail="Game code does not belong to provider")

                cursor.execute("SELECT title_code FROM game_titles WHERE engine_code = %s LIMIT 1", (req.game_code,))
                title_row = cursor.fetchone()
                if not title_row:
                    raise HTTPException(status_code=400, detail="No title for game code")
                title_code = title_row["title_code"]

                res = open_game_round(
                    cursor=cursor,
                    game_code=req.game_code,
                    user_id=req.user_id,
                    game_session_id=req.game_session_id,
                    idempotency_key=idempotency_key,
                    grid_size=0,
                    mine_count=0,
                    bet_amount=req.amount,
                    wallet_type=req.wallet_type,
                    currency=req.currency,
                    title_code=title_code,
                    site_code="casinoking",
                    seamless_request=True,
                )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after_start"]),
                    "already_exists": res.get("already_exists", False),
                }
            except _SEAMLESS_DOMAIN_ERRORS as exc:
                _raise_translated_seamless_error(exc, translate_seamless_error(exc))

@router.post("/wallet/commit", dependencies=_DIPENDENZE)
def commit_funds(req: CommitRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
    idempotency_key = f"{provider_code}:commit:{req.tx_id}"
    
    with db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT provider_code FROM game_engines WHERE engine_code = %s", (req.game_code,))
                row = cursor.fetchone()
                if not row or row["provider_code"] != provider_code:
                    raise HTTPException(status_code=403, detail="Game code does not belong to provider")

                if req.is_win:
                    # PERCHE' payout_amount E NON win_amount: la firma della
                    # piattaforma parla di "payout". safe_reveals_count e' un dato
                    # del gioco Mines che il percorso esterno non ha: si passa 0,
                    # perche' finisce solo nei metadati di avanzamento.
                    res = settle_game_round_win(
                        cursor=cursor,
                        game_code=req.game_code,
                        user_id=req.user_id,
                        game_session_id=req.game_session_id,
                        idempotency_key=idempotency_key,
                        payout_amount=req.amount,
                        safe_reveals_count=0,
                        seamless_request=True,
                        currency=req.currency,
                        reserve_idempotency_key=f"{provider_code}:reserve:{req.reserve_tx_id}",
                    )
                else:
                    # PERCHE' SENZA idempotency_key: settle_game_round_loss non
                    # lo accetta. La perdita non muove denaro nuovo (la puntata e'
                    # gia' stata addebitata alla trattenuta), quindi non apre una
                    # scrittura nuova da proteggere con una chiave.
                    res = settle_game_round_loss(
                        cursor=cursor,
                        game_code=req.game_code,
                        user_id=req.user_id,
                        game_session_id=req.game_session_id,
                        safe_reveals_count=0,
                        seamless_request=True,
                        currency=req.currency,
                        reserve_idempotency_key=f"{provider_code}:reserve:{req.reserve_tx_id}",
                    )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after"]),
                    "already_exists": res.get("already_exists", False),
                }
            except _SEAMLESS_DOMAIN_ERRORS as exc:
                _raise_translated_seamless_error(exc, translate_seamless_error(exc))

@router.post("/wallet/rollback", dependencies=_DIPENDENZE)
def rollback_funds(req: RollbackRequest, provider_code: str = Depends(verify_provider_hmac)) -> dict:
    idempotency_key = f"{provider_code}:rollback:{req.tx_id}"
    
    with db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT provider_code FROM game_engines WHERE engine_code = %s", (req.game_code,))
                row = cursor.fetchone()
                if not row or row["provider_code"] != provider_code:
                    raise HTTPException(status_code=403, detail="Game code does not belong to provider")

                res = rollback_game_round(
                    cursor=cursor,
                    game_code=req.game_code,
                    user_id=req.user_id,
                    game_session_id=req.game_session_id,
                    idempotency_key=idempotency_key,
                    seamless_request=True,
                    currency=req.currency,
                    reserve_idempotency_key=f"{provider_code}:reserve:{req.reserve_tx_id}",
                )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after"]),
                    "already_exists": res.get("already_exists", False),
                }
            except _SEAMLESS_DOMAIN_ERRORS as exc:
                _raise_translated_seamless_error(exc, translate_seamless_error(exc))
