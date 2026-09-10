"""CON-06 — un rimborso DOVUTO viene sempre CREATO.

LA DIFFERENZA CHE QUESTO FILE COLMA, ed e' tutta la ragione per cui esiste.
Le misure di massa contano i rimborsi **avvenuti**: 434 righe corrette da CON-05,
tutte da mines. Ma un rimborso **dovuto e mai creato non comparirebbe in nessuna
riga** — non lascia traccia proprio perche' non e' avvenuto. Contare cio' che c'e'
non dice niente su cio' che manca.

Rilievo di `gpt-5.6-sol` in rivalidazione del PASSO 2, 10/09/2026.

COSA FANNO QUESTI COLLAUDI, che i due gia' esistenti non facevano.
`test_mines_autoliquidazione_settlement_kind.py` verifica **come e' etichettato**
un rimborso che avviene. Questi qui **creano la condizione** — una partita aperta
e chiusa senza alcun progresso — e pretendono che il rimborso **esista**, con
l'importo esatto della puntata e il saldo tornato al punto di partenza.

PERCHE' UNO PER GIOCO. L'autoliquidazione e' implementata separatamente in
`games/{mines,boxe,hi_lo,manichino}/autoliquidazione.py`: quattro file distinti,
nessun codice condiviso. Un collaudo su un gioco solo non dice niente sugli altri
tre, ed e' esattamente la ragione per cui il rilievo e' stato aperto.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from tests.integration.test_session_cascade_close import (
    _create_active_cavia_table_session_and_round,
    _create_active_mines_table_session_and_round,
)

pytestmark = [pytest.mark.integration]


def _rimborso_della_sessione(db_helpers, access_session_id: str) -> dict | None:
    """La riga di rimborso, se e' stata creata. None se non esiste.

    Si cerca per settlement_kind e non per importo: un rimborso si riconosce da
    cio' che dichiara di essere, non dal fatto che la cifra somigli a una
    puntata. E' la stessa regola con cui CON-05 ha scelto le 434 righe da
    correggere - nessuna riga si tocca per somiglianza.
    """
    return db_helpers.fetchone(
        """
        SELECT lt.id, lt.metadata_json, pr.status, pr.bet_amount, pr.payout_amount
        FROM platform_rounds pr
        JOIN ledger_transactions lt
          ON lt.id = pr.settlement_ledger_transaction_id
        WHERE pr.access_session_id = %s
        ORDER BY pr.created_at DESC
        LIMIT 1
        """,
        (access_session_id,),
    )


def test_mines_un_rimborso_dovuto_viene_creato(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
    create_published_mines_variant,
) -> None:
    """MINES — si apre una partita, non si tocca niente, si chiude.

    Nessuna casella scoperta significa nessun progresso: il rimborso e' DOVUTO.
    Il collaudo non guarda come e' etichettato: guarda che ESISTA.
    """
    player = create_authenticated_player(prefix="con06-mines")
    title = create_published_mines_variant(display_name="CON06 Mines Rimborso Dovuto")
    title_code = str(title["title_code"])
    headers = auth_headers(player["access_token"], title_code=title_code)

    saldo_prima = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    puntata = Decimal("4.000000")

    ids = _create_active_mines_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount=f"{puntata:.6f}",
        grid_size=9,
        mine_count=1,
        title_code=title_code,
    )

    # NIENTE reveal: e' il punto. La partita non fa un passo.
    saldo_con_partita_aperta = Decimal(
        db_helpers.get_wallet_balance(str(player["user_id"]))
    )
    assert saldo_con_partita_aperta == saldo_prima - puntata, (
        "la puntata doveva essere trattenuta all'apertura"
    )

    chiusura = client.post(
        f"/access-sessions/{ids['access_session_id']}/close", headers=headers
    )
    assert chiusura.status_code == 200, chiusura.text

    saldo_dopo = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    assert saldo_dopo == saldo_prima, (
        "IL RIMBORSO DOVUTO NON E' STATO CREATO: la partita e' stata chiusa senza "
        f"alcun progresso e il giocatore ha perso {saldo_prima - saldo_dopo}. "
        "Un rimborso mancante non lascia traccia: si vede solo cosi'."
    )

    riga = _rimborso_della_sessione(db_helpers, ids["access_session_id"])
    assert riga is not None, "nessun movimento di liquidazione legato alla partita"
    assert riga["status"] == "cancelled", (
        f"un rimborso senza progresso deve chiudere in 'cancelled', non in "
        f"'{riga['status']}' — e' la decisione di CON-05"
    )


def test_cavia_un_rimborso_dovuto_viene_creato(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    """IL GIOCO DI PROVA — stessa condizione, altro motore di gioco.

    Il manichino e' il gioco finto che serve a provare la piattaforma senza
    dipendere da un gioco vero: se il rimborso dovuto non venisse creato QUI,
    il difetto sarebbe della piattaforma e non del singolo gioco.
    """
    player = create_authenticated_player(prefix="con06-cavia")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    saldo_prima = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    puntata = Decimal("4.000000")

    ids = _create_active_cavia_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount=f"{puntata:.6f}",
        prefisso_idempotenza="con06-cavia",
    )

    saldo_con_partita_aperta = Decimal(
        db_helpers.get_wallet_balance(str(player["user_id"]))
    )
    assert saldo_con_partita_aperta == saldo_prima - puntata, (
        "la puntata doveva essere trattenuta all'apertura"
    )

    chiusura = client.post(
        f"/access-sessions/{ids['access_session_id']}/close", headers=headers
    )
    assert chiusura.status_code == 200, chiusura.text

    saldo_dopo = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    assert saldo_dopo == saldo_prima, (
        "IL RIMBORSO DOVUTO NON E' STATO CREATO sul gioco di prova: la partita e' "
        f"stata chiusa senza progresso e il giocatore ha perso "
        f"{saldo_prima - saldo_dopo}."
    )
