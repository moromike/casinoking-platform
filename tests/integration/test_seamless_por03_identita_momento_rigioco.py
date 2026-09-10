from __future__ import annotations
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


import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute
from httpx import Client

from app.api.v1.seamless import confine
from app.api.v1.seamless.confine import verifica_momento
from app.core.config import settings
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

    # IL MOTIVO DEL RIFIUTO CONTA, NON SOLO IL NUMERO. La stesura precedente
    # accettava 401/403/409 senza guardare il corpo: sarebbe stata verde anche
    # se a fermare la richiesta fosse stato un controllo qualunque - per
    # esempio il conflitto di sessione, come gia' successo con la prima
    # stesura di questo stesso collaudo.
    assert seconda.status_code == 401, seconda.text
    assert seconda.json()["error"]["code"] == "CK.SEAMLESS.NONCE_GIA_USATO", (
        "il rigioco deve essere riconosciuto COME rigioco, non fermato per un "
        f"altro motivo: {seconda.text}"
    )
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
    # IL PRIMO ERRORE DEVE ESSERE QUELLO ATTESO, NON UNO QUALUNQUE. La stesura
    # precedente accettava qualunque non-200: se il rifiuto non fosse dipeso
    # dal saldo - per esempio un 500 - la ricarica qui sotto non cambierebbe
    # le condizioni che lo hanno causato, e il collaudo non misurerebbe
    # niente di quello che promette.
    assert primo.status_code == 422, (
        f"il saldo non bastava, la reserve non doveva riuscire: {primo.text}"
    )
    assert primo.json()["error"]["code"] == "CK.WALLET.INSUFFICIENT_BALANCE", (
        "il primo rifiuto deve essere per saldo insufficiente, altrimenti la "
        f"ricarica qui sotto non e' la condizione che lo ha causato: {primo.text}"
    )

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

    # SI CONFRONTA IL CORPO, NON SOLO IL NUMERO: due 500 uguali avrebbero
    # soddisfatto la stesura precedente. L'esito riprodotto deve essere LO
    # STESSO rifiuto, con lo stesso codice di errore.
    assert secondo.status_code == 422, (
        "la stessa richiesta intercettata e' diventata valida quando il saldo "
        f"e' cambiato: {secondo.text}"
    )
    assert secondo.json()["error"]["code"] == "CK.WALLET.INSUFFICIENT_BALANCE", (
        "l'esito riprodotto deve essere lo stesso rifiuto della prima volta, "
        f"con lo stesso motivo: {secondo.text}"
    )
    assert db_helpers.get_wallet_balance(user_id) == saldo_dopo_ricarica, (
        "una richiesta gia' rifiutata non deve muovere il saldo al secondo invio"
    )


# ------------------------------------------- L0: l'intestazione che mancava

def test_senza_intestazione_provider_i_controlli_non_si_saltano(monkeypatch) -> None:
    """IL BUCO DELL'INTESTAZIONE ASSENTE, trovato il 10/09/2026.

    Senza x-provider-id la prima stesura del confine saltava identita', momento
    e anti-rigioco TUTTI INSIEME, mentre l'autenticazione assegnava comunque il
    fornitore presunto 'm-and-m-games' e, se la firma era la sua, AUTENTICAVA la
    richiesta. Bastava omettere un'intestazione per far sparire tre controlli.

    QUESTO E' UN COLLAUDO DIRETTO DEL GESTORE, NON HTTP. `client` parla con un
    backend in un altro processo: il monkeypatch del processo pytest non puo'
    aggiungergli MANDM_SECRET_KEY. Il gestore riceve quindi una richiesta senza
    intestazione, con un'autenticazione valida simulata tramite il provider
    `ck_collaudo` che il collaudo possiede davvero. Il doppio finto verifica che
    il gestore passa `None` al risolutore di identita' e usa l'identita' risolta
    per autenticare; il timestamp vecchio deve fermarlo prima dell'endpoint.
    """
    vecchio = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    payload = _payload(
        user_id=str(uuid4()),
        game_session_id=str(uuid4()),
        tx_id=f"por03-nohdr-{uuid4().hex}",
        amount="10.00",
        provider_code=PROVIDER_CODE,
        timestamp=vecchio,
    )
    body = json.dumps(payload, separators=(",", ":")).encode()
    identita_richiesta: list[str | None] = []
    autenticazioni: list[tuple[str, bytes, str | None]] = []

    def risolvi_identita(intestazione: str | None) -> str:
        identita_richiesta.append(intestazione)
        return PROVIDER_CODE

    def firma_autenticata(provider: str, corpo: bytes, firma: str | None) -> bool:
        autenticazioni.append((provider, corpo, firma))
        return provider == PROVIDER_CODE and corpo == body and firma == "firma-valida"

    monkeypatch.setattr(confine, "identita_presunta", risolvi_identita)
    monkeypatch.setattr(confine, "firma_valida", firma_autenticata)

    async def endpoint() -> Response:
        raise AssertionError("il timestamp vecchio deve fermare il gestore")

    route = confine.RottaDelConfine(
        "/seamless/wallet/reserve", endpoint=endpoint, methods=["POST"]
    )

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/seamless/wallet/reserve",
            "headers": [(b"x-signature-hmac", b"firma-valida")],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
        },
        receive,
    )

    with pytest.raises(HTTPException) as errore:
        asyncio.run(route.get_route_handler()(request))

    assert identita_richiesta == [None]
    assert autenticazioni == [(PROVIDER_CODE, body, "firma-valida")]
    assert errore.value.status_code == 401
    assert errore.value.detail["error"]["code"] == "CK.SEAMLESS.TIMESTAMP_FUORI_FINESTRA"


