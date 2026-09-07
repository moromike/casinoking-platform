motore: Claude
modello: claude-opus-5
modalita: scrittura non autonoma — PROPOSTA, non applicata
ruolo: proponente
data: 2026-09-07
revisione indipendente: Kimi K3 — due giri, entrambi DA CORREGGERE, entrambi recepiti
impegni: PRO-01, POR-02
perimetro: tutti e cinque i file sono nel perimetro protetto, modo MODIFICA

## Le impronte dei blocchi

Calcolate sui byte fra i marcatori, non dichiarate a mano. Chi rivede le ricalcola:

    sed -n '<prima riga dopo INIZIO>,<ultima riga prima di FINE>p' PROPOSTA.md | sha256sum

| File | sha256 |
|---|---|
| `backend/app/api/v1/seamless/router.py` | `a68b87eb8cc6c2fbc34182c1ab6b578cdb95aefdd046f666ec8c641cba9599c1` |
| `tests/integration/test_seamless_parita_contabile.py` | `ce2301d5289ee00cb94c14575d4a31521f67a33ae8031f6b56e78f083d77d002` |
| `tests/integration/test_seamless_scrive_davvero.py` | `aa73d7e9b0bec50e582189be3b31132e943832c8578b730dcfa6e179b807f7a0` |
| `tests/integration/test_seamless_ordine_operazioni.py` | `4fc5f78928d395c494a6bed5a28d9802680b216cf1572deba946bc1b494157fe` |
| `tests/integration/test_seamless_controlli_di_casa.py` | `9ff9b6c68d46b4a3379c58c721e8d0cafb6972d117b1e0d306dc97e9b4a0a412` |

# PROPOSTA — i campi obbligatori del protocollo entrano nel modello

## Cosa si propone, in una riga

Che le tre rotte che muovono denaro **smettano di accettare richieste incomplete**.

## Perche', e non e' teoria

I collaudi `test_seamless_campi_obbligatori.py`, eseguiti il 7/09/2026 sullo stack
acceso, hanno prodotto **sei rossi**. La causa non e' un controllo debole: **i campi non
esistono nel modello della richiesta**, e pydantic non puo' pretendere cio' che nessuno
ha dichiarato. Oggi le rotte accettano richieste prive di:

| Campo assente | Cosa vuol dire, in pratica |
|---|---|
| `currency` | non si sa in che valuta si sta muovendo il denaro |
| `provider_code` | l'identita' di chi chiede sta solo nell'intestazione, modificabile in transito |
| `timestamp` | la richiesta non invecchia: una intercettata oggi vale per sempre |
| `nonce` | non c'e' niente su cui appoggiare la difesa contro chi rispedisce la stessa richiesta |
| `reserve_tx_id` su `commit` | si puo' chiedere un accredito senza dire quale trattenuta chiude |
| `reserve_tx_id` su `rollback` | un annullamento che non dice cosa annulla risponde «riuscito» e muove i soldi |

L'ultima riga e' quella che pesa: e' l'inizio della strada per cui **la chiave di un
fornitore diventa una stampante di denaro**, che POR-02 chiama l'impegno piu' importante
della fase.

## Cosa cambia, file per file

**`backend/app/api/v1/seamless/router.py`** — un modello comune `_RichiestaSeamless` con i
campi che ogni richiesta deve portare, e i tre modelli esistenti che ereditano da lui.
**Nessun campo ha un valore predefinito:** un default trasformerebbe un dato mancante in
un dato inventato, e su un percorso che muove denaro un dato inventato e' peggio di un
errore. Aggiunto `extra="forbid"`, cosi' un campo di troppo si vede invece di essere
ignorato. **I tre gestori di rotta non sono toccati: nessuna logica contabile cambia.**

**I quattro file di collaudo** — i loro payload imparano a mandare i campi che diventano
obbligatori. Solo aggiunte: **nessuna asserzione viene cancellata, spostata o indebolita**,
e il conteggio degli `assert` resta identico prima e dopo, file per file (15/15, 16/16,
9/9, 3/3). E' il controllo che conta, perche' modificare un collaudo verde e' il modo
classico di far sparire copertura senza che si veda.

In tre di quei file la modifica ha una conseguenza che vale piu' della riga di codice:
`_open_reserve` **restituiva il numero della trattenuta e nessuno lo usava** — in
`test_seamless_controlli_di_casa.py` non lo restituiva nemmeno. Ora chi chiude una
trattenuta dice quale sta chiudendo, che e' esattamente cio' che la rotta comincia a
pretendere.

## Cosa NON copre

