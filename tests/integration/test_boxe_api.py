from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

import psycopg
from psycopg.rows import dict_row
import pytest

from app.modules.games.boxe.randomness import generate_step_outcome
from app.modules.games.boxe.i18n_manifest import validate_default_copy_catalog

MIGRATION_PATH = Path("backend/migrations/sql/0039__boxe_session_tables.sql")
DOWN_SQL = """
DROP TABLE IF EXISTS boxe_idempotency_keys;
DROP TABLE IF EXISTS boxe_picks;
DROP TABLE IF EXISTS boxe_rounds;
DROP TABLE IF EXISTS boxe_sessions;
"""


@pytest.fixture(scope="module", autouse=True)
def boxe_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        _drop_boxe_schema(connection)
        _apply_boxe_migration(connection)
        _seed_boxe_catalog(connection)
        yield


@pytest.fixture
def player_headers(client, create_authenticated_player, auth_headers):
    player = create_authenticated_player(prefix="boxe-api")
    return client, player, auth_headers(player["access_token"], include_game_launch_token=False)


def test_config_success_default(client):
    response = client.get("/games/boxe/config")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["game_code"] == "boxe"
    assert data["title_code"] == "boxe001"
    assert data["rows_enabled"] == [4, 5, 6, 7, 8]


def test_config_missing_title_returns_404(client):
    response = client.get("/games/boxe/config", params={"title_code": "missing"})
    assert_error(response, 404, "TITLE_NOT_PUBLISHED")


def test_config_master_title_is_readable_but_not_launchable(client):
    response = client.get("/games/boxe/config", params={"title_code": "boxe"})
    assert response.status_code == 200


def test_start_success(player_headers):
    api_client, _player, headers = player_headers
    response = start_round(api_client, headers, key="start-success")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "active"
    assert len(data["multipliers"]) == 4
    assert data["server_seed_hash"]


def test_start_requires_idempotency_key(client, player_headers):
    _, _player, headers = player_headers
    response = client.post("/games/boxe/start", headers=headers, json=start_payload())
    assert_error(response, 422, "IDEMPOTENCY_KEY_REQUIRED")


def test_start_requires_player_auth(client):
    response = client.post(
        "/games/boxe/start",
        headers={"Idempotency-Key": "no-auth"},
        json=start_payload(),
    )
    assert_error(response, 401, "UNAUTHORIZED")


def test_real_start_without_table_session_rejects(player_headers, db_connection):
    api_client, _player, headers = player_headers
    response = api_client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": "start-real-missing-table"},
        json=start_payload(wallet_source="cash"),
    )
    assert_error(response, 422, "VALIDATION_ERROR")

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM boxe_sessions
            WHERE player_id = %s
            """,
            (_player["user_id"],),
        )
        session_count = int(cursor.fetchone()["count"])
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM platform_rounds
            WHERE user_id = %s
              AND game_code = 'boxe'
            """,
            (_player["user_id"],),
        )
        platform_count = int(cursor.fetchone()["count"])
    assert session_count == 0
    assert platform_count == 0


def test_start_idempotency_replays_same_response(player_headers):
    api_client, _player, headers = player_headers
    first = start_round(api_client, headers, key="start-replay")
    second = start_round(api_client, headers, key="start-replay")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_start_idempotency_conflict_different_payload(player_headers):
    api_client, _player, headers = player_headers
    first = start_round(api_client, headers, key="start-conflict")
    assert first.status_code == 200
    response = api_client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": "start-conflict"},
        json={**start_payload(), "rows": 5},
    )
    assert_error(response, 409, "IDEMPOTENCY_CONFLICT")


@pytest.mark.parametrize(
    ("payload_override", "status_code", "error_code"),
    [
        ({"title_code": "boxe"}, 403, "LAUNCH_REJECTED_MASTER"),
        ({"title_code": "boxe_missing"}, 404, "TITLE_NOT_PUBLISHED"),
        ({"rows": 9}, 400, "BAD_CONFIG"),
        ({"difficulty": "impossible"}, 400, "BAD_CONFIG"),
        ({"bet_amount": "0"}, 422, "INVALID_BET"),
        ({"bet_amount": "1000001"}, 422, "INSUFFICIENT_BALANCE"),
        ({"wallet_source": "bonus_empty"}, 422, "BONUS_WALLET_EMPTY"),
        ({"wallet_source": "expired_table"}, 409, "TABLE_SESSION_EXPIRED"),
    ],
)
def test_start_error_mapping(player_headers, payload_override, status_code, error_code):
    api_client, _player, headers = player_headers
    response = api_client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": f"start-error-{error_code}-{uuid4().hex}"},
        json={**start_payload(), **payload_override},
    )
    assert_error(response, status_code, error_code)