def test_intestazione_provider_vuota_non_brucia_il_nonce(
    client, create_player, db_helpers
) -> None:
    """IL VALORE VUOTO NON E' UN'INTESTAZIONE MANCANTE.

    Il 10/09/2026 la seconda revisione indipendente ha misurato la divergenza:
    `identita_presunta('')` sceglieva m-and-m-games perche' in Python la stringa
    vuota e' falsa, quindi il confine autenticava e PRENOTAVA IL NONCE; subito
    dopo FastAPI passava "" alla dipendenza, che rispondeva 401 Unknown provider.
    Un estraneo poteva cosi' bruciare i nonce di un fornitore **senza conoscere
    nessuna chiave**: non rubava denaro, gli impediva di lavorare.

    IL COLLAUDO SI FA DA FUORI, VIA HTTP, e non chiamando il gestore a mano: una
    Request costruita a mano non ha lo stack dei middleware di FastAPI e il
    collaudo fallirebbe per una ragione che non c'entra niente con il difetto.
    Provato sul campo, prima stesura di questo file.

    LA PROVA E' CHE IL NONCE SOPRAVVIVE: si tenta con l'intestazione vuota, poi
    si manda la richiesta legittima **con lo stesso nonce**. Se il tentativo
    l'avesse prenotato, la legittima riceverebbe NONCE_GIA_USATO.

    LIMITE DICHIARATO, PERCHE' UN COLLAUDO CHE NON DISTINGUE VA DETTO.
    In questo ambiente il server registra un solo fornitore, `ck_collaudo`
    (verificato: `PROVIDERS.keys()` -> ['ck_collaudo']). Per riprodurre il
    difetto servirebbe una firma valida **per il fornitore presunto**, cioe' la
    chiave di m-and-m-games, che il server non ha. Senza quella, la firma non
    risulta valida ne' con il codice vecchio ne' con quello nuovo, e in entrambi
    i casi la richiesta passa oltre senza prenotare.
    **Quindi questo collaudo verifica la proprieta' giusta ma NON distingue le
    due versioni qui.** Diventa capace di distinguerle il giorno in cui il
    fornitore presunto e' registrato nell'ambiente di collaudo. Il difetto e'
    stato riprodotto dalla revisione indipendente eseguendo le funzioni reali,
    non via HTTP.
    """
    player = create_player(prefix="por03-hdrvuoto")
    user_id = str(player["user_id"])
    nonce = uuid4().hex
    saldo_prima = Decimal(db_helpers.get_wallet_balance(user_id))

    payload = _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"por03-hdrvuoto-{uuid4().hex}",
        amount="10.00",
        nonce=nonce,
    )
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None
    body = json.dumps(payload, separators=(",", ":")).encode()
    firma = hmac.new(secret, body, hashlib.sha256).hexdigest()

    tentativo = client.post(
        "/seamless/wallet/reserve",
        content=body,
        headers={
            "x-provider-id": "",
            "x-signature-hmac": firma,
            "Content-Type": "application/json",
        },
    )
    assert tentativo.status_code != 200, (
        f"un'intestazione vuota non identifica nessuno: {tentativo.text}"
    )
    assert Decimal(db_helpers.get_wallet_balance(user_id)) == saldo_prima

    # LA RICHIESTA LEGITTIMA, CON LO STESSO NONCE.
    legittima = _post(client, "/seamless/wallet/reserve", payload)
    assert legittima.status_code == 200, (
        "il tentativo con intestazione vuota ha bruciato il nonce del fornitore: "
        f"{legittima.text}"
    )
    assert Decimal(db_helpers.get_wallet_balance(user_id)) == saldo_prima - Decimal("10.00")


