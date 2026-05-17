import base64
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import UUID, uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.games.mines.backoffice_config import is_published_configuration_supported
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesSessionVoidedByOperatorError,
    MinesValidationError,
)
from app.modules.games.mines.fairness import create_fairness_artifacts
from app.modules.games.mines.platform_client import DemoPlatformGameClient
from app.modules.games.mines.round_gateway import (
    build_cashout_idempotency_key,
    get_cashout_snapshot,
    get_existing_cashout_by_key,
    is_open_round_idempotency_violation,
    is_settlement_idempotency_violation,
    open_round,
    settle_round_loss,
    settle_round_win,
)
from app.modules.games.mines.runtime import get_multiplier, supports_configuration

GAME_CODE = "mines"
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_WON = "won"
SESSION_STATUS_LOST = "lost"
SESSION_STATUS_CANCELLED = "cancelled"
START_MULTIPLIER = Decimal("1.0000")
DEFAULT_SESSION_HISTORY_LIMIT = 12
MAX_SESSION_HISTORY_LIMIT = 50
LATEST_ACCESS_SESSION_HISTORY_LIMIT = 3


class MinesSessionCursorError(Exception):
    pass


def start_session(
    *,
    user_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: str,
    wallet_type: str,
    access_session_id: str | None = None,
    table_session_id: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    bet_amount_decimal = _parse_bet_amount(bet_amount)
    normalized_wallet_type = wallet_type.strip().lower()
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    request_fingerprint = _build_request_fingerprint(
        user_id=user_id,
        grid_size=grid_size,
        mine_count=mine_count,
        bet_amount=bet_amount_decimal,
        wallet_type=normalized_wallet_type,
        access_session_id=access_session_id,
        table_session_id=table_session_id,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
    )

    if not supports_configuration(grid_size=grid_size, mine_count=mine_count):
        raise MinesValidationError("The selected grid_size and mine_count are not supported")
    if not is_published_configuration_supported(
        grid_size=grid_size,
        mine_count=mine_count,
        title_code=normalized_title_code,
    ):
        raise MinesValidationError("The selected grid_size and mine_count are not published")

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_session = _get_existing_session_by_idempotency(
                    cursor=cursor,
                    user_id=user_id,
                    idempotency_key=idempotency_key,
                )
                if existing_session is not None:
                    if existing_session["request_fingerprint"] != request_fingerprint:
                        raise MinesIdempotencyConflictError(
                            "Idempotency key already used with a different payload"
                        )
                    return _start_response_from_existing(existing_session)

                fairness_nonce = _get_next_fairness_nonce(cursor=cursor)
                fairness_artifacts = create_fairness_artifacts(
                    cursor=cursor,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    nonce=fairness_nonce,
                )

                session_id = str(uuid4())
                round_open_result = open_round(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    idempotency_key=idempotency_key,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    wallet_type=normalized_wallet_type,
                    table_session_id=table_session_id,
                    access_session_id=access_session_id,
                    title_code=normalized_title_code,
                    site_code=normalized_site_code,
                )
                _insert_platform_round(
                    cursor,
                    session_id=session_id,
                    user_id=user_id,
                    access_session_id=access_session_id,
                    title_code=normalized_title_code,
                    site_code=normalized_site_code,
                    wallet_account_id=round_open_result.wallet_account_id,
                    wallet_type=normalized_wallet_type,
                    bet_amount=bet_amount_decimal,
                    start_ledger_transaction_id=round_open_result.ledger_transaction_id,
                    wallet_balance_after_start=round_open_result.wallet_balance_after_start,
                    table_session_id=round_open_result.table_session_id,
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                )
                _insert_mines_game_round(
                    cursor,
                    session_id=session_id,
                    user_id=user_id,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    fairness_artifacts=fairness_artifacts,
                    platform_round_id=round_open_result.platform_round_id,
                    title_code=normalized_title_code,
                    site_code=normalized_site_code,
                )
    except psycopg.errors.UniqueViolation as exc:
        if is_open_round_idempotency_violation(exc):
            existing_session = _get_existing_session_by_idempotency_outside_tx(
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing_session is not None:
                if existing_session["request_fingerprint"] != request_fingerprint:
                    raise MinesIdempotencyConflictError(
                        "Idempotency key already used with a different payload"
                    ) from exc
                return _start_response_from_existing(existing_session)
        raise

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "grid_size": grid_size,
        "mine_count": mine_count,
        "bet_amount": _format_amount(bet_amount_decimal),
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "safe_reveals_count": 0,
        "multiplier_current": _format_multiplier(START_MULTIPLIER),
        "wallet_balance_after": _format_amount(round_open_result.wallet_balance_after_start),
        "ledger_transaction_id": round_open_result.ledger_transaction_id,
        "table_session_id": round_open_result.table_session_id,
        "table_session": round_open_result.table_session,
    }


def start_demo_session(
    *,
    anonymous_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: str,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    bet_amount_decimal = _parse_bet_amount(bet_amount)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    request_fingerprint = _build_request_fingerprint(
        user_id=anonymous_id,
        grid_size=grid_size,
        mine_count=mine_count,
        bet_amount=bet_amount_decimal,
        wallet_type="demo",
        access_session_id=None,
        table_session_id=None,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
    )

    if not supports_configuration(grid_size=grid_size, mine_count=mine_count):
        raise MinesValidationError("The selected grid_size and mine_count are not supported")
    if not is_published_configuration_supported(
        grid_size=grid_size,
        mine_count=mine_count,
        title_code=normalized_title_code,
    ):
        raise MinesValidationError("The selected grid_size and mine_count are not published")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            existing_session = _get_existing_demo_session_by_idempotency(
                cursor=cursor,
                anonymous_id=anonymous_id,
                idempotency_key=idempotency_key,
            )
            if existing_session is not None:
                if existing_session["request_fingerprint"] != request_fingerprint:
                    raise MinesIdempotencyConflictError(
                        "Idempotency key already used with a different payload"
                    )
                return _demo_start_response_from_existing(existing_session)

            fairness_nonce = _get_next_fairness_nonce(cursor=cursor)
            fairness_artifacts = create_fairness_artifacts(
                cursor=cursor,
                grid_size=grid_size,
                mine_count=mine_count,
                nonce=fairness_nonce,
            )
            session_id = str(uuid4())
            demo_client = DemoPlatformGameClient(anonymous_id=anonymous_id)
            round_open_result = demo_client.open_round(
                cursor=cursor,
                user_id=anonymous_id,
                game_round_id=session_id,
                idempotency_key=idempotency_key,
                grid_size=grid_size,
                mine_count=mine_count,
                bet_amount=bet_amount_decimal,
                wallet_type="demo",
                title_code=normalized_title_code,
                site_code=normalized_site_code,
            )
            _insert_demo_mines_game_round(
                cursor,
                session_id=session_id,
                demo_play_session_id=round_open_result.platform_round_id,
                anonymous_id=anonymous_id,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
                grid_size=grid_size,
                mine_count=mine_count,
                bet_amount=bet_amount_decimal,
                fairness_artifacts=fairness_artifacts,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
            )

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "mode": "demo",
        "grid_size": grid_size,
        "mine_count": mine_count,
        "bet_amount": _format_amount(bet_amount_decimal),
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "safe_reveals_count": 0,
        "multiplier_current": _format_multiplier(START_MULTIPLIER),
        "wallet_balance_after": _format_amount(round_open_result.wallet_balance_after_start),
        "ledger_transaction_id": None,
        "demo_event_id": round_open_result.ledger_transaction_id,
        "demo_play_session_id": round_open_result.platform_round_id,
    }


def get_session_for_user(
    *,
    user_id: str,
    session_id: str,
    viewer_role: str = "player",
) -> dict[str, object] | None:
    with db_connection() as connection:
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


def list_recent_sessions_for_user(
    *,
    user_id: str,
    limit: int = DEFAULT_SESSION_HISTORY_LIMIT,
) -> list[dict[str, object]]:
    return list_session_history_page_for_user(user_id=user_id, limit=limit)["items"]


def list_session_history_page_for_user(
    *,
    user_id: str,
    limit: int = DEFAULT_SESSION_HISTORY_LIMIT,
    cursor: str | None = None,
) -> dict[str, object]:
    normalized_limit = max(1, min(limit, MAX_SESSION_HISTORY_LIMIT))
    decoded_cursor = _decode_session_history_cursor(cursor) if cursor else None

    with db_connection() as connection:
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
                    normalized_limit + 1,
                ),
            )
            rows = list(cursor.fetchall())

    page_rows = rows[:normalized_limit]
    next_cursor = (
        _encode_session_history_cursor(page_rows[-1])
        if len(rows) > normalized_limit
        else None
    )
    return {
        "items": [_serialize_session_history_row(row) for row in page_rows],
        "next_cursor": next_cursor,
        "limit": normalized_limit,
    }


