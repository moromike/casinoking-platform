from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import pytest

from app.modules.games.hi_lo import repository, service
from app.modules.games.hi_lo.math import Card
from app.modules.games.hi_lo.randomness import CardDraw
from app.modules.games.hi_lo.state_machine import HiLoStateTransitionError
from app.db import config as db_config_module
from app.db import connection as db_connection_module

MIGRATION_PATHS = [
    Path("backend/migrations/sql/0043__hi_lo_round_tables.sql"),
    Path("backend/migrations/sql/0051__boxe_hilo_cancelled_status.sql"),
    Path("backend/migrations/sql/0052__demo_anon_drop_user_fk.sql"),
]


@pytest.fixture(scope="module", autouse=True)
def hi_lo_schema(database_url: str):
    patched_db_config = replace(
        db_config_module.database_config,
        database_url=database_url,
    )
    db_config_module.database_config = patched_db_config
    db_connection_module.database_config = patched_db_config
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        _apply_hi_lo_migration(connection)
        _clean_hi_lo_runtime(connection)
        yield
        _clean_hi_lo_runtime(connection)


@pytest.fixture
def hi_lo_title(db_connection):
    title_code = f"hilo_api_{uuid4().hex[:8]}"
    with db_connection.cursor() as cursor:
        _upsert_hi_lo_title(cursor=cursor, title_code=title_code)
    yield title_code
    with db_connection.cursor() as cursor:
        _clean_hi_lo_title(cursor=cursor, title_code=title_code)


@pytest.fixture
def hi_lo_player_context(db_connection, create_authenticated_player, hi_lo_title):
    player = create_authenticated_player(prefix="integration-hi-lo")
    yield player
    with db_connection.cursor() as cursor:
        _clean_hi_lo_runtime_for_player_and_title(
            cursor=cursor,
            player_id=str(player["user_id"]),
            title_code=hi_lo_title,
        )


def test_hi_lo_demo_prediction_cashout_and_replay(
    monkeypatch,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=8, suit="hearts"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])

    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="5",
        wallet_source="demo",
        client_seed="test-seed",
        idempotency_key="start-ok",
    )
    assert start.response["status"] == "active"
    assert start.response["current_card"]["rank"] == 7
    assert start.response["wallet_source"] == "demo"

    active = service.get_active_round(player_id=player_id, title_code=hi_lo_title)
    assert active is not None
    assert active["event"] == "resume"
    assert active["round_id"] == start.response["round_id"]
    assert active["current_card"]["rank"] == 7
    assert service.get_active_round(
        player_id=player_id,
        title_code=hi_lo_title,
        wallet_source="demo",
    )["round_id"] == start.response["round_id"]
    assert service.get_active_round(
        player_id=player_id,
        title_code=hi_lo_title,
        wallet_source="cash",
    ) is None

    predicted = service.predict_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        action="up",
        idempotency_key="predict-ok",
    )
    assert predicted.response["status"] == "active"
    assert predicted.response["prediction"]["success"] is True
    assert predicted.response["active_skip_count"] == 0
    assert Decimal(str(predicted.response["payout_current"])) > Decimal("5")

    cashout = service.cashout_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        idempotency_key="cashout-ok",
    )
    assert cashout.response["status"] == "completed_cashout"
    assert cashout.response["outcome"] == "cashout"
    assert cashout.response["terminal"] is True
    assert service.get_active_round(player_id=player_id, title_code=hi_lo_title) is None

    replay = service.get_round_replay(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
    )
    assert replay["round_id"] == start.response["round_id"]
    assert "server_seed" not in replay
    assert replay["server_seed_hash"]
    assert replay["draw_sequence_hash"]
    assert [action["action_type"] for action in replay["actions"]] == [
        "start",
        "prediction",
        "cashout",
    ]