Dichiarare i campi obbligatori non e' ancora POR-03: la **firma** non copre ancora momento,
rotta e chiamante, e il confronto fra `provider_code` firmato e intestazione non c'e'.
`timestamp` non e' validato come data e `nonce` non ha controllo di unicita'. Questa
proposta rende quei campi obbligatori; **farli valere e' il passo dopo**, e il gate di fase
non deve trattare PRO-01 come anti-rigioco chiuso.

## Come ci si e' arrivati: due revisioni indipendenti, due buchi

**Prima revisione (Kimi, 7/09/2026, ore 10:26).** Verdetto **DA CORREGGERE**. La proposta
originale toccava il solo `router.py` e avrebbe fatto passare `test_seamless_parita_contabile.py`
— collaudo **verde** sul percorso del denaro — da 200 a 422. L'autore non se n'era accorto.
La correzione e' entrata come secondo blocco.

**Seconda revisione (Kimi, 7/09/2026, pomeriggio).** Verdetto **DA CORREGGERE** di nuovo, e
il rilievo era piu' grosso del primo: la correzione risanava un file, ma lo stesso problema
colpiva **altri tre file di collaudo**, nati nel secondo lotto dopo la prima revisione. I
loro payload di `commit` e `rollback` non conoscevano `reserve_tx_id`.

**Il conto di Kimi era pero' sbagliato per eccesso: diceva dieci collaudi rovinati.**
Verificato eseguendo la suite invece di leggerla: i collaudi **verdi** che sarebbero
diventati rossi erano **cinque**, non dieci — Kimi contava anche collaudi gia' rossi, che
non possono peggiorare. Gli altri sarebbero comunque passati a fallire per un motivo
sbagliato, che e' un difetto diverso e va detto: un collaudo che fallisce per 422 invece
che per il conflitto di stato che deve provare **nasconde il difetto vero**.

Il rilievo resta valido e blocca la firma finche' non e' chiuso. Questa stesura lo chiude
estendendo la proposta ai tre file.

## La misura, coi numeri, sullo stack acceso

Non e' un ragionamento: e' stata applicata in via provvisoria, misurata, e l'albero
riportato pulito.

| | prima | dopo |
|---|---|---|
| suite intera | **657 verdi, 19 rossi**, 232 saltati | **663 verdi, 13 rossi**, 232 saltati |
| `test_seamless_campi_obbligatori.py` | 6 rossi | **0 rossi** |
| collaudi passati da verde a rosso | — | **nessuno** |

I sei rossi che diventano verdi sono esattamente quelli che la proposta dichiara di voler
chiudere, uno per uno:

```
test_commit_rifiuta_reserve_tx_id_assente_senza_muovere_saldo
test_rollback_rifiuta_reserve_tx_id_assente_senza_muovere_saldo
test_reserve_rifiuta_ogni_campo_pro_01_assente_senza_muovere_saldo[currency]
test_reserve_rifiuta_ogni_campo_pro_01_assente_senza_muovere_saldo[nonce]
test_reserve_rifiuta_ogni_campo_pro_01_assente_senza_muovere_saldo[provider_code]
test_reserve_rifiuta_ogni_campo_pro_01_assente_senza_muovere_saldo[timestamp]
```

I tredici rossi che restano erano rossi anche prima, e sono i lotti B, C e D del mandato di
esecuzione: non e' questa proposta a doverli chiudere.

## Come si verifica, dopo la firma

```
./scripts/ck-test.sh tests/integration/test_seamless_campi_obbligatori.py -q     # 0 rossi
./scripts/ck-test.sh -q --tb=no                                                  # 663 verdi, 13 rossi
```
Se un collaudo verde diventa rosso, l'applicazione si ferma e si torna qui: e' la
condizione di arresto 5 del mandato di esecuzione, e non ha eccezioni.

---

--- INIZIO TESTO PROPOSTO: backend/app/api/v1/seamless/router.py ---
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
    PlatformRoundValidationError,
    PlatformRoundIdempotencyConflictError,
)
from app.modules.platform.catalog.service import CatalogNotFoundError, CatalogValidationError

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
                    title_code=title_code,
                    site_code="casinoking",
                )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after_start"]),
                    "already_exists": res.get("already_exists", False),
                }
            except PlatformRoundIdempotencyConflictError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PlatformRoundValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except (CatalogNotFoundError, CatalogValidationError) as e:
                raise HTTPException(status_code=400, detail=str(e))

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
                    )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after"]),
                    "already_exists": res.get("already_exists", False),
                }
            except PlatformRoundIdempotencyConflictError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PlatformRoundValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except (CatalogNotFoundError, CatalogValidationError) as e:
                raise HTTPException(status_code=400, detail=str(e))

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
                )
                conn.commit()
                return {
                    "status": "success",
                    "tx_id": req.tx_id,
                    "platform_round_id": res["platform_round_id"],
                    "balance_after": str(res["wallet_balance_after"]),
                    "already_exists": res.get("already_exists", False),
                }
            except PlatformRoundIdempotencyConflictError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PlatformRoundValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except (CatalogNotFoundError, CatalogValidationError) as e:
                raise HTTPException(status_code=400, detail=str(e))

