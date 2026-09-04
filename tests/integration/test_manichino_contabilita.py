"""Contabilita' del manichino: la cavia che muove un euro attraverso le tubature vere.

PERCHE' IN-PROCESS E NON VIA HTTP: il backend dello stack gira senza
CK_MANICHINO, quindi le rotte del manichino non esistono li'. I test
costruiscono l'app nel processo di test — dove ck-test.sh propaga
CK_MANICHINO=1 — contro lo STESSO database dello stack: tubature vere,
interruttore vero.

PERCHE' IL GIOCATORE SI REGISTRA VIA API LIVE: il fixture `create_player`
registra sul backend dello stack e ripulisce il DB a fine test. Il login
invece avviene in-process: il token deve essere firmato con il segreto JWT
che vede il TestClient, non quello del container backend.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.modules.games.manichino import TITLE_CODE_MANICHINO_TEST, manichino_attivo

# PERCHE' skip e non fallimento: senza CK_MANICHINO il modulo e' spento per
# contratto (MAN-05) e questi test non hanno nulla da verificare.
pytestmark = pytest.mark.skipif(
    not manichino_attivo(),
    reason="manichino spento: serve CK_MANICHINO=1",
)


@pytest.fixture
def manichino_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def manichino_title(db_connection) -> str:
    # PERCHE' una INSERT diretta e niente catalogo: il titolo serve solo a
    # soddisfare la FK di platform_rounds.title_code. Non va in `site_titles`,
    # cosi' il manichino non compare in lobby ne' nel catalogo pubblico.
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
            VALUES ('manichino', 'Manichino', 'app.modules.games.manichino.service', 'active')
            ON CONFLICT (engine_code) DO NOTHING
            """
        )
        cursor.execute(
            """
            INSERT INTO game_titles (title_code, engine_code, display_name, status)
            VALUES (%s, 'manichino', 'Manichino Test', 'active')
            ON CONFLICT (title_code) DO NOTHING
            """,
            (TITLE_CODE_MANICHINO_TEST,),
        )
    return TITLE_CODE_MANICHINO_TEST


def _login_in_process(client: TestClient, *, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["access_token"])


