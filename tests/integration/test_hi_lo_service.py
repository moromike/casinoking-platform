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

MIGRATION_PATH = Path("backend/migrations/sql/0043__hi_lo_round_tables.sql")


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
    hi_lo_player_context,
    hi_lo_title,
):
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
) -> tuple[str, str]:
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
    return access_session_id, table_response.json()["data"]["id"]


def _apply_hi_lo_migration(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(MIGRATION_PATH.read_text(encoding="utf-8"))


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
    cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))
