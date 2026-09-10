"""POR-03 — l'identita' dichiarata, il momento della richiesta e il rigioco.

I TRE COLLAUDI CHE NON POTEVANO FALLIRE, E PERCHE' ORA POSSONO.
Fino al 10/09/2026 `provider_code`, `timestamp` e `nonce` erano dichiarati
obbligatori nel protocollo e non letti da nessuno: `grep req.provider_code
router.py` -> 0. Erano campi che sembravano controlli di sicurezza senza esserlo.

QUESTI COLLAUDI SI SONO VISTI FALLIRE PRIMA DEL CODICE. Le uscite rosse stanno in
artifacts/passo3/rossi-prima/. Su questo progetto il gate e' stato verde quattro
volte su codice con difetti veri: un collaudo mai visto rosso non prova niente.

COSA NON PROVANO, dichiarato qui perche' non si perda: la firma non copre la
ROTTA. Legarla cambierebbe cio' che il fornitore deve firmare, ed e' una
decisione di Michele, non tecnica. POR-03 e' chiusa per identita' e momento, non
per rotta.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret

pytestmark = [pytest.mark.integration]

PROVIDER_CODE = "ck_collaudo"
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload(*, user_id: str, game_session_id: str, tx_id: str,
             amount: str | None = None, provider_code: str = PROVIDER_CODE,
             timestamp: str | None = None, nonce: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id,
        "game_session_id": game_session_id,
        "provider_code": provider_code,
        "currency": "CHIP",
        "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE,
        "tx_id": tx_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "nonce": nonce or uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    """Firma con la chiave scelta dall'INTESTAZIONE, come fa un fornitore vero."""
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata"
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return client.post(
        route,
        content=body,
        headers={
            "x-provider-id": PROVIDER_CODE,
            "x-signature-hmac": signature,
            "Content-Type": "application/json",
        },
    )


# ---------------------------------------------------------------- L1: identita'

def test_reserve_rifiuta_provider_code_diverso_da_quello_della_firma(
    client, create_player, db_helpers
) -> None:
    """L1 — il corpo dice di essere un altro fornitore: si rifiuta.

    La firma e' valida (la chiave e' quella di ck_collaudo, scelta
    dall'intestazione), ma il corpo dichiara un fornitore diverso. Il commento
    del codice prometteva questo rifiuto da giorni senza farlo.
    """
    player = create_player(prefix="por03-identita")
    user_id = str(player["user_id"])
    saldo_prima = db_helpers.get_wallet_balance(user_id)

    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=str(uuid4()),
            tx_id=f"por03-identita-{uuid4().hex}",
            amount="10.00",
            provider_code="un_altro_fornitore",
        ),
    )

    assert response.status_code in (401, 403), response.text
    assert response.status_code != 500, "un rifiuto non e' un guasto del server"
    assert db_helpers.get_wallet_balance(user_id) == saldo_prima, (
        "una richiesta rifiutata non deve muovere il saldo"
    )


# ------------------------------------------------------------------ L2: momento

def test_reserve_rifiuta_una_richiesta_troppo_vecchia(
    client, create_player, db_helpers
) -> None:
    """L2 — senza momento, una richiesta intercettata resta valida per sempre."""
    player = create_player(prefix="por03-vecchia")
    user_id = str(player["user_id"])
    saldo_prima = db_helpers.get_wallet_balance(user_id)
    vecchio = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=str(uuid4()),
            tx_id=f"por03-vecchia-{uuid4().hex}",
            amount="10.00",
            timestamp=vecchio,
        ),
    )

    assert response.status_code in (401, 403), response.text
    assert db_helpers.get_wallet_balance(user_id) == saldo_prima


def test_reserve_rifiuta_un_timestamp_senza_fuso_orario(
    client, create_player
) -> None:
    """D7 — il fuso di un terzo non si indovina: senza timezone si rifiuta."""
    player = create_player(prefix="por03-nofuso")
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=str(player["user_id"]),
            game_session_id=str(uuid4()),
            tx_id=f"por03-nofuso-{uuid4().hex}",
            amount="10.00",
            timestamp="2026-09-10T13:00:00",
        ),
    )
    assert response.status_code in (401, 403, 422), response.text


def test_reserve_accetta_una_richiesta_di_adesso(client, create_player) -> None:
    """IL CONTROLLO CHE IMPEDISCE DI BARARE.

    Un rifiuto si ottiene anche rifiutando tutto. Questo collaudo dice che la
    finestra accetta cio' che deve accettare: senza, i tre rossi qui sopra
    sarebbero soddisfatti da un `return 401` incondizionato.
    """
    player = create_player(prefix="por03-adesso")
    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=str(player["user_id"]),
            game_session_id=str(uuid4()),
            tx_id=f"por03-adesso-{uuid4().hex}",
            amount="10.00",
        ),
    )
    assert response.status_code == 200, response.text


# ------------------------------------------------------------------- L3: rigioco