# ------------------------------------------------- L2-bis: l'altro bordo

def test_reserve_rifiuta_una_richiesta_dal_futuro_oltre_la_tolleranza(
    client, create_player, db_helpers
) -> None:
    """LA FINESTRA HA DUE BORDI: anche il futuro e' un sospetto.

    Il collaudo della richiesta vecchia copriva solo il passato. La tolleranza
    in avanti (settings.seamless_finestra_futuro_secondi) esiste per lo
    sfasamento degli orologi, non per accettare richieste datate domani: un
    timestamp molto avanti e' un orologio rotto o una richiesta fabbricata, e
    in entrambi i casi si rifiuta.
    """
    player = create_player(prefix="por03-futuro")
    user_id = str(player["user_id"])
    saldo_prima = db_helpers.get_wallet_balance(user_id)
    futuro = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=user_id,
            game_session_id=str(uuid4()),
            tx_id=f"por03-futuro-{uuid4().hex}",
            amount="10.00",
            timestamp=futuro,
        ),
    )

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "CK.SEAMLESS.TIMESTAMP_FUORI_FINESTRA", (
        "una richiesta dal futuro oltre la tolleranza va rifiutata: "
        f"{response.text}"
    )
    assert db_helpers.get_wallet_balance(user_id) == saldo_prima


def test_i_bordi_esatti_della_finestra_stanno_dentro() -> None:
    """IL BORDO STA DENTRO, e si misura con l'orologio iniettato.

    Dalla rete il bordo esatto non e' raggiungibile: fra il momento scritto dal
    collaudo e quello letto dal server passano dei millisecondi, quindi un
    bordo esatto via HTTP misurerebbe lo sfasamento fra i due orologi e non
    l'operatore di confronto. `verifica_momento` accetta `adesso` iniettato
    apposta (lo ha chiesto la sfida al piano): qui il bordo e' ESATTO e deve
    essere accettato, perche' il confronto e' <= e >=, non < e > - una finestra
    che rifiuta il suo stesso bordo e' piu' stretta di quella dichiarata
    (confine.py, verifica_momento).
    """
    adesso = datetime.now(timezone.utc)
    passato = settings.seamless_finestra_passato_secondi
    futuro = settings.seamless_finestra_futuro_secondi

    # Nessuna delle due deve sollevare: il bordo e' DENTRO la finestra.
    verifica_momento(
        {"timestamp": (adesso - timedelta(seconds=passato)).isoformat()},
        adesso=adesso,
    )
    verifica_momento(
        {"timestamp": (adesso + timedelta(seconds=futuro)).isoformat()},
        adesso=adesso,
    )

    # Un secondo OLTRE il bordo, invece, deve sollevare: senza questo
    # controllo, l'accettazione qui sopra sarebbe soddisfatta anche da una
    # finestra che non rifiuta mai.
    for sfasamento in (-passato - 1, futuro + 1):
        with pytest.raises(HTTPException) as errore:
            verifica_momento(
                {"timestamp": (adesso + timedelta(seconds=sfasamento)).isoformat()},
                adesso=adesso,
            )
        assert errore.value.status_code == 401


def test_reserve_accetta_una_richiesta_al_bordo_del_futuro(
    client, create_player
) -> None:
    """IL BORDO DEL FUTURO, ATTRAVERSO TUTTA LA PILA.

    Compagno del collaudo con l'orologio iniettato: dimostra che
    l'accettazione del bordo vale anche per una richiesta vera, firmata e
    passata per il confine. Solo il futuro si puo' misurare da qui: il server
    legge il suo orologio DOPO il collaudo, quindi un bordo del futuro resta
    dentro di qualche millisecondo, mentre un bordo del passato uscirebbe
    sempre di qualche millisecondo - e misurerebbe la rete, non la finestra.
    """
    player = create_player(prefix="por03-bordo")
    al_bordo = (
        datetime.now(timezone.utc)
        + timedelta(seconds=settings.seamless_finestra_futuro_secondi)
    ).isoformat()

    response = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=str(player["user_id"]),
            game_session_id=str(uuid4()),
            tx_id=f"por03-bordo-{uuid4().hex}",
            amount="10.00",
            timestamp=al_bordo,
        ),
    )
    assert response.status_code == 200, response.text