def _start_round(client: TestClient, *, token: str, idempotency_key: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/games/manichino/start",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
        json={"bet_amount": "1.000000", "wallet_type": "cash"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _settle_round(
    client: TestClient,
    *,
    token: str,
    game_session_id: str,
    esito: str,
    idempotency_key: str,
    payout_amount: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"game_session_id": game_session_id, "esito": esito}
    if payout_amount is not None:
        payload["payout_amount"] = payout_amount
    response = client.post(
        "/api/v1/games/manichino/settle",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
        json=payload,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_manichino_vincita_muove_portafoglio_e_registro(
    manichino_client,
    manichino_title,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="manichino-vincita")
    user_id = str(player["user_id"])
    token = _login_in_process(
        manichino_client,
        email=str(player["email"]),
        password=str(player["password"]),
    )
    assert db_helpers.get_wallet_balance(user_id, "cash") == "1000.000000"

    started = _start_round(
        manichino_client,
        token=token,
        idempotency_key=f"manichino-test-start-{uuid4().hex}",
    )
    assert started["game_session_id"]
    assert started["wallet_balance_after_start"] == "999.000000"
    assert started["ledger_transaction_id"]

    settled = _settle_round(
        manichino_client,
        token=token,
        game_session_id=str(started["game_session_id"]),
        esito="vincita",
        payout_amount="1.900000",
        idempotency_key=f"manichino-test-settle-{uuid4().hex}",
    )
    assert settled["wallet_balance_after"] == "1000.900000"
    assert settled["ledger_transaction_id"]
    assert settled["already_exists"] is False

    # Il portafoglio e' cresciuto di 0,90 e il registro quadra.
    assert db_helpers.get_wallet_balance(user_id, "cash") == "1000.900000"
    assert db_helpers.get_wallet_reconciliation(user_id, "cash")["drift"] == "0.000000"

    transactions = db_helpers.get_game_transactions(str(started["game_session_id"]))
    by_type = {str(tx["transaction_type"]): tx for tx in transactions}
    assert set(by_type) == {"bet", "win"}
    win_entries = db_helpers.get_transaction_entries(str(by_type["win"]["id"]))
    assert {
        (str(entry["entry_side"]), f"{Decimal(entry['amount']):.6f}") for entry in win_entries
    } == {("debit", "1.900000"), ("credit", "1.900000")}
    # La vincita esce di casa: addebito su HOUSE_CASH, accredito al giocatore.
    house_sides = {
        str(entry["entry_side"])
        for entry in win_entries
        if entry["account_code"] == "HOUSE_CASH"
    }
    assert house_sides == {"debit"}


def test_manichino_perdita_scala_esattamente_la_puntata(
    manichino_client,
    manichino_title,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="manichino-perdita")
    user_id = str(player["user_id"])
    token = _login_in_process(
        manichino_client,
        email=str(player["email"]),
        password=str(player["password"]),
    )

    started = _start_round(
        manichino_client,
        token=token,
        idempotency_key=f"manichino-test-start-{uuid4().hex}",
    )
    settled = _settle_round(
        manichino_client,
        token=token,
        game_session_id=str(started["game_session_id"]),
        esito="perdita",
        idempotency_key=f"manichino-test-settle-{uuid4().hex}",
    )
    assert settled["wallet_balance_after"] == "999.000000"

    # Il portafoglio e' calato di 1 euro esatto e il registro quadra.
    assert db_helpers.get_wallet_balance(user_id, "cash") == "999.000000"
    assert db_helpers.get_wallet_reconciliation(user_id, "cash")["drift"] == "0.000000"

    transactions = db_helpers.get_game_transactions(str(started["game_session_id"]))
    assert [str(tx["transaction_type"]) for tx in transactions] == ["bet"]


def test_manichino_settle_ripetuto_scrive_una_sola_volta(
    manichino_client,
    manichino_title,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="manichino-idempotenza")
    user_id = str(player["user_id"])
    token = _login_in_process(
        manichino_client,
        email=str(player["email"]),
        password=str(player["password"]),
    )

    started = _start_round(
        manichino_client,
        token=token,
        idempotency_key=f"manichino-test-start-{uuid4().hex}",
    )
    settle_key = f"manichino-test-settle-{uuid4().hex}"
    first = _settle_round(
        manichino_client,
        token=token,
        game_session_id=str(started["game_session_id"]),
        esito="vincita",
        payout_amount="1.900000",
        idempotency_key=settle_key,
    )
    second = _settle_round(
        manichino_client,
        token=token,
        game_session_id=str(started["game_session_id"]),
        esito="vincita",
        payout_amount="1.900000",
        idempotency_key=settle_key,
    )
    assert first["already_exists"] is False
    assert second["already_exists"] is True
    assert second["ledger_transaction_id"] == first["ledger_transaction_id"]

    # Una sola scrittura contabile di vincita, saldo accreditato una volta sola.
    win_transactions = [
        tx
        for tx in db_helpers.get_game_transactions(str(started["game_session_id"]))
        if tx["transaction_type"] == "win"
    ]
    assert len(win_transactions) == 1
    assert db_helpers.get_wallet_balance(user_id, "cash") == "1000.900000"
    assert db_helpers.get_wallet_reconciliation(user_id, "cash")["drift"] == "0.000000"


def test_manichino_non_ha_rotte_anonime(manichino_client) -> None:
    # Stesse regole delle rotte di Mines: senza bearer non si entra.
    response = manichino_client.post(
        "/api/v1/games/manichino/start",
        headers={"Idempotency-Key": f"manichino-test-anon-{uuid4().hex}"},
        json={"bet_amount": "1.000000", "wallet_type": "cash"},
    )
    assert response.status_code == 401
