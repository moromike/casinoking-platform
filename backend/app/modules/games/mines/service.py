from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.games.mines.backoffice_config import is_published_configuration_supported
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesSessionVoidedByOperatorError,
    MinesValidationError,
)
from app.modules.games.mines.fairness import create_fairness_artifacts
from app.modules.games.mines import repository
from app.modules.games.mines.round_gateway import (
    build_cashout_idempotency_key,
    get_existing_cashout_by_key,
    is_open_round_idempotency_violation,
    is_settlement_idempotency_violation,
    open_round,
    settle_round_loss,
    settle_round_win,
)
from app.modules.platform.table_sessions.service import TableSessionStateConflictError
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)
from app.modules.games.mines.runtime import get_multiplier, supports_configuration
from app.modules.games.mines import state_machine

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
    if normalized_wallet_type not in {"cash", "bonus", "demo"}:
        raise MinesValidationError("wallet_type must be demo, cash or bonus")
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

    with db_connection() as connection:
        existing = repository.get_idempotency_result(
            connection,
            player_id=user_id,
            operation="start_round",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )
        if existing is not None:
            return existing

    try:
        with db_connection() as connection:
            fairness_nonce = repository.get_next_fairness_nonce(connection)
            fairness_artifacts = create_fairness_artifacts(
                cursor=connection.cursor(),
                grid_size=grid_size,
                mine_count=mine_count,
                nonce=fairness_nonce,
            )

            session_id = str(uuid4())

            if normalized_wallet_type == "demo":
                demo_session = open_demo_session(
                    cursor=connection.cursor(),
                    anonymous_id=user_id,
                    title_code=normalized_title_code,
                )
                demo_session = debit_for_bet(
                    cursor=connection.cursor(),
                    session_id=str(demo_session["id"]),
                    amount=bet_amount_decimal,
                    idempotency_key=idempotency_key,
                    payload={
                        "game_round_id": session_id,
                        "grid_size": grid_size,
                        "mine_count": mine_count,
                        "title_code": normalized_title_code,
                    },
                )
                repository.create_round(
                    connection,
                    session_id=session_id,
                    user_id=user_id,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    fairness_artifacts=fairness_artifacts,
                    demo_session_id=str(demo_session["id"]),
                    title_code=normalized_title_code,
                    site_code=normalized_site_code,
                    status=SESSION_STATUS_ACTIVE,
                )
                response = {
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
                    "wallet_balance_after": _format_amount(
                        Decimal(demo_session["balance_chips"])
                    ),
                    "ledger_transaction_id": None,
                    "demo_event_id": str(demo_session["event_id"]),
                    "demo_play_session_id": str(demo_session["id"]),
                }
                repository.save_idempotency_result(
                    connection,
                    player_id=user_id,
                    operation="start_round",
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                    response=response,
                    round_id=session_id,
                )
                return response

            round_open_result = open_round(
                cursor=connection.cursor(),
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
                request_fingerprint=request_fingerprint,
            )
            repository.create_round(
                connection,
                session_id=session_id,
                user_id=user_id,
                grid_size=grid_size,
                mine_count=mine_count,
                bet_amount=bet_amount_decimal,
                fairness_artifacts=fairness_artifacts,
                platform_round_id=round_open_result.platform_round_id,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
                status=SESSION_STATUS_ACTIVE,
            )
            response = {
                "game_session_id": session_id,
                "status": SESSION_STATUS_ACTIVE,
                "grid_size": grid_size,
                "mine_count": mine_count,
                "bet_amount": _format_amount(bet_amount_decimal),
                "title_code": normalized_title_code,
                "site_code": normalized_site_code,
                "safe_reveals_count": 0,
                "multiplier_current": _format_multiplier(START_MULTIPLIER),
                "wallet_balance_after": _format_amount(
                    round_open_result.wallet_balance_after_start
                ),
                "ledger_transaction_id": round_open_result.ledger_transaction_id,
                "table_session_id": round_open_result.table_session_id,
                "table_session": round_open_result.table_session,
            }
            repository.save_idempotency_result(
                connection,
                player_id=user_id,
                operation="start_round",
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                response=response,
                round_id=session_id,
            )
            return response
    except psycopg.errors.UniqueViolation as exc:
        if is_open_round_idempotency_violation(exc):
            existing_session = repository.get_existing_session_by_idempotency_outside_tx(
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
    except (DemoWalletInsufficientBalanceError, DemoWalletIdempotencyConflictError, DemoWalletValidationError) as exc:
        if isinstance(exc, DemoWalletInsufficientBalanceError):
            raise MinesInsufficientBalanceError(str(exc)) from exc
        if isinstance(exc, DemoWalletIdempotencyConflictError):
            raise MinesIdempotencyConflictError(str(exc)) from exc
        raise MinesValidationError(str(exc)) from exc


def get_session_for_user(
    *,
    user_id: str,
    session_id: str,
    viewer_role: str = "player",
) -> dict[str, object] | None:
    with db_connection() as connection:
        return repository.get_session_for_user(
            connection,
            user_id=user_id,
            session_id=session_id,
            viewer_role=viewer_role,
        )


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
    decoded_cursor = repository._decode_session_history_cursor(cursor) if cursor else None

    with db_connection() as connection:
        return repository.list_session_history_page(
            connection,
            user_id=user_id,
            limit=normalized_limit,
            decoded_cursor=decoded_cursor,
        )


def list_latest_access_session_history_for_user(
    *,
    user_id: str,
    title_code: str,
    site_code: str,
    limit: int = LATEST_ACCESS_SESSION_HISTORY_LIMIT,
) -> list[dict[str, object]]:
    normalized_limit = max(1, min(limit, LATEST_ACCESS_SESSION_HISTORY_LIMIT))

    with db_connection() as connection:
        return repository.list_latest_access_session_history(
            connection,
            user_id=user_id,
            title_code=title_code,
            site_code=site_code,
            limit=normalized_limit,
        )


def get_session_replay_for_user(*, user_id: str, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        return repository.get_session_replay_for_user(
            connection,
            user_id=user_id,
            session_id=session_id,
        )


def get_session_replay_for_admin(*, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        return repository.get_session_replay_for_admin(
            connection,
            session_id=session_id,
        )


def get_session_fairness_for_user(*, user_id: str, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        return repository.get_session_fairness_for_user(
            connection,
            user_id=user_id,
            session_id=session_id,
        )


def reveal_cell(*, user_id: str, session_id: str, cell_index: int) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (session_id,),
            )
            session = repository.lock_round(
                connection,
                user_id=user_id,
                session_id=session_id,
            )
            if session is None:
                raise MinesGameStateConflictError("Game session is not active for this user")
            state_machine.validate_reveal_attempt(session, cell_index)

            revealed_cells = list(session["revealed_cells_json"])
            mine_positions = set(session["mine_positions_json"])

            if cell_index in mine_positions:
                revealed_cells.append(cell_index)
                if session["demo_session_id"]:
                    recorded = record_loss(
                        cursor=cursor,
                        session_id=str(session["demo_session_id"]),
                        idempotency_key=f"mines:demo:loss:{session_id}",
                        payload={
                            "game_round_id": session_id,
                            "safe_reveals_count": int(session["safe_reveals_count"]),
                        },
                    )
                    repository.update_round_status_to_lost(
                        connection,
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
                        "wallet_balance_after": _format_amount(
                            Decimal(recorded["balance_chips"])
                        ),
                    }
                settle_round_loss(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                )
                repository.update_round_status_to_lost(
                    connection,
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
                if session["demo_session_id"]:
                    credited = credit_for_win(
                        cursor=cursor,
                        session_id=str(session["demo_session_id"]),
                        amount=potential_payout,
                        idempotency_key=f"mines:demo:win:{session_id}:{safe_reveals_count}",
                        payload={
                            "game_round_id": session_id,
                            "safe_reveals_count": safe_reveals_count,
                        },
                    )
                    repository.update_round_status_to_won(
                        connection,
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
                            Decimal(credited["balance_chips"])
                        ),
                    }
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
                repository.update_round_status_to_won(
                    connection,
                    session_id=session_id,
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

            repository.record_safe_reveal(
                connection,
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
    request_fingerprint = f"cashout:{user_id}:{session_id}"
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (session_id,),
                )
                replay = repository.get_idempotency_result(
                    connection,
                    player_id=user_id,
                    operation="cashout",
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                )
                if replay is not None:
                    return replay

                session = repository.lock_round(
                    connection,
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
                        if session["demo_session_id"]:
                            cursor.execute(
                                "SELECT balance_chips FROM demo_play_sessions WHERE id = %s",
                                (str(session["demo_session_id"]),),
                            )
                            bal_row = cursor.fetchone()
                            wallet_balance_after = Decimal(bal_row["balance_chips"]) if bal_row else Decimal("0")
                            response = {
                                "game_session_id": session_id,
                                "status": SESSION_STATUS_WON,
                                "mode": "demo",
                                "payout_amount": _format_amount(Decimal(session["payout_current"])),
                                "wallet_balance_after": _format_amount(wallet_balance_after),
                                "ledger_transaction_id": None,
                                "mine_positions": sorted(repository._normalize_cell_list(session["mine_positions_json"])),
                            }
                            repository.save_idempotency_result(
                                connection,
                                player_id=user_id,
                                operation="cashout",
                                idempotency_key=idempotency_key,
                                request_fingerprint=request_fingerprint,
                                response=response,
                                round_id=session_id,
                            )
                            return response
                        namespaced_idempotency_key = build_cashout_idempotency_key(
                            user_id=user_id,
                            idempotency_key=idempotency_key,
                        )
                        existing_cashout = get_existing_cashout_by_key(
                            cursor=cursor,
                            idempotency_key=namespaced_idempotency_key,
                        )
                        if existing_cashout is not None:
                            if str(existing_cashout["reference_id"]) != session_id:
                                raise MinesIdempotencyConflictError(
                                    "Idempotency key already used with a different payload"
                                )
                            response = _build_cashout_response_from_existing(
                                connection=connection,
                                user_id=user_id,
                                session_id=session_id,
                                cashout_transaction_id=str(existing_cashout["id"]),
                            )
                            repository.save_idempotency_result(
                                connection,
                                player_id=user_id,
                                operation="cashout",
                                idempotency_key=idempotency_key,
                                request_fingerprint=request_fingerprint,
                                response=response,
                                round_id=session_id,
                            )
                            return response
                    raise MinesGameStateConflictError("Game session is not active")
                if session["safe_reveals_count"] <= 0:
                    raise MinesGameStateConflictError(
                        "Cashout is not available before a safe reveal"
                    )

                payout_amount = Decimal(session["payout_current"]).quantize(
                    Decimal("0.000001")
                )

                if session["demo_session_id"]:
                    credited = credit_for_win(
                        cursor=cursor,
                        session_id=str(session["demo_session_id"]),
                        amount=payout_amount,
                        idempotency_key=f"mines:demo:cashout:{session_id}:{idempotency_key}",
                        payload={
                            "game_round_id": session_id,
                            "safe_reveals_count": int(session["safe_reveals_count"]),
                        },
                    )
                    repository.update_round_status_to_won(
                        connection,
                        session_id=session_id,
                        safe_reveals_count=int(session["safe_reveals_count"]),
                        revealed_cells=list(session["revealed_cells_json"]),
                        multiplier_current=session["multiplier_current"],
                        payout_current=payout_amount,
                    )
                    response = {
                        "game_session_id": session_id,
                        "status": SESSION_STATUS_WON,
                        "mode": "demo",
                        "payout_amount": _format_amount(payout_amount),
                        "wallet_balance_after": _format_amount(Decimal(credited["balance_chips"])),
                        "ledger_transaction_id": None,
                        "mine_positions": sorted(repository._normalize_cell_list(session["mine_positions_json"])),
                    }
                    repository.save_idempotency_result(
                        connection,
                        player_id=user_id,
                        operation="cashout",
                        idempotency_key=idempotency_key,
                        request_fingerprint=request_fingerprint,
                        response=response,
                        round_id=session_id,
                    )
                    return response

                namespaced_idempotency_key = build_cashout_idempotency_key(
                    user_id=user_id,
                    idempotency_key=idempotency_key,
                )
                settlement_result = settle_round_win(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    payout_amount=payout_amount,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    idempotency_key=namespaced_idempotency_key,
                )
                repository.update_round_status_to_won(
                    connection,
                    session_id=session_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    revealed_cells=list(session["revealed_cells_json"]),
                    multiplier_current=session["multiplier_current"],
                    payout_current=payout_amount,
                )
                response = {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_WON,
                    "payout_amount": _format_amount(payout_amount),
                    "wallet_balance_after": _format_amount(settlement_result.wallet_balance_after),
                    "ledger_transaction_id": settlement_result.ledger_transaction_id,
                    "mine_positions": sorted(repository._normalize_cell_list(session["mine_positions_json"])),
                }
                repository.save_idempotency_result(
                    connection,
                    player_id=user_id,
                    operation="cashout",
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                    response=response,
                    round_id=session_id,
                )
                return response
    except TableSessionStateConflictError as exc:
        raise MinesGameStateConflictError("Game session is not active") from exc
    except DemoWalletIdempotencyConflictError as exc:
        raise MinesIdempotencyConflictError(str(exc)) from exc
    except psycopg.errors.UniqueViolation as exc:
        if is_settlement_idempotency_violation(exc) or exc.diag.constraint_name == "ledger_transactions_idempotency_key_key":
            with db_connection() as connection:
                with connection.cursor() as cursor:
                    namespaced_idempotency_key = build_cashout_idempotency_key(
                        user_id=user_id,
                        idempotency_key=idempotency_key,
                    )
                    existing_cashout = get_existing_cashout_by_key(
                        cursor=cursor,
                        idempotency_key=namespaced_idempotency_key,
                    )
                    if existing_cashout is not None:
                        if str(existing_cashout["reference_id"]) != session_id:
                            raise MinesIdempotencyConflictError(
                                "Idempotency key already used with a different payload"
                            ) from exc
                        response = _build_cashout_response_from_existing(
                            connection=connection,
                            user_id=user_id,
                            session_id=session_id,
                            cashout_transaction_id=str(existing_cashout["id"]),
                        )
                        repository.save_idempotency_result(
                            connection,
                            player_id=user_id,
                            operation="cashout",
                            idempotency_key=idempotency_key,
                            request_fingerprint=request_fingerprint,
                            response=response,
                            round_id=session_id,
                        )
                        return response
        raise


def session_exists(session_id: str) -> bool:
    with db_connection() as connection:
        return repository.session_exists(connection, session_id)


def session_belongs_to_user(*, session_id: str, user_id: str) -> bool:
    with db_connection() as connection:
        return repository.session_belongs_to_user(
            connection, session_id=session_id, user_id=user_id
        )


def _build_cashout_response_from_existing(
    *,
    connection: psycopg.Connection,
    user_id: str,
    session_id: str,
    cashout_transaction_id: str,
) -> dict[str, object]:
    from app.modules.games.mines.round_gateway import get_cashout_snapshot

    with connection.cursor() as cursor:
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
        "mine_positions": repository.get_closed_round_mine_positions(
            connection,
            user_id=user_id,
            session_id=session_id,
        ),
    }


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


def _parse_bet_amount(raw_value: str) -> Decimal:
    try:
        amount = Decimal(raw_value)
    except InvalidOperation as exc:
        raise MinesValidationError("Bet amount is not valid") from exc
    if amount <= 0:
        raise MinesValidationError("Bet amount must be greater than zero")
    return amount.quantize(Decimal("0.000001"))


def _start_response_from_existing(row: dict[str, object]) -> dict[str, object]:
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
