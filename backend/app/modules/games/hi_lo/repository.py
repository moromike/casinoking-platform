from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from app.modules.games.hi_lo.math import (
    FAIRNESS_VERSION,
    Card,
    calculate_payout,
    get_prediction_quote,
)
from app.modules.games.hi_lo.state_machine import (
    HiLoRoundStatus,
    HiLoTransitionEvent,
    transition,
)


class HiLoIdempotencyConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class LockedRound:
    data: dict[str, Any]

    @property
    def id(self) -> UUID:
        return self.data["id"]

    @property
    def status(self) -> HiLoRoundStatus:
        return HiLoRoundStatus(self.data["status"])


def create_round(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: UUID,
    title_code: str,
    site_code: str,
    wallet_source: str,
    bet_amount: Decimal,
    current_card: Card,
    server_seed: str,
    server_seed_hash: str,
    client_seed: str,
    round_nonce: int,
    start_idempotency_key: str,
    request_fingerprint: str,
    demo_session_id: UUID | None = None,
    access_session_id: UUID | None = None,
    table_session_id: UUID | None = None,
    platform_round_id: UUID | None = None,
    round_id: UUID | None = None,
) -> dict[str, Any]:
    new_id = round_id or uuid4()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO hi_lo_rounds (
                id,
                platform_round_id,
                player_id,
                access_session_id,
                table_session_id,
                demo_session_id,
                title_code,
                site_code,
                status,
                wallet_source,
                bet_amount,
                current_card_rank,
                current_card_suit,
                current_draw_index,
                fairness_version,
                server_seed,
                server_seed_hash,
                client_seed,
                round_nonce,
                start_idempotency_key,
                request_fingerprint
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, 'created', %s, %s,
                %s, %s, 0, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                new_id,
                platform_round_id,
                player_id,
                access_session_id,
                table_session_id,
                demo_session_id,
                title_code,
                site_code,
                wallet_source,
                bet_amount,
                current_card.rank,
                current_card.suit,
                FAIRNESS_VERSION,
                server_seed,
                server_seed_hash,
                client_seed,
                round_nonce,
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
        cursor.execute("SELECT * FROM hi_lo_rounds WHERE id = %s", (round_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_open_round_for_player_title(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: UUID,
    title_code: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM hi_lo_rounds
            WHERE player_id = %s
              AND title_code = %s
              AND status IN ('created', 'active', 'cashout_pending')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (player_id, title_code),
        )
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
            FROM hi_lo_rounds
            WHERE id = %s
            FOR UPDATE
            """,
            (round_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"HI-LO round not found: {round_id}")
        return LockedRound(dict(row))


def apply_transition(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    event: HiLoTransitionEvent | str,
    terminal_reason: str | None = None,
    outcome: str | None = None,
    final_payout_amount: Decimal | None = None,
) -> dict[str, Any]:
    locked = lock_round(connection, round_id=round_id)
    state_transition = transition(locked.status, event)
    return update_round_status(
        connection,
        round_id=round_id,
        status=state_transition.to_status,
        terminal_reason=terminal_reason,
        outcome=outcome,
        final_payout_amount=final_payout_amount,
    )


def update_round_status(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    status: HiLoRoundStatus | str,
    terminal_reason: str | None = None,
    outcome: str | None = None,
    final_payout_amount: Decimal | None = None,
) -> dict[str, Any]:
    status_value = HiLoRoundStatus(status).value
    closed_at_expr = (
        "now()"
        if status_value
        in {"completed_cashout", "failed_prediction", "expired", "quarantined"}
        else "NULL"
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE hi_lo_rounds
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
            raise KeyError(f"HI-LO round not found: {round_id}")
        return dict(row)


def update_round_after_active_skip(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    card: Card,
    draw_index: int,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE hi_lo_rounds
            SET current_card_rank = %s,
                current_card_suit = %s,
                current_draw_index = %s,
                active_skip_count = active_skip_count + 1,
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (card.rank, card.suit, draw_index, round_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"HI-LO round not found: {round_id}")
        return dict(row)


def update_round_after_prediction(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    previous_cumulative_probability: Decimal,
    previous_bet_amount: Decimal,
    previous_card: Card,
    prediction_action: str,
    next_card: Card,
    draw_index: int,
    success: bool,
) -> dict[str, Any]:
    quote = get_prediction_quote(
        current_rank=previous_card.rank,
        action=prediction_action,
        current_cumulative_probability=previous_cumulative_probability,
    )
    if success:
        new_cumulative_probability = quote.cumulative_probability_after_success
        multiplier = quote.multiplier
        payout = calculate_payout(bet_amount=previous_bet_amount, multiplier=multiplier)
        status = HiLoRoundStatus.ACTIVE.value
        outcome = None
        terminal_reason = None
        final_payout_amount = None
        closed_at_expr = "NULL"
    else:
        new_cumulative_probability = previous_cumulative_probability
        multiplier = Decimal("1.0000")
        payout = Decimal("0.000000")
        status = HiLoRoundStatus.FAILED_PREDICTION.value
        outcome = "loss"
        terminal_reason = "prediction_failed"
        final_payout_amount = Decimal("0.000000")
        closed_at_expr = "now()"
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE hi_lo_rounds
            SET status = %s,
                current_card_rank = %s,
                current_card_suit = %s,
                current_draw_index = %s,
                correct_predictions_count = correct_predictions_count + %s,
                active_skip_count = CASE WHEN %s THEN 0 ELSE active_skip_count END,
                cumulative_success_probability = %s,
                multiplier_current = %s,
                payout_current = %s,
                final_payout_amount = COALESCE(%s, final_payout_amount),
                outcome = COALESCE(%s, outcome),
                terminal_reason = COALESCE(%s, terminal_reason),
                closed_at = {closed_at_expr},
                updated_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (
                status,
                next_card.rank,
                next_card.suit,
                draw_index,
                1 if success else 0,
                success,
                new_cumulative_probability,
                multiplier,
                payout,
                final_payout_amount,
                outcome,
                terminal_reason,
                round_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"HI-LO round not found: {round_id}")
        return dict(row)


def record_action(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    action_type: str,
    drawn_card: Card,
    draw_index: int,
    draw_purpose: str,
    rng_material: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
    previous_card: Card | None = None,
    prediction_action: str | None = None,
    success: bool | None = None,
    probability: Decimal | None = None,
    multiplier_after: Decimal = Decimal("1.0000"),
    payout_after: Decimal = Decimal("0.000000"),
) -> dict[str, Any]:
    action_index = next_action_index(connection, round_id=round_id)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO hi_lo_actions (
                id,
                round_id,
                action_index,
                action_type,
                prediction_action,
                success,
                probability,
                multiplier_after,
                payout_after,
                previous_card_json,
                drawn_card_json,
                draw_index,
                draw_purpose,
                rng_material,
                response_json,
                idempotency_key,
                request_fingerprint
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                uuid4(),
                round_id,
                action_index,
                action_type,
                prediction_action,
                success,
                probability,
                multiplier_after,
                payout_after,
                Jsonb(card_payload(previous_card)) if previous_card else None,
                Jsonb(card_payload(drawn_card)),
                draw_index,
                draw_purpose,
                rng_material,
                Jsonb(response),
                idempotency_key,
                request_fingerprint,
            ),
        )
        return dict(cursor.fetchone())


def next_action_index(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COALESCE(MAX(action_index), -1) + 1 AS next_index FROM hi_lo_actions WHERE round_id = %s",
            (round_id,),
        )
        return int(cursor.fetchone()["next_index"])


def get_actions(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM hi_lo_actions
            WHERE round_id = %s
            ORDER BY action_index ASC
            """,
            (round_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def save_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: UUID,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, Any],
    round_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO hi_lo_idempotency_keys (
                id,
                player_id,
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
                player_id,
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
    player_id: UUID,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM hi_lo_idempotency_keys
            WHERE player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (player_id, operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        result = dict(row)
        if result["request_fingerprint"] != request_fingerprint:
            raise HiLoIdempotencyConflict("same idempotency key with different payload")
        return result


def create_platform_round(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    player_id: UUID,
    title_code: str,
    site_code: str,
    access_session_id: UUID | None,
    wallet_account_id: str,
    wallet_type: str,
    bet_amount: Decimal,
    start_ledger_transaction_id: str,
    wallet_balance_after_start: Decimal,
    table_session_id: str | None,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO platform_rounds (
                id,
                user_id,
                game_code,
                title_code,
                site_code,
                access_session_id,
                wallet_account_id,
                wallet_type,
                bet_amount,
                status,
                payout_amount,
                start_ledger_transaction_id,
                wallet_balance_after_start,
                table_session_id,
                idempotency_key,
                request_fingerprint
            )
            VALUES (%s, %s, 'hi_lo', %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                round_id,
                player_id,
                title_code,
                site_code,
                access_session_id,
                wallet_account_id,
                wallet_type,
                bet_amount,
                Decimal("0.000000"),
                start_ledger_transaction_id,
                wallet_balance_after_start,
                table_session_id,
                idempotency_key,
                request_fingerprint,
            ),
        )
        return dict(cursor.fetchone())


def close_platform_round(
    connection: psycopg.Connection[DictRow],
    *,
    round_id: UUID,
    status: str,
    payout_amount: Decimal,
    settlement_ledger_transaction_id: str | None = None,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE platform_rounds
            SET status = %s,
                payout_amount = %s,
                settlement_ledger_transaction_id = COALESCE(%s, settlement_ledger_transaction_id),
                closed_at = now()
            WHERE id = %s
            RETURNING *
            """,
            (status, payout_amount, settlement_ledger_transaction_id, round_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Platform round not found: {round_id}")
        return dict(row)


def list_terminal_rounds(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: UUID,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM hi_lo_rounds
            WHERE player_id = %s
              AND status IN ('completed_cashout', 'failed_prediction', 'expired', 'quarantined')
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (player_id, limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]


def card_payload(card: Card) -> dict[str, object]:
    return {
        "rank": card.rank,
        "rank_label": card.rank_label,
        "suit": card.suit,
        "color": card.color,
    }


def card_from_round(row: dict[str, Any]) -> Card:
    return Card(rank=int(row["current_card_rank"]), suit=str(row["current_card_suit"]))
