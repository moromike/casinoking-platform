"""MAN-01 — Il manichino produce la stessa contabilita' di un gioco vero.

PERCHE' QUESTO TEST E' IL PIU' IMPORTANTE DELLA FASE 7. Il manichino serve a
collaudare la contabilita' della piattaforma **senza** un gioco dentro. Se pero'
scrivesse nel registro contabile in modo diverso da come ci scrive Mines, tutti i
test ricuciti su di lui direbbero una cosa che non vale per i giochi veri: un verde
che non significa niente, cioe' esattamente il difetto contro cui nasce tutta questa
storia.

Quindi qui si gioca lo stesso round due volte — una con Mines, una col manichino,
stessa puntata — e si confronta cio' che resta nel registro.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from tests.integration.helpers import create_game_access_session

PUNTATA = "5.000000"

# PERCHE' LE CHIAVI DI IDEMPOTENZA SONO UNICHE A OGNI ESECUZIONE: con chiavi fisse la
# seconda corsa del test riusa il round della prima invece di aprirne uno nuovo, e il
# test smette di essere ripetibile. Scoperto sabotando apposta il manichino per
# verificare che questa prova sapesse diventare rossa: e' rimasta rossa anche dopo aver
# tolto il sabotaggio.


def _scritture(db_helpers, session_id: str) -> list[tuple]:
    """Le scritture contabili lasciate da un round: tipo, conti, lati e IMPORTI.

    PERCHE' NON BASTANO I TIPI. La prima versione di questo test confrontava solo la
    sequenza dei tipi di movimento (`bet`, `win`). Codex l'ha respinta in revisione, e
    aveva ragione due volte: due registrazioni contabilmente diverse — per esempio una
    vincita accreditata sul conto sbagliato — sarebbero passate per identiche; e due
    liste VUOTE sarebbero passate anche loro, perche' `[] == []` e' vero. Una prova che
    non puo' fallire non e' una prova.
    """
    fuori: list[tuple] = []
    for transazione in db_helpers.get_game_transactions(session_id):
        # ORDINATE: le due righe di una partita doppia (dare e avere) non hanno un
        # ordine con un significato — la query le tira fuori per `created_at, id`, e
        # dentro la stessa transazione l'istante coincide, quindi decide l'id, che e'
        # casuale. Confrontarle in ordine rendeva questo test intermittente pur essendo
        # la contabilita' identica. L'ordine FRA le transazioni invece conta (prima la
        # puntata, poi la vincita) e resta quello del registro.
        entrate = sorted(
            (str(e["account_code"]), str(e["entry_side"]), str(e["amount"]))
            for e in db_helpers.get_transaction_entries(str(transazione["id"]))
        )
        assert entrate, (
            f"La transazione {transazione['id']} non ha nessuna scrittura contabile: "
            "un movimento senza righe non e' contabilita'."
        )
        fuori.append((str(transazione["transaction_type"]), entrate))
    return fuori


def _round_mines(client, headers, db_helpers, title_code: str) -> tuple[str, Decimal]:
    access_session_id = create_game_access_session(
        client, headers, game_code="mines", title_code=title_code
    )
    avvio = client.post(
        "/games/mines/start",
        headers={**headers, "Idempotency-Key": f"parita-mines-start-{uuid4().hex}"},
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": PUNTATA,
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert avvio.status_code == 200, avvio.text
    session_id = avvio.json()["data"]["game_session_id"]

    mine = set(db_helpers.get_mine_positions(session_id))
    casella_sicura = next(i for i in range(25) if i not in mine)
    scopri = client.post(
        "/games/mines/reveal",
        headers=headers,
        json={"game_session_id": session_id, "cell_index": casella_sicura},
    )
    assert scopri.status_code == 200, scopri.text
    incasso = client.post(
        "/games/mines/cashout",
        headers={**headers, "Idempotency-Key": f"parita-mines-cashout-{uuid4().hex}"},
        json={"game_session_id": session_id},
    )
    assert incasso.status_code == 200, incasso.text
    return session_id, Decimal(str(incasso.json()["data"]["payout_amount"]))


def _round_manichino(client, headers, db_helpers, payout: Decimal) -> str:
    avvio = client.post(
        "/games/manichino/start",
        headers={**headers, "Idempotency-Key": f"parita-manichino-start-{uuid4().hex}"},
        json={"bet_amount": PUNTATA, "wallet_type": "cash"},
    )
    assert avvio.status_code == 200, avvio.text
    session_id = avvio.json()["data"]["game_session_id"]

    chiusura = client.post(
        "/games/manichino/settle",
        headers={**headers, "Idempotency-Key": f"parita-manichino-settle-{uuid4().hex}"},
        json={
            "game_session_id": session_id,
            "esito": "vincita",
            "payout_amount": f"{payout:.6f}",
        },
    )
    assert chiusura.status_code == 200, chiusura.text
    return session_id


def test_il_manichino_scrive_nel_registro_come_mines(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    giocatore = create_authenticated_player(prefix="parita-manichino")
    headers = auth_headers(giocatore["access_token"])
    title_code = auth_headers.implicit_title_code() or "mines_auth_default"

    sessione_mines, payout = _round_mines(client, headers, db_helpers, title_code)
    sessione_manichino = _round_manichino(client, headers, db_helpers, payout)

    scritture_mines = _scritture(db_helpers, sessione_mines)
    scritture_manichino = _scritture(db_helpers, sessione_manichino)

    # Una prova che passerebbe sul vuoto non prova niente: prima si pretende che
    # qualcosa sia stato scritto davvero, da entrambe le parti.
    assert scritture_mines, "Il round di Mines non ha lasciato nessuna scrittura contabile"
    assert scritture_manichino, "Il round del manichino non ha lasciato nessuna scrittura contabile"

    assert scritture_manichino == scritture_mines, (
        "Il manichino scrive nel registro in modo diverso da Mines a parita' di "
        f"puntata e vincita.\n  manichino = {scritture_manichino}\n  mines     = {scritture_mines}\n"
        "Finche' differiscono, i test ricuciti sul manichino non dicono nulla sui giochi veri."
    )


def test_dopo_un_round_del_manichino_il_portafoglio_quadra(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    """La stessa verifica di test_reconciliation_integrity, ma senza nessun gioco vero."""
    giocatore = create_authenticated_player(prefix="quadratura-manichino")
    headers = auth_headers(giocatore["access_token"])

    _round_manichino(client, headers, db_helpers, Decimal("9.500000"))

    quadratura = db_helpers.get_wallet_reconciliation(str(giocatore["user_id"]), "cash")
    assert quadratura["drift"] == "0.000000", (
        f"Il portafoglio non quadra dopo un round del manichino: {quadratura}"
    )
    assert quadratura["balance_snapshot"] == quadratura["ledger_balance"]
