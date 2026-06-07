from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
import time
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
import pytest

from app.modules.games.boxe import repository
from app.modules.games.boxe.randomness import build_server_seed_hash
from app.modules.games.boxe.state_machine import (
    BoxeRoundStatus,
    BoxeStateTransitionError,
    BoxeTransitionEvent,
    is_terminal,
    transition,
    transition_to_expired_with_auto_cashout,
    validate_collect_attempt,
    validate_pick_attempt,
)

BOXE_MIGRATION_PATHS = (
    Path("backend/migrations/sql/0039__boxe_session_tables.sql"),
    Path("backend/migrations/sql/0047__boxe_demo_session_id.sql"),
    Path("backend/migrations/sql/0048__boxe_drop_sessions.sql"),
    Path("backend/migrations/sql/0052__demo_anon_drop_user_fk.sql"),
)
BOXE_SESSION_TABLE_NAMES = {
    "boxe_idempotency_keys",
    "boxe_picks",
    "boxe_rounds",
}
DOWN_SQL = """
DROP TABLE IF EXISTS boxe_idempotency_keys;
DROP TABLE IF EXISTS boxe_picks;
DROP TABLE IF EXISTS boxe_rounds;
"""


@pytest.fixture(scope="module", autouse=True)
def boxe_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        _reset_boxe_schema(connection)
        yield
        _reset_boxe_schema(connection)


def test_boxe_migration_up_down_schema(db_connection):
    _drop_boxe_schema(db_connection)
    _apply_boxe_migrations(db_connection)

    table_names = _boxe_table_names(db_connection)
    assert BOXE_SESSION_TABLE_NAMES.issubset(table_names)
    assert "demo_session_id" in _boxe_round_column_names(db_connection)

    _drop_boxe_schema(db_connection)
    assert BOXE_SESSION_TABLE_NAMES.isdisjoint(_boxe_table_names(db_connection))
    _apply_boxe_migrations(db_connection)


@pytest.mark.parametrize(
    ("from_status", "event", "to_status"),
    [
        (None, BoxeTransitionEvent.START_ROUND, BoxeRoundStatus.CREATED),
        (BoxeRoundStatus.CREATED, BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS, BoxeRoundStatus.ACTIVE),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, BoxeRoundStatus.ROW_REVEALED),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, BoxeRoundStatus.ROW_REVEALED),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.MINE_PICK, BoxeRoundStatus.FAILED_MINE),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.MINE_PICK, BoxeRoundStatus.FAILED_MINE),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.MANUAL_COLLECT, BoxeRoundStatus.CASHOUT_PENDING),
        (BoxeRoundStatus.CASHOUT_PENDING, BoxeTransitionEvent.SETTLEMENT_SUCCESS, BoxeRoundStatus.COMPLETED_CASHOUT),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.SAFE_PICK_TOP_ROW, BoxeRoundStatus.COMPLETED_TOP_ROW),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.SAFE_PICK_TOP_ROW, BoxeRoundStatus.COMPLETED_TOP_ROW),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.RECOVERY_AUTO_CASHOUT, BoxeRoundStatus.COMPLETED_CASHOUT),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.RECOVERY_AUTO_CASHOUT, BoxeRoundStatus.COMPLETED_CASHOUT),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.RECOVERY_EXPIRE_ZERO_SAFE, BoxeRoundStatus.EXPIRED),
        (BoxeRoundStatus.CREATED, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY, BoxeRoundStatus.QUARANTINED),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY, BoxeRoundStatus.QUARANTINED),
        (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY, BoxeRoundStatus.QUARANTINED),
        (BoxeRoundStatus.CASHOUT_PENDING, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY, BoxeRoundStatus.QUARANTINED),
    ],
)
def test_legal_transitions_match_spec(from_status, event, to_status):
    result = transition(from_status, event)
    assert result.to_status == to_status
    assert result.terminal is is_terminal(to_status)