--- FINE TESTO PROPOSTO ---

--- INIZIO TESTO PROPOSTO: tests/integration/test_seamless_parita_contabile.py ---
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
        "currency": "EUR",
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
        "currency": "EUR",
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

--- FINE TESTO PROPOSTO ---

--- INIZIO TESTO PROPOSTO: tests/integration/test_seamless_scrive_davvero.py ---
"""POR-06 — le risposte riuscite del seamless devono corrispondere al registro."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"
HOUSE_CASH_ACCOUNT = "HOUSE_CASH"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, amount: str | None = None,
             is_win: bool | None = None,
             reserve_tx_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id, "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE, "currency": "EUR", "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE, "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if is_win is not None:
        payload["is_win"] = is_win
    # LA TRATTENUTA CHE LA CHIUSURA CHIUDE (POR-02): obbligatoria su commit e
    # rollback, assente sulla reserve, che non chiude niente.
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(route, content=body, headers={
        "x-provider-id": PROVIDER_CODE,
        "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
        "Content-Type": "application/json",
    })


def _assert_entries(db_helpers, transaction_id: str, expected: set[tuple[str, str, Decimal]]) -> None:
    actual = {
        (str(entry["account_code"]), str(entry["entry_side"]), Decimal(entry["amount"]))
        for entry in db_helpers.get_transaction_entries(transaction_id)
    }
    assert actual == expected


def _open_reserve(client: Client, user_id: str, amount: str = "10.00") -> tuple[str, str]:
    game_session_id = str(uuid4())
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=game_session_id,
        tx_id=f"scrive-reserve-{uuid4().hex}", amount=amount,
    ))
    assert response.status_code == 200, response.text
    return game_session_id, str(response.json()["tx_id"])


def test_reserve_riuscita_scrive_puntata_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-reserve")
    user_id = str(player["user_id"])
    game_session_id, _tx_id = _open_reserve(client, user_id)

    transactions = db_helpers.get_game_transactions(game_session_id)
    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction["transaction_type"] == "bet"
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(transaction["id"]), {
        (str(wallet_row["account_code"]), "debit", Decimal("10.00")),
        (HOUSE_CASH_ACCOUNT, "credit", Decimal("10.00")),
    })


def test_commit_vincita_riuscita_scrive_accredito_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-win")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"scrive-win-{uuid4().hex}", amount="25.00", is_win=True,
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    win = [tx for tx in transactions if tx["transaction_type"] == "win"]
    assert len(win) == 1
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(win[0]["id"]), {
        (HOUSE_CASH_ACCOUNT, "debit", Decimal("25.00")),
        (str(wallet_row["account_code"]), "credit", Decimal("25.00")),
    })


def test_commit_perdita_riuscita_conserva_la_sola_puntata_nel_registro(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-loss")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"scrive-loss-{uuid4().hex}", amount="0.00", is_win=False,
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    assert [tx["transaction_type"] for tx in transactions] == ["bet"]
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(transactions[0]["id"]), {
        (str(wallet_row["account_code"]), "debit", Decimal("10.00")),
        (HOUSE_CASH_ACCOUNT, "credit", Decimal("10.00")),
    })


def test_rollback_riuscito_scrive_rimborso_sui_conti_giusti(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-ledger-rollback")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    response = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=f"scrive-rollback-{uuid4().hex}",
    ))
    assert response.status_code == 200, response.text

    transactions = db_helpers.get_game_transactions(game_session_id)
    rollback = [tx for tx in transactions if tx["transaction_type"] == "rollback"]
    assert len(rollback) == 1
    wallet_row = db_helpers.fetchone(
        "SELECT la.account_code FROM wallet_accounts wa JOIN ledger_accounts la ON la.id = wa.ledger_account_id WHERE wa.user_id = %s AND wa.wallet_type = %s",
        (user_id, WALLET_TYPE),
    )
    assert wallet_row is not None
    _assert_entries(db_helpers, str(rollback[0]["id"]), {
        (HOUSE_CASH_ACCOUNT, "debit", Decimal("10.00")),
        (str(wallet_row["account_code"]), "credit", Decimal("10.00")),
    })
--- FINE TESTO PROPOSTO ---

--- INIZIO TESTO PROPOSTO: tests/integration/test_seamless_ordine_operazioni.py ---
"""POR-04 — il portafoglio esterno rifiuta operazioni fuori ordine."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload(
    *,
    user_id: str,
    game_session_id: str,
    tx_id: str,
    amount: str | None = None,
    is_win: bool | None = None,
    reserve_tx_id: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id,
        "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE,
        "currency": "EUR",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if is_win is not None:
        payload["is_win"] = is_win
    # LA TRATTENUTA CHE LA CHIUSURA CHIUDE (POR-02): obbligatoria su commit e
    # rollback, assente sulla reserve, che non chiude niente.
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(
        route,
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
            "Content-Type": "application/json",
        },
    )