# ------------------------------------------------- L3-bis: il nonce fra rotte

def test_corpo_firmato_sulla_rotta_sbagliata_non_brucia_il_nonce(
    client, create_player, db_helpers
) -> None:
    """L'AVVELENAMENTO DEL NONCE FRA ROTTE.

    L'ORDINE E' L'ATTACCO MISURATO: prima rollback, poi reserve. Il collaudo
    precedente faceva l'opposto e non poteva vedere il blocco. La firma non
    copre la rotta, ma rollback deve rifiutare lo schema PRIMA di prenotare;
    cosi' la reserve legittima puo' usare il nonce e muovere il saldo una volta.
    """
    player = create_player(prefix="por03-rotte")
    user_id = str(player["user_id"])
    payload = _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"por03-rotte-{uuid4().hex}",
        amount="10.00",
    )

    # Stesso corpo byte per byte (e' lo stesso payload), rotta diversa.
    attacco = _post(client, "/seamless/wallet/rollback", payload)
    assert attacco.status_code == 422, attacco.text
    assert attacco.json()["error"]["code"] == "CK.VALIDATION.INVALID_REQUEST", (
        "la rotta sbagliata deve fallire per il proprio schema: "
        f"{attacco.text}"
    )

    traccia = db_helpers.fetchone(
        """
        SELECT esito, codice_http, corpo_risposta, vincola_nonce
        FROM seamless_richieste_viste
        WHERE provider_code = %s AND nonce = %s AND vincola_nonce = FALSE
        """,
        (PROVIDER_CODE, payload["nonce"]),
    )
    assert traccia is not None, (
        "il 422 firmato e' stato rifiutato senza lasciare la traccia richiesta "
        "da P3-04"
    )
    assert traccia["esito"] == "rifiutato"
    assert traccia["codice_http"] == 422
    assert "INVALID_REQUEST" in str(traccia["corpo_risposta"])
    assert traccia["vincola_nonce"] is False, (
        "una traccia dello schema non deve possedere il nonce della rotta giusta"
    )

    saldo_prima = Decimal(db_helpers.get_wallet_balance(user_id))
    legittima = _post(client, "/seamless/wallet/reserve", payload)

    assert legittima.status_code == 200, (
        "la rotta sbagliata ha bruciato il nonce della reserve legittima: "
        f"{legittima.text}"
    )
    assert Decimal(db_helpers.get_wallet_balance(user_id)) == saldo_prima - Decimal("10.00")

    righe = db_helpers.fetchone(
        """
        SELECT
            COUNT(*) FILTER (WHERE vincola_nonce = FALSE) AS tracce,
            COUNT(*) FILTER (WHERE vincola_nonce = TRUE) AS prenotazioni,
            COUNT(*) FILTER (
                WHERE vincola_nonce = TRUE AND esito = 'accettato'
            ) AS accettate
        FROM seamless_richieste_viste
        WHERE provider_code = %s AND nonce = %s
        """,
        (PROVIDER_CODE, payload["nonce"]),
    )
    assert righe == {"tracce": 1, "prenotazioni": 1, "accettate": 1}, righe


# ------------------------------------- Le due riserve della terza revisione

def test_la_scadenza_di_un_in_corso_sta_dentro_la_finestra_temporale() -> None:
    """I DUE NUMERI DEVONO STARE IN RELAZIONE, E QUI SI INCHIODA.

    La terza revisione indipendente ha misurato che una scadenza fissa di 900 s
    rendeva il recupero IRRAGGIUNGIBILE: il controllo del momento rifiuta a
    300 s e viene prima della prenotazione, quindi nessun ritentativo arrivava
    vivo ai 900 s. Una riga rimasta 'in_corso' dopo un guasto bloccava per
    sempre il nonce di un fornitore legittimo.
    Probe della revisione sulla funzione vera: eta' 299 s accettata, 901 s
    rifiutata.

    E' il difetto ricorrente di questo passo: due valori che devono stare in
    relazione, scelti in due punti diversi. Ora la scadenza si RICAVA dalla
    finestra; questo collaudo impedisce che tornino a divergere il giorno in cui
    qualcuno cambia la finestra e non pensa alla scadenza.
    """
    scadenza = confine.secondi_prima_che_un_in_corso_sia_morto()
    finestra = settings.seamless_finestra_passato_secondi

    assert scadenza < finestra, (
        f"un 'in_corso' scade dopo {scadenza}s ma il controllo del momento "
        f"rifiuta gia' a {finestra}s: il recupero non e' raggiungibile e il "
        "nonce resta bloccato per sempre"
    )
    assert scadenza >= 30, (
        "una scadenza troppo corta ruberebbe la prenotazione di una richiesta "
        "ancora in volo"
    )