@pytest.mark.parametrize(
    ("from_status", "event"),
    [
        (None, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW),
        (BoxeRoundStatus.CREATED, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW),
        (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.MANUAL_COLLECT),
        (BoxeRoundStatus.FAILED_MINE, BoxeTransitionEvent.MANUAL_COLLECT),
        (BoxeRoundStatus.COMPLETED_TOP_ROW, BoxeTransitionEvent.MANUAL_COLLECT),
        (BoxeRoundStatus.COMPLETED_CASHOUT, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW),
    ],
)
def test_illegal_state_transitions_raise(from_status, event):
    with pytest.raises(BoxeStateTransitionError):
        transition(from_status, event)


def test_illegal_pick_attempts_match_spec():
    with pytest.raises(BoxeStateTransitionError, match="pick_before_start"):
        validate_pick_attempt(status=BoxeRoundStatus.CREATED, current_step=0, requested_step=1)
    with pytest.raises(BoxeStateTransitionError, match="pick_future_row"):
        validate_pick_attempt(status=BoxeRoundStatus.ACTIVE, current_step=0, requested_step=2)
    with pytest.raises(BoxeStateTransitionError, match="pick_previous_row"):
        validate_pick_attempt(status=BoxeRoundStatus.ROW_REVEALED, current_step=1, requested_step=1)
    with pytest.raises(BoxeStateTransitionError, match="reveal_after_terminal"):
        validate_pick_attempt(status=BoxeRoundStatus.FAILED_MINE, current_step=1, requested_step=2)


def test_illegal_collect_attempts_match_spec_terminal_replay():
    with pytest.raises(BoxeStateTransitionError, match="collect_before_safe_pick"):
        validate_collect_attempt(status=BoxeRoundStatus.ACTIVE, safe_picks_count=0)

    assert (
        validate_collect_attempt(status=BoxeRoundStatus.FAILED_MINE, safe_picks_count=1)
        == BoxeRoundStatus.FAILED_MINE
    )
    assert (
        validate_collect_attempt(status=BoxeRoundStatus.COMPLETED_TOP_ROW, safe_picks_count=4)
        == BoxeRoundStatus.COMPLETED_TOP_ROW
    )


def test_repository_round_lifecycle_and_idempotency(db_connection):
    round_row = _create_test_round(db_connection)

    active = repository.apply_transition(
        db_connection,
        round_id=round_row["id"],
        event=BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS,
    )
    assert active["status"] == "active"

    saved = repository.save_idempotency_result(
        db_connection,
        player_id=round_row["player_id"],
        round_id=round_row["id"],
        operation="cashout",
        idempotency_key="cashout-1",
        request_fingerprint="cashout:fingerprint",
        response={"status": "cashout_pending"},
    )
    replay = repository.get_idempotency_result(
        db_connection,
        player_id=round_row["player_id"],
        operation="cashout",
        idempotency_key="cashout-1",
        request_fingerprint="cashout:fingerprint",
    )
    assert replay["id"] == saved["id"]
    with pytest.raises(repository.BoxeIdempotencyConflict):
        repository.get_idempotency_result(
            db_connection,
            player_id=round_row["player_id"],
            operation="cashout",
            idempotency_key="cashout-1",
            request_fingerprint="different",
        )


def test_recovery_auto_cashout_interface():
    result = transition_to_expired_with_auto_cashout(BoxeRoundStatus.ROW_REVEALED)
    assert result.to_status == BoxeRoundStatus.COMPLETED_CASHOUT