def test_lo_stesso_nonce_con_un_corpo_diverso_e_un_rigioco_e_si_rifiuta(
    client, create_player, db_helpers
) -> None:
    """L3 — il rigioco a comando, che l'idempotenza non ferma.

    L'anti-doppione su tx_id difende dal duplicato, non dalla ripetizione a
    comando: chi cambia il tx_id passa l'idempotenza. Qui il nonce e' lo stesso
    e il corpo e' cambiato: e' un rigioco, e si rifiuta.
    """
    player = create_player(prefix="por03-rigioco")
    user_id = str(player["user_id"])
    nonce = uuid4().hex

    prima = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(user_id=user_id, game_session_id=str(uuid4()),
                 tx_id=f"por03-rigioco-a-{uuid4().hex}", amount="10.00", nonce=nonce),
    )
    assert prima.status_code == 200, prima.text
    saldo_dopo_la_prima = db_helpers.get_wallet_balance(user_id)

    # SESSIONE DIVERSA, DELIBERATAMENTE. La prima stesura riusava la stessa
    # sessione e il collaudo passava PRIMA del codice anti-rigioco: a fermarlo
    # era il conflitto di sessione, non il nonce. Era un verde per la ragione
    # sbagliata - su questo progetto il gate e' gia' stato verde quattro volte
    # su difetti veri. Con una sessione nuova, l'unica cosa che puo' fermare
    # questa richiesta e' il nonce ripetuto.
    seconda = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(user_id=user_id, game_session_id=str(uuid4()),
                 tx_id=f"por03-rigioco-b-{uuid4().hex}", amount="10.00", nonce=nonce),
    )

    assert seconda.status_code in (401, 403, 409), seconda.text
    assert db_helpers.get_wallet_balance(user_id) == saldo_dopo_la_prima, (
        "il rigioco non deve muovere il saldo una seconda volta"
    )


def test_lo_stesso_nonce_con_lo_stesso_corpo_resta_un_retry_e_non_si_rompe(
    client, create_player, db_helpers
) -> None:
    """D6 — IL COLLAUDO CHE PROTEGGE I FORNITORI DALLA NOSTRA RIPARAZIONE.

    La prima stesura del piano diceva 'nonce gia' visto -> rifiuto', e la sfida
    di Codex l'ha bloccata: test_seamless_ordine_operazioni.py:122-151 manda due
    volte lo stesso payload e pretende 200. Un nonce a uso singolo avrebbe rotto
    un retry deliberato. Questo collaudo fissa il confine fra le due cose.
    """
    player = create_player(prefix="por03-retry")
    user_id = str(player["user_id"])
    payload = _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"por03-retry-{uuid4().hex}",
        amount="10.00",
    )

    prima = _post(client, "/seamless/wallet/reserve", payload)
    assert prima.status_code == 200, prima.text
    saldo = db_helpers.get_wallet_balance(user_id)

    seconda = _post(client, "/seamless/wallet/reserve", payload)

    assert seconda.status_code == 200, seconda.text
    assert seconda.json().get("already_exists") is True
    assert db_helpers.get_wallet_balance(user_id) == saldo


def test_una_richiesta_rifiutata_non_diventa_valida_quando_cambiano_le_condizioni(
    client, create_player, db_helpers
) -> None:
    """IL BUCO CHE LA SFIDA DI CODEX HA TROVATO NELLA v2 DEL PIANO.

    La regola 'stesso nonce + stesso corpo = retry' da sola non basta, e questo
    e' il caso che lo dimostra: un aggressore intercetta una reserve firmata, la
    manda quando il saldo non basta (rifiutata), e la rimanda dopo che il
    giocatore ha ricaricato. Byte identici: la regola la chiamerebbe retry e la
    eseguirebbe. Il denaro si muoverebbe per una richiesta intercettata.

    LA REGOLA GIUSTA, che questo collaudo fissa: l'esito terminale si REGISTRA
    col nonce e si RIPRODUCE, non si riesegue. Un rifiuto resta un rifiuto anche
    se il mondo intorno e' cambiato.

    Trovato da gpt-5.6-sol come rilievo su D6, riprodotto qui prima del codice.
    """
    player = create_player(prefix="por03-condizioni")
    user_id = str(player["user_id"])
    game_session_id = str(uuid4())

    # SI ABBASSA IL SALDO, NON SI ALZA L'IMPORTO. Un importo alto viene
    # rifiutato per "sopra il massimo consentito" (CK.SEAMLESS.AMOUNT_ABOVE_
    # MAXIMUM), che non dipende dal saldo: la ricarica non cambierebbe nulla e
    # il collaudo passerebbe senza misurare niente. Verificato sul campo, due
    # stesure di seguito. L'importo resta piccolo e legale; e' il saldo a non
    # bastare.
    importo = Decimal("10.00")
    db_helpers.fetchone(
        """
        UPDATE wallet_accounts SET balance_snapshot = %s
        WHERE user_id = %s AND wallet_type = 'cash'
        RETURNING balance_snapshot
        """,
        (Decimal("1.00"), user_id),
    )

    payload = _payload(
        user_id=user_id,
        game_session_id=game_session_id,
        tx_id=f"por03-condizioni-{uuid4().hex}",
        amount=f"{importo:.2f}",
    )

    primo = _post(client, "/seamless/wallet/reserve", payload)
    assert primo.status_code != 200, (
        f"il saldo non bastava, la reserve non doveva riuscire: {primo.text}"
    )
    esito_primo = primo.status_code

    # il giocatore ricarica: ora il saldo basterebbe
    db_helpers.fetchone(
        """
        UPDATE wallet_accounts SET balance_snapshot = %s
        WHERE user_id = %s AND wallet_type = 'cash'
        RETURNING balance_snapshot
        """,
        (Decimal("500.00"), user_id),
    )
    saldo_dopo_ricarica = db_helpers.get_wallet_balance(user_id)

    secondo = _post(client, "/seamless/wallet/reserve", payload)

    assert secondo.status_code == esito_primo, (
        "la stessa richiesta intercettata e' diventata valida quando il saldo e' "
        f"cambiato: prima {esito_primo}, ora {secondo.status_code}. "
        f"{secondo.text}"
    )
    assert db_helpers.get_wallet_balance(user_id) == saldo_dopo_ricarica, (
        "una richiesta gia' rifiutata non deve muovere il saldo al secondo invio"
    )