def test_il_recupero_cambia_proprietario_e_il_vecchio_non_puo_chiudere(
    db_helpers,
) -> None:
    """IL PROBE DELLA QUARTA REVISIONE, ORA CONTRO IL DATABASE VERO.

    Dopo la scadenza il retry deve acquisire una generazione nuova. Il vecchio
    500 arriva deliberatamente prima del nuovo 200: senza proprietario fissava
    `rifiutato` e bloccava una richiesta riuscita.
    """
    nonce = uuid4().hex
    corpo = hashlib.sha256(b"recupero-con-proprietario").hexdigest()
    vecchio_proprietario = uuid4()
    scadenza = confine.secondi_prima_che_un_in_corso_sia_morto()

    db_helpers.fetchone(
        """
        INSERT INTO seamless_richieste_viste
            (provider_code, nonce, impronta_corpo, rotta, esito, creato_il,
             proprietario, vincola_nonce)
        VALUES (%s, %s, %s, %s, 'in_corso',
                now() - make_interval(secs => %s), %s, TRUE)
        RETURNING id
        """,
        (
            PROVIDER_CODE,
            nonce,
            corpo,
            "/api/v1/seamless/wallet/reserve",
            scadenza + 1,
            vecchio_proprietario,
        ),
    )

    prosegui, riproduzione, nuovo_proprietario = confine._prenota_o_riproduci(
        PROVIDER_CODE,
        nonce,
        corpo,
        "/api/v1/seamless/wallet/reserve",
    )
    assert prosegui is True
    assert riproduzione is None
    assert nuovo_proprietario not in (None, vecchio_proprietario)

    confine._registra_esito(
        PROVIDER_CODE, nonce, vecchio_proprietario, 500, b'{"vecchio":true}'
    )
    ancora_viva = db_helpers.fetchone(
        """
        SELECT esito, proprietario, codice_http
        FROM seamless_richieste_viste
        WHERE provider_code = %s AND nonce = %s AND vincola_nonce = TRUE
        """,
        (PROVIDER_CODE, nonce),
    )
    assert ancora_viva["esito"] == "in_corso"
    assert ancora_viva["proprietario"] == nuovo_proprietario
    assert ancora_viva["codice_http"] is None

    confine._registra_esito(
        PROVIDER_CODE, nonce, nuovo_proprietario, 200, b'{"nuovo":true}'
    )
    chiusa = db_helpers.fetchone(
        """
        SELECT esito, proprietario, codice_http
        FROM seamless_richieste_viste
        WHERE provider_code = %s AND nonce = %s AND vincola_nonce = TRUE
        """,
        (PROVIDER_CODE, nonce),
    )
    assert chiusa == {
        "esito": "accettato",
        "proprietario": None,
        "codice_http": 200,
    }


def test_una_prenotazione_viva_non_viene_rubata_dal_retry(db_helpers) -> None:
    """Il recupero ha un bordo: prima della scadenza possiede ancora il primo."""
    nonce = uuid4().hex
    corpo = hashlib.sha256(b"prenotazione-ancora-viva").hexdigest()
    proprietario = uuid4()
    db_helpers.fetchone(
        """
        INSERT INTO seamless_richieste_viste
            (provider_code, nonce, impronta_corpo, rotta, esito,
             proprietario, vincola_nonce)
        VALUES (%s, %s, %s, %s, 'in_corso', %s, TRUE)
        RETURNING id
        """,
        (
            PROVIDER_CODE,
            nonce,
            corpo,
            "/api/v1/seamless/wallet/reserve",
            proprietario,
        ),
    )

    with pytest.raises(HTTPException) as errore:
        confine._prenota_o_riproduci(
            PROVIDER_CODE,
            nonce,
            corpo,
            "/api/v1/seamless/wallet/reserve",
        )
    assert errore.value.status_code == 409
    assert errore.value.detail["error"]["code"] == "CK.SEAMLESS.RICHIESTA_IN_CORSO"

    invariata = db_helpers.fetchone(
        """
        SELECT esito, proprietario
        FROM seamless_richieste_viste
        WHERE provider_code = %s AND nonce = %s AND vincola_nonce = TRUE
        """,
        (PROVIDER_CODE, nonce),
    )
    assert invariata == {"esito": "in_corso", "proprietario": proprietario}