def test_hi_lo_start_route_accepts_demo_wallet(
    client,
    auth_headers,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
):
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM platform_rounds
            WHERE user_id = %s
              AND game_code = 'hi_lo'
            """,
            (hi_lo_player_context["user_id"],),
        )
        platform_rounds_before = int(cursor.fetchone()["count"])
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM ledger_transactions
            WHERE user_id = %s
            """,
            (hi_lo_player_context["user_id"],),
        )
        ledger_transactions_before = int(cursor.fetchone()["count"])

    response = client.post(
        "/games/hi-lo/start",
        headers={
            **auth_headers(
                hi_lo_player_context["access_token"],
                include_game_launch_token=False,
            ),
            "Idempotency-Key": "api-start-demo",
        },
        json={
            "title_code": hi_lo_title,
            "bet_amount": "2",
            "wallet_source": "demo",
            "client_seed": "api-seed",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "active"
    assert payload["data"]["game_code"] == "hi_lo"
    assert payload["data"]["wallet_source"] == "demo"
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM platform_rounds
            WHERE user_id = %s
              AND game_code = 'hi_lo'
            """,
            (hi_lo_player_context["user_id"],),
        )
        assert int(cursor.fetchone()["count"]) == platform_rounds_before
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM ledger_transactions
            WHERE user_id = %s
            """,
            (hi_lo_player_context["user_id"],),
        )
        assert int(cursor.fetchone()["count"]) == ledger_transactions_before


def test_hi_lo_real_start_requires_launch_token_and_propagates_launch_site(
    monkeypatch,
    client,
    auth_headers,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=8, suit="hearts"),
            2: Card(rank=9, suit="hearts"),
        },
    )
    monkeypatch.setattr(service, "is_prediction_success", lambda **_: True)
    site_code = f"hilo_site_{uuid4().hex[:8]}"
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    access_session_id, table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
        site_code=site_code,
    )

    missing_token = client.post(
        "/games/hi-lo/start",
        headers={**headers, "Idempotency-Key": f"hilo-missing-token-{uuid4().hex}"},
        json={
            "title_code": hi_lo_title,
            "bet_amount": "1",
            "wallet_source": "cash",
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
    )
    assert missing_token.status_code == 401, missing_token.text
    assert missing_token.json()["error"]["code"] == "GAME_LAUNCH_TOKEN_REQUIRED"

    launch_response = _post_hi_lo_launch_token(
        client,
        headers=headers,
        title_code=hi_lo_title,
        site_code=site_code,
    )
    assert launch_response.status_code == 200, launch_response.text
    launch_data = launch_response.json()["data"]
    assert launch_data["title_code"] == hi_lo_title
    assert launch_data["site_code"] == site_code

    start_response = client.post(
        "/games/hi-lo/start",
        headers={
            **headers,
            "Idempotency-Key": f"hilo-valid-launch-{uuid4().hex}",
            "X-Game-Launch-Token": launch_data["game_launch_token"],
        },
        json={
            "title_code": "payload_title_is_not_authoritative",
            "bet_amount": "1",
            "wallet_source": "cash",
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200, start_response.text
    start_data = start_response.json()["data"]
    assert start_data["title_code"] == hi_lo_title
    assert start_data["site_code"] == site_code
    round_id = start_data["round_id"]

    skip_response = client.post(
        "/games/hi-lo/skip",
        headers={**headers, "Idempotency-Key": f"hilo-skip-no-launch-{uuid4().hex}"},
        json={"round_id": round_id},
    )
    assert skip_response.status_code == 200, skip_response.text

    predict_response = client.post(
        "/games/hi-lo/predict",
        headers={**headers, "Idempotency-Key": f"hilo-predict-no-launch-{uuid4().hex}"},
        json={"round_id": round_id, "action": "red"},
    )
    assert predict_response.status_code == 200, predict_response.text

    player_id = str(hi_lo_player_context["user_id"])
    predict_data = predict_response.json()["data"]
    cashout_round_id = round_id
    if predict_data["status"] != "active" or int(predict_data["correct_predictions_count"]) <= 0:
        cashout_start = service.start_round(
            player_id=player_id,
            title_code=hi_lo_title,
            site_code=site_code,
            bet_amount="1",
            wallet_source="cash",
            client_seed="cashout-no-launch-seed",
            idempotency_key=f"hilo-cashout-start-{uuid4().hex}",
            table_session_id=table_session_id,
            access_session_id=access_session_id,
        )
        cashout_round_id = str(cashout_start.response["round_id"])
        service.predict_round(
            player_id=player_id,
            round_id=cashout_round_id,
            action="red",
            idempotency_key=f"hilo-cashout-predict-{uuid4().hex}",
        )

    cashout_response = client.post(
        "/games/hi-lo/cashout",
        headers={**headers, "Idempotency-Key": f"hilo-cashout-no-launch-{uuid4().hex}"},
        json={"round_id": cashout_round_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    assert cashout_response.json()["data"]["status"] == "completed_cashout"

    replay_response = client.get(f"/games/hi-lo/round/{cashout_round_id}/replay", headers=headers)
    assert replay_response.status_code == 200, replay_response.text
    assert replay_response.json()["data"]["round_id"] == cashout_round_id

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                hr.title_code AS hi_lo_title_code,
                hr.site_code AS hi_lo_site_code,
                pr.title_code AS platform_title_code,
                pr.site_code AS platform_site_code,
                gas.title_code AS access_title_code,
                gas.site_code AS access_site_code
            FROM hi_lo_rounds hr
            JOIN platform_rounds pr ON pr.id = hr.platform_round_id
            JOIN game_access_sessions gas ON gas.id = hr.access_session_id
            WHERE hr.id = %s
            """,
            (round_id,),
        )
        row = cursor.fetchone()
    assert row["hi_lo_title_code"] == hi_lo_title
    assert row["hi_lo_site_code"] == site_code
    assert row["platform_title_code"] == hi_lo_title
    assert row["platform_site_code"] == site_code
    assert row["access_title_code"] == hi_lo_title
    assert row["access_site_code"] == site_code


def test_hi_lo_launch_token_start_rejects_invalid_wrong_player_wrong_game_and_demo(
    client,
    auth_headers,
    create_authenticated_player,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
):
    site_code = f"hilo_site_{uuid4().hex[:8]}"
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    access_session_id, table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
        site_code=site_code,
    )

    wrong_game_issue = _post_hi_lo_launch_token(
        client,
        headers=headers,
        title_code=hi_lo_title,
        site_code=site_code,
        game_code="boxe",
    )
    assert wrong_game_issue.status_code == 422, wrong_game_issue.text

    demo_issue = _post_hi_lo_launch_token(
        client,
        headers=headers,
        title_code=hi_lo_title,
        site_code=site_code,
        mode="demo",
    )
    assert demo_issue.status_code == 422, demo_issue.text

    launch_response = _post_hi_lo_launch_token(
        client,
        headers=headers,
        title_code=hi_lo_title,
        site_code=site_code,
    )
    assert launch_response.status_code == 200, launch_response.text
    launch_token = launch_response.json()["data"]["game_launch_token"]

    invalid_token = client.post(
        "/games/hi-lo/start",
        headers={
            **headers,
            "Idempotency-Key": f"hilo-invalid-launch-{uuid4().hex}",
            "X-Game-Launch-Token": "not-a-valid-launch-token",
        },
        json={
            "title_code": hi_lo_title,
            "bet_amount": "1",
            "wallet_source": "cash",
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
    )
    assert invalid_token.status_code == 401, invalid_token.text
    assert invalid_token.json()["error"]["code"] == "GAME_LAUNCH_TOKEN_INVALID"

    wrong_game_headers = auth_headers(hi_lo_player_context["access_token"])
    wrong_game_token = wrong_game_headers["X-Game-Launch-Token"]
    wrong_game_start = client.post(
        "/games/hi-lo/start",
        headers={
            **headers,
            "Idempotency-Key": f"hilo-wrong-game-launch-{uuid4().hex}",
            "X-Game-Launch-Token": wrong_game_token,
        },
        json={
            "title_code": hi_lo_title,
            "bet_amount": "1",
            "wallet_source": "cash",
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
    )
    assert wrong_game_start.status_code == 403, wrong_game_start.text
    assert wrong_game_start.json()["error"]["code"] == "FORBIDDEN"

    other_player = create_authenticated_player(prefix="integration-hi-lo-wrong-player")
    other_headers = auth_headers(other_player["access_token"], include_game_launch_token=False)
    other_access_session_id, other_table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=other_headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
        site_code=site_code,
    )
    wrong_player = client.post(
        "/games/hi-lo/start",
        headers={
            **other_headers,
            "Idempotency-Key": f"hilo-wrong-player-launch-{uuid4().hex}",
            "X-Game-Launch-Token": launch_token,
        },
        json={
            "title_code": hi_lo_title,
            "bet_amount": "1",
            "wallet_source": "cash",
            "table_session_id": other_table_session_id,
            "access_session_id": other_access_session_id,
        },
    )
    assert wrong_player.status_code == 403, wrong_player.text
    assert wrong_player.json()["error"]["code"] == "FORBIDDEN"

    demo_with_token = client.post(
        "/games/hi-lo/start",
        headers={
            **headers,
            "Idempotency-Key": f"hilo-demo-launch-{uuid4().hex}",
            "X-Game-Launch-Token": launch_token,
        },
        json={
            "title_code": hi_lo_title,
            "bet_amount": "1",
            "wallet_source": "demo",
        },
    )
    assert demo_with_token.status_code == 422, demo_with_token.text
    assert demo_with_token.json()["error"]["code"] == "VALIDATION_ERROR"


def test_hi_lo_real_start_requires_table_session(
    monkeypatch,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(monkeypatch, {0: Card(rank=7, suit="clubs")})

    with pytest.raises(service.HiLoApiError, match="table_session_id is required"):
        service.start_round(
            player_id=str(hi_lo_player_context["user_id"]),
            title_code=hi_lo_title,
            bet_amount="2",
            wallet_source="cash",
            client_seed="real-guard",
            idempotency_key="start-real-without-table",
        )


def test_hi_lo_real_cashout_closes_platform_round_as_won(
    monkeypatch,
    client,
    auth_headers,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=8, suit="hearts"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE site_titles
            SET lobby_visibility = 'visible',
                demo_enabled = true,
                real_enabled = true,
                updated_at = NOW()
            WHERE site_code = 'casinoking'
              AND title_code = %s
            """,
            (hi_lo_title,),
        )

    access_response = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": "hi_lo",
            "title_code": hi_lo_title,
            "site_code": "casinoking",
        },
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = access_response.json()["data"]["id"]

    table_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "hi_lo",
            "title_code": hi_lo_title,
            "site_code": "casinoking",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
        },
    )
    assert table_response.status_code == 200, table_response.text
    table_session_id = table_response.json()["data"]["id"]

    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="5",
        wallet_source="cash",
        client_seed="real-cashout-seed",
        idempotency_key="start-real-cashout",
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )
    predicted = service.predict_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        action="up",
        idempotency_key="predict-real-cashout",
    )
    assert predicted.response["prediction"]["success"] is True

    cashout = service.cashout_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        idempotency_key="cashout-real-cashout",
    )
    assert cashout.response["status"] == "completed_cashout"
    assert cashout.response["outcome"] == "cashout"

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT status,
                   closed_at,
                   payout_amount,
                   settlement_ledger_transaction_id
            FROM platform_rounds
            WHERE id = %s
            """,
            (start.response["round_id"],),
        )
        platform_round = cursor.fetchone()

    assert platform_round is not None
    assert platform_round["status"] == "won"
    assert platform_round["closed_at"] is not None
    assert platform_round["settlement_ledger_transaction_id"] is not None
    assert Decimal(str(platform_round["payout_amount"])) == Decimal(
        str(cashout.response["final_payout_amount"]),
    )


def test_hi_lo_latest_access_sessions_groups_replays_and_filters_scope(
    monkeypatch,
    client,
    auth_headers,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
    create_authenticated_player,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=8, suit="hearts"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    access_session_id, table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
    )

    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="1",
        wallet_source="cash",
        client_seed="latest-hi-lo-terminal",
        idempotency_key=f"latest-hi-lo-start-{uuid4().hex}",
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )
    predicted = service.predict_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        action="up",
        idempotency_key=f"latest-hi-lo-predict-{uuid4().hex}",
    )
    assert predicted.response["prediction"]["success"] is True
    cashout = service.cashout_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        idempotency_key=f"latest-hi-lo-cashout-{uuid4().hex}",
    )
    assert cashout.response["status"] == "completed_cashout"

    active = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="1",
        wallet_source="cash",
        client_seed="latest-hi-lo-active",
        idempotency_key=f"latest-hi-lo-active-{uuid4().hex}",
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )

    latest_response = client.get(
        f"/games/hi-lo/access-sessions/latest?title_code={hi_lo_title}&site_code=casinoking",
        headers=headers,
    )
    assert latest_response.status_code == 200, latest_response.text
    payload = latest_response.json()
    assert payload["meta"] == {
        "limit": 3,
        "title_code": hi_lo_title,
        "site_code": "casinoking",
    }
    assert len(payload["data"]) == 1
    latest_session = payload["data"][0]
    assert latest_session["id"] == access_session_id
    assert latest_session["game_code"] == "hi_lo"
    assert latest_session["title_code"] == hi_lo_title
    assert latest_session["site_code"] == "casinoking"
    assert [round_payload["round_id"] for round_payload in latest_session["rounds"]] == [
        start.response["round_id"]
    ]
    assert active.response["round_id"] not in {
        round_payload["round_id"] for round_payload in latest_session["rounds"]
    }
    round_replay = latest_session["rounds"][0]
    assert round_replay["game_code"] == "hi_lo"
    assert round_replay["status"] == "completed_cashout"
    assert [action["action_type"] for action in round_replay["actions"]] == [
        "start",
        "prediction",
        "cashout",
    ]
    assert "server_seed" not in round_replay

    other_player = create_authenticated_player(prefix="hi-lo-latest-other")
    other_response = client.get(
        f"/games/hi-lo/access-sessions/latest?title_code={hi_lo_title}&site_code=casinoking",
        headers=auth_headers(
            other_player["access_token"],
            include_game_launch_token=False,
        ),
    )
    assert other_response.status_code == 200, other_response.text
    assert other_response.json()["data"] == []

    wrong_site_response = client.get(
        f"/games/hi-lo/access-sessions/latest?title_code={hi_lo_title}&site_code=missing_site",
        headers=headers,
    )
    assert wrong_site_response.status_code == 200, wrong_site_response.text
    assert wrong_site_response.json()["data"] == []

    demo_token = _issue_demo_launch_token(
        client,
        game_code="hi_lo",
        title_code=hi_lo_title,
    )
    demo_response = client.get(
        f"/games/hi-lo/access-sessions/latest?title_code={hi_lo_title}&site_code=casinoking",
        headers={**headers, "X-Game-Launch-Token": demo_token},
    )
    assert demo_response.status_code == 403, demo_response.text
    assert demo_response.json()["error"]["code"] == "FORBIDDEN"


def test_hi_lo_access_close_refunds_real_round_before_prediction(
    monkeypatch,
    client,
    auth_headers,
    db_connection,
    db_helpers,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(monkeypatch, {0: Card(rank=7, suit="clubs")})
    player_id = str(hi_lo_player_context["user_id"])
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    access_session_id, table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
    )
    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="5",
        wallet_source="cash",
        client_seed="real-auto-refund-seed",
        idempotency_key=f"start-real-auto-refund-{uuid4().hex}",
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )
    balance_after_start = Decimal(db_helpers.get_wallet_balance(player_id))

    close_response = client.post(
        f"/access-sessions/{access_session_id}/close",
        headers=headers,
    )
    assert close_response.status_code == 200, close_response.text
    close_payload = close_response.json()["data"]
    assert close_payload["status"] == "closed"
    assert close_payload["auto_cashout"]["game_code"] == "hi_lo"
    assert close_payload["auto_cashout"]["settlement_mode"] == "refund"
    assert close_payload["auto_cashout"]["payout_amount"] == "5.000000"

    assert Decimal(db_helpers.get_wallet_balance(player_id)) == balance_after_start + Decimal("5.000000")
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT status, outcome, final_payout_amount FROM hi_lo_rounds WHERE id = %s", (start.response["round_id"],))
        round_row = cursor.fetchone()
        cursor.execute("SELECT status, payout_amount FROM platform_rounds WHERE id = %s", (start.response["round_id"],))
        platform_row = cursor.fetchone()
        cursor.execute("SELECT action_type FROM hi_lo_actions WHERE round_id = %s ORDER BY action_index", (start.response["round_id"],))
        actions = [row["action_type"] for row in cursor.fetchall()]
    assert round_row["status"] == "completed_cashout"
    assert round_row["outcome"] == "cashout"
    assert Decimal(round_row["final_payout_amount"]) == Decimal("5.000000")
    assert platform_row["status"] == "won"
    assert Decimal(platform_row["payout_amount"]) == Decimal("5.000000")
    assert actions == ["start", "cashout"]


def test_hi_lo_access_close_auto_cashouts_real_round_after_winning_prediction(
    monkeypatch,
    client,
    auth_headers,
    db_connection,
    db_helpers,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=8, suit="hearts"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])
    headers = auth_headers(
        hi_lo_player_context["access_token"],
        include_game_launch_token=False,
    )
    access_session_id, table_session_id = _open_hi_lo_real_table(
        client=client,
        headers=headers,
        db_connection=db_connection,
        hi_lo_title=hi_lo_title,
    )
    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="5",
        wallet_source="cash",
        client_seed="real-auto-cashout-seed",
        idempotency_key=f"start-real-auto-cashout-{uuid4().hex}",
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )
    predicted = service.predict_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        action="up",
        idempotency_key=f"predict-real-auto-cashout-{uuid4().hex}",
    )
    payout = Decimal(str(predicted.response["payout_current"]))
    assert payout > Decimal("5.000000")
    balance_before_close = Decimal(db_helpers.get_wallet_balance(player_id))

    close_response = client.post(
        f"/access-sessions/{access_session_id}/close",
        headers=headers,
    )
    assert close_response.status_code == 200, close_response.text
    close_payload = close_response.json()["data"]
    assert close_payload["auto_cashout"]["game_code"] == "hi_lo"
    assert close_payload["auto_cashout"]["settlement_mode"] == "cashout"
    assert Decimal(close_payload["auto_cashout"]["payout_amount"]) == payout

    assert Decimal(db_helpers.get_wallet_balance(player_id)) == balance_before_close + payout
    replay = service.get_round_replay(player_id=player_id, round_id=str(start.response["round_id"]))
    assert [action["action_type"] for action in replay["actions"]] == [
        "start",
        "prediction",
        "cashout",
    ]


def test_hi_lo_start_idempotency_replays_and_conflicts(
    monkeypatch,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(monkeypatch, {0: Card(rank=7, suit="clubs")})
    player_id = str(hi_lo_player_context["user_id"])

    first = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="3",
        wallet_source="demo",
        client_seed="idem-seed",
        idempotency_key="start-idem",
    )
    replay = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="3",
        wallet_source="demo",
        client_seed="idem-seed",
        idempotency_key="start-idem",
    )
    assert replay.replayed is True
    assert replay.response["round_id"] == first.response["round_id"]

    with pytest.raises(repository.HiLoIdempotencyConflict):
        service.start_round(
            player_id=player_id,
            title_code=hi_lo_title,
            bet_amount="4",
            wallet_source="demo",
            client_seed="idem-seed",
            idempotency_key="start-idem",
        )


def test_hi_lo_wrong_prediction_closes_round_as_loss(
    monkeypatch,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=7, suit="clubs"),
            1: Card(rank=2, suit="hearts"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])
    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="2",
        wallet_source="demo",
        client_seed="loss-seed",
        idempotency_key="start-loss",
    )

    result = service.predict_round(
        player_id=player_id,
        round_id=str(start.response["round_id"]),
        action="up",
        idempotency_key="predict-loss",
    )
    assert result.response["status"] == "failed_prediction"
    assert result.response["outcome"] == "loss"
    assert result.response["terminal"] is True
    assert result.response["payout_current"] == "0.000000"

    history = service.list_sessions(player_id=player_id)
    assert history["items"][0]["round_id"] == start.response["round_id"]
    assert history["items"][0]["outcome"] == "loss"


def test_hi_lo_active_skip_limit_is_enforced(
    monkeypatch,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=6, suit="clubs"),
            1: Card(rank=7, suit="clubs"),
            2: Card(rank=8, suit="clubs"),
            3: Card(rank=9, suit="clubs"),
            4: Card(rank=10, suit="clubs"),
        },
    )
    player_id = str(hi_lo_player_context["user_id"])
    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="1",
        wallet_source="demo",
        client_seed="skip-seed",
        idempotency_key="start-skip",
    )

    for index in range(3):
        result = service.skip_round(
            player_id=player_id,
            round_id=str(start.response["round_id"]),
            idempotency_key=f"skip-{index}",
        )
        assert result.response["active_skip_count"] == index + 1
        assert result.response["active_skip_limit"] == 3

    with pytest.raises(HiLoStateTransitionError, match="active_skip_limit_reached"):
        service.skip_round(
            player_id=player_id,
            round_id=str(start.response["round_id"]),
            idempotency_key="skip-over-limit",
        )


def test_hi_lo_active_skip_limit_uses_published_admin_config(
    monkeypatch,
    db_connection,
    hi_lo_player_context,
    hi_lo_title,
):
    _install_fake_draws(
        monkeypatch,
        {
            0: Card(rank=6, suit="clubs"),
            1: Card(rank=7, suit="clubs"),
            2: Card(rank=8, suit="clubs"),
            3: Card(rank=9, suit="clubs"),
        },
    )
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE title_configs
            SET ui_labels_json = %s,
                draft_ui_labels_json = %s,
                updated_at = NOW()
            WHERE title_code = %s
            """,
            (
                Jsonb({"gameplay_config": {"active_skip_limit": 2}}),
                Jsonb({"gameplay_config": {"active_skip_limit": 2}}),
                hi_lo_title,
            ),
        )

    player_id = str(hi_lo_player_context["user_id"])
    start = service.start_round(
        player_id=player_id,
        title_code=hi_lo_title,
        bet_amount="1",
        wallet_source="demo",
        client_seed="skip-config-seed",
        idempotency_key="start-skip-config",
    )

    for index in range(2):
        result = service.skip_round(
            player_id=player_id,
            round_id=str(start.response["round_id"]),
            idempotency_key=f"skip-config-{index}",
        )
        assert result.response["active_skip_count"] == index + 1
        assert result.response["active_skip_limit"] == 2

    with pytest.raises(HiLoStateTransitionError, match="active_skip_limit_reached"):
        service.skip_round(
            player_id=player_id,
            round_id=str(start.response["round_id"]),
            idempotency_key="skip-config-over-limit",
        )


