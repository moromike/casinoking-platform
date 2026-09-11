from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]

from threading import Barrier
from uuid import uuid4

import httpx

from app.modules.games.boxe import repository, service
from app.modules.games.boxe.randomness import generate_step_outcome
from tests.concurrency._game_idempotency_helpers import (
    auth_headers,
    controlled_double_call,
    open_real_table,
    parallel_posts,
)


TITLE = "boxe001"


def _cash_context(api_base_url: str, player: dict[str, object]) -> tuple[dict[str, str], dict[str, object]]:
    access_id, table_id, launch_token = open_real_table(
        api_base_url=api_base_url,
        access_token=str(player["access_token"]),
        game_code="boxe",
        title_code=TITLE,
    )
    key = f"5a-boxe-start-{uuid4().hex}"
    headers = {
        **auth_headers(str(player["access_token"]), idempotency_key=key),
        "X-Game-Launch-Token": launch_token,
    }
    payload = {
        "title_code": TITLE,
        "rows": 4,
        "difficulty": "easy",
        "bet_amount": "2.000000",
        "wallet_source": "cash",
        "client_seed": f"seed-{key}",
        "table_session_id": table_id,
        "access_session_id": access_id,
    }
    return headers, payload


def _assert_one_cash_start(db_helpers, *, player_id: str, key: str) -> None:
    rows = db_helpers.fetchall(
        """
        SELECT br.id, pr.start_ledger_transaction_id
        FROM boxe_rounds br
        JOIN platform_rounds pr ON pr.id = br.platform_round_id
        WHERE br.player_id = %s AND br.start_idempotency_key = %s
        """,
        (player_id, key),
    )
    assert len(rows) == 1, f"BOXE rounds for key={key}: {rows}"
    debits = db_helpers.fetchall(
        "SELECT id FROM ledger_transactions WHERE id = %s AND transaction_type = 'bet'",
        (rows[0]["start_ledger_transaction_id"],),
    )
    assert len(debits) == 1, f"BOXE bet debits for key={key}: {debits}"