def _open_reserve(client: Client, user_id: str) -> tuple[str, str]:
    game_session_id = str(uuid4())
    tx_id = f"ordine-reserve-{uuid4().hex}"
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(user_id=user_id, game_session_id=game_session_id, tx_id=tx_id, amount="10.00"),
    )
    assert response.status_code == 200, response.text
    return game_session_id, tx_id


def _assert_rejected_without_balance_change(response, before: str, after: str) -> None:
    assert 400 <= response.status_code < 500, response.text
    assert after == before, "L'operazione rifiutata ha modificato il saldo del giocatore"


def test_reserve_su_partita_gia_conclusa_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-reserve-closed")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-close-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            tx_id=f"ordine-reserve-after-close-{uuid4().hex}",
            amount="10.00",
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_doppia_commit_identica_restituisce_prima_risposta_e_muove_denaro_una_sola_volta(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-duplicate-commit")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    payload = _payload(
        user_id=user_id,
        game_session_id=game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"ordine-duplicate-commit-{uuid4().hex}",
        amount="25.00",
        is_win=True,
    )

    first = _post(client, "/seamless/wallet/commit", payload)
    assert first.status_code == 200, first.text
    balance_after_first = db_helpers.get_wallet_balance(user_id)
    second = _post(client, "/seamless/wallet/commit", payload)
    balance_after_second = db_helpers.get_wallet_balance(user_id)

    assert second.status_code == 200, second.text
    assert second.json() == first.json()
    assert balance_after_second == balance_after_first
    transactions = db_helpers.get_game_transactions(game_session_id)
    assert [tx["transaction_type"] for tx in transactions].count("win") == 1


def test_commit_stesso_tx_id_importo_diverso_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-amount-conflict")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    tx_id = f"ordine-same-tx-{uuid4().hex}"
    first = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="25.00", is_win=True),
    )
    assert first.status_code == 200, first.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="26.00", is_win=True),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_commit_ripetuta_divergente_non_aggiorna_importo_in_silenzio(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-silent-update")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    tx_id = f"ordine-silent-update-{uuid4().hex}"
    first = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="25.00", is_win=True),
    )
    assert first.status_code == 200, first.text
    before = db_helpers.get_wallet_balance(user_id)

    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(user_id=user_id, game_session_id=game_session_id, reserve_tx_id=reserve_tx_id, tx_id=tx_id, amount="99.00", is_win=True),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)
    round_row = db_helpers.fetchone(
        "SELECT payout_amount FROM platform_rounds WHERE id = %s", (game_session_id,)
    )
    assert round_row is not None
    assert f"{round_row['payout_amount']:.6f}" == "25.000000"


def test_chiusura_in_perdita_su_partita_gia_conclusa_rifiutata_saldo_invariato(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="seamless-order-loss-after-close")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-win-before-loss-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-loss-after-close-{uuid4().hex}",
            amount="0.00",
            is_win=False,
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)


def test_conflitto_di_stato_risponde_4xx_mai_500(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-order-state-conflict")
    user_id = str(player["user_id"])
    game_session_id, reserve_tx_id = _open_reserve(client, user_id)
    closed = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-close-before-conflict-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    assert closed.status_code == 200, closed.text

    before = db_helpers.get_wallet_balance(user_id)
    response = _post(
        client,
        "/seamless/wallet/commit",
        _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            reserve_tx_id=reserve_tx_id,
            tx_id=f"ordine-state-conflict-{uuid4().hex}",
            amount="25.00",
            is_win=True,
        ),
    )
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(response, before, after)
--- FINE TESTO PROPOSTO ---

