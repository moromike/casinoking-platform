"""Admin force-close of player game sessions with ledger void semantics.

Implements the admin-initiated lifecycle action described in
``docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`` (sezione "Admin
force-close - semantica e scope").

Differs from the normal cascade close (login/logout/X/timeout) in two
ways:

1. Any in-flight round is **voided**, not auto-cashed. The bet is
   refunded via a new ``void`` ledger transaction that reverses the
   original ``bet`` transaction in double-entry. Net P/L on the round
   is zero, audit trail is preserved (CTO note 1).

2. Scope is limited strictly to active/in-flight states. Already
   settled rounds, closed sessions and existing ledger transactions
   are never touched (CTO note 2).
"""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection

ACTION_TYPE_SESSION_VOID = "session_void"
TRANSACTION_TYPE_VOID = "void"
HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
SESSION_CLOSED_REASON = "admin_voided"
ROUND_STATUS_CANCELLED = "cancelled"
TABLE_SESSION_STATUS_CLOSED = "closed"
ACCESS_SESSION_STATUS_CLOSED = "closed"


class AdminForceCloseValidationError(Exception):
    pass


class AdminForceCloseTargetNotFoundError(Exception):
    pass


def force_close_user_game_sessions(
    *,
    admin_user_id: str,
    target_user_id: str,
    game_code: str,
    reason: str,
) -> dict[str, object]:
    """Force-close all active sessions of `target_user_id` for `game_code`.

    Atomic. Idempotent on repeat calls: once the active sessions are
    closed there is no second mutable target, and the void ledger key is
    stable per admin + target + round if a retry happens inside the same
    in-flight state.

    Returns a summary of the void operations performed.
    """
    normalized_game_code = _normalize_game_code(game_code)
    normalized_reason = _normalize_reason(reason)

    voided_rounds: list[dict[str, object]] = []
    closed_table_sessions: list[str] = []
    closed_access_sessions: list[str] = []

    with db_connection() as connection:
        with connection.cursor() as cursor:
            target_user = _ensure_target_user_exists(cursor, target_user_id)

            cursor.execute(
                """
                SELECT
                    id,
                    wallet_type,
                    loss_reserved_amount
                FROM game_table_sessions
                WHERE user_id = %s
                  AND game_code = %s
                  AND status = 'active'
                FOR UPDATE
                """,
                (target_user_id, normalized_game_code),
            )
            table_sessions = cursor.fetchall() or []

            for table_session in table_sessions:
                table_session_id = str(table_session["id"])
                if Decimal(table_session["loss_reserved_amount"]) > 0:
                    while True:
                        void_summary = _void_active_round_for_table_session(
                            cursor=cursor,
                            admin_user_id=admin_user_id,
                            target_user_id=target_user_id,
                            target_user_email=str(target_user["email"]),
                            table_session_id=table_session_id,
                            wallet_type=str(table_session["wallet_type"]),
                            reason=normalized_reason,
                        )
                        if void_summary is None:
                            break
                        voided_rounds.append(void_summary)

                    cursor.execute(
                        """
                        SELECT loss_reserved_amount
                        FROM game_table_sessions
                        WHERE id = %s
                        """,
                        (table_session_id,),
                    )
                    remaining_reserved_row = cursor.fetchone()
                    if (
                        remaining_reserved_row is not None
                        and Decimal(remaining_reserved_row["loss_reserved_amount"]) > 0
                    ):
                        raise AdminForceCloseValidationError(
                            "Table session has reserved loss but no active round to void"
                        )

                cursor.execute(
                    """
                    UPDATE game_table_sessions
                    SET
                        status = %s,
                        closed_reason = %s,
                        closed_at = now()
                    WHERE id = %s
                      AND status = 'active'
                    """,
                    (TABLE_SESSION_STATUS_CLOSED, SESSION_CLOSED_REASON, table_session_id),
                )
                if cursor.rowcount > 0:
                    closed_table_sessions.append(table_session_id)

            cursor.execute(
                """
                SELECT id
                FROM game_access_sessions
                WHERE user_id = %s
                  AND game_code = %s
                  AND status = 'active'
                FOR UPDATE
                """,
                (target_user_id, normalized_game_code),
            )
            access_rows = cursor.fetchall() or []
            for access_row in access_rows:
                access_session_id = str(access_row["id"])
                cursor.execute(
                    """
                    UPDATE game_access_sessions
                    SET
                        ended_at = now(),
                        last_activity_at = now(),
                        status = %s,
                        closed_reason = %s
                    WHERE id = %s
                      AND status = 'active'
                    """,
                    (ACCESS_SESSION_STATUS_CLOSED, SESSION_CLOSED_REASON, access_session_id),
                )
                if cursor.rowcount > 0:
                    closed_access_sessions.append(access_session_id)

    return {
        "target_user_id": target_user_id,
        "game_code": normalized_game_code,
        "voided_rounds": voided_rounds,
        "closed_table_session_ids": closed_table_sessions,
        "closed_access_session_ids": closed_access_sessions,
        "reason": normalized_reason,
    }


