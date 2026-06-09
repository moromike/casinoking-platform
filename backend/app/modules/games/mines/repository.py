from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import DictRow

from app.db.connection import db_connection
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesValidationError,
)


class MinesSessionCursorError(Exception):
    pass

GAME_CODE = "mines"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_WON = "won"
SESSION_STATUS_LOST = "lost"
SESSION_STATUS_CANCELLED = "cancelled"
START_MULTIPLIER = Decimal("1.0000")


@dataclass(frozen=True)
class LockedRound:
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def status(self) -> str:
        return str(self.data["status"])


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def save_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict[str, object],
    round_id: str | None = None,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO mines_idempotency_keys (
                id, player_id, round_id, operation, idempotency_key,
                request_fingerprint, response_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT mines_idempotency_keys_player_operation_key
            DO NOTHING
            """,
            (
                uuid4(),
                player_id,
                round_id,
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
            SELECT response_json
            FROM mines_idempotency_keys
            WHERE player_id = %s
              AND operation = %s
              AND idempotency_key = %s
            """,
            (player_id, operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is not None:
            return dict(row["response_json"])
        return None


def get_idempotency_result(
    connection: psycopg.Connection[DictRow],
    *,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT response_json, request_fingerprint
            FROM mines_idempotency_keys
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
        if row["request_fingerprint"] != request_fingerprint:
            raise MinesIdempotencyConflictError(
                "Idempotency key already used with a different payload"
            )
        return dict(row["response_json"])


# ---------------------------------------------------------------------------
# Existence / ownership
# ---------------------------------------------------------------------------


def session_exists(connection: psycopg.Connection[DictRow], session_id: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM mines_game_rounds
            WHERE id = %s
            """,
            (session_id,),
        )
        row = cursor.fetchone()
    return row is not None


def session_belongs_to_user(
    connection: psycopg.Connection[DictRow], *, session_id: str, user_id: str
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM mines_game_rounds
            WHERE id = %s
              AND user_id = %s
            """,
            (session_id, user_id),
        )
        row = cursor.fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Existing session by idempotency (used for open-round idempotency recovery)
# ---------------------------------------------------------------------------


def get_existing_session_by_idempotency(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                pr.bet_amount,
                pr.title_code,
                pr.site_code,
                mgr.safe_reveals_count,
                mgr.multiplier_current,
                pr.wallet_balance_after_start,
                pr.start_ledger_transaction_id,
                pr.table_session_id,
                pr.request_fingerprint
            FROM platform_rounds pr
            JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
            WHERE pr.user_id = %s
              AND pr.idempotency_key = %s
            """,
            (user_id, idempotency_key),
        )
        return cursor.fetchone()


def get_existing_session_by_idempotency_outside_tx(
    *,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        return get_existing_session_by_idempotency(
            connection,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )


# ---------------------------------------------------------------------------
# Fairness nonce
# ---------------------------------------------------------------------------


def get_next_fairness_nonce(connection: psycopg.Connection[DictRow]) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT nextval('mines_fairness_nonce_seq') AS nonce
            """
        )
        row = cursor.fetchone()
        assert row is not None
        return int(row["nonce"])


# ---------------------------------------------------------------------------
# CRUD: mines_game_rounds
# ---------------------------------------------------------------------------


def create_round(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: str,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    fairness_artifacts: dict[str, object],
    platform_round_id: str | None = None,
    demo_session_id: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
    status: str | None = None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO mines_game_rounds (
                id,
                platform_round_id,
                demo_session_id,
                user_id,
                title_code,
                site_code,
                grid_size,
                mine_count,
                bet_amount,
                status,
                safe_reveals_count,
                revealed_cells_json,
                mine_positions_json,
                multiplier_current,
                payout_current,
                fairness_version,
                nonce,
                server_seed_hash,
                rng_material,
                board_hash
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                session_id,
                platform_round_id,
                demo_session_id,
                user_id,
                title_code,
                site_code,
                grid_size,
                mine_count,
                bet_amount,
                status,
                0,
                "[]",
                json.dumps(fairness_artifacts["mine_positions"]),
                START_MULTIPLIER,
                bet_amount,
                fairness_artifacts["fairness_version"],
                fairness_artifacts["nonce"],
                fairness_artifacts["server_seed_hash"],
                fairness_artifacts["rng_material"],
                fairness_artifacts["board_hash"],
            ),
        )


def lock_round(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                mgr.id,
                mgr.user_id,
                mgr.grid_size,
                mgr.mine_count,
                COALESCE(pr.bet_amount, mgr.bet_amount) AS bet_amount,
                COALESCE(pr.status, mgr.status) AS status,
                COALESCE(pr.title_code, mgr.title_code) AS title_code,
                COALESCE(pr.site_code, mgr.site_code) AS site_code,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.mine_positions_json,
                mgr.multiplier_current,
                mgr.payout_current,
                mgr.platform_round_id,
                mgr.demo_session_id
            FROM mines_game_rounds mgr
            LEFT JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
            WHERE mgr.id = %s
              AND mgr.user_id = %s
            FOR UPDATE OF mgr
            """,
            (session_id, user_id),
        )
        return cursor.fetchone()


def update_round_status_to_lost(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: str,
    revealed_cells: list[int],
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE mines_game_rounds
            SET
                revealed_cells_json = %s::jsonb,
                payout_current = %s,
                status = 'lost',
                closed_at = now()
            WHERE id = %s
              AND status = 'active'
            """,
            (
                json.dumps(revealed_cells),
                Decimal("0.000000"),
                session_id,
            ),
        )
        if cursor.rowcount == 0:
            raise MinesGameStateConflictError("Game session is not active")


def update_round_status_to_won(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE mines_game_rounds
            SET
                safe_reveals_count = %s,
                revealed_cells_json = %s::jsonb,
                multiplier_current = %s,
                payout_current = %s,
                status = 'won',
                closed_at = now()
            WHERE id = %s
              AND status = 'active'
            """,
            (
                safe_reveals_count,
                json.dumps(revealed_cells),
                multiplier_current,
                payout_current,
                session_id,
            ),
        )
        if cursor.rowcount == 0:
            raise MinesGameStateConflictError("Game session is not active")


def record_safe_reveal(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE mines_game_rounds
            SET
                safe_reveals_count = %s,
                revealed_cells_json = %s::jsonb,
                multiplier_current = %s,
                payout_current = %s
            WHERE id = %s
            """,
            (
                safe_reveals_count,
                json.dumps(revealed_cells),
                multiplier_current,
                payout_current,
                session_id,
            ),
        )


def get_closed_round_mine_positions(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    session_id: str,
) -> list[int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT mgr.mine_positions_json
            FROM mines_game_rounds mgr
            JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
            WHERE mgr.id = %s
              AND mgr.user_id = %s
              AND pr.status IN (%s, %s, %s)
            """,
            (
                session_id,
                user_id,
                SESSION_STATUS_WON,
                SESSION_STATUS_LOST,
                SESSION_STATUS_CANCELLED,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            return []
        return sorted(_normalize_cell_list(row["mine_positions_json"]))


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_session_for_user(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    session_id: str,
    viewer_role: str = "player",
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        if viewer_role == "admin":
            cursor.execute(
                """
                SELECT
                    pr.id,
                    pr.status,
                    mgr.grid_size,
                    mgr.mine_count,
                    pr.bet_amount,
                    pr.title_code,
                    pr.site_code,
                    pr.wallet_type,
                    pr.access_session_id,
                    mgr.safe_reveals_count,
                    mgr.revealed_cells_json,
                    mgr.multiplier_current,
                    mgr.payout_current,
                    pr.wallet_balance_after_start,
                    pr.table_session_id,
                    mgr.fairness_version,
                    mgr.nonce,
                    mgr.server_seed_hash,
                    mgr.board_hash,
                    pr.start_ledger_transaction_id,
                    pr.created_at,
                    pr.closed_at
                FROM platform_rounds pr
                JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                WHERE pr.id = %s
                """,
                (session_id,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    pr.id,
                    pr.status,
                    mgr.grid_size,
                    mgr.mine_count,
                    pr.bet_amount,
                    pr.title_code,
                    pr.site_code,
                    pr.wallet_type,
                    pr.access_session_id,
                    mgr.safe_reveals_count,
                    mgr.revealed_cells_json,
                    mgr.multiplier_current,
                    mgr.payout_current,
                    pr.wallet_balance_after_start,
                    pr.table_session_id,
                    mgr.fairness_version,
                    mgr.nonce,
                    mgr.server_seed_hash,
                    mgr.board_hash,
                    pr.start_ledger_transaction_id,
                    pr.created_at,
                    pr.closed_at
                FROM platform_rounds pr
                JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                WHERE pr.id = %s
                  AND pr.user_id = %s
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    """
                    SELECT
                        mgr.id,
                        mgr.status,
                        mgr.grid_size,
                        mgr.mine_count,
                        mgr.bet_amount,
                        mgr.title_code,
                        mgr.site_code,
                        'demo' AS wallet_type,
                        NULL AS access_session_id,
                        mgr.safe_reveals_count,
                        mgr.revealed_cells_json,
                        mgr.multiplier_current,
                        mgr.payout_current,
                        NULL AS wallet_balance_after_start,
                        NULL AS table_session_id,
                        mgr.fairness_version,
                        mgr.nonce,
                        mgr.server_seed_hash,
                        mgr.board_hash,
                        NULL AS start_ledger_transaction_id,
                        mgr.created_at,
                        mgr.closed_at
                    FROM mines_game_rounds mgr
                    WHERE mgr.id = %s
                      AND mgr.user_id = %s
                      AND mgr.demo_session_id IS NOT NULL
                    """,
                    (session_id, user_id),
                )
                row = cursor.fetchone()
                if row is not None:
                    return {
                        "game_session_id": str(row["id"]),
                        "status": row["status"],
                        "mode": "demo",
                        "grid_size": row["grid_size"],
                        "mine_count": row["mine_count"],
                        "bet_amount": _format_amount(row["bet_amount"]),
                        "title_code": row["title_code"],
                        "site_code": row["site_code"],
                        "wallet_type": "demo",
                        "access_session_id": None,
                        "safe_reveals_count": row["safe_reveals_count"],
                        "revealed_cells": row["revealed_cells_json"],
                        "multiplier_current": _format_multiplier(row["multiplier_current"]),
                        "potential_payout": _format_amount(row["payout_current"]),
                        "wallet_balance_after_start": None,
                        "table_session_id": None,
                        "fairness_version": row["fairness_version"],
                        "nonce": row["nonce"],
                        "server_seed_hash": row["server_seed_hash"],
                        "board_hash": row["board_hash"],
                        "ledger_transaction_id": None,
                        "created_at": row["created_at"].isoformat(),
                        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
                    }

        if viewer_role == "admin":
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "wallet_type": row["wallet_type"],
        "access_session_id": str(row["access_session_id"]) if row["access_session_id"] else None,
        "safe_reveals_count": row["safe_reveals_count"],
        "revealed_cells": row["revealed_cells_json"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "potential_payout": _format_amount(row["payout_current"]),
        "wallet_balance_after_start": _format_amount(row["wallet_balance_after_start"]),
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
        "fairness_version": row["fairness_version"],
        "nonce": row["nonce"],
        "server_seed_hash": row["server_seed_hash"],
        "board_hash": row["board_hash"],
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def list_session_history_page(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    limit: int,
    decoded_cursor: dict[str, object] | None,
) -> dict[str, object]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                pr.bet_amount,
                pr.title_code,
                pr.site_code,
                pr.wallet_type,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.multiplier_current,
                mgr.payout_current,
                pr.access_session_id,
                pr.table_session_id,
                gas.game_code AS access_session_game_code,
                gas.title_code AS access_session_title_code,
                gas.site_code AS access_session_site_code,
                gas.started_at AS access_session_started_at,
                gas.last_activity_at AS access_session_last_activity_at,
                gas.ended_at AS access_session_ended_at,
                gas.status AS access_session_status,
                pr.created_at,
                pr.closed_at
            FROM platform_rounds pr
            JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
            LEFT JOIN game_access_sessions gas ON gas.id = pr.access_session_id
            WHERE pr.user_id = %s
              AND pr.game_code = %s
              AND (
                %s::timestamptz IS NULL
                OR (pr.created_at, pr.id) < (%s::timestamptz, %s::uuid)
              )
            ORDER BY pr.created_at DESC, pr.id DESC
            LIMIT %s
            """,
            (
                user_id,
                GAME_CODE,
                decoded_cursor["created_at"] if decoded_cursor else None,
                decoded_cursor["created_at"] if decoded_cursor else None,
                decoded_cursor["game_session_id"] if decoded_cursor else None,
                limit + 1,
            ),
        )
        rows = list(cursor.fetchall())

    page_rows = rows[:limit]
    next_cursor = (
        _encode_session_history_cursor(page_rows[-1])
        if len(rows) > limit
        else None
    )
    return {
        "items": [_serialize_session_history_row(row) for row in page_rows],
        "next_cursor": next_cursor,
        "limit": limit,
    }


def list_latest_access_session_history(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    title_code: str,
    site_code: str,
    limit: int,
) -> list[dict[str, object]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                gas.id,
                gas.game_code,
                gas.title_code,
                gas.site_code,
                gas.started_at,
                gas.last_activity_at,
                gas.ended_at,
                gas.status
            FROM game_access_sessions gas
            WHERE gas.user_id = %s
              AND gas.game_code = %s
              AND gas.title_code = %s
              AND gas.site_code = %s
            ORDER BY gas.started_at DESC, gas.id DESC
            LIMIT %s
            """,
            (user_id, GAME_CODE, title_code, site_code, limit),
        )
        access_session_rows = list(cursor.fetchall())

        if not access_session_rows:
            return []

        access_session_ids = [str(row["id"]) for row in access_session_rows]
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                pr.bet_amount,
                pr.payout_amount,
                pr.title_code,
                pr.site_code,
                pr.wallet_type,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.mine_positions_json,
                mgr.multiplier_current,
                mgr.payout_current,
                mgr.fairness_version,
                mgr.nonce,
                mgr.server_seed_hash,
                mgr.board_hash,
                pr.access_session_id,
                pr.table_session_id,
                pr.start_ledger_transaction_id,
                pr.settlement_ledger_transaction_id,
                pr.user_id,
                pr.created_at,
                pr.closed_at
            FROM platform_rounds pr
            JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
            WHERE pr.user_id = %s
              AND pr.game_code = %s
              AND pr.access_session_id = ANY(%s::uuid[])
              AND pr.status IN (%s, %s, %s)
            ORDER BY pr.created_at DESC, pr.id DESC
            """,
            (
                user_id,
                GAME_CODE,
                access_session_ids,
                SESSION_STATUS_WON,
                SESSION_STATUS_LOST,
                SESSION_STATUS_CANCELLED,
            ),
        )
        round_rows = list(cursor.fetchall())

    rounds_by_access_session_id: dict[str, list[dict[str, object]]] = {
        str(row["id"]): [] for row in access_session_rows
    }
    for row in round_rows:
        access_session_id = str(row["access_session_id"])
        rounds_by_access_session_id.setdefault(access_session_id, []).append(
            _build_session_replay_payload(row)
        )

    return [
        {
            "id": str(row["id"]),
            "game_code": row["game_code"],
            "title_code": row["title_code"],
            "site_code": row["site_code"],
            "status": row["status"],
            "started_at": row["started_at"].isoformat(),
            "last_activity_at": row["last_activity_at"].isoformat(),
            "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
            "rounds": rounds_by_access_session_id.get(str(row["id"]), []),
        }
        for row in access_session_rows
    ]


def get_session_replay_for_user(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                pr.bet_amount,
                pr.payout_amount,
                pr.title_code,
                pr.site_code,
                pr.wallet_type,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.mine_positions_json,
                mgr.multiplier_current,
                mgr.payout_current,
                mgr.fairness_version,
                mgr.nonce,
                mgr.server_seed_hash,
                mgr.board_hash,
                pr.access_session_id,
                pr.table_session_id,
                pr.start_ledger_transaction_id,
                pr.settlement_ledger_transaction_id,
                pr.user_id,
                u.email AS user_email,
                pr.created_at,
                pr.closed_at
            FROM platform_rounds pr
            JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
            JOIN users u ON u.id = pr.user_id
            WHERE pr.id = %s
              AND pr.user_id = %s
              AND pr.game_code = %s
            """,
            (session_id, user_id, GAME_CODE),
        )
        row = cursor.fetchone()
        if row is not None:
            return _build_session_replay_payload(row)

        cursor.execute(
            """
            SELECT
                mgr.id,
                mgr.status,
                mgr.grid_size,
                mgr.mine_count,
                mgr.bet_amount,
                CASE WHEN mgr.status = %s THEN mgr.payout_current ELSE 0 END AS payout_amount,
                mgr.title_code,
                mgr.site_code,
                'demo' AS wallet_type,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.mine_positions_json,
                mgr.multiplier_current,
                mgr.payout_current,
                mgr.fairness_version,
                mgr.nonce,
                mgr.server_seed_hash,
                mgr.board_hash,
                NULL AS access_session_id,
                NULL AS table_session_id,
                NULL AS start_ledger_transaction_id,
                NULL AS settlement_ledger_transaction_id,
                mgr.user_id,
                NULL AS user_email,
                mgr.created_at,
                mgr.closed_at
            FROM mines_game_rounds mgr
            WHERE mgr.id = %s
              AND mgr.user_id = %s
              AND mgr.demo_session_id IS NOT NULL
            """,
            (SESSION_STATUS_WON, session_id, user_id),
        )
        row = cursor.fetchone()
        if row is not None:
            replay = _build_session_replay_payload(row)
            replay["mode"] = "demo"
            replay["start_ledger_transaction_id"] = None
            replay["settlement_ledger_transaction_id"] = None
            return replay

    return None


def get_session_replay_for_admin(
    connection: psycopg.Connection[DictRow],
    *,
    session_id: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                pr.bet_amount,
                pr.payout_amount,
                pr.title_code,
                pr.site_code,
                pr.wallet_type,
                mgr.safe_reveals_count,
                mgr.revealed_cells_json,
                mgr.mine_positions_json,
                mgr.multiplier_current,
                mgr.payout_current,
                mgr.fairness_version,
                mgr.nonce,
                mgr.server_seed_hash,
                mgr.board_hash,
                pr.access_session_id,
                pr.table_session_id,
                pr.start_ledger_transaction_id,
                pr.settlement_ledger_transaction_id,
                pr.user_id,
                u.email AS user_email,
                pr.created_at,
                pr.closed_at
            FROM platform_rounds pr
            JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
            JOIN users u ON u.id = pr.user_id
            WHERE pr.id = %s
              AND pr.game_code = %s
            """,
            (session_id, GAME_CODE),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    replay = _build_session_replay_payload(row)
    replay["admin_context"] = {
        "user_id": str(row["user_id"]),
        "user_email": row["user_email"],
    }
    return replay


def get_session_fairness_for_user(
    connection: psycopg.Connection[DictRow],
    *,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                mgr.id,
                pr.status,
                mgr.grid_size,
                mgr.mine_count,
                mgr.fairness_version,
                mgr.nonce,
                mgr.server_seed_hash,
                mgr.board_hash,
                pr.created_at,
                pr.closed_at
            FROM mines_game_rounds mgr
            JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
            WHERE mgr.id = %s
              AND mgr.user_id = %s
            """,
            (session_id, user_id),
        )
        row = cursor.fetchone()
        if row is not None:
            return {
                "game_session_id": str(row["id"]),
                "status": row["status"],
                "grid_size": row["grid_size"],
                "mine_count": row["mine_count"],
                "fairness_version": row["fairness_version"],
                "nonce": row["nonce"],
                "server_seed_hash": row["server_seed_hash"],
                "board_hash": row["board_hash"],
                "user_verifiable": False,
                "created_at": row["created_at"].isoformat(),
                "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
            }

        cursor.execute(
            """
            SELECT
                id,
                status,
                grid_size,
                mine_count,
                fairness_version,
                nonce,
                server_seed_hash,
                board_hash,
                created_at,
                closed_at
            FROM mines_game_rounds
            WHERE id = %s
              AND user_id = %s
              AND demo_session_id IS NOT NULL
            """,
            (session_id, user_id),
        )
        row = cursor.fetchone()
        if row is not None:
            return {
                "game_session_id": str(row["id"]),
                "status": row["status"],
                "mode": "demo",
                "grid_size": row["grid_size"],
                "mine_count": row["mine_count"],
                "fairness_version": row["fairness_version"],
                "nonce": row["nonce"],
                "server_seed_hash": row["server_seed_hash"],
                "board_hash": row["board_hash"],
                "user_verifiable": False,
                "created_at": row["created_at"].isoformat(),
                "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
            }

    return None


# ---------------------------------------------------------------------------
# Private helpers (moved from service)
# ---------------------------------------------------------------------------


def _build_session_replay_payload(row: dict[str, object]) -> dict[str, object]:
    status = str(row["status"])
    round_is_closed = status in {
        SESSION_STATUS_WON,
        SESSION_STATUS_LOST,
        SESSION_STATUS_CANCELLED,
    }
    revealed_cells = _normalize_cell_list(row["revealed_cells_json"])
    full_mine_positions = _normalize_cell_list(row["mine_positions_json"])
    exposed_mine_positions = full_mine_positions if round_is_closed else []

    return {
        "game_session_id": str(row["id"]),
        "status": status,
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "wallet_type": row["wallet_type"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "payout_amount": _format_amount(row["payout_amount"]),
        "safe_reveals_count": row["safe_reveals_count"],
        "revealed_cells": revealed_cells,
        "mine_positions": exposed_mine_positions,
        "mine_positions_available": round_is_closed,
        "final_revealed_cells": (
            _ordered_unique_cells([*revealed_cells, *full_mine_positions])
            if round_is_closed
            else revealed_cells
        ),
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "potential_payout": _format_amount(row["payout_current"]),
        "access_session_id": str(row["access_session_id"]) if row["access_session_id"] else None,
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
        "start_ledger_transaction_id": (
            str(row["start_ledger_transaction_id"]) if row["start_ledger_transaction_id"] else None
        ),
        "settlement_ledger_transaction_id": (
            str(row["settlement_ledger_transaction_id"])
            if row["settlement_ledger_transaction_id"]
            else None
        ),
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
        "board_reveal_available": round_is_closed,
        "replay_version": "mines-final-snapshot-v1",
        "fairness": {
            "fairness_version": row["fairness_version"],
            "nonce": row["nonce"],
            "server_seed_hash": row["server_seed_hash"],
            "board_hash": row["board_hash"],
            "user_verifiable": False,
        },
    }


def _serialize_session_history_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "wallet_type": row["wallet_type"],
        "safe_reveals_count": row["safe_reveals_count"],
        "revealed_cells_count": len(row["revealed_cells_json"]),
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "potential_payout": _format_amount(row["payout_current"]),
        "access_session_id": str(row["access_session_id"]) if row["access_session_id"] else None,
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
        "access_session": (
            {
                "id": str(row["access_session_id"]),
                "game_code": row["access_session_game_code"],
                "title_code": row["access_session_title_code"],
                "site_code": row["access_session_site_code"],
                "status": row["access_session_status"],
                "started_at": row["access_session_started_at"].isoformat(),
                "last_activity_at": row["access_session_last_activity_at"].isoformat(),
                "ended_at": (
                    row["access_session_ended_at"].isoformat()
                    if row["access_session_ended_at"]
                    else None
                ),
            }
            if row["access_session_id"]
            else None
        ),
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def _encode_session_history_cursor(row: dict[str, object]) -> str:
    payload = {
        "created_at": row["created_at"].isoformat(),
        "game_session_id": str(row["id"]),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_session_history_cursor(cursor: str) -> dict[str, object]:
    try:
        padded_cursor = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded_cursor.encode("ascii")))
        created_at = datetime.fromisoformat(str(payload["created_at"]))
        game_session_id = UUID(str(payload["game_session_id"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MinesSessionCursorError("Mines session cursor is not valid") from exc

    return {
        "created_at": created_at,
        "game_session_id": str(game_session_id),
    }


def _normalize_cell_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    return [int(entry) for entry in value]


def _ordered_unique_cells(cells: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered_cells: list[int] = []
    for cell in cells:
        if cell in seen:
            continue
        seen.add(cell)
        ordered_cells.append(cell)
    return ordered_cells


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _format_multiplier(value: Decimal) -> str:
    return f"{value:.4f}"
