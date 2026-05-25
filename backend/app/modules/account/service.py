from __future__ import annotations

import base64
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
import json
from uuid import UUID

from app.db.connection import db_connection

DEFAULT_WALLET_MOVEMENT_LIMIT = 20
MAX_WALLET_MOVEMENT_LIMIT = 50
DEFAULT_STATEMENT_MOVEMENT_LIMIT = 20
MAX_STATEMENT_MOVEMENT_LIMIT = 50
DEFAULT_STATEMENT_DETAIL_LIMIT = 50
MAX_STATEMENT_DETAIL_LIMIT = 50
DEFAULT_STATEMENT_CATEGORY = "all"
DEFAULT_STATEMENT_PERIOD = "last_30_days"
DEFAULT_STATEMENT_WALLET_TYPE = "cash"
STATEMENT_BALANCE_DISCLAIMER = "Il saldo riflette il wallet, non solo le righe filtrate."

STATEMENT_CATEGORIES = {
    "all",
    "deposits_withdrawals",
    "game",
    "bonus",
    "adjustments",
}
STATEMENT_PERIODS = {
    "today",
    "last_7_days",
    "last_30_days",
    "current_month",
    "previous_month",
    "custom",
}
STATEMENT_WALLET_TYPES = {"cash", "bonus"}


class AccountCursorError(Exception):
    pass


class AccountStatementValidationError(Exception):
    pass


class AccountStatementNotFoundError(Exception):
    pass


