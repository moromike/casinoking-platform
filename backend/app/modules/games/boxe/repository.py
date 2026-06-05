from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from app.modules.games.boxe.math import (
    FAIRNESS_VERSION,
    calculate_payout,
    get_multiplier,
    get_multiplier_ladder,
    normalize_difficulty,
    validate_rows,
)
from app.modules.games.boxe.state_machine import (
    BoxeRoundStatus,
    BoxeTransitionEvent,
    transition,
)


class BoxeRepositoryConflict(RuntimeError):
    pass


class BoxeIdempotencyConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class LockedRound:
    data: dict[str, Any]

    @property
    def id(self) -> UUID:
        return self.data["id"]

    @property
    def status(self) -> BoxeRoundStatus:
        return BoxeRoundStatus(self.data["status"])


def create_session(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: UUID,
    title_code: str,
    site_code: str | None = None,
    access_session_id: UUID | None = None,
    table_session_id: UUID | None = None,
    session_id: UUID | None = None,
) -> dict[str, Any]:
    new_id = session_id or uuid4()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO boxe_sessions (
                id,
                player_id,
                access_session_id,
                table_session_id,
                title_code,
                site_code,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'active')
            RETURNING *
            """,
            (new_id, player_id, access_session_id, table_session_id, title_code, site_code),
        )
        return dict(cursor.fetchone())


def create_round(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: UUID,
    player_id: UUID,
    title_code: str,
    rows: int,
    difficulty: str,
    bet_amount: Decimal,
    server_seed: str,
    server_seed_hash: str,
    client_seed: str,
    nonce: int,
    start_idempotency_key: str,
    request_fingerprint: str,
    site_code: str | None = None,
    platform_round_id: UUID | None = None,
    demo_session_id: UUID | None = None,
    round_id: UUID | None = None,
) -> dict[str, Any]:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    new_id = round_id or uuid4()
    multiplier_ladder = get_multiplier_ladder(rows=rows, difficulty=difficulty)
    config_snapshot = {
        "rows": rows,
        "difficulty": difficulty,
        "rtp": "0.98",
        "fairness_version": FAIRNESS_VERSION,
    }
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO boxe_rounds (
                id,
                session_id,
                platform_round_id,
                demo_session_id,
                player_id,
                title_code,
                site_code,
                status,
                rows_count,
                difficulty,
                bet_amount,
                config_snapshot_json,
                multiplier_table_json,
                fairness_version,
                server_seed,
                server_seed_hash,
                client_seed,
                nonce,
                start_idempotency_key,
                request_fingerprint
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'created', %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                new_id,
                session_id,
                platform_round_id,
                demo_session_id,
                player_id,
                title_code,
                site_code,
                rows,
                difficulty,
                bet_amount,
                Jsonb(config_snapshot),
                Jsonb([str(value) for value in multiplier_ladder]),
                FAIRNESS_VERSION,
                server_seed,
                server_seed_hash,
                client_seed,
                nonce,
                start_idempotency_key,
                request_fingerprint,
            ),
        )
        return dict(cursor.fetchone())


def get_round(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def lock_round(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
) -> LockedRound:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_rounds
            WHERE id = %s
            FOR UPDATE
            """,
            (round_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"BOXE round not found: {round_id}")
        return LockedRound(dict(row))


def apply_transition(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    event: BoxeTransitionEvent | str,
    terminal_reason: str | None = None,
) -> dict[str, Any]:
    locked = lock_round(connection, round_id=round_id)
    state_transition = transition(locked.status, event)
    return update_round_status(
        connection,
        round_id=round_id,
        status=state_transition.to_status,
        terminal_reason=terminal_reason,
    )


def update_round_status(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    status: BoxeRoundStatus | str,
    terminal_reason: str | None = None,
    outcome: str | None = None,
    final_payout_amount: Decimal | None = None,
) -> dict[str, Any]:
    status_value = BoxeRoundStatus(status).value
    closed_at_expr = (
        "now()"
        if status_value
        in {
            "completed_cashout",
            "completed_top_row",
            "failed_mine",
            "expired",
            "quarantined",
        }
        else "NULL"
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE boxe_rounds
            SET status = %s,
                terminal_reason = COALESCE(%s, terminal_reason),
                outcome = COALESCE(%s, outcome),
                final_payout_amount = COALESCE(%s, final_payout_amount),
                closed_at = {closed_at_expr},
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (status_value, terminal_reason, outcome, final_payout_amount, round_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"BOXE round not found: {round_id}")
        return dict(row)


def record_pick(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    step: int,
    row_index: int,
    selected_box_index: int,
    safe: bool,
    rng_material: str,
    success_probability: Decimal,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    locked = lock_round(connection, round_id=round_id)
    rows = int(locked.data["rows_count"])
    difficulty = str(locked.data["difficulty"])
    multiplier_after = get_multiplier(rows=rows, difficulty=difficulty, step=step)
    payout_after = (
        calculate_payout(
            bet_amount=locked.data["bet_amount"],
            rows=rows,
            difficulty=difficulty,
            step=step,
        )
        if safe
        else Decimal("0")
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO boxe_picks (
                id,
                round_id,
                step,
                row_index,
                selected_box_index,
                safe,
                multiplier_after,
                payout_after,
                rng_material,
                success_probability,
                idempotency_key,
                request_fingerprint,
                response_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                uuid4(),
                round_id,
                step,
                row_index,
                selected_box_index,
                safe,
                multiplier_after,
                payout_after,
                rng_material,
                success_probability,
                idempotency_key,
                request_fingerprint,
                Jsonb(response),
            ),
        )
        pick = dict(cursor.fetchone())
        cursor.execute(
            """
            UPDATE boxe_rounds
            SET current_step = GREATEST(current_step, %s),
                safe_picks_count = safe_picks_count + %s,
                multiplier_current = %s,
                payout_current = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (step, 1 if safe else 0, multiplier_after, payout_after, round_id),
        )
        pick["round"] = dict(cursor.fetchone())
        return pick


def get_pick_by_idempotency_key(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    idempotency_key: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_picks
            WHERE round_id = %s AND idempotency_key = %s
            """,
            (round_id, idempotency_key),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def save_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
    session_id: UUID | None = None,
    round_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    if session_id is None and round_id is None:
        raise ValueError("session_id or round_id is required")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO boxe_idempotency_keys (
                id,
                session_id,
                round_id,
                operation,
                idempotency_key,
                request_fingerprint,
                response_json,
                expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                uuid4(),
                session_id,
                round_id,
                operation,
                idempotency_key,
                request_fingerprint,
                Jsonb(response),
                expires_at,
            ),
        )
        return dict(cursor.fetchone())


def get_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    session_id: UUID | None = None,
    round_id: UUID | None = None,
) -> dict[str, Any] | None:
    if session_id is None and round_id is None:
        raise ValueError("session_id or round_id is required")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_idempotency_keys
            WHERE operation = %s
              AND idempotency_key = %s
              AND (session_id IS NOT DISTINCT FROM %s)
              AND (round_id IS NOT DISTINCT FROM %s)
            """,
            (operation, idempotency_key, session_id, round_id),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        result = dict(row)
        if result["request_fingerprint"] != request_fingerprint:
            raise BoxeIdempotencyConflict("same idempotency key with different payload")
        return result
