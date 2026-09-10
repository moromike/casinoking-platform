from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]
"""PRV-03 — il titolo del fornitore di collaudo percorre il lancio completo."""


from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.modules.games.manichino import TITLE_CODE_MANICHINO_TEST, manichino_attivo
from tests.integration.test_manichino_parita_con_mines import PUNTATA, _scritture




# IMPEGNO: PRV-03 — senza l'interruttore la cavia non espone volutamente le rotte.
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


def _crea_access_session(client, headers, *, game_code: str, title_code: str) -> str:
    """La sessione d'accesso, chiesta al client IN-PROCESSO.

    PERCHE' NON L'HELPER CONDIVISO: `tests/integration/helpers.py` chiama
    "/access-sessions" senza prefisso, perche' e' scritto per il client HTTP live, il
    cui base_url finisce gia' in `/api/v1`. Il TestClient in-processo monta l'app a
    partire dalla radice, quindi lo stesso percorso risponde 404 — e un 404 qui si
    legge come "la sessione non si apre", cioe' esattamente il difetto che questo
    collaudo deve saper distinguere.
    """
    response = client.post(
        "/api/v1/access-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": "casinoking",
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["id"])


def _login_in_process(client: TestClient, *, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["access_token"])


def _issue_token(client: TestClient, *, token: str, game_code: str, title_code: str) -> str:
    response = _issue_token_response(
        client, token=token, game_code=game_code, title_code=title_code
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["game_launch_token"])


def _issue_token_response(client: TestClient, *, token: str, game_code: str, title_code: str):
    return client.post(
        "/api/v1/games/mines/launch-token",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": "casinoking",
            "mode": "real",
        },
    )


def _headers(token: str, game_launch_token: str, *, idempotency_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Game-Launch-Token": game_launch_token,
        "Idempotency-Key": idempotency_key,
    }


def _start_manichino(
    client: TestClient,
    *,
    token: str,
    game_launch_token: str,
    access_session_id: str,
    bet_amount: str = "1.000000",
):
    response = client.post(
        "/api/v1/games/manichino/start",
        headers=_headers(token, game_launch_token, idempotency_key=f"provider-start-{uuid4().hex}"),
        json={
            "bet_amount": bet_amount,
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert response.status_code == 200, response.text
    return response


def _settle_manichino(client: TestClient, *, token: str, game_launch_token: str, session_id: str):
    return client.post(
        "/api/v1/games/manichino/settle",
        headers=_headers(token, game_launch_token, idempotency_key=f"provider-settle-{uuid4().hex}"),
        json={"game_session_id": session_id, "esito": "vincita", "payout_amount": "1.900000"},
    )


def test_titolo_provider_collaudo_lancia_e_quadra(
    manichino_client, create_player, db_helpers
) -> None:
    player = create_player(prefix="provider-title")
    token = _login_in_process(
        manichino_client, email=str(player["email"]), password=str(player["password"])
    )

    token_response = _issue_token_response(
        manichino_client, token=token, game_code="manichino", title_code=TITLE_CODE_MANICHINO_TEST
    )
    assert token_response.status_code == 200, token_response.text
    game_launch_token = str(token_response.json()["data"]["game_launch_token"])
    access_response = manichino_client.post(
        "/api/v1/access-sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "game_code": "manichino",
            "title_code": TITLE_CODE_MANICHINO_TEST,
            "site_code": "casinoking",
        },
    )
    # L'ordine conta: dopo il controllo 200 il messaggio non potrebbe piu' comparire,
    # mentre qui segnala direttamente il ritorno del blocco improprio della vetrina.
    assert "Title is not visible in the player library" not in access_response.text
    assert access_response.status_code == 200, access_response.text
    access_session_id = str(access_response.json()["data"]["id"])
    started = _start_manichino(
        manichino_client,
        token=token,
        game_launch_token=game_launch_token,
        access_session_id=access_session_id,
    )
    settled = _settle_manichino(
        manichino_client,
        token=token,
        game_launch_token=game_launch_token,
        session_id=str(started.json()["data"]["game_session_id"]),
    )

    assert settled.status_code == 200, settled.text
    session_id = str(started.json()["data"]["game_session_id"])
    assert db_helpers.get_wallet_balance(str(player["user_id"]), "cash") == "1000.900000"
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")["drift"] == "0.000000"
    assert [str(tx["transaction_type"]) for tx in db_helpers.get_game_transactions(session_id)] == [
        "bet",
        "win",
    ]


def test_titolo_provider_nascosto_blocca_l_access_session_e_si_ripristina(
    manichino_client, create_player, db_connection
) -> None:
    player = create_player(prefix="provider-hidden")
    token = _login_in_process(
        manichino_client, email=str(player["email"]), password=str(player["password"])
    )
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE site_titles SET lobby_visibility = 'hidden' "
                "WHERE site_code = 'casinoking' AND title_code = %s",
                (TITLE_CODE_MANICHINO_TEST,),
            )
        response = manichino_client.post(
            "/api/v1/access-sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "game_code": "manichino",
                "title_code": TITLE_CODE_MANICHINO_TEST,
                "site_code": "casinoking",
            },
        )
        assert response.status_code != 200, response.text
        assert response.json()["error"]["message"] == "Title is not visible in the player library"
    finally:
        # Il titolo e' condiviso dalla suite: lasciarlo nascosto avvelenerebbe gli altri test.
        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE site_titles SET lobby_visibility = 'visible' "
                "WHERE site_code = 'casinoking' AND title_code = %s",
                (TITLE_CODE_MANICHINO_TEST,),
            )