def list_latest_access_session_history_for_user(
    *,
    user_id: str,
    title_code: str,
    site_code: str,
    limit: int = LATEST_ACCESS_SESSION_HISTORY_LIMIT,
) -> list[dict[str, object]]:
    normalized_limit = max(1, min(limit, LATEST_ACCESS_SESSION_HISTORY_LIMIT))

    with db_connection() as connection:
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
                (user_id, GAME_CODE, title_code, site_code, normalized_limit),
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


def get_session_replay_for_user(*, user_id: str, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
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

    if row is None:
        return None

    return _build_session_replay_payload(row)


def get_session_replay_for_admin(*, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
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


def get_demo_session_replay_for_anonymous(
    *,
    anonymous_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    dmgr.id,
                    dmgr.status,
                    dmgr.grid_size,
                    dmgr.mine_count,
                    dmgr.bet_amount,
                    CASE
                        WHEN dmgr.status = %s THEN dmgr.payout_current
                        ELSE 0
                    END AS payout_amount,
                    dmgr.title_code,
                    dmgr.site_code,
                    'demo' AS wallet_type,
                    dmgr.safe_reveals_count,
                    dmgr.revealed_cells_json,
                    dmgr.mine_positions_json,
                    dmgr.multiplier_current,
                    dmgr.payout_current,
                    dmgr.fairness_version,
                    dmgr.nonce,
                    dmgr.server_seed_hash,
                    dmgr.board_hash,
                    NULL AS access_session_id,
                    dmgr.demo_play_session_id AS table_session_id,
                    NULL AS start_ledger_transaction_id,
                    NULL AS settlement_ledger_transaction_id,
                    dmgr.anonymous_id AS user_id,
                    NULL AS user_email,
                    dmgr.created_at,
                    dmgr.closed_at
                FROM demo_mines_game_rounds dmgr
                WHERE dmgr.id = %s
                  AND dmgr.anonymous_id = %s
                """,
                (SESSION_STATUS_WON, session_id, anonymous_id),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    replay = _build_session_replay_payload(row)
    replay["mode"] = "demo"
    replay["start_ledger_transaction_id"] = None
    replay["settlement_ledger_transaction_id"] = None
    return replay


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


def get_session_fairness_for_user(*, user_id: str, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
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

    if row is None:
        return None

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


def reveal_cell(*, user_id: str, session_id: str, cell_index: int) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_session_for_update(
                cursor=cursor,
                user_id=user_id,
                session_id=session_id,
            )
            if session is None:
                raise MinesGameStateConflictError("Game session is not active for this user")
            _ensure_session_active(session)
            _validate_cell_index(cell_index=cell_index, grid_size=session["grid_size"])

            revealed_cells = list(session["revealed_cells_json"])
            if cell_index in revealed_cells:
                raise MinesGameStateConflictError("Cell already revealed")

            mine_positions = set(session["mine_positions_json"])
            if cell_index in mine_positions:
                revealed_cells.append(cell_index)
                settle_round_loss(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                )
                _close_game_round_as_lost(
                    cursor,
                    session_id=session_id,
                    revealed_cells=revealed_cells,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_LOST,
                    "result": "mine",
                    "safe_reveals_count": session["safe_reveals_count"],
                    "mine_positions": sorted(mine_positions),
                }

            revealed_cells.append(cell_index)
            safe_reveals_count = session["safe_reveals_count"] + 1
            multiplier_current = get_multiplier(
                grid_size=session["grid_size"],
                mine_count=session["mine_count"],
                safe_reveals_count=safe_reveals_count,
            )
            potential_payout = (
                session["bet_amount"] * multiplier_current
            ).quantize(Decimal("0.000001"))
            max_safe_reveals = session["grid_size"] - session["mine_count"]

            if safe_reveals_count >= max_safe_reveals:
                auto_cashout_idempotency_key = build_cashout_idempotency_key(
                    user_id=user_id,
                    idempotency_key=f"auto-final-reveal:{session_id}:{safe_reveals_count}",
                )
                settlement_result = settle_round_win(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    payout_amount=potential_payout,
                    safe_reveals_count=safe_reveals_count,
                    idempotency_key=auto_cashout_idempotency_key,
                )
                _close_game_round_as_won(
                    cursor,
                    session_id=session_id,
                    settlement_ledger_transaction_id=settlement_result.ledger_transaction_id,
                    safe_reveals_count=safe_reveals_count,
                    revealed_cells=revealed_cells,
                    multiplier_current=multiplier_current,
                    payout_current=potential_payout,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_WON,
                    "result": "safe",
                    "safe_reveals_count": safe_reveals_count,
                    "multiplier_current": _format_multiplier(multiplier_current),
                    "potential_payout": _format_amount(potential_payout),
                    "payout_amount": _format_amount(potential_payout),
                    "mine_positions": sorted(mine_positions),
                    "wallet_balance_after": _format_amount(
                        settlement_result.wallet_balance_after
                    ),
                }

            _update_game_round_after_safe_reveal(
                cursor,
                session_id=session_id,
                safe_reveals_count=safe_reveals_count,
                revealed_cells=revealed_cells,
                multiplier_current=multiplier_current,
                payout_current=potential_payout,
            )

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "result": "safe",
        "safe_reveals_count": safe_reveals_count,
        "multiplier_current": _format_multiplier(multiplier_current),
        "potential_payout": _format_amount(potential_payout),
    }


def cashout_session(
    *,
    user_id: str,
    session_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    namespaced_idempotency_key = build_cashout_idempotency_key(
        user_id=user_id,
        idempotency_key=idempotency_key,
    )
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_cashout = get_existing_cashout_by_key(
                    cursor=cursor,
                    idempotency_key=namespaced_idempotency_key,
                )
                if existing_cashout is not None:
                    if str(existing_cashout["reference_id"]) != session_id:
                        raise MinesIdempotencyConflictError(
                            "Idempotency key already used with a different payload"
                        )
                    return _build_cashout_response_from_existing(
                        cursor=cursor,
                        user_id=user_id,
                        session_id=session_id,
                        cashout_transaction_id=str(existing_cashout["id"]),
                    )

                session = _get_session_for_update(
                    cursor=cursor,
                    user_id=user_id,
                    session_id=session_id,
                )
                if session is None:
                    raise MinesGameStateConflictError("Game session is not active for this user")
                if session["status"] == SESSION_STATUS_CANCELLED:
                    raise MinesSessionVoidedByOperatorError(
                        "Game session was closed by an operator"
                    )
                if session["status"] != SESSION_STATUS_ACTIVE:
                    if session["status"] == SESSION_STATUS_WON:
                        existing_cashout = get_existing_cashout_by_key(
                            cursor=cursor,
                            idempotency_key=namespaced_idempotency_key,
                        )
                        if existing_cashout is not None:
                            if str(existing_cashout["reference_id"]) != session_id:
                                raise MinesIdempotencyConflictError(
                                    "Idempotency key already used with a different payload"
                                )
                            return _build_cashout_response_from_existing(
                                cursor=cursor,
                                user_id=user_id,
                                session_id=session_id,
                                cashout_transaction_id=str(existing_cashout["id"]),
                            )
                    raise MinesGameStateConflictError("Game session is not active")
                if session["safe_reveals_count"] <= 0:
                    raise MinesGameStateConflictError(
                        "Cashout is not available before a safe reveal"
                    )

                payout_amount = Decimal(session["payout_current"]).quantize(
                    Decimal("0.000001")
                )
                settlement_result = settle_round_win(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    payout_amount=payout_amount,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    idempotency_key=namespaced_idempotency_key,
                )
                _close_game_round_as_won(
                    cursor,
                    session_id=session_id,
                    settlement_ledger_transaction_id=settlement_result.ledger_transaction_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    revealed_cells=list(session["revealed_cells_json"]),
                    multiplier_current=session["multiplier_current"],
                    payout_current=payout_amount,
                )
    except psycopg.errors.UniqueViolation as exc:
        if is_settlement_idempotency_violation(exc):
            with db_connection() as connection:
                with connection.cursor() as cursor:
                    existing_cashout = get_existing_cashout_by_key(
                        cursor=cursor,
                        idempotency_key=namespaced_idempotency_key,
                    )
                    if existing_cashout is not None:
                        if str(existing_cashout["reference_id"]) != session_id:
                            raise MinesIdempotencyConflictError(
                                "Idempotency key already used with a different payload"
                            ) from exc
                        return _build_cashout_response_from_existing(
                            cursor=cursor,
                            user_id=user_id,
                            session_id=session_id,
                            cashout_transaction_id=str(existing_cashout["id"]),
                        )
        raise

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "payout_amount": _format_amount(payout_amount),
        "wallet_balance_after": _format_amount(settlement_result.wallet_balance_after),
        "ledger_transaction_id": settlement_result.ledger_transaction_id,
        "mine_positions": sorted(_normalize_cell_list(session["mine_positions_json"])),
    }


def reveal_demo_cell(
    *,
    anonymous_id: str,
    session_id: str,
    cell_index: int,
) -> dict[str, object]:
    demo_client = DemoPlatformGameClient(anonymous_id=anonymous_id)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_demo_session_for_update(
                cursor=cursor,
                anonymous_id=anonymous_id,
                session_id=session_id,
            )
            if session is None:
                raise MinesGameStateConflictError("Game session is not active for this user")
            _ensure_session_active(session)
            _validate_cell_index(cell_index=cell_index, grid_size=session["grid_size"])

            revealed_cells = list(session["revealed_cells_json"])
            if cell_index in revealed_cells:
                raise MinesGameStateConflictError("Cell already revealed")

            mine_positions = set(session["mine_positions_json"])
            if cell_index in mine_positions:
                revealed_cells.append(cell_index)
                demo_client.settle_loss(
                    cursor=cursor,
                    user_id=anonymous_id,
                    game_round_id=session_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                )
                _close_demo_game_round_as_lost(
                    cursor,
                    session_id=session_id,
                    revealed_cells=revealed_cells,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_LOST,
                    "mode": "demo",
                    "result": "mine",
                    "safe_reveals_count": session["safe_reveals_count"],
                    "mine_positions": sorted(mine_positions),
                }

            revealed_cells.append(cell_index)
            safe_reveals_count = session["safe_reveals_count"] + 1
            multiplier_current = get_multiplier(
                grid_size=session["grid_size"],
                mine_count=session["mine_count"],
                safe_reveals_count=safe_reveals_count,
            )
            potential_payout = (
                session["bet_amount"] * multiplier_current
            ).quantize(Decimal("0.000001"))
            max_safe_reveals = session["grid_size"] - session["mine_count"]

            if safe_reveals_count >= max_safe_reveals:
                auto_cashout_idempotency_key = demo_client.build_cashout_idempotency_key(
                    user_id=anonymous_id,
                    idempotency_key=f"auto-final-reveal:{session_id}:{safe_reveals_count}",
                )
                settlement_result = demo_client.settle_win(
                    cursor=cursor,
                    user_id=anonymous_id,
                    game_round_id=session_id,
                    payout_amount=potential_payout,
                    safe_reveals_count=safe_reveals_count,
                    idempotency_key=auto_cashout_idempotency_key,
                )
                _close_demo_game_round_as_won(
                    cursor,
                    session_id=session_id,
                    safe_reveals_count=safe_reveals_count,
                    revealed_cells=revealed_cells,
                    multiplier_current=multiplier_current,
                    payout_current=potential_payout,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_WON,
                    "mode": "demo",
                    "result": "safe",
                    "safe_reveals_count": safe_reveals_count,
                    "multiplier_current": _format_multiplier(multiplier_current),
                    "potential_payout": _format_amount(potential_payout),
                    "payout_amount": _format_amount(potential_payout),
                    "mine_positions": sorted(mine_positions),
                    "wallet_balance_after": _format_amount(
                        settlement_result.wallet_balance_after
                    ),
                    "ledger_transaction_id": None,
                    "demo_event_id": settlement_result.ledger_transaction_id,
                }

            _update_demo_game_round_after_safe_reveal(
                cursor,
                session_id=session_id,
                safe_reveals_count=safe_reveals_count,
                revealed_cells=revealed_cells,
                multiplier_current=multiplier_current,
                payout_current=potential_payout,
            )

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "mode": "demo",
        "result": "safe",
        "safe_reveals_count": safe_reveals_count,
        "multiplier_current": _format_multiplier(multiplier_current),
        "potential_payout": _format_amount(potential_payout),
    }


def cashout_demo_session(
    *,
    anonymous_id: str,
    session_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    demo_client = DemoPlatformGameClient(anonymous_id=anonymous_id)
    namespaced_idempotency_key = demo_client.build_cashout_idempotency_key(
        user_id=anonymous_id,
        idempotency_key=idempotency_key,
    )
    with db_connection() as connection:
        with connection.cursor() as cursor:
            existing_cashout = demo_client.get_existing_cashout_by_key(
                cursor=cursor,
                idempotency_key=namespaced_idempotency_key,
            )
            if existing_cashout is not None:
                if str(existing_cashout["reference_id"]) != session_id:
                    raise MinesIdempotencyConflictError(
                        "Idempotency key already used with a different payload"
                    )
                return _build_demo_cashout_response_from_existing(
                    cursor=cursor,
                    anonymous_id=anonymous_id,
                    session_id=session_id,
                    demo_event_id=str(existing_cashout["id"]),
                )

            session = _get_demo_session_for_update(
                cursor=cursor,
                anonymous_id=anonymous_id,
                session_id=session_id,
            )
            if session is None:
                raise MinesGameStateConflictError("Game session is not active for this user")
            _ensure_session_active(session)
            if session["safe_reveals_count"] <= 0:
                raise MinesGameStateConflictError(
                    "Cashout is not available before a safe reveal"
                )

            payout_amount = Decimal(session["payout_current"]).quantize(
                Decimal("0.000001")
            )
            settlement_result = demo_client.settle_win(
                cursor=cursor,
                user_id=anonymous_id,
                game_round_id=session_id,
                payout_amount=payout_amount,
                safe_reveals_count=int(session["safe_reveals_count"]),
                idempotency_key=namespaced_idempotency_key,
            )
            _close_demo_game_round_as_won(
                cursor,
                session_id=session_id,
                safe_reveals_count=int(session["safe_reveals_count"]),
                revealed_cells=list(session["revealed_cells_json"]),
                multiplier_current=session["multiplier_current"],
                payout_current=payout_amount,
            )

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "mode": "demo",
        "payout_amount": _format_amount(payout_amount),
        "wallet_balance_after": _format_amount(settlement_result.wallet_balance_after),
        "ledger_transaction_id": None,
        "demo_event_id": settlement_result.ledger_transaction_id,
        "mine_positions": sorted(_normalize_cell_list(session["mine_positions_json"])),
    }


def session_exists(session_id: str) -> bool:
    with db_connection() as connection:
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


def session_belongs_to_user(*, session_id: str, user_id: str) -> bool:
    with db_connection() as connection:
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


def get_demo_session_for_anonymous(
    *,
    anonymous_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    dmgr.id,
                    dmgr.status,
                    dmgr.grid_size,
                    dmgr.mine_count,
                    dmgr.bet_amount,
                    dmgr.title_code,
                    dmgr.site_code,
                    dmgr.safe_reveals_count,
                    dmgr.revealed_cells_json,
                    dmgr.multiplier_current,
                    dmgr.payout_current,
                    dps.balance_chips,
                    dmgr.demo_play_session_id,
                    dmgr.fairness_version,
                    dmgr.nonce,
                    dmgr.server_seed_hash,
                    dmgr.board_hash,
                    dmgr.created_at,
                    dmgr.closed_at
                FROM demo_mines_game_rounds dmgr
                JOIN demo_play_sessions dps ON dps.id = dmgr.demo_play_session_id
                WHERE dmgr.id = %s
                  AND dmgr.anonymous_id = %s
                """,
                (session_id, anonymous_id),
            )
            row = cursor.fetchone()

    if row is None:
        return None

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
        "safe_reveals_count": row["safe_reveals_count"],
        "revealed_cells": row["revealed_cells_json"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "potential_payout": _format_amount(row["payout_current"]),
        "wallet_balance_after_start": None,
        "demo_balance_chips": _format_amount(row["balance_chips"]),
        "demo_play_session_id": str(row["demo_play_session_id"]),
        "fairness_version": row["fairness_version"],
        "nonce": row["nonce"],
        "server_seed_hash": row["server_seed_hash"],
        "board_hash": row["board_hash"],
        "ledger_transaction_id": None,
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def get_demo_session_fairness_for_anonymous(
    *,
    anonymous_id: str,
    session_id: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
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
                FROM demo_mines_game_rounds
                WHERE id = %s
                  AND anonymous_id = %s
                """,
                (session_id, anonymous_id),
            )
            row = cursor.fetchone()

    if row is None:
        return None

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


def demo_session_exists(session_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM demo_mines_game_rounds
                WHERE id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Private helper functions for mines_game_rounds SQL operations.
#
# After the schema split (P4), platform fields live in platform_rounds
# (managed by platform/rounds/service.py) and game fields live in
# mines_game_rounds (managed here).
#
# Platform-field reads go through round_gateway.py, which delegates to the
# configured PlatformGameClient implementation.
# ---------------------------------------------------------------------------


def _insert_mines_game_round(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    fairness_artifacts: dict[str, object],
    platform_round_id: str,
    title_code: str,
    site_code: str,
) -> None:
    """Insert a new mines_game_rounds row. Platform fields are in platform_rounds."""
    cursor.execute(
        """
        INSERT INTO mines_game_rounds (
            id,
            platform_round_id,
            user_id,
            title_code,
            site_code,
            grid_size,
            mine_count,
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
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            session_id,
            platform_round_id,
            user_id,
            title_code,
            site_code,
            grid_size,
            mine_count,
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


def _insert_platform_round(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    user_id: str,
    access_session_id: str | None,
    title_code: str,
    site_code: str,
    wallet_account_id: str,
    wallet_type: str,
    bet_amount: Decimal,
    start_ledger_transaction_id: str,
    wallet_balance_after_start: Decimal,
    table_session_id: str | None,
    idempotency_key: str,
    request_fingerprint: str,
) -> None:
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            session_id,
            user_id,
            GAME_CODE,
            title_code,
            site_code,
            access_session_id,
            wallet_account_id,
            wallet_type,
            bet_amount,
            SESSION_STATUS_ACTIVE,
            Decimal("0.000000"),
            start_ledger_transaction_id,
            wallet_balance_after_start,
            table_session_id,
            idempotency_key,
            request_fingerprint,
        ),
    )


def _close_game_round_as_lost(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    revealed_cells: list[int],
) -> None:
    """Mark a mines game round as lost (mine hit)."""
    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET
            revealed_cells_json = %s::jsonb,
            payout_current = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            json.dumps(revealed_cells),
            Decimal("0.000000"),
            session_id,
        ),
    )
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = %s,
            payout_amount = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_LOST,
            Decimal("0.000000"),
            session_id,
        ),
    )