def test_start_parallelo_stessa_chiave_una_sola_partita(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-boxe-http-start")
    headers, payload = _cash_context(api_base_url, player)
    responses = parallel_posts(
        api_base_url=api_base_url,
        path="/games/boxe/start",
        headers=headers,
        payload=payload,
    )
    evidence = [(response.status_code, response.text) for response in responses]
    print(f"BOXE HTTP start responses: {evidence}")
    assert all(200 <= response.status_code < 300 for response in responses), evidence
    round_ids = {response.json()["data"]["round_id"] for response in responses}
    assert len(round_ids) == 1, evidence
    _assert_one_cash_start(
        db_helpers,
        player_id=str(player["user_id"]),
        key=headers["Idempotency-Key"],
    )


def test_start_parallelo_stessa_chiave_deterministico(
    monkeypatch, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-boxe-controlled-start")
    key = f"5a-boxe-controlled-{uuid4().hex}"
    barrier = Barrier(2)
    original = repository.get_idempotency_result

    def synchronized_get(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get("operation") == "start_round" and kwargs.get("idempotency_key") == key:
            try:
                barrier.wait(timeout=2)
            except Exception:
                pass
        return result

    monkeypatch.setattr(repository, "get_idempotency_result", synchronized_get)
    results = controlled_double_call(
        lambda: service.start_round(
            player_id=str(player["user_id"]), title_code=TITLE, rows=4,
            difficulty="easy", bet_amount="2", wallet_source="demo",
            client_seed="controlled-seed", idempotency_key=key,
        )
    )
    printable = [(kind, value.response if kind == "ok" else value) for kind, value in results]
    print(f"BOXE controlled start results: {printable}")
    assert [kind for kind, _ in results] == ["ok", "ok"], printable
    assert len({value.response["round_id"] for _, value in results}) == 1
    rounds = db_helpers.fetchall(
        "SELECT id FROM boxe_rounds WHERE player_id = %s AND start_idempotency_key = %s",
        (player["user_id"], key),
    )
    assert len(rounds) == 1, rounds


def test_start_demo_parallelo_stessa_chiave_una_sola_partita_e_addebito(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-boxe-demo-start")
    key = f"5a-boxe-demo-{uuid4().hex}"
    responses = parallel_posts(
        api_base_url=api_base_url,
        path="/games/boxe/start",
        headers=auth_headers(str(player["access_token"]), idempotency_key=key),
        payload={"title_code": TITLE, "rows": 4, "difficulty": "easy", "bet_amount": "2", "wallet_source": "demo", "client_seed": "demo-seed"},
    )
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"BOXE demo start responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert len({r.json()["data"]["round_id"] for r in responses}) == 1, evidence
    assert db_helpers.fetchone(
        "SELECT COUNT(*) AS n FROM boxe_rounds WHERE player_id = %s AND start_idempotency_key = %s",
        (player["user_id"], key),
    )["n"] == 1
    assert db_helpers.fetchone(
        "SELECT COUNT(*) AS n FROM demo_round_events WHERE idempotency_key LIKE %s AND kind = 'bet'",
        (f"%:{key}",),
    )["n"] == 1


def _start_demo(api_base_url: str, player: dict[str, object], key: str) -> tuple[dict[str, str], str]:
    headers = auth_headers(str(player["access_token"]), idempotency_key=key)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        response = client.post("/games/boxe/start", headers=headers, json={"title_code": TITLE, "rows": 4, "difficulty": "easy", "bet_amount": "2", "wallet_source": "demo", "client_seed": key})
    assert response.status_code == 200, response.text
    return headers, response.json()["data"]["round_id"]


def _safe_pick(db_helpers, round_id: str) -> tuple[int, int]:
    row = db_helpers.fetchone("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
    for position in range(int(row["rows_count"]) + 1):
        outcome = generate_step_outcome(rows=int(row["rows_count"]), difficulty=str(row["difficulty"]), step=1, selected_box_index=position, server_seed=str(row["server_seed"]), client_seed=str(row["client_seed"]), nonce=int(row["nonce"]))
        if outcome.safe:
            return 0, position
    raise AssertionError("No safe BOXE first pick")


def test_replay_parallelo_reveal_stessa_chiave_stessa_risposta(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-boxe-reveal")
    headers, round_id = _start_demo(api_base_url, player, f"5a-boxe-reveal-start-{uuid4().hex}")
    headers["Idempotency-Key"] = f"5a-boxe-reveal-{uuid4().hex}"
    row, position = _safe_pick(db_helpers, round_id)
    responses = parallel_posts(api_base_url=api_base_url, path="/games/boxe/reveal", headers=headers, payload={"round_id": round_id, "row": row, "position": position})
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"BOXE reveal replay responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert responses[0].json() == responses[1].json(), evidence


def test_replay_parallelo_cashout_stessa_chiave_stessa_risposta(
    api_base_url, create_authenticated_player, db_helpers,
) -> None:
    player = create_authenticated_player(prefix="5a-boxe-cashout")
    headers, round_id = _start_demo(api_base_url, player, f"5a-boxe-cashout-start-{uuid4().hex}")
    row, position = _safe_pick(db_helpers, round_id)
    headers["Idempotency-Key"] = f"5a-boxe-cashout-reveal-{uuid4().hex}"
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        reveal = client.post("/games/boxe/reveal", headers=headers, json={"round_id": round_id, "row": row, "position": position})
    assert reveal.status_code == 200, reveal.text
    headers["Idempotency-Key"] = f"5a-boxe-cashout-{uuid4().hex}"
    responses = parallel_posts(api_base_url=api_base_url, path="/games/boxe/cashout", headers=headers, payload={"round_id": round_id})
    evidence = [(r.status_code, r.text) for r in responses]
    print(f"BOXE cashout replay responses: {evidence}")
    assert all(200 <= r.status_code < 300 for r in responses), evidence
    assert responses[0].json() == responses[1].json(), evidence

