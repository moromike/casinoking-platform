"""POR-03 — l'identita' dichiarata, il momento della richiesta e il rigioco.

PERCHE' QUESTO FILE ESISTE, E PERCHE' STA IN UN PUNTO SOLO.
Fino al 10/09/2026 `provider_code`, `timestamp` e `nonce` erano dichiarati
obbligatori nel protocollo e non letti da nessuno: tre campi che sembravano
controlli di sicurezza senza esserlo. Il commento del router prometteva il
rifiuto, e il rifiuto non avveniva. E' la classe di difetto che fa credere a una
revisione che un confine sia controllato quando non lo e'.

PERCHE' UNA APIRoute E NON TRE CONTROLLI NEGLI HANDLER.
Il controllo deve vedere il corpo ESATTO che e' stato firmato e l'esito della
richiesta. Una rotta nuova aggiunta domani lo eredita senza che nessuno debba
ricordarsene, che e' la stessa ragione per cui `fuori_produzione` sta nelle
dipendenze del router e non nelle singole rotte.

COSA QUESTO FILE FA E NON FA, dichiarato qui perche' non si perda.
La firma HMAC copre METODO, token di operazione e corpo (3bE, 11/09/2026):
legare la rotta tramite un token stabile risolve il problema di proxy,
prefissi e alias che un percorso URL non puo' garantire. POR-03 resta
chiusa per **identita' e momento**; il token di operazione aggiunge la
protezione cross-route senza dipendere dalla forma del percorso.
La porta di produzione resta chiusa: chi legge questo file e pensa di
poter togliere il 503 deve leggere prima `fuori_produzione` nel router.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.errors import build_error_payload
from app.api.errors import HTTP_422_UNPROCESSABLE_ENTITY
from app.core.config import settings
from app.db.connection import db_connection
from app.modules.providers.auth import (
    firma_valida,
    identita_presunta,
    messaggio_firmato,
    token_da_percorso,
)

# I codici che il fornitore vede. Stanno qui e non sparsi, perche' un confine
# si giudica su cio' che rifiuta e su come lo dice.
CODICE_IDENTITA = "CK.SEAMLESS.PROVIDER_MISMATCH"
CODICE_MOMENTO = "CK.SEAMLESS.TIMESTAMP_FUORI_FINESTRA"
CODICE_MOMENTO_MALFORMATO = "CK.SEAMLESS.TIMESTAMP_MALFORMATO"
CODICE_RIGIOCO = "CK.SEAMLESS.NONCE_GIA_USATO"
CODICE_IN_VOLO = "CK.SEAMLESS.RICHIESTA_IN_CORSO"

logger = logging.getLogger(__name__)


def _rifiuto(status_code: int, codice: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=build_error_payload(code=codice))


def impronta(corpo: bytes) -> str:
    """L'impronta del corpo esatto che e' stato firmato, non del corpo riletto.

    Si usa il byte per byte e non il JSON interpretato: due corpi che
    significano la stessa cosa ma sono scritti diversamente hanno firme diverse,
    quindi sono richieste diverse.
    """
    return hashlib.sha256(corpo).hexdigest()


def verifica_identita_dichiarata(corpo_json: dict, provider_autenticato: str) -> None:
    """L1 — l'intestazione sceglie la chiave, il corpo dice chi e': devono coincidere.

    Il commento del router lo prometteva da giorni senza farlo. Da solo questo
    controllo pesa poco (il legame gioco-fornitore a router.py:143-146 gia'
    impedisce a un fornitore di impersonarne un altro), ma un campo obbligatorio
    che nessuno legge e' peggio di un campo assente: mente a chi legge il codice.
    """
    dichiarato = corpo_json.get("provider_code")
    if dichiarato != provider_autenticato:
        raise _rifiuto(401, CODICE_IDENTITA)


def verifica_momento(corpo_json: dict, adesso: datetime | None = None) -> None:
    """L2 — senza momento, una richiesta intercettata resta valida per sempre.

    `adesso` e' iniettabile perche' un controllo temporale che non si puo'
    collaudare al bordo non e' collaudato: la sfida al piano lo ha chiesto
    esplicitamente.
    """
    if settings.seamless_finestra_disattivata:
        # Vietata in produzione da config.validate_for_environment.
        return

    grezzo = corpo_json.get("timestamp")
    if not isinstance(grezzo, str) or not grezzo.strip():
        raise _rifiuto(401, CODICE_MOMENTO_MALFORMATO)

    try:
        momento = datetime.fromisoformat(grezzo.replace("Z", "+00:00"))
    except ValueError:
        raise _rifiuto(401, CODICE_MOMENTO_MALFORMATO)

    # IL FUSO DI UN TERZO NON SI INDOVINA. Interpretare un orario senza fuso
    # come "ora locale del server" e' inventare un dato su un percorso che muove
    # denaro, ed e' la stessa ragione per cui nessun campo del protocollo ha un
    # valore predefinito (PRO-01, commit fd5bb71).
    if momento.tzinfo is None:
        raise _rifiuto(401, CODICE_MOMENTO_MALFORMATO)

    adesso = adesso or datetime.now(timezone.utc)
    passato = timedelta(seconds=settings.seamless_finestra_passato_secondi)
    futuro = timedelta(seconds=settings.seamless_finestra_futuro_secondi)

    # Il bordo sta DENTRO: <= e >=, non < e >. Una finestra che rifiuta il suo
    # stesso bordo e' una finestra piu' stretta di quella dichiarata.
    if momento < adesso - passato or momento > adesso + futuro:
        raise _rifiuto(401, CODICE_MOMENTO)


# QUANTO VIVE UN "in_corso" PRIMA DI ESSERE CONSIDERATO MORTO.
# Se il processo muore fra la prenotazione e la registrazione dell'esito, la riga
# resta 'in_corso' e senza questa scadenza **quel nonce sarebbe bloccato per
# sempre**: ogni ritentativo del fornitore riceverebbe 409 in eterno.
#
# IL VALORE SI RICAVA DALLA FINESTRA, NON SI SCEGLIE A PARTE — e questa e' la
# correzione del 10/09/2026, terza revisione indipendente.
# Prima era un 900 fisso, e la revisione ha mostrato che rendeva il recupero
# IRRAGGIUNGIBILE: il controllo del momento rifiuta a 300 s e viene PRIMA della
# prenotazione, quindi nessun ritentativo poteva arrivare vivo ai 900 s.
# Probe della revisione sulla funzione reale: eta' 299 s accettata, eta' 901 s
# rifiutata FUORI_FINESTRA. La riga morta restava morta.
#   Il difetto e' quello di tutta la giornata: due numeri che devono stare in
#   relazione, scelti in due punti diversi. Legarli per costruzione e' l'unico
#   modo perche' non divergano di nuovo quando qualcuno cambiera' la finestra.
# La meta' della finestra lascia comunque a una richiesta in volo molto piu'
# tempo di quanto ne impieghi (una chiamata HTTP dura secondi, non minuti),
# quindi non rischia di rubare una prenotazione ancora viva.
def secondi_prima_che_un_in_corso_sia_morto() -> int:
    return max(30, settings.seamless_finestra_passato_secondi // 2)


def _prenota_o_riproduci(
    provider_code: str, nonce: str, impronta_corpo: str, rotta: str
) -> tuple[bool, Response | None, UUID | None]:
    """L3 — il registro delle richieste gia' viste.

    Torna (prosegui, risposta_da_riprodurre, proprietario).

    LA RIGA CHE FA IL LAVORO E' L'INSERT, NON LA SELECT. Guardare prima e
    scrivere poi lascia in mezzo una finestra in cui due richieste gemelle
    passano entrambe: in concorrenza solo il vincolo di unicita' del database
    puo' dire quale delle due e' arrivata prima. Percio' si tenta di scrivere, e
    si legge solo se la scrittura viene respinta.
    Il proprietario non e' un dettaglio della chiamata: e' la generazione della
    prenotazione. Solo chi riceve quel valore puo' chiudere la riga.
    """
    proprietario = uuid4()
    with db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seamless_richieste_viste
                    (provider_code, nonce, impronta_corpo, rotta, esito,
                     proprietario, vincola_nonce)
                VALUES (%s, %s, %s, %s, 'in_corso', %s, TRUE)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (provider_code, nonce, impronta_corpo, rotta, proprietario),
            )
            if cursor.fetchone() is not None:
                conn.commit()
                return True, None, proprietario

            # LA RIGA MORTA CAMBIA PROPRIETARIO, NON SOLO DATA. Il probe della
            # quarta revisione ha fatto proseguire sia il vecchio esecutore sia
            # il retry dopo 151 s: il vecchio 500 chiudeva prima del nuovo 200 e
            # lasciava l'esito rifiutato. Un UUID nuovo rende il recupero una
            # nuova generazione: la chiusura vecchia non possiede piu' la riga.
            # Se una prenotazione e'
            # rimasta 'in_corso' oltre la scadenza, il processo che la teneva non
            # esiste piu': la si riassegna a questa richiesta invece di lasciare
            # il nonce bloccato per sempre. Impronta e rotta devono comunque
            # coincidere: il recupero cambia proprietario, non identita'.
            cursor.execute(
                """
                UPDATE seamless_richieste_viste
                SET creato_il = now(), proprietario = %s
                WHERE provider_code = %s AND nonce = %s
                  AND impronta_corpo = %s
                  AND rotta = %s
                  AND vincola_nonce = TRUE
                  AND esito = 'in_corso'
                  AND creato_il < now() - make_interval(secs => %s)
                RETURNING id
                """,
                (
                    proprietario,
                    provider_code,
                    nonce,
                    impronta_corpo,
                    rotta,
                    secondi_prima_che_un_in_corso_sia_morto(),
                ),
            )
            if cursor.fetchone() is not None:
                conn.commit()
                return True, None, proprietario

            cursor.execute(
                """
                SELECT impronta_corpo, rotta, esito, codice_http, corpo_risposta
                FROM seamless_richieste_viste
                WHERE provider_code = %s AND nonce = %s
                  AND vincola_nonce = TRUE
                """,
                (provider_code, nonce),
            )
            vista = cursor.fetchone()
            conn.commit()

    if vista is None:
        # La riga e' sparita fra le due interrogazioni: e' l'unico caso in cui
        # non sappiamo niente, e non si tira a indovinare su un confine.
        raise _rifiuto(409, CODICE_IN_VOLO)

    # CORPO DIVERSO = RIGIOCO. Chi rimanda lo stesso nonce con un corpo cambiato
    # sta riusando una firma per dire un'altra cosa.
    if vista["impronta_corpo"] != impronta_corpo:
        raise _rifiuto(401, CODICE_RIGIOCO)

    # LA ROTTA SI CONFRONTA, ANCHE SE LA FIRMA NON LA COPRE.
    # La revisione indipendente ha mostrato un avvelenamento vero: si intercetta
    # un corpo firmato per `reserve`, lo si manda prima a `rollback` — dove
    # prenota il nonce e poi fallisce lo schema — e da quel momento la reserve
    # legittima riceve 409. Non muove denaro, ma impedisce a un fornitore di
    # lavorare, e non serve nessuna chiave per farlo.
    # Questo NON e' "legare la rotta alla firma" (POR-03/L4): quella cambia cio'
    # che il fornitore deve firmare ed e' una decisione di Michele. Qui si
    # riconosce soltanto che lo stesso nonce su due rotte diverse e' un rigioco.
    if vista["rotta"] != rotta:
        raise _rifiuto(401, CODICE_RIGIOCO)

    if vista["esito"] == "in_corso":
        # Una gemella e' in volo, o una richiesta e' morta a meta'. Non sappiamo
        # se il denaro si e' mosso: indovinare sarebbe la cosa peggiore.
        raise _rifiuto(409, CODICE_IN_VOLO)

    # ESITO ACCETTATO: SI PROSEGUE, NON SI RIPRODUCE.
    # Sembra un'incoerenza e non lo e'. Riprodurre la risposta registrata
    # romperebbe il retry idempotente: la prima risposta porta
    # already_exists=False, e restituirla di nuovo direbbe al fornitore che ha
    # appena aperto una seconda partita. Provato sul campo il 10/09/2026, il
    # collaudo del retry e' diventato rosso.
    #   Chi prosegue trova l'idempotenza su tx_id, che e' persistente, e' un
    #   vincolo di database e risponde gia' 200 con already_exists=True senza
    #   muovere il denaro una seconda volta. E' collaudata da
    #   test_seamless_ordine_operazioni.py:122-153 dal 7/09.
    # Il denaro e' protetto dall'idempotenza; il RIGIOCO e' protetto qui sopra,
    # dal confronto delle impronte. Sono due controlli diversi e servono
    # entrambi.
    if vista["esito"] == "accettato":
        return True, None, None

    # ESITO RIFIUTATO: SI RIPRODUCE, NON SI RIESEGUE.
    # E' il buco che la sfida al piano ha trovato, e non era teorico: si
    # intercetta una reserve, la si manda quando il saldo non basta (rifiutata),
    # la si rimanda dopo una ricarica. Byte identici, quindi "retry", quindi
    # eseguita. Un rifiuto deve restare un rifiuto anche se il mondo intorno e'
    # cambiato: la richiesta e' stata giudicata, e non si rigiudica.
    return False, JSONResponse(
        status_code=vista["codice_http"] or 409,
        content=vista["corpo_risposta"] if vista["corpo_risposta"] is not None else {},
    ), None


def _registra_esito(
    provider_code: str,
    nonce: str,
    proprietario: UUID | None,
    codice_http: int,
    corpo: bytes | None,
) -> None:
    """Chiude la riga con l'esito terminale. Non solleva mai: registrare non deve
    poter rompere una richiesta che e' gia' andata a buon fine."""
    if proprietario is None:
        return
    try:
        contenuto = None
        if corpo:
            try:
                contenuto = json.dumps(json.loads(corpo))
            except (ValueError, TypeError):
                contenuto = None
        esito = "accettato" if 200 <= codice_http < 300 else "rifiutato"
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE seamless_richieste_viste
                    SET esito = %s, codice_http = %s, corpo_risposta = %s,
                        chiuso_il = now(), proprietario = NULL
                    WHERE provider_code = %s AND nonce = %s
                      AND proprietario = %s
                      AND vincola_nonce = TRUE
                      AND esito = 'in_corso'
                    """,
                    (
                        esito,
                        codice_http,
                        contenuto,
                        provider_code,
                        nonce,
                        proprietario,
                    ),
                )
                conn.commit()
    except Exception:  # noqa: BLE001 - vedi docstring
        pass


