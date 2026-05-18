from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
import pytest

from app.modules.games.boxe.randomness import generate_step_outcome

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
        yield
        _drop_boxe_schema(connection)


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
    round_id = prepare_cashoutable_round(api_client, headers, db_connection, key_prefix="cashout-success")
    first = cashout(api_client, headers, round_id=round_id, key="cashout-retry")
    second = cashout(api_client, headers, round_id=round_id, key="cashout-retry")
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json()["data"]["status"] == "completed_cashout"


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


def start_payload(**overrides):
    payload = {
        "title_code": "boxe001",
        "rows": 4,
        "difficulty": "easy",
        "bet_amount": "1.00",
        "wallet_source": "cash",
        "client_seed": "test-client-seed",
    }
    payload.update(overrides)
    return payload


def start_round(client, headers, *, key: str):
    return client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": key},
        json=start_payload(client_seed=f"seed-{key}"),
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


def prepare_cashoutable_round(client, headers, db_connection, *, key_prefix: str) -> str:
    round_id = start_round(client, headers, key=f"{key_prefix}-start").json()["data"]["round_id"]
    row, position = first_safe_pick(db_connection, round_id)
    response = reveal(client, headers, round_id=round_id, row=row, position=position, key=f"{key_prefix}-reveal")
    assert response.status_code == 200, response.text
    assert response.json()["data"]["outcome"] == "safe"
    return round_id


def completed_cashout_round(client, headers, db_connection) -> str:
    round_id = prepare_cashoutable_round(client, headers, db_connection, key_prefix=f"completed-{uuid4().hex}")
    response = cashout(client, headers, round_id=round_id, key=f"completed-cashout-{uuid4().hex}")
    assert response.status_code == 200, response.text
    return round_id


def first_safe_pick(db_connection, round_id: str) -> tuple[int, int]:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
    for position in range(20):
        outcome = generate_step_outcome(
            rows=int(round_row["rows_count"]),
            difficulty=str(round_row["difficulty"]),
            step=1,
            selected_box_index=position,
            server_seed=str(round_row["server_seed"]),
            client_seed=str(round_row["client_seed"]),
            nonce=int(round_row["nonce"]),
        )
        if outcome.safe:
            return 0, position
    raise AssertionError("No safe pick found for test seed")


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