def list_wallet_movements_for_user(
    *,
    user_id: str,
    limit: int = DEFAULT_WALLET_MOVEMENT_LIMIT,
    cursor: str | None = None,
) -> dict[str, object]:
    normalized_limit = max(1, min(limit, MAX_WALLET_MOVEMENT_LIMIT))
    decoded_cursor = _decode_cursor(cursor) if cursor else None

    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                WITH wallet_movements AS (
                    SELECT
                        lt.id AS transaction_id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.created_at,
                        wa.id AS wallet_account_id,
                        wa.wallet_type,
                        wa.currency_code,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE -le.amount
                        END AS signed_amount
                    FROM ledger_transactions lt
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN wallet_accounts wa ON wa.ledger_account_id = le.ledger_account_id
                    WHERE lt.user_id = %s
                      AND wa.user_id = %s
                ),
                ordered_movements AS (
                    SELECT
                        *,
                        SUM(signed_amount) OVER (
                            PARTITION BY wallet_account_id
                            ORDER BY created_at ASC, transaction_id ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS balance_after
                    FROM wallet_movements
                )
                SELECT
                    transaction_id,
                    transaction_type,
                    reference_type,
                    reference_id,
                    created_at,
                    wallet_account_id,
                    wallet_type,
                    currency_code,
                    signed_amount,
                    balance_after
                FROM ordered_movements
                WHERE (
                    %s::timestamptz IS NULL
                    OR (created_at, transaction_id, wallet_account_id)
                        < (%s::timestamptz, %s::uuid, %s::uuid)
                )
                ORDER BY created_at DESC, transaction_id DESC, wallet_account_id DESC
                LIMIT %s
                """,
                (
                    user_id,
                    user_id,
                    decoded_cursor["created_at"] if decoded_cursor else None,
                    decoded_cursor["created_at"] if decoded_cursor else None,
                    decoded_cursor["transaction_id"] if decoded_cursor else None,
                    decoded_cursor["wallet_account_id"] if decoded_cursor else None,
                    normalized_limit + 1,
                ),
            )
            rows = list(db_cursor.fetchall())

    page_rows = rows[:normalized_limit]
    next_cursor = _encode_cursor(page_rows[-1]) if len(rows) > normalized_limit else None
    return {
        "items": [_serialize_wallet_movement(row) for row in page_rows],
        "next_cursor": next_cursor,
        "limit": normalized_limit,
    }


def list_statement_movements_for_user(
    *,
    user_id: str,
    category: str = DEFAULT_STATEMENT_CATEGORY,
    wallet_type: str = DEFAULT_STATEMENT_WALLET_TYPE,
    period: str = DEFAULT_STATEMENT_PERIOD,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = DEFAULT_STATEMENT_MOVEMENT_LIMIT,
    cursor: str | None = None,
) -> dict[str, object]:
    normalized_category = _normalize_statement_category(category)
    normalized_wallet_type = _normalize_statement_wallet_type(wallet_type)
    normalized_period = _normalize_statement_period(period)
    normalized_limit = max(1, min(limit, MAX_STATEMENT_MOVEMENT_LIMIT))
    period_start, period_end = _resolve_statement_period(
        period=normalized_period,
        date_from=date_from,
        date_to=date_to,
    )
    decoded_cursor = _decode_statement_cursor(cursor) if cursor else None

    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                WITH wallet_events AS (
                    SELECT
                        lt.id AS transaction_id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.created_at,
                        wa.id AS wallet_account_id,
                        wa.wallet_type,
                        wa.currency_code,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE -le.amount
                        END AS signed_amount,
                        CASE
                            WHEN le.entry_side = 'debit' THEN le.amount
                            ELSE 0
                        END AS debit_amount,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE 0
                        END AS credit_amount
                    FROM ledger_transactions lt
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN wallet_accounts wa ON wa.ledger_account_id = le.ledger_account_id
                    WHERE lt.user_id = %s
                      AND wa.user_id = %s
                      AND wa.wallet_type = %s
                ),
                ordered_events AS (
                    SELECT
                        *,
                        SUM(signed_amount) OVER (
                            PARTITION BY wallet_account_id
                            ORDER BY created_at ASC, transaction_id ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS balance_after
                    FROM wallet_events
                ),
                game_events AS (
                    SELECT
                        CASE
                            WHEN pr.access_session_id IS NOT NULL
                                THEN 'game:' || pr.access_session_id::text
                            ELSE 'game_round:' || pr.id::text
                        END AS movement_id,
                        pr.id AS platform_round_id,
                        pr.game_code,
                        pr.access_session_id,
                        gas.started_at AS access_session_started_at,
                        pr.created_at AS round_created_at,
                        pr.closed_at AS round_closed_at,
                        oe.transaction_id,
                        oe.transaction_type,
                        oe.created_at AS event_at,
                        oe.wallet_type,
                        oe.currency_code,
                        oe.signed_amount,
                        oe.debit_amount,
                        oe.credit_amount,
                        oe.balance_after
                    FROM ordered_events oe
                    JOIN platform_rounds pr
                      ON oe.reference_type = 'game_session'
                     AND oe.reference_id = pr.id
                    LEFT JOIN game_access_sessions gas ON gas.id = pr.access_session_id
                ),
                latest_game_balances AS (
                    SELECT DISTINCT ON (movement_id)
                        movement_id,
                        balance_after
                    FROM game_events
                    ORDER BY movement_id, event_at DESC, transaction_id DESC
                ),
                game_movements AS (
                    SELECT
                        ge.movement_id,
                        'game' AS movement_family,
                        'Sessione gioco' AS movement_label,
                        CASE
                            WHEN MIN(ge.game_code) = 'mines' THEN 'Mines'
                            WHEN MIN(ge.game_code) = 'boxe' THEN 'BOXE'
                            WHEN MIN(ge.game_code) = 'hi_lo' THEN 'HI-LO'
                            ELSE MIN(ge.game_code)
                        END AS description,
                        'Sessione gioco' AS causale,
                        MIN(ge.game_code) AS movement_type,
                        ge.wallet_type,
                        ge.currency_code,
                        MIN(COALESCE(ge.access_session_started_at, ge.round_created_at)) AS started_at,
                        MAX(COALESCE(ge.round_closed_at, ge.event_at)) AS competency_at,
                        MAX(ge.event_at) AS sort_at,
                        COUNT(DISTINCT ge.platform_round_id) AS detail_count,
                        COALESCE(SUM(ge.debit_amount), 0) AS debit_amount,
                        COALESCE(SUM(ge.credit_amount), 0) AS credit_amount,
                        COALESCE(SUM(ge.signed_amount), 0) AS net_amount,
                        lgb.balance_after,
                        TRUE AS expandable,
                        BOOL_OR(ge.transaction_type = 'void') AS contains_adjustments
                    FROM game_events ge
                    JOIN latest_game_balances lgb ON lgb.movement_id = ge.movement_id
                    GROUP BY
                        ge.movement_id,
                        ge.wallet_type,
                        ge.currency_code,
                        lgb.balance_after
                ),
                bonus_movements AS (
                    SELECT
                        'bonus:' || aa.id::text AS movement_id,
                        'bonus' AS movement_family,
                        'Bonus accreditato' AS movement_label,
                        'Bonus' AS description,
                        'Bonus accreditato' AS causale,
                        oe.transaction_type AS movement_type,
                        oe.wallet_type,
                        oe.currency_code,
                        oe.created_at AS started_at,
                        oe.created_at AS competency_at,
                        oe.created_at AS sort_at,
                        1 AS detail_count,
                        oe.debit_amount,
                        oe.credit_amount,
                        oe.signed_amount AS net_amount,
                        oe.balance_after,
                        TRUE AS expandable,
                        FALSE AS contains_adjustments
                    FROM ordered_events oe
                    JOIN admin_actions aa
                      ON aa.ledger_transaction_id = oe.transaction_id
                     AND aa.action_type = 'bonus_grant'
                    WHERE oe.transaction_type = 'bonus_grant'
                ),
                adjustment_movements AS (
                    SELECT
                        'adjustment:' || oe.transaction_id::text AS movement_id,
                        'adjustment' AS movement_family,
                        CASE
                            WHEN oe.transaction_type = 'signup_credit' THEN 'Credito iniziale'
                            ELSE 'Rettifica saldo'
                        END AS movement_label,
                        CASE
                            WHEN oe.transaction_type = 'signup_credit' THEN 'Credito iniziale'
                            ELSE 'Rettifica saldo'
                        END AS description,
                        CASE
                            WHEN oe.transaction_type = 'signup_credit' THEN 'Credito iniziale'
                            ELSE 'Rettifica'
                        END AS causale,
                        oe.transaction_type AS movement_type,
                        oe.wallet_type,
                        oe.currency_code,
                        oe.created_at AS started_at,
                        oe.created_at AS competency_at,
                        oe.created_at AS sort_at,
                        1 AS detail_count,
                        oe.debit_amount,
                        oe.credit_amount,
                        oe.signed_amount AS net_amount,
                        oe.balance_after,
                        TRUE AS expandable,
                        oe.transaction_type = 'admin_adjustment' AS contains_adjustments
                    FROM ordered_events oe
                    WHERE oe.transaction_type IN ('admin_adjustment', 'signup_credit')
                ),
                statement_movements AS (
                    SELECT * FROM game_movements
                    UNION ALL
                    SELECT * FROM bonus_movements
                    UNION ALL
                    SELECT * FROM adjustment_movements
                )
                SELECT
                    movement_id,
                    movement_family,
                    movement_label,
                    description,
                    causale,
                    movement_type,
                    wallet_type,
                    currency_code,
                    started_at,
                    competency_at,
                    sort_at,
                    detail_count,
                    debit_amount,
                    credit_amount,
                    net_amount,
                    balance_after,
                    expandable,
                    contains_adjustments
                FROM statement_movements
                WHERE sort_at >= %s
                  AND sort_at < %s
                  AND (
                    %s = 'all'
                    OR (%s = 'game' AND movement_family = 'game')
                    OR (%s = 'bonus' AND movement_family = 'bonus')
                    OR (%s = 'adjustments' AND movement_family = 'adjustment')
                    OR (
                        %s = 'deposits_withdrawals'
                        AND movement_family IN ('deposit', 'withdrawal')
                    )
                  )
                  AND (
                    %s::timestamptz IS NULL
                    OR (sort_at, movement_id) < (%s::timestamptz, %s::text)
                  )
                ORDER BY sort_at DESC, movement_id DESC
                LIMIT %s
                """,
                (
                    user_id,
                    user_id,
                    normalized_wallet_type,
                    period_start,
                    period_end,
                    normalized_category,
                    normalized_category,
                    normalized_category,
                    normalized_category,
                    normalized_category,
                    decoded_cursor["sort_at"] if decoded_cursor else None,
                    decoded_cursor["sort_at"] if decoded_cursor else None,
                    decoded_cursor["movement_id"] if decoded_cursor else None,
                    normalized_limit + 1,
                ),
            )
            rows = list(db_cursor.fetchall())

    page_rows = rows[:normalized_limit]
    next_cursor = (
        _encode_statement_cursor(page_rows[-1])
        if len(rows) > normalized_limit
        else None
    )
    return {
        "items": [_serialize_statement_movement(row) for row in page_rows],
        "next_cursor": next_cursor,
        "limit": normalized_limit,
        "category": normalized_category,
        "wallet_type": normalized_wallet_type,
        "period": normalized_period,
        "date_from": period_start.date().isoformat(),
        "date_to": (period_end - timedelta(days=1)).date().isoformat(),
        "balance_disclaimer": (
            STATEMENT_BALANCE_DISCLAIMER if normalized_category != "all" else None
        ),
    }


