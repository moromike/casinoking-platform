from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]

from threading import Barrier
from uuid import uuid4

import httpx

from app.modules.games.hi_lo import repository, service
from tests.concurrency._game_idempotency_helpers import (
    auth_headers,
    controlled_double_call,
    open_real_table,
    parallel_posts,
)


TITLE = "hilo001"


def _cash_context(api_base_url: str, player: dict[str, object]) -> tuple[dict[str, str], dict[str, object]]:
    access_id, table_id, launch_token = open_real_table(
        api_base_url=api_base_url,
        access_token=str(player["access_token"]),
        game_code="hi_lo",
        title_code=TITLE,
    )
    key = f"5a-hilo-start-{uuid4().hex}"
    return (
        {**auth_headers(str(player["access_token"]), idempotency_key=key), "X-Game-Launch-Token": launch_token},
        {"title_code": TITLE, "bet_amount": "2", "wallet_source": "cash", "client_seed": f"seed-{key}", "table_session_id": table_id, "access_session_id": access_id},
    )


def _assert_one_cash_start(db_helpers, *, player_id: str, key: str) -> None:
    rows = db_helpers.fetchall(
        """
        SELECT hr.id, pr.start_ledger_transaction_id
        FROM hi_lo_rounds hr
        JOIN platform_rounds pr ON pr.id = hr.platform_round_id
        WHERE hr.player_id = %s AND hr.start_idempotency_key = %s
        """,
        (player_id, key),
    )
    assert len(rows) == 1, f"HI-LO rounds for key={key}: {rows}"
    debits = db_helpers.fetchall(
        "SELECT id FROM ledger_transactions WHERE id = %s AND transaction_type = 'bet'",
        (rows[0]["start_ledger_transaction_id"],),
    )
    assert len(debits) == 1, f"HI-LO bet debits for key={key}: {debits}"


def test_start_parallelo_stessa_chiave_una_sola_partita(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-hilo-http-start")
    headers, payload = _cash_context(api_base_url, player)
    responses = parallel_posts(api_base_url=api_base_url, path="/games/hi-lo/start", headers=headers, payload=payload)
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"HI-LO HTTP start responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert len({r.json()["data"]["round_id"] for r in responses}) == 1, evidence
    _assert_one_cash_start(db_helpers, player_id=str(player["user_id"]), key=headers["Idempotency-Key"])


def test_start_parallelo_stessa_chiave_deterministico(
    monkeypatch, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-hilo-controlled-start")
    key = f"5a-hilo-controlled-{uuid4().hex}"
    barrier = Barrier(2)
    original = repository.get_idempotency_result

    def synchronized_get(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get("operation") == "start_round" and kwargs.get("idempotency_key") == key:
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(repository, "get_idempotency_result", synchronized_get)
    results = controlled_double_call(
        lambda: service.start_round(
            player_id=str(player["user_id"]), title_code=TITLE, bet_amount="2",
            wallet_source="demo", client_seed="controlled-seed", idempotency_key=key,
        )
    )
    printable = [(kind, value.response if kind == "ok" else value) for kind, value in results]
    print(f"HI-LO controlled start results: {printable}")
    assert [kind for kind, _ in results] == ["ok", "ok"], printable
    assert len({value.response["round_id"] for _, value in results}) == 1
    rounds = db_helpers.fetchall(
        "SELECT id FROM hi_lo_rounds WHERE player_id = %s AND start_idempotency_key = %s",
        (player["user_id"], key),
    )
    assert len(rounds) == 1, rounds


def test_start_demo_parallelo_stessa_chiave_una_sola_partita_e_addebito(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-hilo-demo-start")
    key = f"5a-hilo-demo-{uuid4().hex}"
    responses = parallel_posts(
        api_base_url=api_base_url, path="/games/hi-lo/start",
        headers=auth_headers(str(player["access_token"]), idempotency_key=key),
        payload={"title_code": TITLE, "bet_amount": "2", "wallet_source": "demo", "client_seed": "demo-seed"},
    )
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"HI-LO demo start responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert len({r.json()["data"]["round_id"] for r in responses}) == 1, evidence
    assert db_helpers.fetchone(
        "SELECT COUNT(*) AS n FROM hi_lo_rounds WHERE player_id = %s AND start_idempotency_key = %s",
        (player["user_id"], key),
    )["n"] == 1
    assert db_helpers.fetchone(
        "SELECT COUNT(*) AS n FROM demo_round_events WHERE idempotency_key LIKE %s AND kind = 'bet'",
        (f"%:{key}",),
    )["n"] == 1


def _start_demo(api_base_url: str, player: dict[str, object], key: str) -> tuple[dict[str, str], str]:
    headers = auth_headers(str(player["access_token"]), idempotency_key=key)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        response = client.post("/games/hi-lo/start", headers=headers, json={"title_code": TITLE, "bet_amount": "2", "wallet_source": "demo", "client_seed": key})
    assert response.status_code == 200, response.text
    return headers, response.json()["data"]["round_id"]


def test_replay_parallelo_predict_stessa_chiave_stessa_risposta(
    api_base_url, create_authenticated_player,
) -> None:
    player = create_authenticated_player(prefix="5a-hilo-predict")
    headers, round_id = _start_demo(api_base_url, player, f"5a-hilo-predict-start-{uuid4().hex}")
    headers["Idempotency-Key"] = f"5a-hilo-predict-{uuid4().hex}"
    responses = parallel_posts(api_base_url=api_base_url, path="/games/hi-lo/predict", headers=headers, payload={"round_id": round_id, "action": "up"})
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"HI-LO predict replay responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert responses[0].json() == responses[1].json(), evidence


def test_replay_parallelo_cashout_stessa_chiave_stessa_risposta(
    api_base_url, create_authenticated_player, db_connection,
) -> None:
    player = create_authenticated_player(prefix="5a-hilo-cashout")
    headers, round_id = _start_demo(api_base_url, player, f"5a-hilo-cashout-start-{uuid4().hex}")
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE hi_lo_rounds SET correct_predictions_count = 1, multiplier_current = 2, payout_current = bet_amount * 2 WHERE id = %s",
            (round_id,),
        )
    headers["Idempotency-Key"] = f"5a-hilo-cashout-{uuid4().hex}"
    responses = parallel_posts(api_base_url=api_base_url, path="/games/hi-lo/cashout", headers=headers, payload={"round_id": round_id})
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"HI-LO cashout replay responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert responses[0].json() == responses[1].json(), evidence