def _install_fake_draws(monkeypatch, cards_by_draw_index: dict[int, Card]) -> None:
    def fake_draw_card(
        *,
        server_seed: str,
        client_seed: str,
        round_nonce: int,
        draw_index: int,
        draw_purpose: str,
        fairness_version: str = "hi_lo_seed_v1",
    ) -> CardDraw:
        card = cards_by_draw_index[draw_index]
        return CardDraw(
            card=card,
            card_index=(draw_index % 52),
            unit_interval=Decimal("0.1"),
            rng_material=f"fake:{server_seed}:{client_seed}:{round_nonce}:{draw_index}:{draw_purpose}:{fairness_version}",
            digest=f"{draw_index:064x}",
            rejection_counter=0,
        )

    monkeypatch.setattr(service, "draw_card", fake_draw_card)


def _open_hi_lo_real_table(
    *,
    client,
    headers,
    db_connection,
    hi_lo_title: str,
    site_code: str = "casinoking",
) -> tuple[str, str]:
    with db_connection.cursor() as cursor:
        _publish_hi_lo_title_for_site(
            cursor=cursor,
            title_code=hi_lo_title,
            site_code=site_code,
        )
    access_response = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": "hi_lo",
            "title_code": hi_lo_title,
            "site_code": site_code,
        },
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = access_response.json()["data"]["id"]
    table_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "hi_lo",
            "title_code": hi_lo_title,
            "site_code": site_code,
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
        },
    )
    assert table_response.status_code == 200, table_response.text
    return access_session_id, table_response.json()["data"]["id"]