def get_statement_movement_detail_for_user(
    *,
    user_id: str,
    movement_id: str,
    wallet_type: str = DEFAULT_STATEMENT_WALLET_TYPE,
    limit: int = DEFAULT_STATEMENT_DETAIL_LIMIT,
    cursor: str | None = None,
) -> dict[str, object]:
    normalized_wallet_type = _normalize_statement_wallet_type(wallet_type)
    normalized_limit = max(1, min(limit, MAX_STATEMENT_DETAIL_LIMIT))
    parsed_movement = _parse_statement_movement_id(movement_id)
    decoded_cursor = _decode_statement_detail_cursor(cursor) if cursor else None

    if parsed_movement["prefix"] in {"game", "game_round"}:
        return _get_game_statement_detail_for_user(
            user_id=user_id,
            movement_id=movement_id,
            movement_prefix=parsed_movement["prefix"],
            raw_id=parsed_movement["raw_id"],
            wallet_type=normalized_wallet_type,
            limit=normalized_limit,
            decoded_cursor=decoded_cursor,
        )

    if parsed_movement["prefix"] == "bonus":
        return _get_single_admin_statement_detail_for_user(
            user_id=user_id,
            movement_id=movement_id,
            admin_action_id=parsed_movement["raw_id"],
            wallet_type=normalized_wallet_type,
            expected_action_type="bonus_grant",
        )

    if parsed_movement["prefix"] == "adjustment":
        return _get_single_transaction_statement_detail_for_user(
            user_id=user_id,
            movement_id=movement_id,
            ledger_transaction_id=parsed_movement["raw_id"],
            wallet_type=normalized_wallet_type,
        )

    raise AccountStatementValidationError("Statement movement type is not supported yet")


