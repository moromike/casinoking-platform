from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import UUID, uuid4

from psycopg.rows import DictRow

from app.db.connection import db_connection
from app.modules.games.boxe import repository
from app.modules.games.boxe.admin_config import (
    get_public_admin_config,
    is_published_configuration_supported,
)
from app.modules.games.boxe.fairness import create_fairness_artifacts
from app.modules.games.boxe.math import (
    DIFFICULTIES,
    FAIRNESS_VERSION,
    SUPPORTED_ROWS,
    calculate_payout,
    cells_for_row,
    get_all_multiplier_ladders,
    get_multiplier,
    get_multiplier_ladder,
)
from app.modules.games.boxe.randomness import (
    build_server_seed_hash,
    generate_pyramid_full_reveal,
    generate_step_outcome,
)
from app.modules.games.boxe.round_gateway import (
    BoxePlatformIdempotencyConflictError,
    BoxePlatformInsufficientBalanceError,
    BoxePlatformValidationError,
    build_cashout_idempotency_key,
    open_round as open_platform_round,
    settle_loss as settle_platform_loss,
    settle_win as settle_platform_win,
)
from app.modules.games.boxe.state_machine import (
    BoxeRoundStatus,
    BoxeStateTransitionError,
    BoxeTransitionEvent,
    is_terminal,
    transition,
    validate_collect_attempt,
    validate_pick_attempt,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_published_title_for_launch,
)
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)

GAME_CODE = "boxe"
DEFAULT_TITLE_CODE = "boxe001"
MASTER_TITLE_CODE = "boxe"
DEFAULT_SITE_CODE = "casinoking"
IDEMPOTENCY_TTL_SECONDS = 86_400
DEFAULT_HISTORY_LIMIT = 20
MAX_HISTORY_LIMIT = 100
LATEST_ACCESS_SESSION_HISTORY_LIMIT = 3
SUPPORTED_WALLET_SOURCES = {"cash", "bonus", "demo"}
PUBLIC_ERROR_CODES = {
    "CONFIG_MISSING",
    "TITLE_NOT_PUBLISHED",
    "LAUNCH_REJECTED_MASTER",
    "TABLE_SESSION_EXPIRED",
    "INSUFFICIENT_BALANCE",
    "BONUS_WALLET_EMPTY",
    "NETWORK_RETRY_REQUIRED",
    "BACKEND_UNAVAILABLE",
    "ROUND_ALREADY_CLOSED",
    "RECOVERY_AUTO_CASHOUT_PENDING",
    "LOSS_CONFIRMED",
}


class BoxeApiError(RuntimeError):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class BoxeCursorError(ValueError):
    pass


@dataclass(frozen=True)
class IdempotentResult:
    response: dict[str, object]
    replayed: bool