def _close_game_round_as_won(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    settlement_ledger_transaction_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    """Mark a mines game round as won (cashout or auto-cashout on final reveal)."""
    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET
            safe_reveals_count = %s,
            revealed_cells_json = %s::jsonb,
            multiplier_current = %s,
            payout_current = %s,
            closed_at = now()
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
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = %s,
            payout_amount = %s,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_WON,
            payout_current,
            settlement_ledger_transaction_id,
            session_id,
        ),
    )


def _close_demo_game_round_as_lost(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    revealed_cells: list[int],
) -> None:
    cursor.execute(
        """
        UPDATE demo_mines_game_rounds
        SET
            status = %s,
            revealed_cells_json = %s::jsonb,
            payout_current = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_LOST,
            json.dumps(revealed_cells),
            Decimal("0.000000"),
            session_id,
        ),
    )


def _close_demo_game_round_as_won(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    cursor.execute(
        """
        UPDATE demo_mines_game_rounds
        SET
            status = %s,
            safe_reveals_count = %s,
            revealed_cells_json = %s::jsonb,
            multiplier_current = %s,
            payout_current = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_WON,
            safe_reveals_count,
            json.dumps(revealed_cells),
            multiplier_current,
            payout_current,
            session_id,
        ),
    )


def _insert_demo_mines_game_round(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    demo_play_session_id: str,
    anonymous_id: str,
    title_code: str,
    site_code: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    fairness_artifacts: dict[str, object],
    idempotency_key: str,
    request_fingerprint: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO demo_mines_game_rounds (
            id,
            demo_play_session_id,
            anonymous_id,
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
            board_hash,
            idempotency_key,
            request_fingerprint
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            session_id,
            demo_play_session_id,
            anonymous_id,
            title_code,
            site_code,
            grid_size,
            mine_count,
            bet_amount,
            SESSION_STATUS_ACTIVE,
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
            idempotency_key,
            request_fingerprint,
        ),
    )