def _serialize_wallet_movement(row: dict[str, object]) -> dict[str, object]:
    signed_amount = Decimal(row["signed_amount"])
    return {
        "id": f"{row['transaction_id']}:{row['wallet_account_id']}",
        "ledger_transaction_id": str(row["transaction_id"]),
        "transaction_type": row["transaction_type"],
        "reference_type": row["reference_type"],
        "reference_id": str(row["reference_id"]) if row["reference_id"] else None,
        "wallet_type": row["wallet_type"],
        "currency_code": row["currency_code"],
        "direction": "credit" if signed_amount >= Decimal("0") else "debit",
        "amount": _format_amount(signed_amount),
        "balance_after": _format_amount(Decimal(row["balance_after"])),
        "created_at": row["created_at"].isoformat(),
    }


def _get_game_statement_detail_for_user(
    *,
    user_id: str,
    movement_id: str,
    movement_prefix: str,
    raw_id: str,
    wallet_type: str,
    limit: int,
    decoded_cursor: dict[str, object] | None,
) -> dict[str, object]:
    filter_clause = "pr.access_session_id = %s" if movement_prefix == "game" else "pr.id = %s"

    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                f"""
                WITH wallet_events AS (
                    SELECT
                        lt.id AS transaction_id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.created_at,
                        wa.id AS wallet_account_id,
                        wa.wallet_type,
                        wa.currency_code,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE -le.amount
                        END AS signed_amount,
                        CASE
                            WHEN le.entry_side = 'debit' THEN le.amount
                            ELSE 0
                        END AS debit_amount,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE 0
                        END AS credit_amount
                    FROM ledger_transactions lt
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN wallet_accounts wa ON wa.ledger_account_id = le.ledger_account_id
                    WHERE lt.user_id = %s
                      AND wa.user_id = %s
                      AND wa.wallet_type = %s
                ),
                ordered_events AS (
                    SELECT
                        *,
                        SUM(signed_amount) OVER (
                            PARTITION BY wallet_account_id
                            ORDER BY created_at ASC, transaction_id ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS balance_after
                    FROM wallet_events
                ),
                round_events AS (
                    SELECT
                        pr.id AS platform_round_id,
                        pr.game_code,
                        pr.title_code,
                        pr.site_code,
                        pr.status,
                        pr.bet_amount,
                        pr.payout_amount,
                        pr.created_at AS round_created_at,
                        pr.closed_at AS round_closed_at,
                        mgr.grid_size,
                        mgr.mine_count,
                        mgr.safe_reveals_count,
                        br.rows_count AS boxe_rows_count,
                        br.difficulty AS boxe_difficulty,
                        br.safe_picks_count AS boxe_safe_picks_count,
                        hlr.correct_predictions_count AS hi_lo_correct_predictions_count,
                        hlr.active_skip_count AS hi_lo_active_skip_count,
                        oe.transaction_id,
                        oe.transaction_type,
                        oe.created_at AS event_at,
                        oe.wallet_type,
                        oe.currency_code,
                        oe.debit_amount,
                        oe.credit_amount,
                        oe.signed_amount,
                        oe.balance_after
                    FROM platform_rounds pr
                    LEFT JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                    LEFT JOIN boxe_rounds br ON br.platform_round_id = pr.id
                    LEFT JOIN hi_lo_rounds hlr ON hlr.platform_round_id = pr.id
                    JOIN ordered_events oe
                      ON oe.reference_type = 'game_session'
                     AND oe.reference_id = pr.id
                    WHERE pr.user_id = %s
                      AND pr.wallet_type = %s
                      AND {filter_clause}
                ),
                latest_round_balances AS (
                    SELECT DISTINCT ON (platform_round_id)
                        platform_round_id,
                        balance_after
                    FROM round_events
                    ORDER BY platform_round_id, event_at DESC, transaction_id DESC
                ),
                round_rows AS (
                    SELECT
                        re.platform_round_id,
                        MIN(re.game_code) AS game_code,
                        MIN(re.title_code) AS title_code,
                        MIN(re.site_code) AS site_code,
                        MIN(re.status) AS status,
                        MIN(re.bet_amount) AS bet_amount,
                        MAX(re.payout_amount) AS payout_amount,
                        MIN(re.round_created_at) AS round_created_at,
                        MAX(COALESCE(re.round_closed_at, re.event_at)) AS competency_at,
                        MAX(re.event_at) AS sort_at,
                        MIN(re.grid_size) AS grid_size,
                        MIN(re.mine_count) AS mine_count,
                        MAX(re.safe_reveals_count) AS safe_reveals_count,
                        MIN(re.boxe_rows_count) AS boxe_rows_count,
                        MIN(re.boxe_difficulty) AS boxe_difficulty,
                        MAX(re.boxe_safe_picks_count) AS boxe_safe_picks_count,
                        MAX(re.hi_lo_correct_predictions_count) AS hi_lo_correct_predictions_count,
                        MAX(re.hi_lo_active_skip_count) AS hi_lo_active_skip_count,
                        MIN(re.wallet_type) AS wallet_type,
                        MIN(re.currency_code) AS currency_code,
                        COALESCE(SUM(re.debit_amount), 0) AS debit_amount,
                        COALESCE(SUM(re.credit_amount), 0) AS credit_amount,
                        COALESCE(SUM(re.signed_amount), 0) AS net_amount,
                        lrb.balance_after,
                        BOOL_OR(re.transaction_type = 'void') AS contains_adjustments
                    FROM round_events re
                    JOIN latest_round_balances lrb ON lrb.platform_round_id = re.platform_round_id
                    GROUP BY re.platform_round_id, lrb.balance_after
                )
                SELECT
                    platform_round_id,
                    game_code,
                    title_code,
                    site_code,
                    status,
                    bet_amount,
                    payout_amount,
                    round_created_at,
                    competency_at,
                    sort_at,
                    grid_size,
                    mine_count,
                    safe_reveals_count,
                    boxe_rows_count,
                    boxe_difficulty,
                    boxe_safe_picks_count,
                    hi_lo_correct_predictions_count,
                    hi_lo_active_skip_count,
                    wallet_type,
                    currency_code,
                    debit_amount,
                    credit_amount,
                    net_amount,
                    balance_after,
                    contains_adjustments
                FROM round_rows
                WHERE (
                    %s::timestamptz IS NULL
                    OR (sort_at, platform_round_id) < (%s::timestamptz, %s::uuid)
                )
                ORDER BY sort_at DESC, platform_round_id DESC
                LIMIT %s
                """,
                (
                    user_id,
                    user_id,
                    wallet_type,
                    user_id,
                    wallet_type,
                    raw_id,
                    decoded_cursor["sort_at"] if decoded_cursor else None,
                    decoded_cursor["sort_at"] if decoded_cursor else None,
                    decoded_cursor["item_id"] if decoded_cursor else None,
                    limit + 1,
                ),
            )
            rows = list(db_cursor.fetchall())

    if not rows:
        raise AccountStatementNotFoundError("Statement movement detail not found")

    page_rows = rows[:limit]
    next_cursor = (
        _encode_statement_detail_cursor(
            sort_at=page_rows[-1]["sort_at"],
            item_id=str(page_rows[-1]["platform_round_id"]),
        )
        if len(rows) > limit
        else None
    )
    return {
        "movement_id": movement_id,
        "movement_family": "game",
        "items": [_serialize_game_statement_detail_row(row) for row in page_rows],
        "next_cursor": next_cursor,
        "limit": limit,
        "wallet_type": wallet_type,
    }