def get_public_config(
    *,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    resolved_title = title_code or DEFAULT_TITLE_CODE
    resolved_site = site_code or DEFAULT_SITE_CODE
    _validate_title_for_read(title_code=resolved_title, site_code=resolved_site)
    admin_config = get_public_admin_config(title_code=resolved_title)
    return {
        "game_code": GAME_CODE,
        "title_code": resolved_title,
        "site_code": resolved_site,
        "default_rows": admin_config["default_rows"],
        "rows_enabled": admin_config["rows_enabled"],
        "default_difficulty": admin_config["default_difficulty"],
        "difficulty_enabled": admin_config["difficulty_enabled"],
        "rtp_label": "98%",
        "multiplier_paths": {
            str(rows): {
                difficulty: [str(value) for value in ladder]
                for difficulty, ladder in difficulty_map.items()
            }
            for rows, difficulty_map in get_all_multiplier_ladders().items()
        },
        "copy_refs": {
            "rules": "boxe.rules",
            "failure": "boxe.failure",
        },
        "presentation_config": {
            "default_locale": admin_config["default_locale"],
            "copy": admin_config["copy"],
            "rules_html": admin_config["rules_html"],
        },
    }


def start_round(
    *,
    player_id: str,
    title_code: str,
    site_code: str | None = None,
    rows: int,
    difficulty: str,
    bet_amount: str,
    wallet_source: str,
    client_seed: str | None,
    idempotency_key: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> IdempotentResult:
    resolved_site_code = (site_code or DEFAULT_SITE_CODE).strip().lower()
    if not resolved_site_code:
        raise BoxeApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Site code is required",
        )
    _validate_title_for_launch(title_code=title_code, site_code=resolved_site_code)
    _validate_config(rows=rows, difficulty=difficulty, title_code=title_code)
    normalized_wallet = _validate_wallet_source(wallet_source)
    if normalized_wallet in {"cash", "bonus"} and table_session_id is None:
        raise BoxeApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="table_session_id is required for BOXE real play",
        )
    bet = _parse_bet_amount(bet_amount)
    _validate_synthetic_money_preconditions(wallet_source=normalized_wallet, bet_amount=bet)
    payload_fingerprint = _fingerprint(
        {
            "operation": "start_round",
            "player_id": player_id,
            "title_code": title_code,
            "site_code": resolved_site_code,
            "rows": rows,
            "difficulty": difficulty,
            "bet_amount": str(bet),
            "wallet_source": normalized_wallet,
            "client_seed": client_seed,
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        }
    )
    with db_connection() as connection:
        replay = _get_session_idempotency_replay(
            connection=connection,
            player_id=player_id,
            operation="start_round",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=replay, replayed=True)

        round_id = uuid4()
        platform_open = None
        demo_session = None
        if normalized_wallet != "demo":
            with connection.cursor() as cursor:
                platform_open = open_platform_round(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=str(round_id),
                    idempotency_key=idempotency_key,
                    rows=rows,
                    difficulty=difficulty,
                    bet_amount=bet,
                    wallet_type=normalized_wallet,
                    title_code=title_code,
                    site_code=resolved_site_code,
                    table_session_id=table_session_id,
                    access_session_id=access_session_id,
                    request_fingerprint=payload_fingerprint,
                )
        else:
            try:
                with connection.cursor() as cursor:
                    demo_session = open_demo_session(
                        anonymous_id=player_id,
                        title_code=title_code,
                        cursor=cursor,
                    )
                    demo_session = debit_for_bet(
                        session_id=demo_session["id"],
                        amount=bet,
                        idempotency_key=f"boxe:start:{round_id}:{idempotency_key}",
                        payload={
                            "game_code": GAME_CODE,
                            "round_id": str(round_id),
                            "title_code": title_code,
                            "site_code": resolved_site_code,
                            "rows": rows,
                            "difficulty": difficulty,
                        },
                        cursor=cursor,
                    )
            except (
                DemoWalletValidationError,
                DemoWalletInsufficientBalanceError,
                DemoWalletIdempotencyConflictError,
            ) as exc:
                _raise_demo_wallet_error(exc)
        session = repository.create_session(
            connection,
            player_id=UUID(player_id),
            title_code=title_code,
            site_code=resolved_site_code,
            access_session_id=UUID(access_session_id) if access_session_id else None,
            table_session_id=UUID(platform_open.table_session_id) if platform_open else None,
        )
        server_seed = f"boxe:{uuid4().hex}:{idempotency_key}"
        server_seed_hash = build_server_seed_hash(server_seed)
        round_row = repository.create_round(
            connection,
            session_id=session["id"],
            player_id=UUID(player_id),
            round_id=round_id,
            platform_round_id=UUID(platform_open.platform_round_id) if platform_open else None,
            demo_session_id=UUID(str(demo_session["id"])) if demo_session else None,
            title_code=title_code,
            site_code=resolved_site_code,
            rows=rows,
            difficulty=difficulty,
            bet_amount=bet,
            server_seed=server_seed,
            server_seed_hash=server_seed_hash,
            client_seed=client_seed or f"client:{player_id}:{idempotency_key}",
            nonce=1,
            start_idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        repository.apply_transition(
            connection,
            round_id=round_row["id"],
            event=BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS,
        )
        response = _round_start_response(
            session_id=session["id"],
            round_row=repository.get_round(connection, round_id=round_row["id"]),
            table_session_id=platform_open.table_session_id if platform_open else None,
            table_session=platform_open.table_session if platform_open else None,
            wallet_balance_after_start=str(demo_session["balance_chips"]) if demo_session else None,
        )
        repository.save_idempotency_result(
            connection,
            session_id=session["id"],
            operation="start_round",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def reveal_pick(
    *,
    player_id: str,
    round_id: str,
    row: int,
    position: int,
    idempotency_key: str,
) -> IdempotentResult:
    round_uuid = _parse_uuid(round_id, "round_id")
    payload_fingerprint = _fingerprint(
        {
            "operation": "reveal_pick",
            "player_id": player_id,
            "round_id": round_id,
            "row": row,
            "position": position,
        }
    )
    with db_connection() as connection:
        global_replay = _get_round_idempotency_replay(
            connection=connection,
            player_id=player_id,
            operation="reveal_pick",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if global_replay is not None:
            return IdempotentResult(response=global_replay, replayed=True)
        replay = repository.get_idempotency_result(
            connection,
            round_id=round_uuid,
            operation="reveal_pick",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)

        locked = repository.lock_round(connection, round_id=round_uuid)
        _ensure_round_owner(locked.data, player_id)
        if is_terminal(locked.status):
            raise BoxeApiError(
                status_code=409,
                code="ROUND_ALREADY_CLOSED",
                message="Round is already closed",
            )
        rows = int(locked.data["rows_count"])
        if row < 0 or row >= rows:
            raise BoxeApiError(status_code=400, code="INVALID_ROW", message="Row is not valid")
        if position < 0:
            raise BoxeApiError(
                status_code=400,
                code="INVALID_POSITION",
                message="Position is not valid",
            )
        if position >= cells_for_row(row, rows):
            raise BoxeApiError(
                status_code=400,
                code="INVALID_POSITION",
                message="Position is not valid",
            )
        requested_step = row + 1
        validate_pick_attempt(
            status=locked.status,
            current_step=int(locked.data["current_step"]),
            requested_step=requested_step,
        )
        outcome = generate_step_outcome(
            rows=rows,
            difficulty=str(locked.data["difficulty"]),
            step=requested_step,
            selected_box_index=position,
            server_seed=str(locked.data["server_seed"]),
            client_seed=str(locked.data["client_seed"]),
            nonce=int(locked.data["nonce"]),
        )
        top_row = requested_step == rows
        if outcome.safe and top_row:
            next_status = transition(locked.status, BoxeTransitionEvent.SAFE_PICK_TOP_ROW).to_status
            outcome_name = "top_row"
        elif outcome.safe:
            next_status = transition(locked.status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW).to_status
            outcome_name = "safe"
        else:
            next_status = transition(locked.status, BoxeTransitionEvent.MINE_PICK).to_status
            outcome_name = "mine"

        multiplier = get_multiplier(
            rows=rows,
            difficulty=str(locked.data["difficulty"]),
            step=requested_step,
        )
        payout = (
            calculate_payout(
                bet_amount=locked.data["bet_amount"],
                rows=rows,
                difficulty=str(locked.data["difficulty"]),
                step=requested_step,
            )
            if outcome.safe
            else Decimal("0")
        )
        terminal_picks = _list_picks(connection, round_id=round_uuid)
        terminal_picks.append(
            {
                "row_index": row,
                "selected_box_index": position,
            }
        )
        response = {
            "round_id": str(round_uuid),
            "outcome": outcome_name,
            "multiplier": str(multiplier),
            "payout": str(payout),
            "next_step_options": [] if next_status in {BoxeRoundStatus.COMPLETED_TOP_ROW, BoxeRoundStatus.FAILED_MINE} else _next_step_options(requested_step, rows),
            "status": next_status.value,
        }
        if is_terminal(next_status):
            response["pyramid_full_reveal"] = _pyramid_full_reveal(
                round_row=locked.data,
                picks=terminal_picks,
            )
        repository.record_pick(
            connection,
            round_id=round_uuid,
            step=requested_step,
            row_index=row,
            selected_box_index=position,
            safe=outcome.safe,
            rng_material=outcome.rng_material,
            success_probability=outcome.success_probability,
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        if next_status == BoxeRoundStatus.COMPLETED_TOP_ROW and locked.data["platform_round_id"]:
            with connection.cursor() as cursor:
                settlement = settle_platform_win(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=str(locked.data["platform_round_id"]),
                    payout_amount=payout,
                    safe_picks_count=int(locked.data["safe_picks_count"]) + 1,
                    idempotency_key=build_cashout_idempotency_key(
                        user_id=player_id,
                        idempotency_key=f"top-row:{idempotency_key}",
                    ),
                )
            if settlement.table_session is not None:
                response["table_session"] = settlement.table_session
        elif next_status == BoxeRoundStatus.COMPLETED_TOP_ROW and locked.data.get("demo_session_id"):
            try:
                with connection.cursor() as cursor:
                    demo_session = credit_for_win(
                        session_id=locked.data["demo_session_id"],
                        amount=payout,
                        idempotency_key=f"boxe:top-row:{round_uuid}:{idempotency_key}",
                        payload={
                            "game_code": GAME_CODE,
                            "round_id": str(round_uuid),
                            "safe_picks_count": int(locked.data["safe_picks_count"]) + 1,
                        },
                        cursor=cursor,
                    )
                response["settlement"] = _demo_settlement_payload(demo_session)
            except (
                DemoWalletValidationError,
                DemoWalletInsufficientBalanceError,
                DemoWalletIdempotencyConflictError,
            ) as exc:
                _raise_demo_wallet_error(exc)
        elif next_status == BoxeRoundStatus.FAILED_MINE and locked.data["platform_round_id"]:
            with connection.cursor() as cursor:
                settlement = settle_platform_loss(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=str(locked.data["platform_round_id"]),
                    safe_picks_count=int(locked.data["safe_picks_count"]),
                )
            if settlement.table_session is not None:
                response["table_session"] = settlement.table_session
        elif next_status == BoxeRoundStatus.FAILED_MINE and locked.data.get("demo_session_id"):
            try:
                with connection.cursor() as cursor:
                    demo_session = record_loss(
                        session_id=locked.data["demo_session_id"],
                        idempotency_key=f"boxe:loss:{round_uuid}:{idempotency_key}",
                        payload={
                            "game_code": GAME_CODE,
                            "round_id": str(round_uuid),
                            "safe_picks_count": int(locked.data["safe_picks_count"]),
                        },
                        cursor=cursor,
                    )
                response["settlement"] = _demo_settlement_payload(demo_session)
            except (
                DemoWalletValidationError,
                DemoWalletInsufficientBalanceError,
                DemoWalletIdempotencyConflictError,
            ) as exc:
                _raise_demo_wallet_error(exc)
        repository.update_round_status(
            connection,
            round_id=round_uuid,
            status=next_status,
            outcome=_terminal_outcome(next_status),
            final_payout_amount=payout if next_status in {BoxeRoundStatus.COMPLETED_TOP_ROW, BoxeRoundStatus.FAILED_MINE} else None,
            terminal_reason=next_status.value if is_terminal(next_status) else None,
        )
        repository.save_idempotency_result(
            connection,
            round_id=round_uuid,
            operation="reveal_pick",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def cashout_round(
    *,
    player_id: str,
    round_id: str,
    idempotency_key: str,
) -> IdempotentResult:
    round_uuid = _parse_uuid(round_id, "round_id")
    payload_fingerprint = _fingerprint(
        {
            "operation": "cashout",
            "player_id": player_id,
            "round_id": round_id,
        }
    )
    with db_connection() as connection:
        global_replay = _get_round_idempotency_replay(
            connection=connection,
            player_id=player_id,
            operation="cashout",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if global_replay is not None:
            return IdempotentResult(response=global_replay, replayed=True)
        replay = repository.get_idempotency_result(
            connection,
            round_id=round_uuid,
            operation="cashout",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)
        locked = repository.lock_round(connection, round_id=round_uuid)
        _ensure_round_owner(locked.data, player_id)
        terminal_replay = validate_collect_attempt(
            status=locked.status,
            safe_picks_count=int(locked.data["safe_picks_count"]),
        )
        if terminal_replay is not None:
            raise BoxeApiError(
                status_code=409,
                code="ROUND_ALREADY_CLOSED",
                message="Round is already closed",
            )
        pending = transition(locked.status, BoxeTransitionEvent.MANUAL_COLLECT)
        repository.update_round_status(
            connection,
            round_id=round_uuid,
            status=pending.to_status,
        )
        completed = transition(pending.to_status, BoxeTransitionEvent.SETTLEMENT_SUCCESS)
        payout = locked.data["payout_current"]
        picks = _list_picks(connection, round_id=round_uuid)
        settlement = None
        demo_settlement = None
        if locked.data["platform_round_id"]:
            with connection.cursor() as cursor:
                settlement = settle_platform_win(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=str(locked.data["platform_round_id"]),
                    payout_amount=payout,
                    safe_picks_count=int(locked.data["safe_picks_count"]),
                    idempotency_key=build_cashout_idempotency_key(
                        user_id=player_id,
                        idempotency_key=idempotency_key,
                    ),
                )
        elif locked.data.get("demo_session_id"):
            try:
                with connection.cursor() as cursor:
                    demo_session = credit_for_win(
                        session_id=locked.data["demo_session_id"],
                        amount=payout,
                        idempotency_key=f"boxe:cashout:{round_uuid}:{idempotency_key}",
                        payload={
                            "game_code": GAME_CODE,
                            "round_id": str(round_uuid),
                            "safe_picks_count": int(locked.data["safe_picks_count"]),
                        },
                        cursor=cursor,
                    )
                demo_settlement = _demo_settlement_payload(demo_session)
            except (
                DemoWalletValidationError,
                DemoWalletInsufficientBalanceError,
                DemoWalletIdempotencyConflictError,
            ) as exc:
                _raise_demo_wallet_error(exc)
        repository.update_round_status(
            connection,
            round_id=round_uuid,
            status=completed.to_status,
            outcome="cashout",
            final_payout_amount=payout,
            terminal_reason="manual_cashout",
        )
        response = {
            "round_id": str(round_uuid),
            "payout": str(payout),
            "status": BoxeRoundStatus.COMPLETED_CASHOUT.value,
            "pyramid_full_reveal": _pyramid_full_reveal(
                round_row=locked.data,
                picks=picks,
            ),
        }
        if settlement is not None:
            response["platform_round_id"] = settlement.platform_round_id
            response["ledger_transaction_id"] = settlement.ledger_transaction_id
            response["table_session"] = settlement.table_session
        if demo_settlement is not None:
            response["settlement"] = demo_settlement
        repository.save_idempotency_result(
            connection,
            round_id=round_uuid,
            operation="cashout",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def get_session(*, player_id: str, session_id: str) -> dict[str, object]:
    session_uuid = _parse_uuid(session_id, "session_id")
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM boxe_sessions
                WHERE id = %s
                """,
                (session_uuid,),
            )
            session = cursor.fetchone()
            if session is None:
                raise BoxeApiError(status_code=404, code="SESSION_NOT_FOUND", message="Session not found")
            if str(session["player_id"]) != player_id:
                raise BoxeApiError(status_code=403, code="FORBIDDEN", message="Session does not belong to player")
            cursor.execute(
                """
                SELECT *
                FROM boxe_rounds
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (session_uuid,),
            )
            round_row = cursor.fetchone()
        return {
            "session": _session_payload(dict(session)),
            "last_round": _round_payload(dict(round_row)) if round_row else None,
        }


def get_round_replay(*, player_id: str, round_id: str) -> dict[str, object]:
    round_uuid = _parse_uuid(round_id, "round_id")
    with db_connection() as connection:
        round_row = repository.get_round(connection, round_id=round_uuid)
        if round_row is None:
            raise BoxeApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")
        _ensure_round_owner(round_row, player_id)
        picks = _list_picks(connection, round_id=round_uuid)
        return _replay_payload(round_row=round_row, picks=picks)


def get_round_replay_for_admin(*, round_id: str) -> dict[str, object]:
    round_uuid = _parse_uuid(round_id, "round_id")
    with db_connection() as connection:
        round_row = repository.get_round(connection, round_id=round_uuid)
        if round_row is None:
            round_row = _get_round_by_platform_round_id(connection, platform_round_id=round_uuid)
        if round_row is None:
            raise BoxeApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")
        picks = _list_picks(connection, round_id=round_uuid)
        replay = _replay_payload(round_row=round_row, picks=picks)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT email
                FROM users
                WHERE id = %s
                """,
                (round_row["player_id"],),
            )
            user_row = cursor.fetchone()
        replay["admin_context"] = {
            "user_id": str(round_row["player_id"]),
            "user_email": user_row["email"] if user_row else None,
        }
        return replay


def list_latest_access_session_history_for_user(
    *,
    user_id: str,
    title_code: str,
    site_code: str,
    limit: int = LATEST_ACCESS_SESSION_HISTORY_LIMIT,
) -> list[dict[str, object]]:
    normalized_limit = max(1, min(limit, LATEST_ACCESS_SESSION_HISTORY_LIMIT))
    player_uuid = _parse_uuid(user_id, "user_id")

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
                (player_uuid, GAME_CODE, title_code, site_code, normalized_limit),
            )
            access_session_rows = [dict(row) for row in cursor.fetchall()]

            if not access_session_rows:
                return []

            access_session_ids = [str(row["id"]) for row in access_session_rows]
            cursor.execute(
                """
                SELECT
                    r.*,
                    pr.access_session_id AS replay_access_session_id
                FROM platform_rounds pr
                JOIN boxe_rounds r ON r.platform_round_id = pr.id
                WHERE pr.access_session_id = ANY(%s::uuid[])
                  AND pr.user_id = %s
                  AND pr.game_code = %s
                  AND pr.title_code = %s
                  AND pr.site_code = %s
                  AND r.player_id = %s
                  AND r.title_code = %s
                  AND r.site_code = %s
                  AND r.status IN (
                      'completed_cashout',
                      'completed_top_row',
                      'failed_mine',
                      'expired',
                      'quarantined'
                  )
                ORDER BY pr.created_at DESC, pr.id DESC
                """,
                (
                    access_session_ids,
                    player_uuid,
                    GAME_CODE,
                    title_code,
                    site_code,
                    player_uuid,
                    title_code,
                    site_code,
                ),
            )
            round_rows = [dict(row) for row in cursor.fetchall()]
            picks_by_round_id = _list_picks_for_rounds(
                connection,
                round_ids=[str(row["id"]) for row in round_rows],
            )

    rounds_by_access_session_id: dict[str, list[dict[str, object]]] = {
        str(row["id"]): [] for row in access_session_rows
    }
    for row in round_rows:
        access_session_id = (
            str(row["replay_access_session_id"])
            if row.get("replay_access_session_id")
            else None
        )
        if access_session_id is None:
            continue
        rounds_by_access_session_id.setdefault(access_session_id, []).append(
            _replay_payload(
                round_row=row,
                picks=picks_by_round_id.get(str(row["id"]), []),
            )
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


def _get_round_by_platform_round_id(
    connection,
    *,
    platform_round_id,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_rounds
            WHERE platform_round_id = %s
            """,
            (platform_round_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_sessions(*, player_id: str, limit: int, cursor: str | None) -> dict[str, object]:
    if limit < 1 or limit > MAX_HISTORY_LIMIT:
        raise BoxeApiError(status_code=422, code="VALIDATION_ERROR", message="Limit is not valid")
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except ValueError as exc:
            raise BoxeCursorError("Cursor is not valid") from exc
    with db_connection() as connection:
        with connection.cursor() as db_cursor:
            db_cursor.execute(
                """
                SELECT
                    s.*,
                    r.id AS last_round_id,
                    r.status AS last_round_status,
                    r.outcome,
                    r.final_payout_amount,
                    r.rows_count,
                    r.difficulty,
                    r.bet_amount,
                    CASE
                        WHEN r.demo_session_id IS NOT NULL THEN 'demo'
                        ELSE pr.wallet_type
                    END AS wallet_source,
                    r.safe_picks_count,
                    r.created_at AS round_created_at,
                    r.closed_at AS round_closed_at
                FROM boxe_sessions s
                JOIN boxe_rounds r ON r.session_id = s.id
                LEFT JOIN platform_rounds pr ON pr.id = r.platform_round_id
                WHERE s.player_id = %s
                  AND r.status IN ('completed_cashout', 'completed_top_row', 'failed_mine', 'expired', 'quarantined')
                ORDER BY r.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (UUID(player_id), limit + 1, offset),
            )
            rows = [dict(row) for row in db_cursor.fetchall()]
    has_next = len(rows) > limit
    items = rows[:limit]
    return {
        "items": [_history_item(row) for row in items],
        "next_cursor": str(offset + limit) if has_next else None,
        "limit": limit,
    }


def _get_session_idempotency_replay(
    *,
    connection,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ik.response_json, ik.request_fingerprint
            FROM boxe_idempotency_keys ik
            JOIN boxe_sessions s ON s.id = ik.session_id
            WHERE s.player_id = %s
              AND ik.operation = %s
              AND ik.idempotency_key = %s
            ORDER BY ik.created_at DESC
            LIMIT 1
            """,
            (UUID(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise repository.BoxeIdempotencyConflict(
                "Same idempotency key used with different payload"
            )
        return dict(row["response_json"])


def _get_round_idempotency_replay(
    *,
    connection,
    player_id: str,
    operation: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ik.response_json, ik.request_fingerprint
            FROM boxe_idempotency_keys ik
            JOIN boxe_rounds r ON r.id = ik.round_id
            WHERE r.player_id = %s
              AND ik.operation = %s
              AND ik.idempotency_key = %s
            ORDER BY ik.created_at DESC
            LIMIT 1
            """,
            (UUID(player_id), operation, idempotency_key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        if row["request_fingerprint"] != request_fingerprint:
            raise repository.BoxeIdempotencyConflict(
                "Same idempotency key used with different payload"
            )
        return dict(row["response_json"])


def _round_start_response(
    *,
    session_id,
    round_row: DictRow | dict | None,
    table_session_id: str | None = None,
    table_session: dict[str, object] | None = None,
    wallet_balance_after_start: str | None = None,
) -> dict[str, object]:
    if round_row is None:
        raise BoxeApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")
    return {
        "session_id": str(session_id),
        "round_id": str(round_row["id"]),
        "multipliers": [str(value) for value in get_multiplier_ladder(rows=int(round_row["rows_count"]), difficulty=str(round_row["difficulty"]))],
        "status": str(round_row["status"]),
        "server_seed_hash": str(round_row["server_seed_hash"]),
        "table_session_id": table_session_id,
        "table_session": table_session,
        "wallet_balance_after_start": wallet_balance_after_start,
    }


def _demo_settlement_payload(demo_session: dict[str, object]) -> dict[str, object]:
    return {
        "wallet_balance_after": str(demo_session["balance_chips"]),
        "ledger_transaction_id": str(demo_session["event_id"]) if demo_session.get("event_id") else None,
        "already_exists": False,
    }


def _raise_demo_wallet_error(exc: Exception) -> None:
    if isinstance(exc, DemoWalletIdempotencyConflictError):
        raise repository.BoxeIdempotencyConflict(
            "Same idempotency key used with different payload"
        ) from exc
    if isinstance(exc, DemoWalletInsufficientBalanceError):
        raise BoxeApiError(
            status_code=422,
            code="INSUFFICIENT_BALANCE",
            message="Insufficient demo balance for bet",
        ) from exc
    raise BoxeApiError(
        status_code=422,
        code="VALIDATION_ERROR",
        message=str(exc) or "Demo wallet validation failed",
    ) from exc


def _session_payload(session: dict[str, object]) -> dict[str, object]:
    return {
        "session_id": str(session["id"]),
        "title_code": session["title_code"],
        "site_code": session["site_code"],
        "status": session["status"],
        "created_at": session["created_at"].isoformat(),
    }


def _round_payload(round_row: dict[str, object]) -> dict[str, object]:
    return {
        "round_id": str(round_row["id"]),
        "status": round_row["status"],
        "rows": round_row["rows_count"],
        "difficulty": round_row["difficulty"],
        "safe_picks_count": round_row["safe_picks_count"],
        "payout_current": str(round_row["payout_current"]),
    }


def _replay_payload(*, round_row: dict[str, object], picks: list[dict[str, object]]) -> dict[str, object]:
    safe_picks = [pick for pick in picks if pick["safe"]]
    final_pick = picks[-1] if picks else None
    terminal = is_terminal(round_row["status"])
    full_reveal = round_row.get("pyramid_full_reveal")
    if full_reveal is None:
        full_reveal = round_row.get("pyramid_full_reveal_json")
    if terminal and full_reveal is None:
        full_reveal = _pyramid_full_reveal(round_row=round_row, picks=picks)
    artifacts = create_fairness_artifacts(
        rows=int(round_row["rows_count"]),
        difficulty=str(round_row["difficulty"]),
        selected_box_indexes=[int(pick["selected_box_index"]) for pick in picks],
        server_seed=str(round_row["server_seed"]),
        client_seed=str(round_row["client_seed"]),
        nonce=int(round_row["nonce"]),
    )
    return {
        "game_code": GAME_CODE,
        "session_id": str(round_row["session_id"]),
        "round_id": str(round_row["id"]),
        "platform_round_id": str(round_row["platform_round_id"]) if round_row["platform_round_id"] else None,
        "title_code": round_row["title_code"],
        "site_code": round_row["site_code"],
        "status": round_row["status"],
        "rows": round_row["rows_count"],
        "difficulty": round_row["difficulty"],
        "bet_amount": str(round_row["bet_amount"]),
        "currency": "CHIP",
        "multiplier_ladder": [
            str(value)
            for value in get_multiplier_ladder(
                rows=int(round_row["rows_count"]),
                difficulty=str(round_row["difficulty"]),
            )
        ],
        "picks": [_pick_payload(pick) for pick in picks],
        "revealed_current_row": _pick_payload(final_pick) if final_pick and not final_pick["safe"] else None,
        "safe_path": [_pick_payload(pick) for pick in safe_picks],
        "outcome": round_row["outcome"],
        "terminal_status": round_row["status"] if terminal else None,
        "multiplier_final": str(round_row["multiplier_current"]),
        "cashout_multiplier": str(round_row["multiplier_current"]) if round_row["outcome"] == "cashout" else None,
        "payout_amount": str(round_row["final_payout_amount"] or Decimal("0")),
        "created_at": round_row["created_at"].isoformat(),
        "closed_at": round_row["closed_at"].isoformat() if round_row["closed_at"] else None,
        "pyramid_full_reveal": full_reveal if terminal else None,
        "pyramid_full_reveal_available": bool(full_reveal) and terminal,
        "replay_version": "boxe-path-snapshot-v1",
        "fairness": {
            "fairness_version": round_row["fairness_version"],
            "server_seed_hash": round_row["server_seed_hash"],
            "client_seed": round_row["client_seed"],
            "nonce": round_row["nonce"],
            "round_path_hash": artifacts["round_path_hash"],
            "outcome_verification": artifacts["round_path_hash"],
            "user_verifiable": False,
        },
    }


def _pick_payload(pick: dict[str, object] | None) -> dict[str, object] | None:
    if pick is None:
        return None
    return {
        "step": pick["step"],
        "row": pick["row_index"],
        "position": pick["selected_box_index"],
        "safe": pick["safe"],
        "multiplier_after": str(pick["multiplier_after"]),
        "payout_after": str(pick["payout_after"]),
    }


def _list_picks(connection, *, round_id: UUID) -> list[dict[str, object]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_picks
            WHERE round_id = %s
            ORDER BY step ASC
            """,
            (round_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def _list_picks_for_rounds(connection, *, round_ids: list[str]) -> dict[str, list[dict[str, object]]]:
    picks_by_round_id: dict[str, list[dict[str, object]]] = {
        round_id: [] for round_id in round_ids
    }
    if not round_ids:
        return picks_by_round_id

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM boxe_picks
            WHERE round_id = ANY(%s::uuid[])
            ORDER BY round_id ASC, step ASC
            """,
            (round_ids,),
        )
        for row in cursor.fetchall():
            pick = dict(row)
            picks_by_round_id.setdefault(str(pick["round_id"]), []).append(pick)
    return picks_by_round_id


def _pyramid_full_reveal(
    *,
    round_row: dict[str, object],
    picks: list[dict[str, object]],
) -> list[dict[str, object]]:
    picked_cells = [
        (int(pick["row_index"]), int(pick["selected_box_index"]))
        for pick in picks
    ]
    return generate_pyramid_full_reveal(
        rows=int(round_row["rows_count"]),
        difficulty=str(round_row["difficulty"]),
        server_seed=str(round_row["server_seed"]),
        client_seed=str(round_row["client_seed"]),
        nonce=int(round_row["nonce"]),
        picked_cells=picked_cells,
        fairness_version=str(round_row.get("fairness_version") or FAIRNESS_VERSION),
    )


def _history_item(row: dict[str, object]) -> dict[str, object]:
    return {
        "game_code": GAME_CODE,
        "session_id": str(row["id"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "last_round_id": str(row["last_round_id"]),
        "status": row["last_round_status"],
        "outcome": row["outcome"],
        "rows": row["rows_count"],
        "difficulty": row["difficulty"],
        "bet_amount": str(row["bet_amount"]),
        "wallet_source": row.get("wallet_source") or "legacy",
        "safe_picks_count": row["safe_picks_count"],
        "created_at": row["round_created_at"].isoformat(),
        "closed_at": row["round_closed_at"].isoformat() if row["round_closed_at"] else None,
        "payout_amount": str(row["final_payout_amount"] or Decimal("0")),
    }


def _next_step_options(current_step: int, rows: int) -> list[dict[str, int]]:
    if current_step >= rows:
        return []
    return [
        {"row": current_step, "position": position}
        for position in range(cells_for_row(current_step, rows))
    ]


def _terminal_outcome(status: BoxeRoundStatus) -> str | None:
    return {
        BoxeRoundStatus.COMPLETED_TOP_ROW: "top_row",
        BoxeRoundStatus.FAILED_MINE: "loss",
        BoxeRoundStatus.EXPIRED: "expired",
        BoxeRoundStatus.QUARANTINED: "quarantined",
        BoxeRoundStatus.COMPLETED_CASHOUT: "cashout",
    }.get(status)


def _ensure_round_owner(round_row: dict[str, object], player_id: str) -> None:
    if str(round_row["player_id"]) != player_id:
        raise BoxeApiError(status_code=403, code="FORBIDDEN", message="Round does not belong to player")


def _validate_title_for_read(
    *,
    title_code: str,
    site_code: str | None = None,
) -> None:
    if title_code == MASTER_TITLE_CODE:
        return
    try:
        title = get_published_title_for_launch(
            site_code=site_code or DEFAULT_SITE_CODE,
            title_code=title_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise BoxeApiError(
            status_code=404,
            code="TITLE_NOT_PUBLISHED",
            message="BOXE title is not published",
        ) from exc
    if title["engine_code"] != GAME_CODE:
        raise BoxeApiError(
            status_code=404,
            code="TITLE_NOT_PUBLISHED",
            message="BOXE title is not published",
        )


def _validate_title_for_launch(*, title_code: str, site_code: str | None = None) -> None:
    if title_code == MASTER_TITLE_CODE:
        raise BoxeApiError(
            status_code=403,
            code="LAUNCH_REJECTED_MASTER",
            message="Master title cannot be launched publicly",
        )
    _validate_title_for_read(title_code=title_code, site_code=site_code)


def _validate_config(*, rows: int, difficulty: str, title_code: str) -> None:
    if rows not in SUPPORTED_ROWS:
        raise BoxeApiError(status_code=400, code="BAD_CONFIG", message="Rows value is not valid")
    if difficulty.strip().lower() not in DIFFICULTIES:
        raise BoxeApiError(status_code=400, code="BAD_CONFIG", message="Difficulty value is not valid")
    if not is_published_configuration_supported(rows=rows, difficulty=difficulty, title_code=title_code):
        raise BoxeApiError(status_code=400, code="BAD_CONFIG", message="BOXE configuration is not enabled")


def _validate_wallet_source(wallet_source: str) -> str:
    normalized = wallet_source.strip().lower()
    if normalized in {"expired_table", "bonus_empty"}:
        return normalized
    if normalized not in SUPPORTED_WALLET_SOURCES:
        raise BoxeApiError(status_code=400, code="INVALID_WALLET_SOURCE", message="Wallet source is not valid")
    return normalized


def _validate_synthetic_money_preconditions(*, wallet_source: str, bet_amount: Decimal) -> None:
    if wallet_source == "expired_table":
        raise BoxeApiError(
            status_code=409,
            code="TABLE_SESSION_EXPIRED",
            message="Table session is expired",
        )
    if wallet_source == "bonus_empty":
        raise BoxeApiError(
            status_code=422,
            code="BONUS_WALLET_EMPTY",
            message="Bonus wallet is empty",
        )
    if bet_amount > Decimal("1000000"):
        raise BoxeApiError(
            status_code=422,
            code="INSUFFICIENT_BALANCE",
            message="Insufficient balance for bet",
        )


def _parse_bet_amount(value: str) -> Decimal:
    try:
        bet = Decimal(value)
    except InvalidOperation as exc:
        raise BoxeApiError(status_code=422, code="INVALID_BET", message="Bet amount is not valid") from exc
    if bet <= 0:
        raise BoxeApiError(status_code=422, code="INVALID_BET", message="Bet amount must be positive")
    return bet.quantize(Decimal("0.000001"))


def _parse_uuid(value: str, label: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise BoxeApiError(status_code=400, code="VALIDATION_ERROR", message=f"{label} is not valid") from exc


def _fingerprint(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
