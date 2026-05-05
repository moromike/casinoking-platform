from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
import json
from typing import Iterator

import psycopg

from app.db.connection import db_connection

DEMO_STARTING_BALANCE = Decimal("100.000000")
DEMO_STATUS_ACTIVE = "active"
DEMO_STATUS_EXHAUSTED = "exhausted"


class DemoWalletValidationError(Exception):
    pass


class DemoWalletInsufficientBalanceError(Exception):
    pass


class DemoWalletIdempotencyConflictError(Exception):
    pass


@contextmanager
def _managed_cursor(
    cursor: psycopg.Cursor | None,
) -> Iterator[psycopg.Cursor]:
    if cursor is not None:
        yield cursor
        return

    with db_connection() as connection:
        with connection.cursor() as managed:
            yield managed


def open_demo_session(
    *,
    anonymous_id: str,
    title_code: str,
    cursor: psycopg.Cursor | None = None,
) -> dict[str, object]:
    with _managed_cursor(cursor) as active_cursor:
        active_cursor.execute(
            """
            SELECT *
            FROM demo_play_sessions
            WHERE anonymous_id = %s
              AND title_code = %s
              AND status = %s
            ORDER BY opened_at DESC
            LIMIT 1
            FOR UPDATE
            """,
            (anonymous_id, title_code, DEMO_STATUS_ACTIVE),
        )
        row = active_cursor.fetchone()
        if row is not None:
            return _serialize_session(row)

        active_cursor.execute(
            """
            INSERT INTO demo_play_sessions (
                anonymous_id,
                title_code,
                balance_chips,
                starting_balance_chips
            )
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (
                anonymous_id,
                title_code,
                DEMO_STARTING_BALANCE,
                DEMO_STARTING_BALANCE,
            ),
        )
        created = active_cursor.fetchone()
        assert created is not None
        return _serialize_session(created)


def get_active_session(
    *,
    anonymous_id: str,
    title_code: str,
    cursor: psycopg.Cursor | None = None,
) -> dict[str, object] | None:
    with _managed_cursor(cursor) as active_cursor:
        active_cursor.execute(
            """
            SELECT *
            FROM demo_play_sessions
            WHERE anonymous_id = %s
              AND title_code = %s
              AND status = %s
            ORDER BY opened_at DESC
            LIMIT 1
            """,
            (anonymous_id, title_code, DEMO_STATUS_ACTIVE),
        )
        row = active_cursor.fetchone()
        return _serialize_session(row) if row is not None else None


def debit_for_bet(
    *,
    session_id: str,
    amount: Decimal,
    idempotency_key: str,
    payload: dict[str, object] | None = None,
    cursor: psycopg.Cursor | None = None,
) -> dict[str, object]:
    normalized_amount = _normalize_amount(amount)
    if normalized_amount <= 0:
        raise DemoWalletValidationError("Bet amount must be greater than zero")

    with _managed_cursor(cursor) as active_cursor:
        session = _lock_session(active_cursor, session_id=session_id)
        existing_event = _get_event_by_key(
            active_cursor,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
        payload_json = _canonical_payload(payload)
        if existing_event is not None:
            _ensure_same_event(
                existing_event,
                expected_kind="bet",
                expected_amount=normalized_amount,
                expected_payload=payload_json,
            )
            return _serialize_session(session, event_id=str(existing_event["id"]))

        if session["status"] != DEMO_STATUS_ACTIVE:
            raise DemoWalletValidationError("Demo session is not active")
        if Decimal(session["balance_chips"]) < normalized_amount:
            raise DemoWalletInsufficientBalanceError("Not enough demo chips")

        active_cursor.execute(
            """
            UPDATE demo_play_sessions
            SET balance_chips = balance_chips - %s
            WHERE id = %s
            RETURNING *
            """,
            (normalized_amount, session_id),
        )
        updated = active_cursor.fetchone()
        assert updated is not None
        event_id = _insert_event(
            active_cursor,
            session_id=session_id,
            kind="bet",
            amount=normalized_amount,
            idempotency_key=idempotency_key,
            payload_json=payload_json,
        )
        return _serialize_session(updated, event_id=event_id)


def credit_for_win(
    *,
    session_id: str,
    amount: Decimal,
    idempotency_key: str,
    payload: dict[str, object] | None = None,
    cursor: psycopg.Cursor | None = None,
) -> dict[str, object]:
    normalized_amount = _normalize_amount(amount)
    if normalized_amount <= 0:
        raise DemoWalletValidationError("Win amount must be greater than zero")

    with _managed_cursor(cursor) as active_cursor:
        session = _lock_session(active_cursor, session_id=session_id)
        existing_event = _get_event_by_key(
            active_cursor,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
        payload_json = _canonical_payload(payload)
        if existing_event is not None:
            _ensure_same_event(
                existing_event,
                expected_kind="win",
                expected_amount=normalized_amount,
                expected_payload=payload_json,
            )
            return _serialize_session(session, event_id=str(existing_event["id"]))

        if session["status"] != DEMO_STATUS_ACTIVE:
            raise DemoWalletValidationError("Demo session is not active")

        active_cursor.execute(
            """
            UPDATE demo_play_sessions
            SET balance_chips = balance_chips + %s
            WHERE id = %s
            RETURNING *
            """,
            (normalized_amount, session_id),
        )
        updated = active_cursor.fetchone()
        assert updated is not None
        event_id = _insert_event(
            active_cursor,
            session_id=session_id,
            kind="win",
            amount=normalized_amount,
            idempotency_key=idempotency_key,
            payload_json=payload_json,
        )
        return _serialize_session(updated, event_id=event_id)


def record_loss(
    *,
    session_id: str,
    idempotency_key: str,
    payload: dict[str, object] | None = None,
    cursor: psycopg.Cursor | None = None,
) -> dict[str, object]:
    with _managed_cursor(cursor) as active_cursor:
        session = _lock_session(active_cursor, session_id=session_id)
        payload_json = _canonical_payload(payload)
        existing_event = _get_event_by_key(
            active_cursor,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
        if existing_event is not None:
            _ensure_same_event(
                existing_event,
                expected_kind="mine_hit",
                expected_amount=Decimal("0.000000"),
                expected_payload=payload_json,
            )
            return _serialize_session(session, event_id=str(existing_event["id"]))

        event_id = _insert_event(
            active_cursor,
            session_id=session_id,
            kind="mine_hit",
            amount=Decimal("0.000000"),
            idempotency_key=idempotency_key,
            payload_json=payload_json,
        )
        if Decimal(session["balance_chips"]) == Decimal("0.000000"):
            active_cursor.execute(
                """
                UPDATE demo_play_sessions
                SET status = %s,
                    closed_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (DEMO_STATUS_EXHAUSTED, session_id),
            )
            updated = active_cursor.fetchone()
            assert updated is not None
            return _serialize_session(updated, event_id=event_id)
        return _serialize_session(session, event_id=event_id)