def _get_single_admin_statement_detail_for_user(
    *,
    user_id: str,
    movement_id: str,
    admin_action_id: str,
    wallet_type: str,
    expected_action_type: str,
) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                WITH wallet_events AS (
                    SELECT
                        lt.id AS transaction_id,
                        lt.transaction_type,
                        lt.created_at,
                        wa.id AS wallet_account_id,
                        wa.wallet_type,
                        wa.currency_code,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE -le.amount
                        END AS signed_amount,
                        CASE
                            WHEN le.entry_side = 'debit' THEN le.amount
                            ELSE 0
                        END AS debit_amount,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE 0
                        END AS credit_amount
                    FROM ledger_transactions lt
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN wallet_accounts wa ON wa.ledger_account_id = le.ledger_account_id
                    WHERE lt.user_id = %s
                      AND wa.user_id = %s
                      AND wa.wallet_type = %s
                ),
                ordered_events AS (
                    SELECT
                        *,
                        SUM(signed_amount) OVER (
                            PARTITION BY wallet_account_id
                            ORDER BY created_at ASC, transaction_id ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS balance_after
                    FROM wallet_events
                ),
                target_events AS (
                    SELECT oe.*
                    FROM admin_actions aa
                    JOIN ordered_events oe ON oe.transaction_id = aa.ledger_transaction_id
                    WHERE aa.id = %s
                      AND aa.target_user_id = %s
                      AND aa.action_type = %s
                )
                SELECT *
                FROM target_events
                ORDER BY created_at DESC, transaction_id DESC
                LIMIT 1
                """,
                (
                    user_id,
                    user_id,
                    wallet_type,
                    admin_action_id,
                    user_id,
                    expected_action_type,
                ),
            )
            row = db_cursor.fetchone()

    if row is None:
        raise AccountStatementNotFoundError("Statement movement detail not found")

    return {
        "movement_id": movement_id,
        "movement_family": "bonus",
        "items": [_serialize_single_statement_detail_row(row)],
        "next_cursor": None,
        "limit": 1,
        "wallet_type": wallet_type,
    }


def _get_single_transaction_statement_detail_for_user(
    *,
    user_id: str,
    movement_id: str,
    ledger_transaction_id: str,
    wallet_type: str,
) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                WITH wallet_events AS (
                    SELECT
                        lt.id AS transaction_id,
                        lt.transaction_type,
                        lt.created_at,
                        wa.id AS wallet_account_id,
                        wa.wallet_type,
                        wa.currency_code,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE -le.amount
                        END AS signed_amount,
                        CASE
                            WHEN le.entry_side = 'debit' THEN le.amount
                            ELSE 0
                        END AS debit_amount,
                        CASE
                            WHEN le.entry_side = 'credit' THEN le.amount
                            ELSE 0
                        END AS credit_amount
                    FROM ledger_transactions lt
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN wallet_accounts wa ON wa.ledger_account_id = le.ledger_account_id
                    WHERE lt.user_id = %s
                      AND wa.user_id = %s
                      AND wa.wallet_type = %s
                ),
                ordered_events AS (
                    SELECT
                        *,
                        SUM(signed_amount) OVER (
                            PARTITION BY wallet_account_id
                            ORDER BY created_at ASC, transaction_id ASC
                            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                        ) AS balance_after
                    FROM wallet_events
                )
                SELECT *
                FROM ordered_events
                WHERE transaction_id = %s
                  AND transaction_type IN ('admin_adjustment', 'signup_credit')
                ORDER BY created_at DESC, transaction_id DESC
                LIMIT 1
                """,
                (user_id, user_id, wallet_type, ledger_transaction_id),
            )
            row = db_cursor.fetchone()

    if row is None:
        raise AccountStatementNotFoundError("Statement movement detail not found")

    return {
        "movement_id": movement_id,
        "movement_family": "adjustment",
        "items": [_serialize_single_statement_detail_row(row)],
        "next_cursor": None,
        "limit": 1,
        "wallet_type": wallet_type,
    }