def test_concurrent_reveals_are_serialized(database_url):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        round_row = _create_test_round(connection)
        repository.apply_transition(
            connection,
            round_id=round_row["id"],
            event=BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS,
        )

    def reveal(idempotency_key: str) -> str:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.transaction():
                locked = repository.lock_round(connection, round_id=round_row["id"])
                existing = repository.get_pick_by_idempotency_key(
                    connection,
                    round_id=round_row["id"],
                    idempotency_key=idempotency_key,
                )
                if existing:
                    return "idempotent"
                if int(locked.data["current_step"]) >= 1:
                    return "conflict"
                time.sleep(0.05)
                validate_pick_attempt(
                    status=locked.status,
                    current_step=int(locked.data["current_step"]),
                    requested_step=1,
                )
                repository.record_pick(
                    connection,
                    round_id=round_row["id"],
                    step=1,
                    row_index=0,
                    selected_box_index=0,
                    safe=True,
                    rng_material="a" * 64,
                    success_probability=Decimal("0.715328467153"),
                    idempotency_key=idempotency_key,
                    request_fingerprint=f"reveal:{idempotency_key}",
                    response={"safe": True},
                )
                repository.apply_transition(
                    connection,
                    round_id=round_row["id"],
                    event=BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW,
                )
                return "winner"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(reveal, ["reveal-a", "reveal-b"]))

    assert results == ["conflict", "winner"]
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) AS count FROM boxe_picks WHERE round_id = %s", (round_row["id"],))
            assert cursor.fetchone()["count"] == 1


@pytest.mark.parametrize("run", range(3))
def test_concurrent_cashout_vs_reveal_is_serialized(database_url, run):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        round_row = _create_test_round(connection)
        repository.apply_transition(
            connection,
            round_id=round_row["id"],
            event=BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS,
        )
        repository.record_pick(
            connection,
            round_id=round_row["id"],
            step=1,
            row_index=0,
            selected_box_index=0,
            safe=True,
            rng_material="b" * 64,
            success_probability=Decimal("0.715328467153"),
            idempotency_key=f"initial-{run}",
            request_fingerprint=f"initial:{run}",
            response={"safe": True},
        )
        repository.apply_transition(
            connection,
            round_id=round_row["id"],
            event=BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW,
        )

    def cashout() -> str:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.transaction():
                locked = repository.lock_round(connection, round_id=round_row["id"])
                validate_collect_attempt(
                    status=locked.status,
                    safe_picks_count=int(locked.data["safe_picks_count"]),
                )
                time.sleep(0.05)
                repository.apply_transition(
                    connection,
                    round_id=round_row["id"],
                    event=BoxeTransitionEvent.MANUAL_COLLECT,
                )
                return "cashout"

    def reveal() -> str:
        time.sleep(0.01)
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.transaction():
                locked = repository.lock_round(connection, round_id=round_row["id"])
                if locked.status == BoxeRoundStatus.CASHOUT_PENDING:
                    return "conflict"
                validate_pick_attempt(
                    status=locked.status,
                    current_step=int(locked.data["current_step"]),
                    requested_step=2,
                )
                return "reveal"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(cashout), executor.submit(reveal)]
        results = sorted(future.result() for future in futures)

    assert results == ["cashout", "conflict"]


def _create_test_player(connection):
    player_id = uuid4()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (id, email, role, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (player_id, f"{player_id}@test.com", "player", "active"),
        )
    return player_id


def _create_test_round(connection):
    player_id = _create_test_player(connection)
    return repository.create_round(
        connection,
        player_id=player_id,
        title_code="boxe001",
        site_code="test",
        rows=4,
        difficulty="easy",
        bet_amount=Decimal("1.00"),
        server_seed="server-seed",
        server_seed_hash=build_server_seed_hash("server-seed"),
        client_seed="client-seed",
        nonce=1,
        start_idempotency_key=f"start-{uuid4()}",
        request_fingerprint="start:fingerprint",
    )


def _reset_boxe_schema(connection) -> None:
    _drop_boxe_schema(connection)
    _apply_boxe_migrations(connection)


def _apply_boxe_migrations(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in BOXE_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))


def _drop_boxe_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(DOWN_SQL)


def _boxe_table_names(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name LIKE 'boxe_%'
            """
        )
        return {row["table_name"] for row in cursor.fetchall()}


def _boxe_round_column_names(connection) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'boxe_rounds'
            """
        )
        return {row["column_name"] for row in cursor.fetchall()}