def _lock_session(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        SELECT *
        FROM demo_play_sessions
        WHERE id = %s
        FOR UPDATE
        """,
        (session_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise DemoWalletValidationError("Demo session not found")
    return row


def _get_event_by_key(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT *
        FROM demo_round_events
        WHERE demo_play_session_id = %s
          AND idempotency_key = %s
        """,
        (session_id, idempotency_key),
    )
    return cursor.fetchone()


def _insert_event(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    kind: str,
    amount: Decimal,
    idempotency_key: str,
    payload_json: str | None,
) -> str:
    cursor.execute(
        """
        INSERT INTO demo_round_events (
            demo_play_session_id,
            kind,
            amount,
            idempotency_key,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (session_id, kind, amount, idempotency_key, payload_json),
    )
    row = cursor.fetchone()
    assert row is not None
    return str(row["id"])


def _ensure_same_event(
    row: dict[str, object],
    *,
    expected_kind: str,
    expected_amount: Decimal,
    expected_payload: str | None,
) -> None:
    stored_payload = (
        json.dumps(row["payload_json"], separators=(",", ":"), sort_keys=True)
        if row["payload_json"] is not None
        else None
    )
    if (
        row["kind"] != expected_kind
        or Decimal(row["amount"]) != expected_amount
        or stored_payload != expected_payload
    ):
        raise DemoWalletIdempotencyConflictError(
            "Idempotency key already used with a different payload"
        )


def _normalize_amount(amount: Decimal) -> Decimal:
    return Decimal(amount).quantize(Decimal("0.000001"))


def _canonical_payload(payload: dict[str, object] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _serialize_session(
    row: dict[str, object],
    *,
    event_id: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "id": str(row["id"]),
        "anonymous_id": str(row["anonymous_id"]),
        "user_id": str(row["user_id"]) if row["user_id"] else None,
        "title_code": row["title_code"],
        "balance_chips": Decimal(row["balance_chips"]),
        "starting_balance_chips": Decimal(row["starting_balance_chips"]),
        "status": row["status"],
        "opened_at": row["opened_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }
    if event_id is not None:
        result["event_id"] = event_id
    return result