def _serialize_statement_movement(row: dict[str, object]) -> dict[str, object]:
    movement_id = str(row["movement_id"])
    started_at = row["started_at"]
    competency_at = row["competency_at"]
    detail_count = int(row["detail_count"])
    return {
        "id": movement_id,
        "movement_family": row["movement_family"],
        "movement_label": row["movement_label"],
        "description": row["description"],
        "code": _build_statement_code(movement_id=movement_id, family=str(row["movement_family"])),
        "causale": row["causale"],
        "movement_type": row["movement_type"],
        "wallet_type": row["wallet_type"],
        "currency_code": row["currency_code"],
        "started_at": started_at.isoformat(),
        "competency_at": competency_at.isoformat(),
        "show_competency_at": competency_at != started_at,
        "detail_count": detail_count,
        "show_detail_count": detail_count > 1,
        "debit_amount": _format_amount(Decimal(row["debit_amount"])),
        "credit_amount": _format_amount(Decimal(row["credit_amount"])),
        "net_amount": _format_amount(Decimal(row["net_amount"])),
        "balance_after": _format_amount(Decimal(row["balance_after"])),
        "expandable": bool(row["expandable"]),
        "contains_adjustments": bool(row["contains_adjustments"]),
    }


def _serialize_game_statement_detail_row(row: dict[str, object]) -> dict[str, object]:
    platform_round_id = str(row["platform_round_id"])
    return {
        "id": f"round:{platform_round_id}",
        "item_type": "game_round",
        "timestamp": row["round_created_at"].isoformat(),
        "competency_at": row["competency_at"].isoformat(),
        "round_code": f"RND-{platform_round_id.replace('-', '').upper()[:8]}",
        "platform_round_id": platform_round_id,
        "game_code": row["game_code"],
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "result": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "safe_reveals_count": row["safe_reveals_count"],
        "boxe_rows_count": row["boxe_rows_count"],
        "boxe_difficulty": row["boxe_difficulty"],
        "boxe_safe_picks_count": row["boxe_safe_picks_count"],
        "bet_amount": _format_amount(Decimal(row["bet_amount"])),
        "win_amount": _format_amount(Decimal(row["credit_amount"])),
        "debit_amount": _format_amount(Decimal(row["debit_amount"])),
        "credit_amount": _format_amount(Decimal(row["credit_amount"])),
        "net_amount": _format_amount(Decimal(row["net_amount"])),
        "balance_after": _format_amount(Decimal(row["balance_after"])),
        "wallet_type": row["wallet_type"],
        "currency_code": row["currency_code"],
        "contains_adjustments": bool(row["contains_adjustments"]),
        "game_summary": _build_game_detail_summary(row),
    }