--- INIZIO TESTO PROPOSTO: tests/integration/test_seamless_controlli_di_casa.py ---
"""POR-07 e REG-02 — il seamless eredita i controlli di casa senza bloccare sessioni aperte."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, amount: str | None = None,
             currency: str = "EUR", is_win: bool | None = None,
             reserve_tx_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id, "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE, "currency": currency, "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE, "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if is_win is not None:
        payload["is_win"] = is_win
    # LA TRATTENUTA CHE LA CHIUSURA CHIUDE (POR-02): obbligatoria su commit e
    # rollback, assente sulla reserve, che non chiude niente.
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(route, content=body, headers={
        "x-provider-id": PROVIDER_CODE,
        "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
        "Content-Type": "application/json",
    })


def _assert_rejected_without_balance_change(response, before: str, after: str) -> None:
    assert 400 <= response.status_code < 500, response.text
    assert after == before, "Il rifiuto ha modificato il saldo del giocatore"


def _set_player_status(db_connection, user_id: str, status: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("UPDATE users SET status = %s WHERE id = %s", (status, user_id))


def _open_reserve(client: Client, user_id: str, game_session_id: str) -> str:
    """Restituisce il tx_id della trattenuta aperta.

    Prima lo buttava via. Con reserve_tx_id obbligatorio su commit e rollback
    (POR-02) chi chiude deve dire QUALE trattenuta sta chiudendo, e quel dato
    puo' arrivare solo da qui.
    """
    tx_id = f"controlli-reserve-{uuid4().hex}"
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=game_session_id,
        tx_id=tx_id, amount="10.00",
    ))
    assert response.status_code == 200, response.text
    return tx_id


def test_valuta_diversa_da_quella_del_conto_rifiutata_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-currency")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"wrong-currency-{uuid4().hex}",
        amount="10.00", currency="USD",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_saldo_insufficiente_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-balance")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"insufficient-{uuid4().hex}", amount="1000.01",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_importo_sotto_minimo_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-minimum")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"below-minimum-{uuid4().hex}", amount="0.00",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_importo_sopra_massimo_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-maximum")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"above-maximum-{uuid4().hex}", amount="999.99",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_reg02_sospensione_non_blocca_sessione_aperta_ma_blocca_sessione_nuova(
    client, create_player, db_connection, db_helpers
) -> None:
    """I casi 1--4 sono sequenziali per rendere verificabile il legame fra le due sessioni."""
    player = create_player(prefix="seamless-reg02")
    user_id = str(player["user_id"])
    existing_game_session_id = str(uuid4())

    # Caso 1: trattenuta aperta, poi sospensione: la commit deve ancora passare.
    reserve_tx_id = _open_reserve(client, user_id, existing_game_session_id)
    _set_player_status(db_connection, user_id, "suspended")
    commit = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=existing_game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"reg02-commit-open-session-{uuid4().hex}", amount="25.00", is_win=True,
    ))
    assert commit.status_code == 200, commit.text

    # Caso 2: STESSA game_session_id del caso 1; una nuova trattenuta deve passare.
    same_game_session_id = existing_game_session_id
    assert same_game_session_id == existing_game_session_id
    reserve_in_existing_session = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=same_game_session_id,
        tx_id=f"reg02-reserve-existing-session-{uuid4().hex}", amount="10.00",
    ))
    assert reserve_in_existing_session.status_code == 200, reserve_in_existing_session.text

    # Caso 3: trattenuta aperta, giocatore sospeso, rollback deve passare.
    rollback_game_session_id = str(uuid4())
    _set_player_status(db_connection, user_id, "active")
    rollback_reserve_tx_id = _open_reserve(client, user_id, rollback_game_session_id)
    _set_player_status(db_connection, user_id, "suspended")
    rollback = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id, game_session_id=rollback_game_session_id,
        reserve_tx_id=rollback_reserve_tx_id,
        tx_id=f"reg02-rollback-open-session-{uuid4().hex}",
    ))
    assert rollback.status_code == 200, rollback.text

    # Caso 4: game_session_id DIVERSO: una sessione nuova e' rifiutata e non muove saldo.
    new_game_session_id = str(uuid4())
    assert new_game_session_id != existing_game_session_id
    before = db_helpers.get_wallet_balance(user_id)
    new_session = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=new_game_session_id,
        tx_id=f"reg02-reserve-new-session-{uuid4().hex}", amount="10.00",
    ))
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(new_session, before, after)
--- FINE TESTO PROPOSTO ---