def _void_active_round_for_table_session(
    *,
    cursor: psycopg.Cursor,
    admin_user_id: str,
    target_user_id: str,
    target_user_email: str,
    table_session_id: str,
    wallet_type: str,
    reason: str,
) -> dict[str, object] | None:
    """Void the in-flight Mines round linked to this table session.

    Writes a reversal ``void`` ledger transaction in double-entry,
    refunds the bet to the player wallet, releases the reserved loss
    on the table session, marks the round as ``cancelled`` and inserts
    a ``session_void`` admin_actions audit row.

    Idempotent on repeat calls: the unique idempotency key on
    ``ledger_transactions`` and ``admin_actions`` blocks duplicate
    inserts; the round stays cancelled, the wallet stays whole.
    """
    cursor.execute(
        """
        SELECT
            pr.id AS round_id,
            pr.bet_amount,
            wa.id AS wallet_id,
            wa.balance_snapshot,
            wa.ledger_account_id AS player_ledger_account_id
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        WHERE pr.table_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
        ORDER BY pr.created_at DESC
        LIMIT 1
        FOR UPDATE OF pr, wa
        """,
        (table_session_id, target_user_id),
    )
    round_row = cursor.fetchone()
    if round_row is None:
        return None

    round_id = str(round_row["round_id"])
    bet_amount = Decimal(round_row["bet_amount"]).quantize(Decimal("0.000001"))
    player_ledger_account_id = str(round_row["player_ledger_account_id"])
    wallet_id = str(round_row["wallet_id"])

    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (HOUSE_CASH_ACCOUNT_CODE,),
    )
    house_cash = cursor.fetchone()
    if house_cash is None:
        raise AdminForceCloseValidationError("Required system account is missing")
    house_cash_account_id = str(house_cash["id"])

    idempotency_key = _build_void_idempotency_key(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        round_id=round_id,
    )
    request_fingerprint = sha256(
        f"{admin_user_id}:{target_user_id}:{round_id}:{reason}".encode("utf-8")
    ).hexdigest()[:64]

    existing_action = _get_existing_admin_action_by_idempotency_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )
    if existing_action is not None:
        return {
            "round_id": round_id,
            "bet_amount": f"{bet_amount:.6f}",
            "ledger_transaction_id": str(existing_action["ledger_transaction_id"]),
            "admin_action_id": str(existing_action["id"]),
            "already_existed": True,
        }

    transaction_id = str(uuid4())
    admin_action_id = str(uuid4())
    wallet_balance_after = (
        Decimal(round_row["balance_snapshot"]) + bet_amount
    ).quantize(Decimal("0.000001"))

    metadata = json.dumps(
        {
            "action_type": ACTION_TYPE_SESSION_VOID,
            "admin_user_id": admin_user_id,
            "target_user_id": target_user_id,
            "target_user_email": target_user_email,
            "table_session_id": table_session_id,
            "round_id": round_id,
            "reason": reason,
        },
        separators=(",", ":"),
        sort_keys=True,
    )

    cursor.execute(
        """
        INSERT INTO ledger_transactions (
            id,
            user_id,
            transaction_type,
            reference_type,
            reference_id,
            idempotency_key,
            metadata_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            transaction_id,
            target_user_id,
            TRANSACTION_TYPE_VOID,
            "admin_action",
            admin_action_id,
            idempotency_key,
            metadata,
        ),
    )

    cursor.execute(
        """
        INSERT INTO ledger_entries (
            id,
            transaction_id,
            ledger_account_id,
            entry_side,
            amount
        )
        VALUES
            (%s, %s, %s, 'debit', %s),
            (%s, %s, %s, 'credit', %s)
        """,
        (
            str(uuid4()),
            transaction_id,
            house_cash_account_id,
            bet_amount,
            str(uuid4()),
            transaction_id,
            player_ledger_account_id,
            bet_amount,
        ),
    )

    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot + %s
        WHERE id = %s
        """,
        (bet_amount, wallet_id),
    )

    cursor.execute(
        """
        UPDATE game_table_sessions
        SET
            loss_reserved_amount = loss_reserved_amount - %s,
            table_balance_amount = table_balance_amount + %s,
            loss_consumed_amount = GREATEST(
                loss_limit_amount
                - (table_balance_amount + %s)
                - (loss_reserved_amount - %s),
                0
            )
        WHERE id = %s
          AND loss_reserved_amount >= %s
        """,
        (bet_amount, bet_amount, bet_amount, bet_amount, table_session_id, bet_amount),
    )
    if cursor.rowcount != 1:
        raise AdminForceCloseValidationError("Table session reserved amount is not valid")

    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET closed_at = now()
        WHERE platform_round_id = %s
        """,
        (round_id,),
    )

    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = %s,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
          AND status = 'active'
        """,
        (ROUND_STATUS_CANCELLED, transaction_id, round_id),
    )

    cursor.execute(
        """
        INSERT INTO admin_actions (
            id,
            admin_user_id,
            target_user_id,
            action_type,
            wallet_type,
            direction,
            amount,
            reason,
            wallet_balance_after,
            ledger_transaction_id,
            idempotency_key,
            request_fingerprint,
            metadata_json
        )
        VALUES (
            %s, %s, %s, %s, %s, 'credit', %s, %s, %s, %s, %s, %s, %s::jsonb
        )
        """,
        (
            admin_action_id,
            admin_user_id,
            target_user_id,
            ACTION_TYPE_SESSION_VOID,
            wallet_type,
            bet_amount,
            reason,
            wallet_balance_after,
            transaction_id,
            idempotency_key,
            request_fingerprint,
            metadata,
        ),
    )

    return {
        "round_id": round_id,
        "bet_amount": f"{bet_amount:.6f}",
        "ledger_transaction_id": transaction_id,
        "admin_action_id": admin_action_id,
        "already_existed": False,
    }