def _traccia_rifiuto_anticipato(
    provider_code: str,
    nonce: object,
    rotta: str,
    impronta_corpo: str,
    codice_http: int,
    corpo: bytes | None,
) -> None:
    """La riga di un rifiuto avvenuto PRIMA che il nonce fosse prenotato.

    Non solleva mai: registrare un rifiuto non deve poter trasformare un 401 in
    un 500. Un rifiuto che non si riesce a scrivere resta comunque un rifiuto.
    """
    try:
        if not isinstance(nonce, str) or not nonce.strip():
            return
        contenuto = None
        if corpo:
            try:
                contenuto = json.dumps(json.loads(corpo))
            except (ValueError, TypeError):
                contenuto = None
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO seamless_richieste_viste
                        (provider_code, nonce, impronta_corpo, rotta, esito,
                         codice_http, corpo_risposta, chiuso_il, vincola_nonce)
                    VALUES (%s, %s, %s, %s, 'rifiutato', %s, %s, now(), FALSE)
                    """,
                    (
                        provider_code,
                        nonce,
                        impronta_corpo,
                        rotta,
                        codice_http,
                        contenuto,
                    ),
                )
                conn.commit()
    except Exception:  # noqa: BLE001 - il rifiuto originale deve restare intatto
        # La quarta revisione ha forzato il DB a fallire e ha misurato silenzio
        # totale. Il log rende osservabile la perdita della traccia senza
        # trasformare un rifiuto legittimo in un 500.
        logger.exception("Impossibile registrare il rifiuto anticipato seamless")


class RottaDelConfine(APIRoute):
    """La rotta che porta i controlli del confine, per tutte le rotte seamless.

    L'ordine dei controlli non e' casuale: identita', momento, schema, rigioco.
    I primi tre lasciano una traccia non vincolante; solo il quarto prenota.
    Cosi' un rifiuto resta osservabile ma non puo' essere usato per bruciare i
    numeri di un fornitore.
    """

    def get_route_handler(self) -> Callable:
        handler_originale = super().get_route_handler()
        campo_corpo = self.body_field

        async def handler(request: Request) -> Response:
            corpo = await request.body()
            try:
                corpo_json = json.loads(corpo) if corpo else {}
            except ValueError:
                # Un corpo illeggibile lo rifiuta gia' pydantic con il suo
                # messaggio: qui si lascia passare per non dare due risposte
                # diverse allo stesso errore.
                return await handler_originale(request)
            if not isinstance(corpo_json, dict):
                return await handler_originale(request)

            # L'IDENTITA' SI RISOLVE COME LA RISOLVE L'AUTENTICAZIONE, non a modo
            # nostro. La prima stesura leggeva l'intestazione e, se mancava,
            # lasciava passare la richiesta senza controlli — mentre
            # verify_provider_hmac le assegnava comunque il fornitore presunto e
            # la autenticava. Bastava OMETTERE l'intestazione per saltare
            # identita', momento e anti-rigioco tutti insieme.
            # Trovato dalla revisione indipendente del 10/09/2026, eseguendo il
            # vero gestore con una richiesta senza intestazione: identita' 0,
            # momento 0, nonce 0, handler 1.
            provider = identita_presunta(request.headers.get("x-provider-id"))

            # PRIMA SI AUTENTICA, POI SI SCRIVE. Il registro e' una tabella che
            # cresce: se la si scrive prima di verificare la firma, chiunque puo'
            # riempirla senza possedere nessuna chiave, mandando nonce sempre
            # nuovi. Anche questo lo ha trovato la revisione indipendente.
            # La firma viene poi riverificata da verify_provider_hmac come
            # dipendenza della rotta: e' un confronto di impronte, costa nulla, e
            # avere due punti che la controllano e' meglio che averne zero prima
            # di una scrittura.
            # 3bE: la firma copre METODO\nTOKEN-OPERAZIONE\nCORPO. Il token si
            # ricava dalla rotta che ha ricevuto la richiesta, non da cio' che
            # il client dichiara. Una firma calcolata solo sul corpo (vecchio
            # schema) produce un messaggio diverso e viene rifiutata.
            token_op = token_da_percorso(request.url.path)
            if token_op is not None:
                msg = messaggio_firmato(request.method, token_op, corpo)
            else:
                msg = corpo
            if not firma_valida(provider, msg, request.headers.get("x-signature-hmac")):
                # Non si anticipa il messaggio dell'autenticazione: si lascia che
                # sia lei a dirlo, cosi' il fornitore vede una risposta sola.
                return await handler_originale(request)

            # I RIFIUTI PRIMA DELLA PRENOTAZIONE LASCIANO TRACCIA ANCHE LORO.
            # P3-04 pretende che il registro dica di OGNI operazione se e' stata
            # accettata o rifiutata **e perche'**. Identita' e momento si
            # giudicano prima che esista una riga, quindi finivano nel nulla: il
            # confine rifiutava e nessuno poteva saperlo. Tre revisioni di
            # seguito lo hanno chiamato falso verde, e avevano ragione.
            # Si registra solo DOPO che la firma e' stata verificata, quindi
            # queste righe le puo' creare soltanto chi possiede una chiave: un
            # anonimo non puo' gonfiare la tabella.
            try:
                verifica_identita_dichiarata(corpo_json, provider)
                verifica_momento(corpo_json)
            except HTTPException as rifiuto:
                _traccia_rifiuto_anticipato(
                    provider,
                    corpo_json.get("nonce"),
                    request.url.path,
                    impronta(corpo),
                    rifiuto.status_code,
                    json.dumps(rifiuto.detail).encode()
                    if rifiuto.detail is not None
                    else None,
                )
                raise

            nonce = corpo_json.get("nonce")
            if not isinstance(nonce, str) or not nonce.strip():
                # Campo obbligatorio: lo rifiuta pydantic, con il suo messaggio.
                return await handler_originale(request)

            # LO SCHEMA DELLA ROTTA VIENE GIUDICATO PRIMA DI PRENOTARE. Il
            # 10/09/2026 e' stato riprodotto questo blocco: un corpo `reserve`
            # firmato, mandato prima a `rollback`, prenotava il nonce e falliva
            # solo dopo per `reserve_tx_id` mancante; la reserve vera restava
            # quindi rifiutata. La validazione anticipata non cambia la firma e
            # mantiene il nonce unico fra rotte; se fallisce, il gestore FastAPI
            # formula lo stesso 422. Poi lo si registra come traccia NON
            # vincolante: P3-04 vede il motivo, ma la rotta giusta puo' ancora
            # acquisire quello stesso nonce.
            if campo_corpo is not None:
                _, errori_schema = campo_corpo.validate(
                    corpo_json, {}, loc=("body",)
                )
                if errori_schema:
                    # IL GESTORE ORIGINALE *SOLLEVA*, NON TORNA. Un corpo che non
                    # rispetta lo schema fa alzare RequestValidationError, ed e'
                    # l'applicazione a trasformarla in 422: qui non arriva nessuna
                    # risposta da leggere. Chi si aspettava un valore di ritorno
                    # perdeva la traccia — e nessuno se ne accorgeva, perche' la
                    # scrittura del registro ingoia i propri errori.
                    # Riprodotto il 10/09/2026 lanciando il collaudo che questa
                    # stessa riparazione aveva scritto senza poterlo eseguire.
                    try:
                        risposta = await handler_originale(request)
                    except RequestValidationError as errore_schema:
                        _traccia_rifiuto_anticipato(
                            provider,
                            nonce,
                            request.url.path,
                            impronta(corpo),
                            HTTP_422_UNPROCESSABLE_ENTITY,
                            json.dumps(
                                build_error_payload(
                                    code="CK.VALIDATION.INVALID_REQUEST",
                                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                                    details={"fields": errore_schema.errors()},
                                ),
                                default=str,
                            ).encode(),
                        )
                        raise
                    _traccia_rifiuto_anticipato(
                        provider,
                        nonce,
                        request.url.path,
                        impronta(corpo),
                        risposta.status_code,
                        getattr(risposta, "body", None),
                    )
                    return risposta

            prosegui, riproduzione, proprietario = _prenota_o_riproduci(
                provider, nonce, impronta(corpo), request.url.path
            )
            if not prosegui and riproduzione is not None:
                return riproduzione

            # OGNI USCITA REGISTRA IL SUO ESITO, NON SOLO LE DUE PREVISTE.
            # La prima stesura catturava il solo HTTPException: una
            # RequestValidationError, o qualunque guasto, lasciava la riga
            # 'in_corso' e da quel momento ogni ritentativo riceveva 409 senza
            # scadenza ne' recupero. Ora l'esito si registra sempre, e la riga
            # morta ha comunque una scadenza (vedi _prenota_o_riproduci).
            try:
                risposta = await handler_originale(request)
            except HTTPException as exc:
                _registra_esito(
                    provider,
                    nonce,
                    proprietario,
                    exc.status_code,
                    json.dumps(exc.detail).encode() if exc.detail is not None else None,
                )
                raise
            except Exception:
                # Non sappiamo come sia finita: si registra un rifiuto generico,
                # cosi' il nonce non resta appeso. Il 500 lo formula chi di
                # dovere, piu' in alto.
                _registra_esito(provider, nonce, proprietario, 500, None)
                raise

            corpo_risposta = getattr(risposta, "body", None)
            _registra_esito(
                provider, nonce, proprietario, risposta.status_code, corpo_risposta
            )
            return risposta

        return handler
