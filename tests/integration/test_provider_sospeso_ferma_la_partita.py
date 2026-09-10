from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]
"""PRV-04-bis — sospendere un fornitore ferma solo le sue partite."""


from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.modules.games.manichino import TITLE_CODE_MANICHINO_TEST, manichino_attivo
from tests.integration.test_lancio_titolo_provider import (


    _crea_access_session,
    _headers,
    _issue_token,
    _login_in_process,
    _start_manichino,
)


# IMPEGNO: PRV-04-bis — la cavia e' intenzionalmente assente se l'interruttore e' spento.
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


def test_provider_sospeso_blocca_settle_ma_non_mines(
    manichino_client,
    create_player,
    create_published_mines_variant,
    db_connection,
    db_helpers, mines_db_helpers,
) -> None:
    player = create_player(prefix="provider-sospeso")
    token = _login_in_process(
        manichino_client, email=str(player["email"]), password=str(player["password"])
    )
    manichino_token = _issue_token(
        manichino_client, token=token, game_code="manichino", title_code=TITLE_CODE_MANICHINO_TEST
    )
    manichino_access_session_id = _crea_access_session(
        manichino_client,
        {"Authorization": f"Bearer {token}"},
        game_code="manichino",
        title_code=TITLE_CODE_MANICHINO_TEST,
    )
    started = _start_manichino(
        manichino_client,
        token=token,
        game_launch_token=manichino_token,
        access_session_id=manichino_access_session_id,
    )
    manichino_session_id = str(started.json()["data"]["game_session_id"])

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM game_providers WHERE provider_code = 'ck_collaudo'"
        )
        original_status = str(cursor.fetchone()["status"])

    try:
        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE game_providers SET status = 'suspended' WHERE provider_code = 'ck_collaudo'"
            )

        rejected = manichino_client.post(
            "/api/v1/games/manichino/settle",
            headers=_headers(token, manichino_token, idempotency_key=f"provider-suspended-{uuid4().hex}"),
            json={
                "game_session_id": manichino_session_id,
                "esito": "vincita",
                "payout_amount": "1.900000",
            },
        )
        assert rejected.status_code == 403, rejected.text
        assert rejected.json()["error"]["code"] == "FORBIDDEN", rejected.text
        assert [str(tx["transaction_type"]) for tx in db_helpers.get_game_transactions(manichino_session_id)] == [
            "bet"
        ], f"Il round e' stato liquidato nonostante il provider sospeso: {rejected.text}"

        # Contrappeso: il provider interno resta disponibile, altrimenti abbiamo spento il casino.
        # PERCHE' NON `mines001`: il contrappeso apre un round VERO di Mines, e Mines
        # pretende che la coppia griglia/mine sia pubblicata per quel titolo. Il fixture
        # ne prepara una gia' pubblicata e la ripulisce da solo; `mines001` risponderebbe
        # "The selected grid_size and mine_count are not published", cioe' un rosso che
        # non c'entra niente con la sospensione del fornitore.
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
            headers=_headers(token, mines_token, idempotency_key=f"mines-counterweight-{uuid4().hex}"),
            json={
                "grid_size": 25,
                "mine_count": 3,
                "bet_amount": "1.000000",
                "wallet_type": "cash",
                "access_session_id": mines_access_session_id,
            },
        )
        assert mines_start.status_code == 200, mines_start.text
        mines_session_id = str(mines_start.json()["data"]["game_session_id"])
        mine_positions = set(mines_db_helpers.get_mine_positions(mines_session_id))
        safe_cell = next(index for index in range(25) if index not in mine_positions)
        mines_reveal = manichino_client.post(
            "/api/v1/games/mines/reveal",
            headers={"Authorization": f"Bearer {token}"},
            json={"game_session_id": mines_session_id, "cell_index": safe_cell},
        )
        assert mines_reveal.status_code == 200, mines_reveal.text
        mines_cashout = manichino_client.post(
            "/api/v1/games/mines/cashout",
            headers=_headers(token, mines_token, idempotency_key=f"mines-counterweight-cashout-{uuid4().hex}"),
            json={"game_session_id": mines_session_id},
        )
        assert mines_cashout.status_code == 200, mines_cashout.text

        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE game_providers SET status = 'active' WHERE provider_code = 'ck_collaudo'"
            )

        resumed = manichino_client.post(
            "/api/v1/games/manichino/settle",
            headers=_headers(token, manichino_token, idempotency_key=f"provider-resumed-{uuid4().hex}"),
            json={
                "game_session_id": manichino_session_id,
                "esito": "vincita",
                "payout_amount": "1.900000",
            },
        )
        assert resumed.status_code == 200, resumed.text
    finally:
        # Il fornitore e' condiviso dalla suite: il ripristino deve avvenire anche su errore.
        with db_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE game_providers SET status = %s WHERE provider_code = 'ck_collaudo'",
                (original_status,),
            )
