"""Shared idempotency module — one table (game_idempotency_keys) for all games.

Pattern: ON CONFLICT DO NOTHING + SELECT recovery + fingerprint comparison.
Extracted from the Mines repository (the only correct pre-unification
implementation) and promoted to serve Boxe, Hi-Lo, and Mines uniformly.

Fingerprint semantics are game-specific and INVARIANT: the caller computes
the fingerprint (sha256 for Boxe/Hi-Lo, plain string for Mines cashout) and
passes it in.  This module compares bytes-for-bytes and nothing else.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import DictRow


class GameIdempotencyConflict(Exception):
    """Raised when the same idempotency key is reused with a different fingerprint."""


def save_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    game_code: str,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
    round_id: str | UUID | None = None,
) -> dict[str, Any] | None:
    """INSERT with ON CONFLICT DO NOTHING, then recover on conflict.

    Returns:
        The *response* dict if the row was freshly inserted.
        The stored response_json if the key already existed with a matching
        fingerprint (replay).
    Raises:
        GameIdempotencyConflict: key exists with a *different* fingerprint.
    Returns None:
        Only if the conflict row cannot be found (should not happen under
        normal operation).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_idempotency_keys (
                id, game_code, player_id, round_id, operation, idempotency_key,
                request_fingerprint, response_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT game_idempotency_keys_player_operation_key
            DO NOTHING
            """,
            (
                uuid4(),
                game_code,
                str(player_id),
                str(round_id) if round_id is not None else None,
                operation,
                idempotency_key,
                request_fingerprint,
                json.dumps(response),
            ),
        )
        if cursor.rowcount == 1:
            return response
        cursor.execute(
            """
            SELECT response_json, request_fingerprint
            FROM game_idempotency_keys
            WHERE game_code = %s
              AND player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            """,
            (game_code, str(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise GameIdempotencyConflict(
                f"Idempotency key already used with a different payload "
                f"(game={game_code}, operation={operation})"
            )
        return dict(row["response_json"])


def get_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    game_code: str,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, Any] | None:
    """Look up a previously stored response.

    Returns:
        The stored response_json dict on a matching replay.
        None if no row exists for this key.
    Raises:
        GameIdempotencyConflict: key exists with a *different* fingerprint.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT response_json, request_fingerprint
            FROM game_idempotency_keys
            WHERE game_code = %s
              AND player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            """,
            (game_code, str(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise GameIdempotencyConflict(
                f"Idempotency key already used with a different payload "
                f"(game={game_code}, operation={operation})"
            )
        return dict(row["response_json"])


def recover_after_unique_violation(
    *,
    game_code: str,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, Any] | None:
    """Read the stored response on a *fresh* connection after a UniqueViolation.

    Used by Boxe/Hi-Lo start_round: the original transaction has been rolled
    back by the UniqueViolation, so we cannot reuse its connection.

    Returns:
        The stored response_json if found with a matching fingerprint.
    Raises:
        GameIdempotencyConflict: key exists with a different fingerprint.
    Returns None:
        If no row exists for this key — the UniqueViolation was NOT from
        the idempotency constraint, and the original error should propagate.
    """
    from app.db.connection import db_connection

    with db_connection() as conn:
        return get_idempotency_result(
            conn,
            game_code=game_code,
            player_id=player_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )


def save_idempotency_row(
    connection: psycopg.Connection[DictRow],
    *,
    game_code: str,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
    round_id: str | UUID | None = None,
) -> dict[str, Any] | None:
    """INSERT with ON CONFLICT DO NOTHING, then recover on conflict.

    Returns the FULL ROW (id, created_at, response_json, etc.) — matching
    the pre-unification Boxe/Hi-Lo repository behavior.
    """
    new_id = uuid4()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_idempotency_keys (
                id, game_code, player_id, round_id, operation, idempotency_key,
                request_fingerprint, response_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT game_idempotency_keys_player_operation_key
            DO NOTHING
            """,
            (
                new_id,
                game_code,
                str(player_id),
                str(round_id) if round_id is not None else None,
                operation,
                idempotency_key,
                request_fingerprint,
                json.dumps(response),
            ),
        )
        if cursor.rowcount == 1:
            cursor.execute(
                "SELECT * FROM game_idempotency_keys WHERE id = %s",
                (new_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        cursor.execute(
            """
            SELECT *
            FROM game_idempotency_keys
            WHERE game_code = %s
              AND player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            """,
            (game_code, str(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise GameIdempotencyConflict(
                f"Idempotency key already used with a different payload "
                f"(game={game_code}, operation={operation})"
            )
        return dict(row)


def get_idempotency_row(
    connection: psycopg.Connection[DictRow],
    *,
    game_code: str,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, Any] | None:
    """Look up a previously stored response.

    Returns the FULL ROW (id, created_at, response_json, etc.) — matching
    the pre-unification Boxe/Hi-Lo repository behavior.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM game_idempotency_keys
            WHERE game_code = %s
              AND player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            """,
            (game_code, str(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise GameIdempotencyConflict(
                f"Idempotency key already used with a different payload "
                f"(game={game_code}, operation={operation})"
            )
        return dict(row)