def test_titolo_provider_scrive_come_mines_attraverso_lancio_e_access_session(
    manichino_client, create_player, create_published_mines_variant, db_helpers, mines_db_helpers
) -> None:
    player = create_player(prefix="provider-parita")
    token = _login_in_process(
        manichino_client, email=str(player["email"]), password=str(player["password"])
    )
    # PERCHE' UNA VARIANTE E NON `mines001`: la parita' apre un round VERO di Mines, e
    # Mines pretende che la coppia griglia/mine sia PUBBLICATA per quel titolo. Su
    # `mines001` non lo e', e la prova morirebbe con
    # "The selected grid_size and mine_count are not published" — un rosso che non dice
    # niente sulla parita' contabile, cioe' rumore al posto del segnale.
    mines_title_code = str(create_published_mines_variant()["title_code"])

    mines_token = _issue_token(
        manichino_client, token=token, game_code="mines", title_code=mines_title_code
    )
    mines_access_session_id = _crea_access_session(
        manichino_client,
        {"Authorization": f"Bearer {token}"},
        game_code="mines",
        title_code=mines_title_code,
    )
    mines_start = manichino_client.post(
        "/api/v1/games/mines/start",
        headers=_headers(token, mines_token, idempotency_key=f"provider-mines-start-{uuid4().hex}"),
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": PUNTATA,
            "wallet_type": "cash",
            "access_session_id": mines_access_session_id,
        },
    )
    assert mines_start.status_code == 200, mines_start.text
    mines_session_id = str(mines_start.json()["data"]["game_session_id"])
    mine_positions = set(mines_db_helpers.get_mine_positions(mines_session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)
    reveal = manichino_client.post(
        "/api/v1/games/mines/reveal",
        headers={"Authorization": f"Bearer {token}"},
        json={"game_session_id": mines_session_id, "cell_index": safe_cell},
    )
    assert reveal.status_code == 200, reveal.text
    cashout = manichino_client.post(
        "/api/v1/games/mines/cashout",
        headers=_headers(token, mines_token, idempotency_key=f"provider-mines-cashout-{uuid4().hex}"),
        json={"game_session_id": mines_session_id},
    )
    assert cashout.status_code == 200, cashout.text

    manichino_token = _issue_token(
        manichino_client, token=token, game_code="manichino", title_code=TITLE_CODE_MANICHINO_TEST
    )
    manichino_access_session_id = _crea_access_session(
        manichino_client,
        {"Authorization": f"Bearer {token}"},
        game_code="manichino",
        title_code=TITLE_CODE_MANICHINO_TEST,
    )
    manichino_start = _start_manichino(
        manichino_client,
        token=token,
        game_launch_token=manichino_token,
        access_session_id=manichino_access_session_id,
        bet_amount=PUNTATA,
    )
    manichino_session_id = str(manichino_start.json()["data"]["game_session_id"])
    manichino_settle = manichino_client.post(
        "/api/v1/games/manichino/settle",
        headers=_headers(token, manichino_token, idempotency_key=f"provider-manichino-settle-{uuid4().hex}"),
        json={
            "game_session_id": manichino_session_id,
            "esito": "vincita",
            "payout_amount": str(cashout.json()["data"]["payout_amount"]),
        },
    )
    assert manichino_settle.status_code == 200, manichino_settle.text

    scritture_mines = _scritture(db_helpers, mines_db_helpers, mines_session_id)
    scritture_manichino = _scritture(db_helpers, mines_db_helpers, manichino_session_id)
    assert scritture_mines, "Il round di Mines non ha lasciato nessuna scrittura contabile"
    assert scritture_manichino, "Il round del manichino non ha lasciato nessuna scrittura contabile"
    assert scritture_manichino == scritture_mines