def test_reveal_success_and_idempotency_replay(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id = start_round(api_client, headers, key="reveal-success").json()["data"]["round_id"]
    row, position = first_safe_pick(db_connection, round_id)
    first = reveal(api_client, headers, round_id=round_id, row=row, position=position, key="reveal-replay")
    second = reveal(api_client, headers, round_id=round_id, row=row, position=position, key="reveal-replay")
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["data"]["outcome"] in {"safe", "top_row"}
    assert first.json()["data"].get("pyramid_full_reveal") is None


def test_reveal_idempotency_conflict(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id = start_round(api_client, headers, key="reveal-conflict-start").json()["data"]["round_id"]
    row, position = first_safe_pick(db_connection, round_id)
    assert reveal(api_client, headers, round_id=round_id, row=row, position=position, key="reveal-conflict").status_code == 200
    response = reveal(api_client, headers, round_id=round_id, row=row, position=position + 1, key="reveal-conflict")
    assert_error(response, 409, "IDEMPOTENCY_CONFLICT")


@pytest.mark.parametrize(
    ("row", "position", "status_code", "error_code"),
    [
        (-1, 0, 400, "INVALID_ROW"),
        (9, 0, 400, "INVALID_ROW"),
        (0, -1, 400, "INVALID_POSITION"),
        (2, 0, 422, "CASHOUT_NOT_ALLOWED"),
    ],
)
def test_reveal_error_mapping(player_headers, row, position, status_code, error_code):
    api_client, _player, headers = player_headers
    round_id = start_round(api_client, headers, key=f"reveal-error-{row}-{position}").json()["data"]["round_id"]
    response = reveal(api_client, headers, round_id=round_id, row=row, position=position, key=f"reveal-error-{uuid4().hex}")
    assert_error(response, status_code, error_code)


def test_reveal_round_not_found(player_headers):
    api_client, _player, headers = player_headers
    response = reveal(api_client, headers, round_id=str(uuid4()), row=0, position=0, key="reveal-404")
    assert_error(response, 404, "ROUND_NOT_FOUND")


def test_reveal_after_terminal_returns_closed_error(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id = completed_cashout_round(api_client, headers, db_connection)
    response = reveal(api_client, headers, round_id=round_id, row=1, position=0, key="reveal-terminal")
    assert_error(response, 409, "ROUND_ALREADY_CLOSED")


def test_cashout_success_and_retry_idempotent(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id, row, position = round_with_pick_within_board(
        api_client,
        headers,
        db_connection,
        key_prefix="cashout-success",
        want_safe=True,
    )
    reveal_response = reveal(
        api_client,
        headers,
        round_id=round_id,
        row=row,
        position=position,
        key="cashout-success-reveal",
    )
    assert reveal_response.status_code == 200, reveal_response.text
    first = cashout(api_client, headers, round_id=round_id, key="cashout-retry")
    second = cashout(api_client, headers, round_id=round_id, key="cashout-retry")
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["data"]["status"] == "completed_cashout"
    assert_pyramid_full_reveal(
        first.json()["data"]["pyramid_full_reveal"],
        db_connection,
        round_id,
        expected_picks=[(row, position)],
    )


def test_reveal_loss_returns_server_authoritative_full_pyramid(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id, row, position = round_with_pick_within_board(
        api_client,
        headers,
        db_connection,
        key_prefix="loss-full-reveal",
        want_safe=False,
    )
    response = reveal(
        api_client,
        headers,
        round_id=round_id,
        row=row,
        position=position,
        key="loss-full-reveal-hit",
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["outcome"] == "mine"
    assert data["status"] == "failed_mine"
    assert_pyramid_full_reveal(
        data["pyramid_full_reveal"],
        db_connection,
        round_id,
        expected_picks=[(row, position)],
    )


def test_top_row_win_returns_server_authoritative_full_pyramid(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id, path = round_with_safe_path_within_board(
        api_client,
        headers,
        db_connection,
        key_prefix="top-row-full-reveal",
    )
    final_response = None
    for index, (row, position) in enumerate(path):
        final_response = reveal(
            api_client,
            headers,
            round_id=round_id,
            row=row,
            position=position,
            key=f"top-row-full-reveal-{index}",
        )
        assert final_response.status_code == 200, final_response.text

    assert final_response is not None
    data = final_response.json()["data"]
    assert data["outcome"] == "top_row"
    assert data["status"] == "completed_top_row"
    assert_pyramid_full_reveal(
        data["pyramid_full_reveal"],
        db_connection,
        round_id,
        expected_picks=path,
    )


def test_cashout_idempotency_conflict(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_a = prepare_cashoutable_round(api_client, headers, db_connection, key_prefix="cashout-conflict-a")
    round_b = prepare_cashoutable_round(api_client, headers, db_connection, key_prefix="cashout-conflict-b")
    assert cashout(api_client, headers, round_id=round_a, key="cashout-conflict").status_code == 200
    response = cashout(api_client, headers, round_id=round_b, key="cashout-conflict")
    assert_error(response, 409, "IDEMPOTENCY_CONFLICT")


def test_cashout_not_allowed_before_safe_pick(player_headers):
    api_client, _player, headers = player_headers
    round_id = start_round(api_client, headers, key="cashout-no-safe").json()["data"]["round_id"]
    response = cashout(api_client, headers, round_id=round_id, key="cashout-no-safe")
    assert_error(response, 422, "CASHOUT_NOT_ALLOWED")


def test_cashout_after_terminal_returns_closed_error(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id = completed_cashout_round(api_client, headers, db_connection)
    response = cashout(api_client, headers, round_id=round_id, key="cashout-terminal")
    assert_error(response, 409, "ROUND_ALREADY_CLOSED")


def test_cashout_round_not_found(player_headers):
    api_client, _player, headers = player_headers
    response = cashout(api_client, headers, round_id=str(uuid4()), key="cashout-404")
    assert_error(response, 404, "ROUND_NOT_FOUND")


def test_get_session_success_and_not_found(player_headers):
    api_client, _player, headers = player_headers
    data = start_round(api_client, headers, key="session-success").json()["data"]
    response = api_client.get(f"/games/boxe/session/{data['session_id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["last_round"]["round_id"] == data["round_id"]

    missing = api_client.get(f"/games/boxe/session/{uuid4()}", headers=headers)
    assert_error(missing, 404, "SESSION_NOT_FOUND")


def test_get_session_forbidden_for_other_player(client, create_authenticated_player, auth_headers):
    owner = create_authenticated_player(prefix="boxe-owner")
    other = create_authenticated_player(prefix="boxe-other")
    owner_headers = auth_headers(owner["access_token"], include_game_launch_token=False)
    other_headers = auth_headers(other["access_token"], include_game_launch_token=False)
    session_id = start_round(client, owner_headers, key="session-forbidden").json()["data"]["session_id"]
    response = client.get(f"/games/boxe/session/{session_id}", headers=other_headers)
    assert_error(response, 403, "FORBIDDEN")


def test_replay_rejects_active_and_returns_terminal_payload(player_headers, db_connection):
    api_client, _player, headers = player_headers
    active_round_id = start_round(api_client, headers, key="replay-active").json()["data"]["round_id"]
    active_response = api_client.get(f"/games/boxe/round/{active_round_id}/replay", headers=headers)
    assert_error(active_response, 409, "ROUND_STILL_ACTIVE")

    terminal_round_id = completed_cashout_round(api_client, headers, db_connection)
    replay_response = api_client.get(f"/games/boxe/round/{terminal_round_id}/replay", headers=headers)
    assert replay_response.status_code == 200, replay_response.text
    replay = replay_response.json()["data"]
    assert replay["round_id"] == terminal_round_id
    assert replay["outcome"] == "cashout"
    assert "server_seed" not in replay["fairness"]
    assert_pyramid_full_reveal(
        replay["pyramid_full_reveal"],
        db_connection,
        terminal_round_id,
        expected_picks=[first_safe_pick_from_db(db_connection, terminal_round_id)],
    )


def test_replay_full_pyramid_matches_terminal_cashout_response(player_headers, db_connection):
    api_client, _player, headers = player_headers
    round_id, row, position = round_with_pick_within_board(
        api_client,
        headers,
        db_connection,
        key_prefix="replay-full-reveal",
        want_safe=True,
    )
    reveal_response = reveal(
        api_client,
        headers,
        round_id=round_id,
        row=row,
        position=position,
        key="replay-full-reveal-safe",
    )
    assert reveal_response.status_code == 200, reveal_response.text
    cashout_response = cashout(
        api_client,
        headers,
        round_id=round_id,
        key="replay-full-reveal-cashout",
    )
    assert cashout_response.status_code == 200, cashout_response.text
    terminal_reveal = cashout_response.json()["data"]["pyramid_full_reveal"]

    first_replay = api_client.get(f"/games/boxe/round/{round_id}/replay", headers=headers)
    second_replay = api_client.get(f"/games/boxe/round/{round_id}/replay", headers=headers)
    assert first_replay.status_code == 200, first_replay.text
    assert second_replay.status_code == 200, second_replay.text
    assert first_replay.json() == second_replay.json()
    assert first_replay.json()["data"]["pyramid_full_reveal"] == terminal_reveal


def test_replay_not_found(player_headers):
    api_client, _player, headers = player_headers
    response = api_client.get(f"/games/boxe/round/{uuid4()}/replay", headers=headers)
    assert_error(response, 404, "ROUND_NOT_FOUND")


def test_sessions_history_only_terminal_rounds(player_headers, db_connection):
    api_client, _player, headers = player_headers
    active = start_round(api_client, headers, key="history-active").json()["data"]["round_id"]
    terminal = completed_cashout_round(api_client, headers, db_connection)
    response = api_client.get("/games/boxe/sessions", headers=headers, params={"limit": 10})
    assert response.status_code == 200
    ids = {item["last_round_id"] for item in response.json()["data"]}
    assert terminal in ids
    assert active not in ids


def test_sessions_history_invalid_cursor(player_headers):
    api_client, _player, headers = player_headers
    response = api_client.get("/games/boxe/sessions", headers=headers, params={"cursor": "bad"})
    assert_error(response, 422, "VALIDATION_ERROR")


def test_player_failure_matrix_error_codes(player_headers):
    api_client, _player, headers = player_headers
    cases = [
        ("Config missing", api_client.get("/games/boxe/config", params={"title_code": "nope"}), 404, "TITLE_NOT_PUBLISHED"),
        ("Title not published", api_client.get("/games/boxe/config", params={"title_code": "boxe_missing"}), 404, "TITLE_NOT_PUBLISHED"),
        ("Master title launch", api_client.post("/games/boxe/start", headers={**headers, "Idempotency-Key": "matrix-master"}, json={**start_payload(), "title_code": "boxe"}), 403, "LAUNCH_REJECTED_MASTER"),
        ("Table session expired", api_client.post("/games/boxe/start", headers={**headers, "Idempotency-Key": "matrix-expired"}, json={**start_payload(), "wallet_source": "expired_table"}), 409, "TABLE_SESSION_EXPIRED"),
        ("Balance < bet", api_client.post("/games/boxe/start", headers={**headers, "Idempotency-Key": "matrix-balance"}, json={**start_payload(), "bet_amount": "1000001"}), 422, "INSUFFICIENT_BALANCE"),
        ("Bonus wallet empty", api_client.post("/games/boxe/start", headers={**headers, "Idempotency-Key": "matrix-bonus"}, json={**start_payload(), "wallet_source": "bonus_empty"}), 422, "BONUS_WALLET_EMPTY"),
        ("Backend unreachable", api_client.post("/games/boxe/start", headers={**headers, "Idempotency-Key": "matrix-invalid"}, json={**start_payload(), "rows": 99}), 400, "BAD_CONFIG"),
    ]
    for _scenario, response, status_code, error_code in cases:
        assert_error(response, status_code, error_code)


def test_platform_adapter_demo_round_is_isolated(player_headers, db_connection):
    api_client, _player, headers = player_headers
    response = api_client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": "adapter-demo-start"},
        json=start_payload(wallet_source="demo", client_seed="adapter-demo"),
    )
    assert response.status_code == 200, response.text
    round_id = response.json()["data"]["round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT platform_round_id FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS count FROM platform_rounds WHERE id = %s", (round_id,))
        platform_count = cursor.fetchone()["count"]
    assert round_row["platform_round_id"] is None
    assert platform_count == 0


def test_platform_adapter_real_cashout_settles_wallet_ledger_statement_finance_and_replay(
    player_headers,
    db_connection,
    create_admin_user,
    auth_headers,
):
    api_client, player, headers = player_headers
    before_balance = wallet_balance(db_connection, player["user_id"], "cash")
    round_id = prepare_cashoutable_round(
        api_client,
        headers,
        db_connection,
        key_prefix="adapter-real-cashout",
        wallet_source="cash",
    )
    cashout_response = cashout(api_client, headers, round_id=round_id, key="adapter-real-cashout-settle")
    assert cashout_response.status_code == 200, cashout_response.text
    payload = cashout_response.json()["data"]
    payout = Decimal(payload["payout"])

    platform_row = platform_round(db_connection, round_id)
    assert platform_row["game_code"] == "boxe"
    assert platform_row["status"] == "won"
    assert Decimal(platform_row["payout_amount"]) == payout
    assert platform_row["settlement_ledger_transaction_id"] is not None
    assert ledger_transaction_count(db_connection, round_id, "bet") == 1
    assert ledger_transaction_count(db_connection, round_id, "win") == 1
    assert wallet_balance(db_connection, player["user_id"], "cash") == before_balance - Decimal("1.000000") + payout

    admin = create_admin_user(prefix="boxe-finance-admin")
    finance = api_client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(admin["access_token"], include_game_launch_token=False),
        params={"user_id": str(player["user_id"])},
    )
    assert finance.status_code == 200, finance.text
    sessions = finance.json()["data"]["sessions"]
    finance_session = next(session for session in sessions if session["game_code"] == "boxe")
    finance_detail = api_client.get(
        f"/admin/reports/financial/sessions/{finance_session['session_id']}",
        headers=auth_headers(admin["access_token"], include_game_launch_token=False),
    )
    assert finance_detail.status_code == 200, finance_detail.text
    finance_events = finance_detail.json()["data"]["events"]
    assert {event["transaction_type"] for event in finance_events} == {"bet", "win"}
    assert all(event["game_enrichment"].startswith("BOXE") for event in finance_events)

    statement = api_client.get("/account/statement-movements?category=game", headers=headers)
    assert statement.status_code == 200, statement.text
    items = statement.json()["data"]
    boxe_item = next(item for item in items if item["description"] == "BOXE")
    detail = api_client.get(
        f"/account/statement-movements/{quote(boxe_item['id'], safe='')}?wallet_type=cash",
        headers=headers,
    )
    assert detail.status_code == 200, detail.text
    detail_items = detail.json()["data"]["items"]
    assert any(item["platform_round_id"] == round_id and item["game_code"] == "boxe" for item in detail_items)

    replay = api_client.get(f"/games/boxe/round/{round_id}/replay", headers=headers)
    assert replay.status_code == 200, replay.text
    replay_data = replay.json()["data"]
    assert replay_data["platform_round_id"] == round_id
    assert Decimal(replay_data["payout_amount"]) == payout


def test_platform_adapter_bonus_cashout_uses_bonus_wallet(player_headers, db_connection):
    api_client, player, headers = player_headers
    grant_bonus_balance(db_connection, player["user_id"], Decimal("25.000000"))
    before_bonus = wallet_balance(db_connection, player["user_id"], "bonus")
    start = start_round(
        api_client,
        headers,
        key="adapter-bonus-start",
        wallet_source="bonus",
    )
    assert start.status_code == 200, start.text
    round_id = start.json()["data"]["round_id"]
    row, position = first_safe_pick(db_connection, round_id)
    assert reveal(api_client, headers, round_id=round_id, row=row, position=position, key="adapter-bonus-reveal").status_code == 200
    cashout_response = cashout(api_client, headers, round_id=round_id, key="adapter-bonus-cashout")
    assert cashout_response.status_code == 200, cashout_response.text

    platform_row = platform_round(db_connection, round_id)
    payout = Decimal(cashout_response.json()["data"]["payout"])
    assert platform_row["wallet_type"] == "bonus"
    assert platform_row["status"] == "won"
    assert wallet_balance(db_connection, player["user_id"], "bonus") == before_bonus - Decimal("1.000000") + payout


def test_platform_adapter_real_loss_consumes_bet_without_credit(player_headers, db_connection):
    api_client, player, headers = player_headers
    before_balance = wallet_balance(db_connection, player["user_id"], "cash")
    start = start_round(api_client, headers, key="adapter-loss-start", wallet_source="cash")
    assert start.status_code == 200, start.text
    round_id = start.json()["data"]["round_id"]
    row, position = first_mine_pick(db_connection, round_id)
    response = reveal(api_client, headers, round_id=round_id, row=row, position=position, key="adapter-loss-reveal")
    assert response.status_code == 200, response.text
    assert response.json()["data"]["outcome"] == "mine"

    platform_row = platform_round(db_connection, round_id)
    assert platform_row["status"] == "lost"
    assert Decimal(platform_row["payout_amount"]) == Decimal("0.000000")
    assert platform_row["settlement_ledger_transaction_id"] is None
    assert ledger_transaction_count(db_connection, round_id, "bet") == 1
    assert ledger_transaction_count(db_connection, round_id, "win") == 0
    assert wallet_balance(db_connection, player["user_id"], "cash") == before_balance - Decimal("1.000000")


def test_platform_adapter_top_row_auto_collect_settles_without_cashout(player_headers, db_connection):
    api_client, _player, headers = player_headers
    start = start_round(api_client, headers, key="adapter-top-row-start", wallet_source="cash")
    assert start.status_code == 200, start.text
    round_id = start.json()["data"]["round_id"]

    final_response = None
    for row, position in safe_path(db_connection, round_id):
        final_response = reveal(
            api_client,
            headers,
            round_id=round_id,
            row=row,
            position=position,
            key=f"adapter-top-row-reveal-{row}",
        )
        assert final_response.status_code == 200, final_response.text

    assert final_response is not None
    assert final_response.json()["data"]["outcome"] == "top_row"
    platform_row = platform_round(db_connection, round_id)
    assert platform_row["status"] == "won"
    assert platform_row["settlement_ledger_transaction_id"] is not None
    assert ledger_transaction_count(db_connection, round_id, "win") == 1


def test_platform_adapter_cashout_retry_does_not_double_credit(player_headers, db_connection):
    api_client, player, headers = player_headers
    round_id = prepare_cashoutable_round(
        api_client,
        headers,
        db_connection,
        key_prefix="adapter-retry",
        wallet_source="cash",
    )
    before_cashout = wallet_balance(db_connection, player["user_id"], "cash")
    first = cashout(api_client, headers, round_id=round_id, key="adapter-retry-cashout")
    second = cashout(api_client, headers, round_id=round_id, key="adapter-retry-cashout")
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    payout = Decimal(first.json()["data"]["payout"])
    assert ledger_transaction_count(db_connection, round_id, "win") == 1
    assert wallet_balance(db_connection, player["user_id"], "cash") == before_cashout + payout


def test_platform_adapter_concurrent_cashout_does_not_double_credit(player_headers, db_connection):
    api_client, player, headers = player_headers
    round_id = prepare_cashoutable_round(
        api_client,
        headers,
        db_connection,
        key_prefix="adapter-concurrent",
        wallet_source="cash",
    )
    before_cashout = wallet_balance(db_connection, player["user_id"], "cash")

    def _cashout(key: str):
        return cashout(api_client, headers, round_id=round_id, key=key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                _cashout,
                ["adapter-concurrent-a", "adapter-concurrent-b"],
            )
        )

    status_codes = sorted(response.status_code for response in responses)
    assert status_codes == [200, 409]
    winner = next(response for response in responses if response.status_code == 200)
    payout = Decimal(winner.json()["data"]["payout"])
    assert ledger_transaction_count(db_connection, round_id, "win") == 1
    assert wallet_balance(db_connection, player["user_id"], "cash") == before_cashout + payout


def test_boxe_i18n_manifest_defaults_are_valid():
    assert validate_default_copy_catalog() == []


def test_table_session_lifecycle_real_cash_start_reserves_table_balance(player_headers, db_connection):
    api_client, player, headers = player_headers
    table_session, access_session_id = create_boxe_table_session(api_client, headers, wallet_type="cash")
    response = start_round(
        api_client,
        headers,
        key="lifecycle-real-cash-start",
        wallet_source="cash",
        table_session_id=table_session["id"],
        access_session_id=access_session_id,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    round_id = data["round_id"]
    assert data["table_session_id"] == table_session["id"]
    assert data["table_session"]["table_balance_amount"] == "9.000000"
    assert data["table_session"]["loss_reserved_amount"] == "1.000000"

    session_row = boxe_session(db_connection, data["session_id"])
    platform_row = platform_round(db_connection, round_id)
    table_row = table_session_row(db_connection, table_session["id"])
    assert str(session_row["table_session_id"]) == table_session["id"]
    assert str(session_row["access_session_id"]) == access_session_id
    assert str(platform_row["table_session_id"]) == table_session["id"]
    assert str(platform_row["access_session_id"]) == access_session_id
    assert platform_row["wallet_type"] == "cash"
    assert f"{table_row['table_balance_amount']:.6f}" == "9.000000"
    assert f"{table_row['loss_reserved_amount']:.6f}" == "1.000000"
    assert f"{table_row['loss_consumed_amount']:.6f}" == "0.000000"
    assert wallet_balance(db_connection, player["user_id"], "cash") == Decimal("999.000000")


def test_table_session_lifecycle_real_bonus_start_reserves_bonus_table_balance(player_headers, db_connection):
    api_client, player, headers = player_headers
    grant_bonus_balance(db_connection, player["user_id"], Decimal("25.000000"))
    table_session, access_session_id = create_boxe_table_session(api_client, headers, wallet_type="bonus")
    response = start_round(
        api_client,
        headers,
        key="lifecycle-real-bonus-start",
        wallet_source="bonus",
        table_session_id=table_session["id"],
        access_session_id=access_session_id,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    platform_row = platform_round(db_connection, data["round_id"])
    table_row = table_session_row(db_connection, table_session["id"])
    assert platform_row["wallet_type"] == "bonus"
    assert str(platform_row["table_session_id"]) == table_session["id"]
    assert str(platform_row["access_session_id"]) == access_session_id
    assert f"{table_row['table_balance_amount']:.6f}" == "9.000000"
    assert f"{table_row['loss_reserved_amount']:.6f}" == "1.000000"
    assert f"{table_row['loss_consumed_amount']:.6f}" == "0.000000"
    assert wallet_balance(db_connection, player["user_id"], "bonus") == Decimal("24.000000")


def test_table_session_lifecycle_demo_start_has_no_platform_round(player_headers, db_connection):
    api_client, _player, headers = player_headers
    response = start_round(api_client, headers, key="lifecycle-demo-start")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["table_session_id"] is None
    assert data["table_session"] is None

    session_row = boxe_session(db_connection, data["session_id"])
    assert session_row["table_session_id"] is None
    assert session_row["access_session_id"] is None
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM platform_rounds WHERE id = %s", (data["round_id"],))
        assert int(cursor.fetchone()["count"]) == 0


def test_table_session_lifecycle_rejects_table_session_mismatch(player_headers, db_connection):
    api_client, _player, headers = player_headers
    wrong_game_table, _access_session_id = create_boxe_table_session(
        api_client,
        headers,
        game_code="mines",
        wallet_type="cash",
    )
    wrong_game_response = start_round(
        api_client,
        headers,
        key="lifecycle-mismatch-game",
        wallet_source="cash",
        table_session_id=wrong_game_table["id"],
    )
    assert_error(wrong_game_response, 422, "VALIDATION_ERROR")

    cash_table, _cash_access_session_id = create_boxe_table_session(
        api_client,
        headers,
        wallet_type="cash",
    )
    wallet_mismatch_response = start_round(
        api_client,
        headers,
        key="lifecycle-mismatch-wallet",
        wallet_source="bonus",
        table_session_id=cash_table["id"],
    )
    assert_error(wallet_mismatch_response, 422, "VALIDATION_ERROR")


def start_payload(**overrides):
    payload = {
        "title_code": "boxe001",
        "rows": 4,
        "difficulty": "easy",
        "bet_amount": "1.00",
        "wallet_source": "demo",
        "client_seed": "test-client-seed",
    }
    payload.update(overrides)
    return payload


def start_round(
    client,
    headers,
    *,
    key: str,
    wallet_source: str = "demo",
    table_session_id: str | None = None,
    access_session_id: str | None = None,
):
    payload = start_payload(wallet_source=wallet_source, client_seed=f"seed-{key}")
    if wallet_source in {"cash", "bonus"} and table_session_id is None:
        table_session, created_access_session_id = create_boxe_table_session(
            client,
            headers,
            wallet_type=wallet_source,
        )
        table_session_id = table_session["id"]
        access_session_id = created_access_session_id
    if table_session_id is not None:
        payload["table_session_id"] = table_session_id
    if access_session_id is not None:
        payload["access_session_id"] = access_session_id
    return client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": key},
        json=payload,
    )


def reveal(client, headers, *, round_id: str, row: int, position: int, key: str):
    return client.post(
        "/games/boxe/reveal",
        headers={**headers, "Idempotency-Key": key},
        json={"round_id": round_id, "row": row, "position": position},
    )


def cashout(client, headers, *, round_id: str, key: str):
    return client.post(
        "/games/boxe/cashout",
        headers={**headers, "Idempotency-Key": key},
        json={"round_id": round_id},
    )


def prepare_cashoutable_round(
    client,
    headers,
    db_connection,
    *,
    key_prefix: str,
    wallet_source: str = "demo",
) -> str:
    round_id = start_round(
        client,
        headers,
        key=f"{key_prefix}-start",
        wallet_source=wallet_source,
    ).json()["data"]["round_id"]
    row, position = first_safe_pick(db_connection, round_id)
    response = reveal(client, headers, round_id=round_id, row=row, position=position, key=f"{key_prefix}-reveal")
    assert response.status_code == 200, response.text
    assert response.json()["data"]["outcome"] == "safe"
    return round_id


def completed_cashout_round(client, headers, db_connection) -> str:
    key_prefix = f"completed-{uuid4().hex}"
    round_id, row, position = round_with_pick_within_board(
        client,
        headers,
        db_connection,
        key_prefix=key_prefix,
        want_safe=True,
    )
    reveal_response = reveal(
        client,
        headers,
        round_id=round_id,
        row=row,
        position=position,
        key=f"{key_prefix}-reveal",
    )
    assert reveal_response.status_code == 200, reveal_response.text
    response = cashout(client, headers, round_id=round_id, key=f"completed-cashout-{uuid4().hex}")
    assert response.status_code == 200, response.text
    return round_id


def round_with_pick_within_board(
    client,
    headers,
    db_connection,
    *,
    key_prefix: str,
    want_safe: bool,
) -> tuple[str, int, int]:
    for attempt in range(30):
        round_id = start_round(
            client,
            headers,
            key=f"{key_prefix}-start-{attempt}",
        ).json()["data"]["round_id"]
        pick = pick_for_step_within_board(
            db_connection,
            round_id,
            step=1,
            want_safe=want_safe,
        )
        if pick is not None:
            row, position = pick
            return round_id, row, position
    raise AssertionError(f"No BOXE board pick found for want_safe={want_safe}")


def round_with_safe_path_within_board(
    client,
    headers,
    db_connection,
    *,
    key_prefix: str,
) -> tuple[str, list[tuple[int, int]]]:
    for attempt in range(30):
        round_id = start_round(
            client,
            headers,
            key=f"{key_prefix}-start-{attempt}",
        ).json()["data"]["round_id"]
        path = safe_path_within_board(db_connection, round_id)
        if path is not None:
            return round_id, path
    raise AssertionError("No BOXE safe path found within board geometry")


def first_safe_pick(db_connection, round_id: str) -> tuple[int, int]:
    return pick_for_step(db_connection, round_id, step=1, want_safe=True)


def first_safe_pick_from_db(db_connection, round_id: str) -> tuple[int, int]:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT row_index, selected_box_index
            FROM boxe_picks
            WHERE round_id = %s
            ORDER BY step ASC
            LIMIT 1
            """,
            (round_id,),
        )
        row = cursor.fetchone()
    assert row is not None
    return int(row["row_index"]), int(row["selected_box_index"])


def first_mine_pick(db_connection, round_id: str) -> tuple[int, int]:
    return pick_for_step(db_connection, round_id, step=1, want_safe=False)


def safe_path(db_connection, round_id: str) -> list[tuple[int, int]]:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT rows_count FROM boxe_rounds WHERE id = %s", (round_id,))
        rows = int(cursor.fetchone()["rows_count"])
    return [pick_for_step(db_connection, round_id, step=step, want_safe=True) for step in range(1, rows + 1)]


def safe_path_within_board(db_connection, round_id: str) -> list[tuple[int, int]] | None:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT rows_count FROM boxe_rounds WHERE id = %s", (round_id,))
        rows = int(cursor.fetchone()["rows_count"])
    path: list[tuple[int, int]] = []
    for step in range(1, rows + 1):
        pick = pick_for_step_within_board(
            db_connection,
            round_id,
            step=step,
            want_safe=True,
        )
        if pick is None:
            return None
        path.append(pick)
    return path


def pick_for_step_within_board(
    db_connection,
    round_id: str,
    *,
    step: int,
    want_safe: bool,
) -> tuple[int, int] | None:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
    row = step - 1
    for position in range(int(round_row["rows_count"]) - row + 1):
        outcome = generate_step_outcome(
            rows=int(round_row["rows_count"]),
            difficulty=str(round_row["difficulty"]),
            step=step,
            selected_box_index=position,
            server_seed=str(round_row["server_seed"]),
            client_seed=str(round_row["client_seed"]),
            nonce=int(round_row["nonce"]),
        )
        if outcome.safe is want_safe:
            return row, position
    return None


def pick_for_step(db_connection, round_id: str, *, step: int, want_safe: bool) -> tuple[int, int]:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
    for position in range(20):
        outcome = generate_step_outcome(
            rows=int(round_row["rows_count"]),
            difficulty=str(round_row["difficulty"]),
            step=step,
            selected_box_index=position,
            server_seed=str(round_row["server_seed"]),
            client_seed=str(round_row["client_seed"]),
            nonce=int(round_row["nonce"]),
        )
        if outcome.safe is want_safe:
            return step - 1, position
    raise AssertionError("No matching pick found for test seed")


def assert_pyramid_full_reveal(
    reveal_payload,
    db_connection,
    round_id: str,
    *,
    expected_picks: list[tuple[int, int]],
) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
    rows_count = int(round_row["rows_count"])
    assert [row["row"] for row in reveal_payload] == list(range(rows_count))
    assert [len(row["cells"]) for row in reveal_payload] == [
        rows_count - row + 1 for row in range(rows_count)
    ]
    expected_pick_set = set(expected_picks)
    seen_pick_set = set()
    for reveal_row in reveal_payload:
        row = int(reveal_row["row"])
        for cell in reveal_row["cells"]:
            position = int(cell["position"])
            outcome = generate_step_outcome(
                rows=rows_count,
                difficulty=str(round_row["difficulty"]),
                step=row + 1,
                selected_box_index=position,
                server_seed=str(round_row["server_seed"]),
                client_seed=str(round_row["client_seed"]),
                nonce=int(round_row["nonce"]),
            )
            is_picked = (row, position) in expected_pick_set
            if cell["picked"]:
                seen_pick_set.add((row, position))
            assert cell["state"] == ("safe" if outcome.safe else "mine")
            assert cell["picked"] is is_picked
            assert cell["reveal_scope"] == (
                "picked_path" if is_picked else "terminal_full_reveal"
            )
    assert seen_pick_set == expected_pick_set


def platform_round(db_connection, round_id: str):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM platform_rounds WHERE id = %s", (round_id,))
        row = cursor.fetchone()
    assert row is not None
    return row


def boxe_session(db_connection, session_id: str):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_sessions WHERE id = %s", (session_id,))
        row = cursor.fetchone()
    assert row is not None
    return row


def table_session_row(db_connection, table_session_id: str):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM game_table_sessions WHERE id = %s", (table_session_id,))
        row = cursor.fetchone()
    assert row is not None
    return row


def create_boxe_table_session(
    client,
    headers,
    *,
    wallet_type: str = "cash",
    game_code: str = "boxe",
):
    access_session_id = None
    if game_code == "boxe":
        access_response = client.post(
            "/access-sessions",
            headers=headers,
            json={
                "game_code": "boxe",
                "title_code": "boxe001",
                "site_code": "casinoking",
            },
        )
        assert access_response.status_code == 200, access_response.text
        access_session_id = access_response.json()["data"]["id"]

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": "boxe001",
            "site_code": "casinoking",
            "wallet_type": wallet_type,
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
        },
    )
    assert create_response.status_code == 200, create_response.text
    return create_response.json()["data"], access_session_id


def ledger_transaction_count(db_connection, round_id: str, transaction_type: str) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM ledger_transactions
            WHERE reference_type = 'game_session'
              AND reference_id = %s
              AND transaction_type = %s
            """,
            (round_id, transaction_type),
        )
        return int(cursor.fetchone()["count"])


def wallet_balance(db_connection, user_id: str, wallet_type: str) -> Decimal:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT balance_snapshot
            FROM wallet_accounts
            WHERE user_id = %s
              AND wallet_type = %s
            """,
            (user_id, wallet_type),
        )
        row = cursor.fetchone()
    assert row is not None
    return Decimal(row["balance_snapshot"]).quantize(Decimal("0.000001"))


def grant_bonus_balance(db_connection, user_id: str, amount: Decimal) -> None:
    with db_connection.transaction():
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE wallet_accounts
                SET balance_snapshot = balance_snapshot + %s
                WHERE user_id = %s
                  AND wallet_type = 'bonus'
                """,
                (amount, user_id),
            )


def assert_error(response, status_code: int, code: str):
    assert response.status_code == status_code, response.text
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == code


def _apply_boxe_migration(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(MIGRATION_PATH.read_text(encoding="utf-8"))


def _drop_boxe_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(DOWN_SQL)


def _seed_boxe_catalog(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
            VALUES ('boxe', 'BOXE', 'app.modules.games.boxe', 'active')
            ON CONFLICT (engine_code) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                runtime_module = EXCLUDED.runtime_module,
                status = 'active'
            """
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
            VALUES
                ('boxe', 'boxe', 'BOXE Master', 'active', true, NULL),
                ('boxe001', 'boxe', 'BOXE 001', 'active', false, 'boxe')
            ON CONFLICT (title_code) DO UPDATE
            SET engine_code = EXCLUDED.engine_code,
                display_name = EXCLUDED.display_name,
                status = 'active',
                is_master = EXCLUDED.is_master,
                source_title_code = EXCLUDED.source_title_code,
                updated_at = NOW()
            """
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
            VALUES
                ('casinoking', 'boxe', 900, 'active', 'hidden', false, false, 'BOXE Master', 'Master BOXE', false),
                ('casinoking', 'boxe001', 901, 'active', 'visible', true, true, 'BOXE', 'BOXE test title', false)
            ON CONFLICT (site_code, title_code) DO UPDATE
            SET status = 'active',
                lobby_visibility = EXCLUDED.lobby_visibility,
                demo_enabled = EXCLUDED.demo_enabled,
                real_enabled = EXCLUDED.real_enabled,
                lobby_display_name = EXCLUDED.lobby_display_name,
                lobby_description = EXCLUDED.lobby_description,
                featured = EXCLUDED.featured,
                updated_at = NOW()
            """
        )