def _update_game_round_after_safe_reveal(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    """Update mines game round state after a safe (non-mine) cell reveal."""
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


def _update_demo_game_round_after_safe_reveal(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    cursor.execute(
        """
        UPDATE demo_mines_game_rounds
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


def _get_session_for_update(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            mgr.id,
            mgr.user_id,
            mgr.grid_size,
            mgr.mine_count,
            pr.bet_amount,
            pr.status,
            mgr.safe_reveals_count,
            mgr.revealed_cells_json,
            mgr.mine_positions_json,
            mgr.multiplier_current,
            mgr.payout_current
        FROM mines_game_rounds mgr
        JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
        WHERE mgr.id = %s
          AND mgr.user_id = %s
        FOR UPDATE OF mgr, pr
        """,
        (session_id, user_id),
    )
    return cursor.fetchone()


def _get_demo_session_for_update(
    *,
    cursor: psycopg.Cursor,
    anonymous_id: str,
    session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            dmgr.id,
            dmgr.anonymous_id,
            dmgr.grid_size,
            dmgr.mine_count,
            dmgr.bet_amount,
            dmgr.status,
            dmgr.safe_reveals_count,
            dmgr.revealed_cells_json,
            dmgr.mine_positions_json,
            dmgr.multiplier_current,
            dmgr.payout_current,
            dmgr.demo_play_session_id,
            dps.balance_chips
        FROM demo_mines_game_rounds dmgr
        JOIN demo_play_sessions dps ON dps.id = dmgr.demo_play_session_id
        WHERE dmgr.id = %s
          AND dmgr.anonymous_id = %s
        FOR UPDATE OF dmgr, dps
        """,
        (session_id, anonymous_id),
    )
    return cursor.fetchone()


def _get_existing_session_by_idempotency(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
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


def _get_existing_demo_session_by_idempotency(
    *,
    cursor: psycopg.Cursor,
    anonymous_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            dmgr.id,
            dmgr.status,
            dmgr.grid_size,
            dmgr.mine_count,
            dmgr.bet_amount,
            dmgr.title_code,
            dmgr.site_code,
            dmgr.safe_reveals_count,
            dmgr.multiplier_current,
            dps.balance_chips,
            dmgr.demo_play_session_id,
            dmgr.request_fingerprint
        FROM demo_mines_game_rounds dmgr
        JOIN demo_play_sessions dps ON dps.id = dmgr.demo_play_session_id
        WHERE dmgr.anonymous_id = %s
          AND dmgr.idempotency_key = %s
        """,
        (anonymous_id, idempotency_key),
    )
    return cursor.fetchone()


def _get_existing_session_by_idempotency_outside_tx(
    *,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return _get_existing_session_by_idempotency(
                cursor=cursor,
                user_id=user_id,
                idempotency_key=idempotency_key,
            )


def _get_next_fairness_nonce(*, cursor: psycopg.Cursor) -> int:
    cursor.execute(
        """
        SELECT nextval('mines_fairness_nonce_seq') AS nonce
        """
    )
    row = cursor.fetchone()
    assert row is not None
    return int(row["nonce"])


def _build_cashout_response_from_existing(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
    cashout_transaction_id: str,
) -> dict[str, object]:
    snapshot = get_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_round_id=session_id,
    )
    if snapshot is None:
        raise MinesGameStateConflictError("Game session is not active for this user")

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "payout_amount": _format_amount(snapshot["payout_current"]),
        "wallet_balance_after": _format_amount(snapshot["wallet_balance_after"]),
        "ledger_transaction_id": cashout_transaction_id,
        "mine_positions": _get_closed_round_mine_positions(
            cursor=cursor,
            user_id=user_id,
            session_id=session_id,
        ),
    }


def _build_demo_cashout_response_from_existing(
    *,
    cursor: psycopg.Cursor,
    anonymous_id: str,
    session_id: str,
    demo_event_id: str,
) -> dict[str, object]:
    snapshot = DemoPlatformGameClient(anonymous_id=anonymous_id).get_cashout_snapshot(
        cursor=cursor,
        user_id=anonymous_id,
        game_round_id=session_id,
    )
    if snapshot is None:
        raise MinesGameStateConflictError("Game session is not active for this user")

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "mode": "demo",
        "payout_amount": _format_amount(snapshot["payout_current"]),
        "wallet_balance_after": _format_amount(snapshot["wallet_balance_after"]),
        "ledger_transaction_id": None,
        "demo_event_id": demo_event_id,
        "mine_positions": _get_closed_demo_round_mine_positions(
            cursor=cursor,
            anonymous_id=anonymous_id,
            session_id=session_id,
        ),
    }


