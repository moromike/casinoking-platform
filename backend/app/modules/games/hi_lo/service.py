from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import UUID, uuid4

from psycopg.rows import DictRow

from app.db.connection import db_connection
from app.modules.games.hi_lo import repository
from app.modules.games.hi_lo.admin_config import (
    DEFAULT_ACTIVE_SKIP_LIMIT,
    get_active_skip_limit,
)
from app.modules.games.hi_lo.fairness import DrawRequest, create_fairness_artifacts
from app.modules.games.hi_lo.math import (
    FAIRNESS_VERSION,
    GAME_CODE,
    Card,
    get_prediction_quote,
    get_prediction_quotes,
    is_prediction_success,
    normalize_action,
)
from app.modules.games.hi_lo.randomness import build_server_seed_hash, draw_card
from app.modules.games.hi_lo.round_gateway import (
    HiLoPlatformIdempotencyConflictError,
    HiLoPlatformInsufficientBalanceError,
    HiLoPlatformValidationError,
    build_cashout_idempotency_key,
    open_round as open_platform_round,
    settle_loss as settle_platform_loss,
    settle_win as settle_platform_win,
)
from app.modules.games.hi_lo.state_machine import (
    HiLoStateTransitionError,
    HiLoTransitionEvent,
    is_terminal,
    validate_cashout_attempt,
    validate_prediction_attempt,
    validate_skip_attempt,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_published_title_for_launch,
)
from app.modules.platform.table_sessions.service import (
    TableSessionNotFoundError,
    get_table_session,
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

DEFAULT_TITLE_CODE = "hilo001"
DEFAULT_SITE_CODE = "casinoking"
DEFAULT_HISTORY_LIMIT = 20
MAX_HISTORY_LIMIT = 100
SUPPORTED_WALLET_SOURCES = {"cash", "bonus", "demo"}


class HiLoApiError(RuntimeError):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class HiLoCursorError(ValueError):
    pass


@dataclass(frozen=True)
class IdempotentResult:
    response: dict[str, object]
    replayed: bool


def get_public_config(*, title_code: str | None = None) -> dict[str, object]:
    resolved_title = title_code or DEFAULT_TITLE_CODE
    _validate_title_for_read(title_code=resolved_title)
    from app.modules.games.hi_lo.admin_config import get_public_admin_config

    presentation_config = get_public_admin_config(title_code=resolved_title)
    active_skip_limit = _active_skip_limit_from_presentation(presentation_config)
    return {
        "game_code": GAME_CODE,
        "title_code": resolved_title,
        "rtp_label": "98%",
        "active_skip_limit": active_skip_limit,
        "actions": ["black", "red", "down", "up"],
        "fairness_version": FAIRNESS_VERSION,
        "copy_refs": {
            "rules": "hi_lo.rules",
            "failure": "hi_lo.failure",
        },
        "presentation_config": presentation_config,
    }


def _active_skip_limit_from_presentation(presentation_config: dict[str, object]) -> int:
    gameplay_config = presentation_config.get("gameplay_config")
    if not isinstance(gameplay_config, dict):
        return DEFAULT_ACTIVE_SKIP_LIMIT
    try:
        return int(gameplay_config.get("active_skip_limit", DEFAULT_ACTIVE_SKIP_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_ACTIVE_SKIP_LIMIT


def start_round(
    *,
    player_id: str,
    title_code: str,
    bet_amount: str,
    wallet_source: str,
    client_seed: str | None,
    idempotency_key: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> IdempotentResult:
    _validate_title_for_launch(title_code=title_code)
    normalized_wallet = _validate_wallet_source(wallet_source)
    if normalized_wallet in {"cash", "bonus"} and table_session_id is None:
        raise HiLoApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="table_session_id is required for HI-LO real play",
        )
    bet = _parse_bet_amount(bet_amount)
    payload_fingerprint = _fingerprint(
        {
            "operation": "start_round",
            "player_id": player_id,
            "title_code": title_code,
            "bet_amount": str(bet),
            "wallet_source": normalized_wallet,
            "client_seed": client_seed,
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        }
    )
    player_uuid = _parse_uuid(player_id, "player_id")
    with db_connection() as connection:
        replay = repository.get_idempotency_result(
            connection,
            player_id=player_uuid,
            operation="start_round",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)

        open_round = repository.get_open_round_for_player_title(
            connection,
            player_id=player_uuid,
            title_code=title_code,
        )
        if open_round is not None:
            raise HiLoApiError(
                status_code=409,
                code="ROUND_ALREADY_ACTIVE",
                message="An active HI-LO round is already open",
            )

        round_id = uuid4()
        normalized_client_seed = client_seed or f"client:{player_id}:{idempotency_key}"
        server_seed = f"hi_lo:{uuid4().hex}:{idempotency_key}"
        server_seed_hash = build_server_seed_hash(server_seed)
        start_draw = draw_card(
            server_seed=server_seed,
            client_seed=normalized_client_seed,
            round_nonce=1,
            draw_index=0,
            draw_purpose="start_card",
        )

        platform_open = None
        demo_session = None
        if normalized_wallet == "demo":
            with connection.cursor() as cursor:
                demo_session = open_demo_session(
                    anonymous_id=player_id,
                    title_code=title_code,
                    cursor=cursor,
                )
                demo_session = debit_for_bet(
                    session_id=str(demo_session["id"]),
                    amount=bet,
                    idempotency_key=f"hi_lo:start:{round_id}:{idempotency_key}",
                    payload={
                        "game_code": GAME_CODE,
                        "round_id": str(round_id),
                        "title_code": title_code,
                    },
                    cursor=cursor,
                )
        else:
            with connection.cursor() as cursor:
                platform_open = open_platform_round(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=str(round_id),
                    idempotency_key=idempotency_key,
                    bet_amount=bet,
                    wallet_type=normalized_wallet,
                    title_code=title_code,
                    site_code=DEFAULT_SITE_CODE,
                    table_session_id=table_session_id,
                    access_session_id=access_session_id,
                )
                repository.create_platform_round(
                    connection,
                    round_id=round_id,
                    player_id=player_uuid,
                    title_code=title_code,
                    site_code=DEFAULT_SITE_CODE,
                    access_session_id=_optional_uuid(access_session_id),
                    wallet_account_id=platform_open.wallet_account_id,
                    wallet_type=normalized_wallet,
                    bet_amount=bet,
                    start_ledger_transaction_id=platform_open.ledger_transaction_id,
                    wallet_balance_after_start=platform_open.wallet_balance_after_start,
                    table_session_id=platform_open.table_session_id,
                    idempotency_key=idempotency_key,
                    request_fingerprint=payload_fingerprint,
                )

        round_row = repository.create_round(
            connection,
            player_id=player_uuid,
            round_id=round_id,
            platform_round_id=round_id if platform_open else None,
            demo_session_id=UUID(str(demo_session["id"])) if demo_session else None,
            access_session_id=_optional_uuid(access_session_id),
            table_session_id=UUID(platform_open.table_session_id) if platform_open else None,
            title_code=title_code,
            site_code=DEFAULT_SITE_CODE,
            wallet_source=normalized_wallet,
            bet_amount=bet,
            current_card=start_draw.card,
            server_seed=server_seed,
            server_seed_hash=server_seed_hash,
            client_seed=normalized_client_seed,
            round_nonce=1,
            start_idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        round_row = repository.apply_transition(
            connection,
            round_id=round_row["id"],
            event=HiLoTransitionEvent.PLATFORM_OPEN_SUCCESS,
        )
        response = _round_response(
            round_row=round_row,
            event="start",
            table_session_id=platform_open.table_session_id if platform_open else None,
            table_session=platform_open.table_session if platform_open else None,
            wallet_balance_after_start=(
                str(platform_open.wallet_balance_after_start)
                if platform_open
                else str(demo_session["balance_chips"])
            ),
        )
        repository.record_action(
            connection,
            round_id=round_row["id"],
            action_type="start",
            drawn_card=start_draw.card,
            draw_index=0,
            draw_purpose="start_card",
            rng_material=start_draw.rng_material,
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        repository.save_idempotency_result(
            connection,
            player_id=player_uuid,
            round_id=round_row["id"],
            operation="start_round",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def predict_round(
    *,
    player_id: str,
    round_id: str,
    action: str,
    idempotency_key: str,
) -> IdempotentResult:
    round_uuid = _parse_uuid(round_id, "round_id")
    player_uuid = _parse_uuid(player_id, "player_id")
    normalized_action = normalize_action(action)
    payload_fingerprint = _fingerprint(
        {
            "operation": "predict",
            "player_id": player_id,
            "round_id": round_id,
            "action": normalized_action,
        }
    )
    with db_connection() as connection:
        replay = repository.get_idempotency_result(
            connection,
            player_id=player_uuid,
            operation="predict",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)

        locked = repository.lock_round(connection, round_id=round_uuid)
        _ensure_round_owner(locked.data, player_id)
        validate_prediction_attempt(status=locked.status)
        previous_card = repository.card_from_round(locked.data)
        draw_index = int(locked.data["current_draw_index"]) + 1
        card_draw = draw_card(
            server_seed=str(locked.data["server_seed"]),
            client_seed=str(locked.data["client_seed"]),
            round_nonce=int(locked.data["round_nonce"]),
            draw_index=draw_index,
            draw_purpose="prediction_card",
        )
        success = is_prediction_success(
            current_card=previous_card,
            action=normalized_action,
            next_card=card_draw.card,
        )
        quote = get_prediction_quote(
            current_rank=previous_card.rank,
            action=normalized_action,
            current_cumulative_probability=Decimal(locked.data["cumulative_success_probability"]),
        )
        updated = repository.update_round_after_prediction(
            connection,
            round_id=round_uuid,
            previous_cumulative_probability=Decimal(locked.data["cumulative_success_probability"]),
            previous_bet_amount=Decimal(locked.data["bet_amount"]),
            previous_card=previous_card,
            prediction_action=normalized_action,
            next_card=card_draw.card,
            draw_index=draw_index,
            success=success,
        )
        settlement = None
        if not success:
            if locked.data["platform_round_id"] is not None:
                with connection.cursor() as cursor:
                    settlement = settle_platform_loss(
                        cursor=cursor,
                        user_id=player_id,
                        round_id=round_id,
                        successful_predictions_count=int(locked.data["correct_predictions_count"]),
                    )
                    repository.close_platform_round(
                        connection,
                        round_id=round_uuid,
                        status="lost",
                        payout_amount=Decimal("0.000000"),
                        settlement_ledger_transaction_id=settlement.ledger_transaction_id,
                    )
            elif locked.data["demo_session_id"] is not None:
                with connection.cursor() as cursor:
                    record_loss(
                        session_id=str(locked.data["demo_session_id"]),
                        idempotency_key=f"hi_lo:loss:{round_id}:{idempotency_key}",
                        payload={
                            "game_code": GAME_CODE,
                            "round_id": round_id,
                            "action": normalized_action,
                        },
                        cursor=cursor,
                    )
        response = _round_response(
            round_row=updated,
            event="prediction",
            prediction={
                "action": normalized_action,
                "label": quote.label,
                "success": success,
                "probability": str(quote.probability),
            },
            previous_card=previous_card,
            drawn_card=card_draw.card,
            settlement=_settlement_payload(settlement),
        )
        repository.record_action(
            connection,
            round_id=round_uuid,
            action_type="prediction",
            previous_card=previous_card,
            drawn_card=card_draw.card,
            draw_index=draw_index,
            draw_purpose="prediction_card",
            rng_material=card_draw.rng_material,
            prediction_action=normalized_action,
            success=success,
            probability=quote.probability,
            multiplier_after=Decimal(updated["multiplier_current"]),
            payout_after=Decimal(updated["payout_current"]),
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        repository.save_idempotency_result(
            connection,
            player_id=player_uuid,
            round_id=round_uuid,
            operation="predict",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def skip_round(
    *,
    player_id: str,
    round_id: str,
    idempotency_key: str,
) -> IdempotentResult:
    round_uuid = _parse_uuid(round_id, "round_id")
    player_uuid = _parse_uuid(player_id, "player_id")
    payload_fingerprint = _fingerprint(
        {
            "operation": "active_skip",
            "player_id": player_id,
            "round_id": round_id,
        }
    )
    with db_connection() as connection:
        replay = repository.get_idempotency_result(
            connection,
            player_id=player_uuid,
            operation="active_skip",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)

        locked = repository.lock_round(connection, round_id=round_uuid)
        _ensure_round_owner(locked.data, player_id)
        active_skip_limit = get_active_skip_limit(title_code=str(locked.data["title_code"]))
        validate_skip_attempt(
            status=locked.status,
            active_skip_count=int(locked.data["active_skip_count"]),
            active_skip_limit=active_skip_limit,
        )
        previous_card = repository.card_from_round(locked.data)
        draw_index = int(locked.data["current_draw_index"]) + 1
        card_draw = draw_card(
            server_seed=str(locked.data["server_seed"]),
            client_seed=str(locked.data["client_seed"]),
            round_nonce=int(locked.data["round_nonce"]),
            draw_index=draw_index,
            draw_purpose="active_skip_card",
        )
        updated = repository.update_round_after_active_skip(
            connection,
            round_id=round_uuid,
            card=card_draw.card,
            draw_index=draw_index,
        )
        response = _round_response(
            round_row=updated,
            event="active_skip",
            active_skip_limit=active_skip_limit,
            previous_card=previous_card,
            drawn_card=card_draw.card,
        )
        repository.record_action(
            connection,
            round_id=round_uuid,
            action_type="active_skip",
            previous_card=previous_card,
            drawn_card=card_draw.card,
            draw_index=draw_index,
            draw_purpose="active_skip_card",
            rng_material=card_draw.rng_material,
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
            multiplier_after=Decimal(updated["multiplier_current"]),
            payout_after=Decimal(updated["payout_current"]),
        )
        repository.save_idempotency_result(
            connection,
            player_id=player_uuid,
            round_id=round_uuid,
            operation="active_skip",
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
    player_uuid = _parse_uuid(player_id, "player_id")
    payload_fingerprint = _fingerprint(
        {
            "operation": "cashout",
            "player_id": player_id,
            "round_id": round_id,
        }
    )
    with db_connection() as connection:
        replay = repository.get_idempotency_result(
            connection,
            player_id=player_uuid,
            operation="cashout",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
        )
        if replay is not None:
            return IdempotentResult(response=dict(replay["response_json"]), replayed=True)

        locked = repository.lock_round(connection, round_id=round_uuid)
        _ensure_round_owner(locked.data, player_id)
        validate_cashout_attempt(
            status=locked.status,
            correct_predictions_count=int(locked.data["correct_predictions_count"]),
        )
        repository.apply_transition(
            connection,
            round_id=round_uuid,
            event=HiLoTransitionEvent.MANUAL_CASHOUT,
        )
        payout = Decimal(locked.data["payout_current"])
        settlement = None
        if locked.data["platform_round_id"] is not None:
            with connection.cursor() as cursor:
                settlement = settle_platform_win(
                    cursor=cursor,
                    user_id=player_id,
                    round_id=round_id,
                    payout_amount=payout,
                    successful_predictions_count=int(locked.data["correct_predictions_count"]),
                    idempotency_key=build_cashout_idempotency_key(
                        user_id=player_id,
                        idempotency_key=idempotency_key,
                    ),
                )
                repository.close_platform_round(
                    connection,
                    round_id=round_uuid,
                    status="won",
                    payout_amount=payout,
                    settlement_ledger_transaction_id=settlement.ledger_transaction_id,
                )
        elif locked.data["demo_session_id"] is not None:
            with connection.cursor() as cursor:
                demo_session = credit_for_win(
                    session_id=str(locked.data["demo_session_id"]),
                    amount=payout,
                    idempotency_key=f"hi_lo:cashout:{round_id}:{idempotency_key}",
                    payload={
                        "game_code": GAME_CODE,
                        "round_id": round_id,
                        "correct_predictions_count": int(locked.data["correct_predictions_count"]),
                    },
                    cursor=cursor,
                )
                settlement = {
                    "wallet_balance_after": str(demo_session["balance_chips"]),
                    "ledger_transaction_id": str(demo_session.get("event_id")),
                    "already_exists": False,
                }
        updated = repository.apply_transition(
            connection,
            round_id=round_uuid,
            event=HiLoTransitionEvent.SETTLEMENT_SUCCESS,
            terminal_reason="manual_cashout",
            outcome="cashout",
            final_payout_amount=payout,
        )
        current_card = repository.card_from_round(updated)
        response = _round_response(
            round_row=updated,
            event="cashout",
            drawn_card=current_card,
            settlement=_settlement_payload(settlement),
        )
        repository.record_action(
            connection,
            round_id=round_uuid,
            action_type="cashout",
            drawn_card=current_card,
            draw_index=int(updated["current_draw_index"]),
            draw_purpose="cashout_no_draw",
            rng_material="cashout_no_draw",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
            multiplier_after=Decimal(updated["multiplier_current"]),
            payout_after=Decimal(updated["payout_current"]),
        )
        repository.save_idempotency_result(
            connection,
            player_id=player_uuid,
            round_id=round_uuid,
            operation="cashout",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_fingerprint,
            response=response,
        )
        return IdempotentResult(response=response, replayed=False)


def get_round_replay(*, player_id: str, round_id: str) -> dict[str, object]:
    round_uuid = _parse_uuid(round_id, "round_id")
    with db_connection() as connection:
        round_row = repository.get_round(connection, round_id=round_uuid)
        if round_row is None:
            raise HiLoApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")
        _ensure_round_owner(round_row, player_id)
        actions = repository.get_actions(connection, round_id=round_uuid)
    return _replay_payload(round_row=round_row, actions=actions, include_server_seed=False)


def get_round_replay_for_admin(*, round_id: str) -> dict[str, object]:
    round_uuid = _parse_uuid(round_id, "round_id")
    with db_connection() as connection:
        round_row = repository.get_round(connection, round_id=round_uuid)
        if round_row is None:
            raise HiLoApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")
        actions = repository.get_actions(connection, round_id=round_uuid)
    return _replay_payload(round_row=round_row, actions=actions, include_server_seed=True)


def get_active_round(
    *,
    player_id: str,
    title_code: str,
    wallet_source: str | None = None,
) -> dict[str, object] | None:
    _validate_title_for_launch(title_code=title_code)
    player_uuid = _parse_uuid(player_id, "player_id")
    normalized_wallet_source = (
        _validate_wallet_source(wallet_source)
        if wallet_source is not None
        else None
    )
    with db_connection() as connection:
        round_row = repository.get_open_round_for_player_title(
            connection,
            player_id=player_uuid,
            title_code=title_code,
            wallet_source=normalized_wallet_source,
        )
    if round_row is None:
        return None

    table_session = None
    if round_row.get("table_session_id") is not None:
        try:
            table_session = get_table_session(
                user_id=player_id,
                table_session_id=str(round_row["table_session_id"]),
            )
        except TableSessionNotFoundError:
            table_session = None

    return _round_response(
        round_row=round_row,
        event="resume",
        active_skip_limit=get_active_skip_limit(title_code=title_code),
        table_session_id=str(round_row["table_session_id"]) if round_row.get("table_session_id") else None,
        table_session=table_session,
    )


def get_session(*, player_id: str, session_id: str) -> dict[str, object]:
    round_uuid = _parse_uuid(session_id, "session_id")
    with db_connection() as connection:
        round_row = repository.get_round(connection, round_id=round_uuid)
        if round_row is None:
            raise HiLoApiError(status_code=404, code="SESSION_NOT_FOUND", message="Session not found")
        _ensure_round_owner(round_row, player_id)
    return _history_item(round_row)


def list_sessions(*, player_id: str, limit: int = DEFAULT_HISTORY_LIMIT, cursor: str | None = None) -> dict[str, object]:
    offset = _parse_cursor(cursor)
    normalized_limit = min(max(1, int(limit)), MAX_HISTORY_LIMIT)
    with db_connection() as connection:
        rows = repository.list_terminal_rounds(
            connection,
            player_id=_parse_uuid(player_id, "player_id"),
            limit=normalized_limit + 1,
            offset=offset,
        )
    has_next = len(rows) > normalized_limit
    items = rows[:normalized_limit]
    return {
        "items": [_history_item(row) for row in items],
        "next_cursor": str(offset + normalized_limit) if has_next else None,
        "limit": normalized_limit,
    }


def _round_response(
    *,
    round_row: DictRow | dict,
    event: str,
    active_skip_limit: int | None = None,
    previous_card: Card | None = None,
    drawn_card: Card | None = None,
    prediction: dict[str, object] | None = None,
    settlement: dict[str, object] | None = None,
    table_session_id: str | None = None,
    table_session: dict[str, object] | None = None,
    wallet_balance_after_start: str | None = None,
) -> dict[str, object]:
    current_card = repository.card_from_round(dict(round_row))
    resolved_active_skip_limit = (
        active_skip_limit
        if active_skip_limit is not None
        else get_active_skip_limit(title_code=str(round_row["title_code"]))
    )
    return {
        "game_code": GAME_CODE,
        "session_id": str(round_row["id"]),
        "round_id": str(round_row["id"]),
        "title_code": str(round_row["title_code"]),
        "site_code": str(round_row["site_code"]),
        "event": event,
        "status": str(round_row["status"]),
        "wallet_source": str(round_row["wallet_source"]),
        "bet_amount": str(round_row["bet_amount"]),
        "current_card": repository.card_payload(current_card),
        "previous_card": repository.card_payload(previous_card) if previous_card else None,
        "drawn_card": repository.card_payload(drawn_card) if drawn_card else None,
        "quotes": _quote_payloads(round_row),
        "correct_predictions_count": int(round_row["correct_predictions_count"]),
        "active_skip_count": int(round_row["active_skip_count"]),
        "active_skip_limit": resolved_active_skip_limit,
        "cumulative_success_probability": str(round_row["cumulative_success_probability"]),
        "multiplier_current": str(round_row["multiplier_current"]),
        "payout_current": str(round_row["payout_current"]),
        "final_payout_amount": str(round_row["final_payout_amount"]) if round_row["final_payout_amount"] is not None else None,
        "outcome": round_row["outcome"],
        "terminal": is_terminal(round_row["status"]),
        "prediction": prediction,
        "settlement": settlement,
        "server_seed_hash": str(round_row["server_seed_hash"]),
        "fairness_version": str(round_row["fairness_version"]),
        "table_session_id": table_session_id or (str(round_row["table_session_id"]) if round_row["table_session_id"] else None),
        "table_session": table_session,
        "wallet_balance_after_start": wallet_balance_after_start,
    }


def _quote_payloads(round_row: DictRow | dict) -> list[dict[str, object]]:
    if is_terminal(round_row["status"]):
        return []
    current_card = repository.card_from_round(dict(round_row))
    return [
        {
            "action": quote.action,
            "label": quote.label,
            "probability": str(quote.probability),
            "probability_percent": str(quote.probability_percent),
            "multiplier": str(quote.multiplier),
            "cumulative_success_probability_after_success": str(
                quote.cumulative_probability_after_success
            ),
        }
        for quote in get_prediction_quotes(
            current_rank=current_card.rank,
            current_cumulative_probability=Decimal(round_row["cumulative_success_probability"]),
        )
    ]


def _replay_payload(
    *,
    round_row: dict[str, object],
    actions: list[dict[str, object]],
    include_server_seed: bool,
) -> dict[str, object]:
    draw_requests = [
        DrawRequest(draw_index=int(action["draw_index"]), draw_purpose=str(action["draw_purpose"]))
        for action in actions
        if str(action["draw_purpose"]) != "cashout_no_draw"
    ]
    artifacts = create_fairness_artifacts(
        server_seed=str(round_row["server_seed"]),
        client_seed=str(round_row["client_seed"]),
        round_nonce=int(round_row["round_nonce"]),
        draw_requests=draw_requests,
    )
    payload = {
        "game_code": GAME_CODE,
        "session_id": str(round_row["id"]),
        "round_id": str(round_row["id"]),
        "platform_round_id": str(round_row["platform_round_id"]) if round_row["platform_round_id"] else None,
        "title_code": round_row["title_code"],
        "site_code": round_row["site_code"],
        "status": round_row["status"],
        "outcome": round_row["outcome"],
        "bet_amount": str(round_row["bet_amount"]),
        "final_payout_amount": str(round_row["final_payout_amount"]) if round_row["final_payout_amount"] is not None else None,
        "server_seed_hash": round_row["server_seed_hash"],
        "client_seed": round_row["client_seed"],
        "fairness_version": round_row["fairness_version"],
        "draw_sequence_hash": artifacts["draw_sequence_hash"],
        "actions": [_action_payload(action) for action in actions],
        "created_at": _iso(round_row["created_at"]),
        "closed_at": _iso(round_row["closed_at"]),
    }
    if include_server_seed:
        payload["server_seed"] = round_row["server_seed"]
    return payload


def _action_payload(action: dict[str, object]) -> dict[str, object]:
    return {
        "action_index": int(action["action_index"]),
        "action_type": action["action_type"],
        "prediction_action": action["prediction_action"],
        "success": action["success"],
        "probability": str(action["probability"]) if action["probability"] is not None else None,
        "multiplier_after": str(action["multiplier_after"]),
        "payout_after": str(action["payout_after"]),
        "previous_card": action["previous_card_json"],
        "drawn_card": action["drawn_card_json"],
        "draw_index": int(action["draw_index"]),
        "draw_purpose": action["draw_purpose"],
        "rng_material": action["rng_material"],
        "created_at": _iso(action["created_at"]),
    }


def _history_item(row: dict[str, object]) -> dict[str, object]:
    return {
        "session_id": str(row["id"]),
        "round_id": str(row["id"]),
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "status": row["status"],
        "wallet_source": row["wallet_source"],
        "outcome": row["outcome"],
        "bet_amount": str(row["bet_amount"]),
        "final_payout_amount": str(row["final_payout_amount"]) if row["final_payout_amount"] is not None else None,
        "correct_predictions_count": int(row["correct_predictions_count"]),
        "created_at": _iso(row["created_at"]),
        "closed_at": _iso(row["closed_at"]),
    }


def _settlement_payload(settlement: object | None) -> dict[str, object] | None:
    if settlement is None:
        return None
    if isinstance(settlement, dict):
        return settlement
    return {
        "wallet_balance_after": str(settlement.wallet_balance_after),
        "ledger_transaction_id": settlement.ledger_transaction_id,
        "already_exists": settlement.already_exists,
    }


def _validate_title_for_read(*, title_code: str) -> None:
    try:
        title = get_published_title_for_launch(site_code=DEFAULT_SITE_CODE, title_code=title_code)
    except CatalogNotFoundError as exc:
        raise HiLoApiError(status_code=404, code="CONFIG_MISSING", message=str(exc)) from exc
    except CatalogValidationError as exc:
        raise HiLoApiError(status_code=422, code="TITLE_NOT_PUBLISHED", message=str(exc)) from exc
    if title["engine_code"] != GAME_CODE:
        raise HiLoApiError(status_code=422, code="VALIDATION_ERROR", message="Title does not belong to HI-LO")


def _validate_title_for_launch(*, title_code: str) -> None:
    if title_code == GAME_CODE:
        raise HiLoApiError(
            status_code=422,
            code="LAUNCH_REJECTED_MASTER",
            message="Launch a concrete HI-LO title, not the master engine",
        )
    _validate_title_for_read(title_code=title_code)


def _validate_wallet_source(wallet_source: str) -> str:
    normalized = wallet_source.strip().lower()
    if normalized not in SUPPORTED_WALLET_SOURCES:
        raise HiLoApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="wallet_source must be demo, cash or bonus",
        )
    return normalized


def _parse_bet_amount(raw_value: str) -> Decimal:
    try:
        bet = Decimal(str(raw_value)).quantize(Decimal("0.000001"))
    except (InvalidOperation, ValueError) as exc:
        raise HiLoApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="bet_amount must be numeric",
        ) from exc
    if bet <= 0:
        raise HiLoApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="bet_amount must be greater than zero",
        )
    return bet


def _parse_uuid(raw_value: str, field_name: str) -> UUID:
    try:
        return UUID(str(raw_value))
    except ValueError as exc:
        raise HiLoApiError(
            status_code=422,
            code="VALIDATION_ERROR",
            message=f"{field_name} is not a valid UUID",
        ) from exc


def _optional_uuid(raw_value: str | None) -> UUID | None:
    return _parse_uuid(raw_value, "uuid") if raw_value else None


def _ensure_round_owner(round_row: dict[str, object], player_id: str) -> None:
    if str(round_row["player_id"]) != player_id:
        raise HiLoApiError(status_code=404, code="ROUND_NOT_FOUND", message="Round not found")


def _parse_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        offset = int(cursor)
    except ValueError as exc:
        raise HiLoCursorError("cursor must be an integer offset") from exc
    if offset < 0:
        raise HiLoCursorError("cursor must be non-negative")
    return offset


def _fingerprint(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
