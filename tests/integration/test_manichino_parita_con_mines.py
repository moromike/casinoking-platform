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

import pytest

from tests.integration.helpers import create_game_access_session

PUNTATA = "5.000000"


def _tipi_delle_scritture(db_helpers, session_id: str) -> list[str]:
    """I tipi di movimento contabile lasciati da un round, in ordine."""
    tipi: list[str] = []
    for transazione in db_helpers.get_game_transactions(session_id):
        tipi.append(str(transazione["transaction_type"]))
    return tipi


def _round_mines(client, headers, db_helpers, title_code: str) -> tuple[str, Decimal]:
    access_session_id = create_game_access_session(
        client, headers, game_code="mines", title_code=title_code
    )
    avvio = client.post(
        "/games/mines/start",
        headers={**headers, "Idempotency-Key": "parita-mines-start"},
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
        headers={**headers, "Idempotency-Key": "parita-mines-cashout"},
        json={"game_session_id": session_id},
    )
    assert incasso.status_code == 200, incasso.text
    return session_id, Decimal(str(incasso.json()["data"]["payout_amount"]))


def _round_manichino(client, headers, db_helpers, payout: Decimal) -> str:
    avvio = client.post(
        "/games/manichino/start",
        headers={**headers, "Idempotency-Key": "parita-manichino-start"},
        json={"bet_amount": PUNTATA, "wallet_type": "cash"},
    )
    assert avvio.status_code == 200, avvio.text
    session_id = avvio.json()["data"]["game_session_id"]

    chiusura = client.post(
        "/games/manichino/settle",
        headers={**headers, "Idempotency-Key": "parita-manichino-settle"},
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

    tipi_mines = _tipi_delle_scritture(db_helpers, sessione_mines)
    tipi_manichino = _tipi_delle_scritture(db_helpers, sessione_manichino)

    assert tipi_manichino == tipi_mines, (
        "Il manichino lascia scritture contabili diverse da Mines a parita' di "
        f"puntata e vincita: manichino={tipi_manichino} mines={tipi_mines}. "
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