def _get_closed_round_mine_positions(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
) -> list[int]:
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


def _get_closed_demo_round_mine_positions(
    *,
    cursor: psycopg.Cursor,
    anonymous_id: str,
    session_id: str,
) -> list[int]:
    cursor.execute(
        """
        SELECT mine_positions_json
        FROM demo_mines_game_rounds
        WHERE id = %s
          AND anonymous_id = %s
          AND status IN (%s, %s, %s)
        """,
        (
            session_id,
            anonymous_id,
            SESSION_STATUS_WON,
            SESSION_STATUS_LOST,
            SESSION_STATUS_CANCELLED,
        ),
    )
    row = cursor.fetchone()
    if row is None:
        return []
    return sorted(_normalize_cell_list(row["mine_positions_json"]))


def _build_request_fingerprint(
    *,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
    access_session_id: str | None,
    table_session_id: str | None,
    title_code: str,
    site_code: str,
) -> str:
    payload = json.dumps(
        {
            "user_id": user_id,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": _format_amount(bet_amount),
            "wallet_type": wallet_type,
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
            "title_code": title_code,
            "site_code": site_code,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _ensure_session_active(session: dict[str, object]) -> None:
    if session["status"] == SESSION_STATUS_CANCELLED:
        raise MinesSessionVoidedByOperatorError("Game session was closed by an operator")
    if session["status"] != SESSION_STATUS_ACTIVE:
        raise MinesGameStateConflictError("Game session is not active")


def _validate_cell_index(*, cell_index: int, grid_size: int) -> None:
    if cell_index < 0 or cell_index >= grid_size:
        raise MinesValidationError("Cell index is not valid")


def _parse_bet_amount(raw_value: str) -> Decimal:
    try:
        amount = Decimal(raw_value)
    except InvalidOperation as exc:
        raise MinesValidationError("Bet amount is not valid") from exc
    if amount <= 0:
        raise MinesValidationError("Bet amount must be greater than zero")
    return amount.quantize(Decimal("0.000001"))


def _start_response_from_existing(row: dict[str, object]) -> dict[str, object]:
    """Build the start-session response from an existing idempotent session row.

    Uses get_round_start_snapshot via round_gateway to read platform fields
    (wallet_balance_after_start, start_ledger_transaction_id) instead of
    accessing them directly from the row, keeping platform field knowledge
    encapsulated in the gateway layer.
    """
    # For the idempotent path, the row already contains the platform fields
    # from _get_existing_session_by_idempotency. We read them through the row
    # to avoid an extra DB query, but the field names are the same as what
    # get_round_start_snapshot would return.
    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "safe_reveals_count": row["safe_reveals_count"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "wallet_balance_after": _format_amount(row["wallet_balance_after_start"]),
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
    }


def _demo_start_response_from_existing(row: dict[str, object]) -> dict[str, object]:
    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "mode": "demo",
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "safe_reveals_count": row["safe_reveals_count"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "wallet_balance_after": _format_amount(row["balance_chips"]),
        "ledger_transaction_id": None,
        "demo_play_session_id": str(row["demo_play_session_id"]),
    }


def _normalize_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise MinesValidationError("Title code is required")
    return normalized_title_code


def _normalize_site_code(site_code: str) -> str:
    normalized_site_code = site_code.strip().lower()
    if not normalized_site_code:
        raise MinesValidationError("Site code is required")
    return normalized_site_code


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _format_multiplier(value: Decimal) -> str:
    return f"{value:.4f}"