def _get_existing_admin_action_by_idempotency_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT id, ledger_transaction_id
        FROM admin_actions
        WHERE idempotency_key = %s
        """,
        (idempotency_key,),
    )
    return cursor.fetchone()


def _ensure_target_user_exists(
    cursor: psycopg.Cursor,
    target_user_id: str,
) -> dict[str, object]:
    cursor.execute(
        """
        SELECT id, email
        FROM users
        WHERE id = %s
        """,
        (target_user_id,),
    )
    user = cursor.fetchone()
    if user is None:
        raise AdminForceCloseTargetNotFoundError("Target user not found")
    return user


def _build_void_idempotency_key(
    *,
    admin_user_id: str,
    target_user_id: str,
    round_id: str,
) -> str:
    digest = sha256(
        f"{admin_user_id}:{target_user_id}:{round_id}".encode("utf-8")
    ).hexdigest()[:32]
    return f"admin:session_void:{digest}"


def _normalize_game_code(game_code: str) -> str:
    normalized = game_code.strip().lower()
    if not normalized:
        raise AdminForceCloseValidationError("Game code is required")
    if normalized != "mines":
        raise AdminForceCloseValidationError("Game code is not supported")
    return normalized


def _normalize_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized:
        raise AdminForceCloseValidationError("Reason is required")
    if len(normalized) > 255:
        raise AdminForceCloseValidationError("Reason is too long")
    return normalized