def _post_hi_lo_launch_token(
    client,
    *,
    headers,
    title_code: str,
    site_code: str = "casinoking",
    game_code: str = "hi_lo",
    mode: str = "real",
):
    return client.post(
        "/games/hi-lo/launch-token",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
            "mode": mode,
        },
    )


def _issue_demo_launch_token(
    client,
    *,
    game_code: str,
    title_code: str,
    site_code: str = "casinoking",
) -> str:
    token_response = client.post("/demo/token")
    assert token_response.status_code == 200, token_response.text
    launch_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": token_response.json()["data"]["anonymous_token"]},
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
        },
    )
    assert launch_response.status_code == 200, launch_response.text
    return launch_response.json()["data"]["game_launch_token"]


def _apply_hi_lo_migration(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))


def _clean_hi_lo_runtime(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM hi_lo_idempotency_keys")
        cursor.execute("DELETE FROM hi_lo_actions")
        cursor.execute("DELETE FROM hi_lo_rounds")


def _upsert_hi_lo_title(*, cursor, title_code: str) -> None:
    cursor.execute(
        """
        INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
        VALUES ('hi_lo', 'HI-LO', 'app.modules.games.hi_lo', 'active')
        ON CONFLICT (engine_code) DO UPDATE
        SET display_name = EXCLUDED.display_name,
            runtime_module = EXCLUDED.runtime_module,
            status = 'active'
        """,
    )
    cursor.execute(
        """
        INSERT INTO game_titles (
            title_code,
            engine_code,
            display_name,
            status,
            is_master,
            source_title_code
        )
        VALUES ('hi_lo', 'hi_lo', 'HI-LO Master', 'active', true, NULL)
        ON CONFLICT (title_code) DO UPDATE
        SET engine_code = 'hi_lo',
            display_name = 'HI-LO Master',
            status = 'active',
            is_master = true,
            source_title_code = NULL,
            updated_at = NOW()
        """,
    )
    cursor.execute(
        """
        INSERT INTO game_titles (
            title_code,
            engine_code,
            display_name,
            status,
            is_master,
            source_title_code
        )
        VALUES (%s, 'hi_lo', 'HI-LO API Test', 'active', false, 'hi_lo')
        ON CONFLICT (title_code) DO UPDATE
        SET engine_code = 'hi_lo',
            display_name = EXCLUDED.display_name,
            status = 'active',
            is_master = false,
            source_title_code = 'hi_lo',
            updated_at = NOW()
        """,
        (title_code,),
    )
    cursor.execute(
        """
        INSERT INTO site_titles (
            site_code,
            title_code,
            position,
            status,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            lobby_display_name,
            lobby_description,
            featured
        )
        VALUES (
            'casinoking',
            %s,
            999,
            'active',
            'hidden',
            true,
            false,
            'HI-LO API Test',
            'Integration test title',
            false
        )
        ON CONFLICT (site_code, title_code) DO UPDATE
        SET status = 'active',
            lobby_visibility = EXCLUDED.lobby_visibility,
            demo_enabled = EXCLUDED.demo_enabled,
            real_enabled = EXCLUDED.real_enabled,
            lobby_display_name = EXCLUDED.lobby_display_name,
            lobby_description = EXCLUDED.lobby_description,
            featured = EXCLUDED.featured,
            updated_at = NOW()
        """,
        (title_code,),
    )
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            created_at,
            updated_at
        )
        VALUES (%s, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
        ON CONFLICT (title_code) DO NOTHING
        """,
        (title_code,),
    )


def _publish_hi_lo_title_for_site(*, cursor, title_code: str, site_code: str) -> None:
    cursor.execute(
        """
        INSERT INTO sites (
            site_code,
            display_name,
            base_url,
            status
        )
        VALUES (%s, %s, NULL, 'active')
        ON CONFLICT (site_code) DO UPDATE
        SET display_name = EXCLUDED.display_name,
            status = 'active',
            updated_at = NOW()
        """,
        (site_code, f"HI-LO Test Site {site_code}"),
    )
    cursor.execute(
        """
        INSERT INTO site_titles (
            site_code,
            title_code,
            position,
            status,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            lobby_display_name,
            lobby_description,
            featured
        )
        VALUES (
            %s,
            %s,
            999,
            'active',
            'visible',
            true,
            true,
            'HI-LO API Test',
            'Integration test title',
            false
        )
        ON CONFLICT (site_code, title_code) DO UPDATE
        SET status = 'active',
            lobby_visibility = EXCLUDED.lobby_visibility,
            demo_enabled = EXCLUDED.demo_enabled,
            real_enabled = EXCLUDED.real_enabled,
            lobby_display_name = EXCLUDED.lobby_display_name,
            lobby_description = EXCLUDED.lobby_description,
            featured = EXCLUDED.featured,
            updated_at = NOW()
        """,
        (site_code, title_code),
    )


def _clean_hi_lo_runtime_for_player_and_title(*, cursor, player_id: str, title_code: str) -> None:
    cursor.execute(
        """
        DELETE FROM hi_lo_idempotency_keys
        WHERE player_id = %s
           OR round_id IN (SELECT id FROM hi_lo_rounds WHERE title_code = %s)
        """,
        (player_id, title_code),
    )
    cursor.execute(
        "DELETE FROM hi_lo_actions WHERE round_id IN (SELECT id FROM hi_lo_rounds WHERE title_code = %s)",
        (title_code,),
    )
    cursor.execute("DELETE FROM hi_lo_rounds WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM platform_rounds WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM game_table_sessions WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM game_access_sessions WHERE title_code = %s", (title_code,))
    cursor.execute(
        """
        DELETE FROM demo_round_events
        WHERE demo_play_session_id IN (
            SELECT id FROM demo_play_sessions WHERE title_code = %s
        )
        """,
        (title_code,),
    )
    cursor.execute("DELETE FROM demo_play_sessions WHERE title_code = %s", (title_code,))


def _clean_hi_lo_title(*, cursor, title_code: str) -> None:
    _clean_hi_lo_runtime_for_player_and_title(cursor=cursor, player_id=str(uuid4()), title_code=title_code)
    cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
    cursor.execute(
        """
        DELETE FROM sites s
        WHERE s.site_code LIKE 'hilo_site_%'
          AND NOT EXISTS (
              SELECT 1 FROM site_titles st WHERE st.site_code = s.site_code
          )
          AND NOT EXISTS (
              SELECT 1 FROM game_access_sessions gas WHERE gas.site_code = s.site_code
          )
          AND NOT EXISTS (
              SELECT 1 FROM game_table_sessions gts WHERE gts.site_code = s.site_code
          )
          AND NOT EXISTS (
              SELECT 1 FROM platform_rounds pr WHERE pr.site_code = s.site_code
          )
          AND NOT EXISTS (
              SELECT 1 FROM hi_lo_rounds hr WHERE hr.site_code = s.site_code
          )
        """,
    )
    cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))