def test_il_registro_del_confine_scrive_davvero_le_tracce(
    client, create_player, db_helpers
) -> None:
    """P3-04 — IL REGISTRO SI INTERROGA, NON SI SUPPONE.

    Le revisioni hanno segnalato che nessun collaudo interrogava mai
    `seamless_richieste_viste`: il registro poteva smettere di scrivere e
    nessuno se ne sarebbe accorto, che e' esattamente il difetto per cui il
    contratto pretende un registro *misurato*. E' la stessa lezione della
    guardia dell'harness, rimasta senza log per giorni.

    COSA QUESTO COLLAUDO NON COPRE, dichiarato perche' resta un impegno aperto:
    i rifiuti di identita' e di momento avvengono PRIMA della prenotazione e non
    lasciano traccia. Qui si inchioda cio' che il registro fa oggi, non cio' che
    dovrebbe fare quando P3-04 sara' completo.
    """
    player = create_player(prefix="por03-registro")
    nonce = uuid4().hex

    risposta = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=str(player["user_id"]),
            game_session_id=str(uuid4()),
            tx_id=f"por03-registro-{uuid4().hex}",
            amount="10.00",
            nonce=nonce,
        ),
    )
    assert risposta.status_code == 200, risposta.text

    riga = db_helpers.fetchone(
        """
        SELECT provider_code, rotta, esito, codice_http
        FROM seamless_richieste_viste
        WHERE nonce = %s
        """,
        (nonce,),
    )
    assert riga is not None, (
        "il confine non ha lasciato traccia di un'operazione accettata: il "
        "registro di controllo non sta registrando"
    )
    assert riga["provider_code"] == PROVIDER_CODE
    assert riga["rotta"] == "/api/v1/seamless/wallet/reserve", riga["rotta"]
    assert riga["esito"] == "accettato", riga["esito"]
    assert riga["codice_http"] == 200, riga["codice_http"]


def test_anche_un_rifiuto_lascia_la_sua_traccia_col_motivo(
    client, create_player, db_helpers
) -> None:
    """P3-04 — «ogni operazione, accettata o rifiutata E PERCHE'».

    Identita' e momento si giudicano PRIMA che la riga esista, quindi i loro
    rifiuti finivano nel nulla: il confine rifiutava e nessuno poteva saperlo.
    Tre revisioni indipendenti di seguito lo hanno chiamato falso verde.
    Un registro che tace proprio sui rifiuti e' un registro che non serve: i
    rifiuti sono l'unica cosa che un confine produce di suo.
    """
    player = create_player(prefix="por03-traccia-rifiuto")
    nonce = uuid4().hex
    vecchio = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

    risposta = _post(
        client,
        "/seamless/wallet/reserve",
        _payload(
            user_id=str(player["user_id"]),
            game_session_id=str(uuid4()),
            tx_id=f"por03-traccia-{uuid4().hex}",
            amount="10.00",
            timestamp=vecchio,
            nonce=nonce,
        ),
    )
    assert risposta.status_code == 401, risposta.text

    riga = db_helpers.fetchone(
        """
        SELECT esito, codice_http, corpo_risposta
        FROM seamless_richieste_viste
        WHERE nonce = %s
        """,
        (nonce,),
    )
    assert riga is not None, (
        "il confine ha rifiutato una richiesta e non ne ha lasciato traccia: "
        "il registro tace proprio su cio' che un confine produce di suo"
    )
    assert riga["esito"] == "rifiutato", riga["esito"]
    assert riga["codice_http"] == 401, riga["codice_http"]
    assert riga["corpo_risposta"] is not None, (
        "la traccia dice CHE e' stato rifiutato ma non PERCHE': il contratto "
        "pretende il motivo"
    )
    assert "TIMESTAMP" in str(riga["corpo_risposta"]), riga["corpo_risposta"]
