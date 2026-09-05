"""CAP-03: registro e fail-closed della liquidazione d'ufficio."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.modules.platform.access_sessions import registro_liquidazione
from app.modules.platform.access_sessions.bootstrap_liquidazione import assicura_iscrizioni
from app.modules.platform.manichino_flag import GAME_CODE_MANICHINO, manichino_attivo
from tests.integration.helpers import apri_partita_cavia


pytestmark = pytest.mark.skipif(
    not manichino_attivo(), reason="manichino spento: serve CK_MANICHINO=1"
)


@pytest.fixture
def cap03_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    with TestClient(app) as test_client:
        yield test_client


def _headers_in_process(client: TestClient, player: dict[str, object]) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": player["email"], "password": player["password"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _apri_cavia(
    client: TestClient,
    headers: dict[str, str],
    *,
    bet_amount: str = "5.000000",
) -> dict[str, str]:
    return apri_partita_cavia(
        client,
        headers,
        bet_amount=bet_amount,
        prefisso_idempotenza="cap03",
        prefisso="/api/v1",
    )


def _apri_mines_senza_progressi(
    client: TestClient,
    headers: dict[str, str],
    *,
    title_code: str,
    bet_amount: str = "5.000000",
) -> dict[str, str]:
    access_response = client.post(
        "/api/v1/access-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "title_code": title_code,
            "site_code": "casinoking",
        },
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = str(access_response.json()["data"]["id"])
    # PERCHE' il gettone: /games/mines/start lo pretende in modalita' reale, e va emesso
    # per LO STESSO titolo su cui si apre la partita. Senza, risponde 401 e la parita'
    # non si potrebbe nemmeno misurare.
    token_response = client.post(
        "/api/v1/games/mines/launch-token",
        headers=headers,
        json={
            "game_code": "mines",
            "title_code": title_code,
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert token_response.status_code == 200, token_response.text
    game_launch_token = str(token_response.json()["data"]["game_launch_token"])
    start_response = client.post(
        "/api/v1/games/mines/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"cap03-mines-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": bet_amount,
            "wallet_type": "cash",
            "access_session_id": access_session_id,
            "title_code": title_code,
        },
    )
    assert start_response.status_code == 200, start_response.text
    return {
        "access_session_id": access_session_id,
        "game_session_id": str(start_response.json()["data"]["game_session_id"]),
    }


def _chiudi(client: TestClient, headers: dict[str, str], access_session_id: str):
    return client.post(
        f"/api/v1/access-sessions/{access_session_id}/close",
        headers=headers,
    )


def _firma_scritture_liquidazione(
    db_helpers, transaction_id: str, *, bet_amount: Decimal
) -> tuple[str, list[tuple]]:
    transaction = db_helpers.fetchone(
        "SELECT transaction_type FROM ledger_transactions WHERE id = %s",
        (transaction_id,),
    )
    assert transaction is not None
    entries = db_helpers.get_transaction_entries(transaction_id)
    assert entries
    # PERCHE' ANCHE L'IMPORTO. Confrontare solo conti e lati lascia passare un rimborso
    # dell'importo sbagliato: stessi conti, stessi lati, cifra diversa. Gli importi si
    # confrontano NORMALIZZATI sulla puntata, perche' le due partite possono avere
    # puntate diverse e cio' che deve coincidere e' il RAPPORTO, non il numero.
    signature = sorted(
        (
            str(entry["account_code"]),
            str(entry["entry_side"]),
            f"{(Decimal(entry['amount']) / bet_amount):.6f}",
        )
        for entry in entries
    )
    return str(transaction["transaction_type"]), signature


def test_close_liquida_il_round_aperto_della_cavia(
    cap03_client, create_player, db_helpers
) -> None:
    player = create_player(prefix="cap03-close-cavia")
    headers = _headers_in_process(cap03_client, player)
    cavia = _apri_cavia(cap03_client, headers)

    response = _chiudi(cap03_client, headers, cavia["access_session_id"])

    assert response.status_code == 200, response.text
    auto_cashout = response.json()["data"]["auto_cashout"]
    assert auto_cashout is not None
    assert auto_cashout["game_code"] == GAME_CODE_MANICHINO
    assert auto_cashout["settlement_mode"] == "refund"
    round_row = db_helpers.fetchone(
        """
        SELECT status, closed_at, settlement_ledger_transaction_id
        FROM platform_rounds
        WHERE id = %s
        """,
        (cavia["game_session_id"],),
    )
    assert round_row is not None
    assert round_row["status"] != "active"
    assert round_row["closed_at"] is not None
    assert round_row["settlement_ledger_transaction_id"] is not None


def test_liquidazione_cavia_e_refund_mines_hanno_scritture_pari(
    cap03_client,
    create_player,
    create_published_mines_variant,
    db_helpers,
) -> None:
    player = create_player(prefix="cap03-parita")
    headers = _headers_in_process(cap03_client, player)
    title = create_published_mines_variant(display_name="CAP-03 Mines Refund")
    mines = _apri_mines_senza_progressi(
        cap03_client,
        headers,
        title_code=str(title["title_code"]),
    )
    cavia = _apri_cavia(cap03_client, headers)

    mines_close = _chiudi(cap03_client, headers, mines["access_session_id"])
    cavia_close = _chiudi(cap03_client, headers, cavia["access_session_id"])
    assert mines_close.status_code == 200, mines_close.text
    assert cavia_close.status_code == 200, cavia_close.text
    mines_tx = str(mines_close.json()["data"]["auto_cashout"]["ledger_transaction_id"])
    cavia_tx = str(cavia_close.json()["data"]["auto_cashout"]["ledger_transaction_id"])
    firma_mines = _firma_scritture_liquidazione(
        db_helpers, mines_tx, bet_amount=Decimal("5.000000")
    )
    firma_cavia = _firma_scritture_liquidazione(
        db_helpers, cavia_tx, bet_amount=Decimal("5.000000")
    )

    print("gioco | tipo_transazione | conto | lato | importo/puntata")
    for gioco, firma in (("mines", firma_mines), ("manichino", firma_cavia)):
        tipo, scritture = firma
        for conto, lato, rapporto in scritture:
            print(f"{gioco} | {tipo} | {conto} | {lato} | {rapporto}")

    assert firma_cavia == firma_mines


def test_portafoglio_quadra_dopo_liquidazione_cavia(
    cap03_client, create_player, db_helpers
) -> None:
    player = create_player(prefix="cap03-quadratura")
    headers = _headers_in_process(cap03_client, player)
    cavia = _apri_cavia(cap03_client, headers)

    response = _chiudi(cap03_client, headers, cavia["access_session_id"])

    assert response.status_code == 200, response.text
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")[
        "drift"
    ] == "0.000000"


def test_registro_svuotato_per_cavia_blocca_la_chiusura(
    cap03_client, create_player, db_helpers, monkeypatch
) -> None:
    player = create_player(prefix="cap03-registro-vuoto")
    headers = _headers_in_process(cap03_client, player)
    cavia = _apri_cavia(cap03_client, headers)
    assicura_iscrizioni()
    senza_cavia = {
        code: handler
        for code, handler in registro_liquidazione._LIQUIDAZIONI.items()
        if code != GAME_CODE_MANICHINO
    }

    with monkeypatch.context() as context:
        context.setattr(registro_liquidazione, "_LIQUIDAZIONI", senza_cavia)
        response = _chiudi(cap03_client, headers, cavia["access_session_id"])

    assert response.status_code == 503
    round_row = db_helpers.fetchone(
        "SELECT status FROM platform_rounds WHERE id = %s",
        (cavia["game_session_id"],),
    )
    assert round_row is not None
    assert round_row["status"] == "active"
    assert _chiudi(cap03_client, headers, cavia["access_session_id"]).status_code == 200


def test_round_di_gioco_non_iscritto_blocca_la_chiusura(
    cap03_client, create_player, db_helpers, db_connection
) -> None:
    player = create_player(prefix="cap03-gioco-non-iscritto")
    headers = _headers_in_process(cap03_client, player)
    cavia = _apri_cavia(cap03_client, headers)
    codice_non_iscritto = "cap03_non_iscritto"
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            (codice_non_iscritto, cavia["game_session_id"]),
        )

    response = _chiudi(cap03_client, headers, cavia["access_session_id"])

    assert response.status_code == 503
    round_row = db_helpers.fetchone(
        "SELECT status FROM platform_rounds WHERE id = %s",
        (cavia["game_session_id"],),
    )
    assert round_row is not None
    assert round_row["status"] == "active"
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            (GAME_CODE_MANICHINO, cavia["game_session_id"]),
        )
    assert _chiudi(cap03_client, headers, cavia["access_session_id"]).status_code == 200


def test_una_sessione_non_liquidabile_non_blocca_le_altre(
    cap03_client, create_player, db_helpers, db_connection, monkeypatch
) -> None:
    """R1a — il fail-closed deve fermare QUELLA sessione, non lo spazzino.

    Le sessioni scadute si liquidano in ordine dalla piu' vecchia. Senza isolamento,
    una sola sessione i cui soldi non si possono restituire farebbe fallire l'intero
    lotto e, restando sempre la prima della lista, bloccherebbe la liquidazione di
    tutte le altre a ogni giro, per sempre.
    """
    from app.modules.platform.access_sessions.service import (
        timeout_expired_access_sessions,
    )

    guasto = create_player(prefix="cap03-guasta")
    headers_guasto = _headers_in_process(cap03_client, guasto)
    partita_guasta = _apri_cavia(cap03_client, headers_guasto)

    sano = create_player(prefix="cap03-sana")
    headers_sano = _headers_in_process(cap03_client, sano)
    partita_sana = _apri_cavia(cap03_client, headers_sano)

    # La sessione guasta e' la PIU' VECCHIA: e' quella che lo spazzino incontra per
    # prima, cioe' il caso peggiore.
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            ("cap03_mai_iscritto", partita_guasta["game_session_id"]),
        )
        cursor.execute(
            "UPDATE game_access_sessions SET last_activity_at = now() - interval '30 minutes' "
            "WHERE id = %s",
            (partita_guasta["access_session_id"],),
        )
        cursor.execute(
            "UPDATE game_access_sessions SET last_activity_at = now() - interval '10 minutes' "
            "WHERE id = %s",
            (partita_sana["access_session_id"],),
        )

    timeout_expired_access_sessions(limit=50)

    guasta = db_helpers.fetchone(
        "SELECT status FROM game_access_sessions WHERE id = %s",
        (partita_guasta["access_session_id"],),
    )
    sana = db_helpers.fetchone(
        "SELECT status FROM game_access_sessions WHERE id = %s",
        (partita_sana["access_session_id"],),
    )
    round_guasto = db_helpers.fetchone(
        "SELECT status FROM platform_rounds WHERE id = %s",
        (partita_guasta["game_session_id"],),
    )
    round_sano = db_helpers.fetchone(
        "SELECT status FROM platform_rounds WHERE id = %s",
        (partita_sana["game_session_id"],),
    )

    # La guasta resta aperta APPOSTA: i soldi non si potevano restituire.
    assert guasta["status"] == "active"
    assert round_guasto["status"] == "active"
    # La sana e' stata liquidata lo stesso: e' il punto di questo collaudo.
    assert sana["status"] == "timed_out", (
        "La sessione sana NON e' stata liquidata: una sessione guasta ha bloccato lo "
        "spazzino per tutte le altre."
    )
    assert round_sano["status"] != "active"

    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            (GAME_CODE_MANICHINO, partita_guasta["game_session_id"]),
        )


def test_un_round_non_liquidabile_non_impedisce_il_login(
    cap03_client, create_player, db_helpers, db_connection
) -> None:
    """R1b — il login chiama la chiusura forzata delle sessioni attive.

    Un round che non si puo' liquidare deve lasciare la SUA sessione aperta, non
    chiudere fuori il giocatore dal proprio conto.
    """
    player = create_player(prefix="cap03-login")
    headers = _headers_in_process(cap03_client, player)
    partita = _apri_cavia(cap03_client, headers)

    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            ("cap03_mai_iscritto", partita["game_session_id"]),
        )

    risposta = cap03_client.post(
        "/api/v1/auth/login",
        json={"email": player["email"], "password": player["password"]},
    )

    assert risposta.status_code == 200, (
        f"Il login e' stato rifiutato per un round non liquidabile: {risposta.text}"
    )
    sessione = db_helpers.fetchone(
        "SELECT status FROM game_access_sessions WHERE id = %s",
        (partita["access_session_id"],),
    )
    assert sessione["status"] == "active", (
        "La sessione si e' chiusa mentre i soldi restavano trattenuti."
    )

    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET game_code = %s WHERE id = %s",
            (GAME_CODE_MANICHINO, partita["game_session_id"]),
        )