def _serialize_single_statement_detail_row(row: dict[str, object]) -> dict[str, object]:
    transaction_id = str(row["transaction_id"])
    return {
        "id": f"transaction:{transaction_id}",
        "item_type": "transaction",
        "timestamp": row["created_at"].isoformat(),
        "transaction_code": f"MOV-{transaction_id.replace('-', '').upper()[:8]}",
        "transaction_type": row["transaction_type"],
        "debit_amount": _format_amount(Decimal(row["debit_amount"])),
        "credit_amount": _format_amount(Decimal(row["credit_amount"])),
        "net_amount": _format_amount(Decimal(row["signed_amount"])),
        "balance_after": _format_amount(Decimal(row["balance_after"])),
        "wallet_type": row["wallet_type"],
        "currency_code": row["currency_code"],
    }


def _encode_cursor(row: dict[str, object]) -> str:
    payload = {
        "created_at": row["created_at"].isoformat(),
        "transaction_id": str(row["transaction_id"]),
        "wallet_account_id": str(row["wallet_account_id"]),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> dict[str, object]:
    try:
        padded_cursor = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded_cursor.encode("ascii")))
        created_at = datetime.fromisoformat(str(payload["created_at"]))
        transaction_id = UUID(str(payload["transaction_id"]))
        wallet_account_id = UUID(str(payload["wallet_account_id"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AccountCursorError("Wallet movement cursor is not valid") from exc

    return {
        "created_at": created_at,
        "transaction_id": str(transaction_id),
        "wallet_account_id": str(wallet_account_id),
    }


def _encode_statement_cursor(row: dict[str, object]) -> str:
    payload = {
        "sort_at": row["sort_at"].isoformat(),
        "movement_id": str(row["movement_id"]),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_statement_cursor(cursor: str) -> dict[str, object]:
    try:
        padded_cursor = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded_cursor.encode("ascii")))
        sort_at = datetime.fromisoformat(str(payload["sort_at"]))
        movement_id = str(payload["movement_id"])
        _validate_statement_movement_id(movement_id)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AccountCursorError("Statement movement cursor is not valid") from exc

    return {
        "sort_at": sort_at,
        "movement_id": movement_id,
    }


def _encode_statement_detail_cursor(*, sort_at: datetime, item_id: str) -> str:
    payload = {
        "sort_at": sort_at.isoformat(),
        "item_id": item_id,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_statement_detail_cursor(cursor: str) -> dict[str, object]:
    try:
        padded_cursor = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded_cursor.encode("ascii")))
        sort_at = datetime.fromisoformat(str(payload["sort_at"]))
        item_id = UUID(str(payload["item_id"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AccountCursorError("Statement movement detail cursor is not valid") from exc

    return {
        "sort_at": sort_at,
        "item_id": str(item_id),
    }


def _normalize_statement_category(category: str) -> str:
    normalized = category.strip().lower()
    if normalized not in STATEMENT_CATEGORIES:
        raise AccountStatementValidationError("Statement movement category is not valid")
    return normalized


def _normalize_statement_wallet_type(wallet_type: str) -> str:
    normalized = wallet_type.strip().lower()
    if normalized not in STATEMENT_WALLET_TYPES:
        raise AccountStatementValidationError("Statement movement wallet_type is not valid")
    return normalized


def _normalize_statement_period(period: str) -> str:
    normalized = period.strip().lower()
    if normalized not in STATEMENT_PERIODS:
        raise AccountStatementValidationError("Statement movement period is not valid")
    return normalized


def _resolve_statement_period(
    *,
    period: str,
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime, datetime]:
    today = datetime.now(UTC).date()
    if period == "today":
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == "last_7_days":
        start_date = today - timedelta(days=6)
        end_date = today + timedelta(days=1)
    elif period == "last_30_days":
        start_date = today - timedelta(days=29)
        end_date = today + timedelta(days=1)
    elif period == "current_month":
        start_date = today.replace(day=1)
        end_date = _first_day_of_next_month(today)
    elif period == "previous_month":
        current_month_start = today.replace(day=1)
        previous_month_end = current_month_start
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        start_date = previous_month_start
        end_date = previous_month_end
    else:
        if date_from is None or date_to is None:
            raise AccountStatementValidationError(
                "date_from and date_to are required for custom statement period"
            )
        if date_from > date_to:
            raise AccountStatementValidationError(
                "date_from must be earlier than or equal to date_to"
            )
        start_date = date_from
        end_date = date_to + timedelta(days=1)

    return (
        datetime.combine(start_date, time.min, tzinfo=UTC),
        datetime.combine(end_date, time.min, tzinfo=UTC),
    )


def _first_day_of_next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _parse_statement_movement_id(movement_id: str) -> dict[str, str]:
    prefix, separator, raw_id = movement_id.partition(":")
    if separator != ":" or not raw_id:
        raise AccountStatementValidationError("Statement movement id is not valid")
    if prefix not in {"game", "game_round", "bonus", "adjustment", "deposit", "withdrawal"}:
        raise AccountStatementValidationError("Statement movement id prefix is not valid")
    try:
        UUID(raw_id)
    except ValueError as exc:
        raise AccountStatementValidationError("Statement movement id is not valid") from exc
    return {"prefix": prefix, "raw_id": raw_id}


def _validate_statement_movement_id(movement_id: str) -> None:
    _parse_statement_movement_id(movement_id)


def _build_statement_code(*, movement_id: str, family: str) -> str:
    raw_id = movement_id.rsplit(":", 1)[-1].replace("-", "").upper()
    prefixes = {
        "game": "SES",
        "bonus": "BON",
        "adjustment": "MOV",
        "deposit": "DEP",
        "withdrawal": "PRE",
    }
    return f"{prefixes.get(family, 'MOV')}-{raw_id[:8]}"


def _build_mines_game_detail_summary(row: dict[str, object]) -> str:
    return (
        f"Mines {row['grid_size']} celle, {row['mine_count']} mine, "
        f"{row['safe_reveals_count']} safe"
    )


def _build_boxe_game_detail_summary(row: dict[str, object]) -> str:
    return (
        f"BOXE {row['boxe_rows_count']} rows, {row['boxe_difficulty']}, "
        f"{row['boxe_safe_picks_count']} safe"
    )


def _build_hi_lo_game_detail_summary(row: dict[str, object]) -> str:
    return (
        f"HI-LO {row.get('hi_lo_correct_predictions_count') or 0} corrette, "
        f"{row.get('hi_lo_active_skip_count') or 0} skip"
    )


_GAME_DETAIL_SUMMARY_BUILDERS = {
    "mines": _build_mines_game_detail_summary,
    "boxe": _build_boxe_game_detail_summary,
    "hi_lo": _build_hi_lo_game_detail_summary,
}


def _build_game_detail_summary(row: dict[str, object]) -> str:
    game_code = str(row["game_code"])
    builder = _GAME_DETAIL_SUMMARY_BUILDERS.get(game_code)
    if builder is None:
        return game_code
    return builder(row)


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"
