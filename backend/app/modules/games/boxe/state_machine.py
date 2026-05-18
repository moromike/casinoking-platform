from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import logging

logger = logging.getLogger(__name__)


class BoxeRoundStatus(StrEnum):
    CREATED = "created"
    ACTIVE = "active"
    ROW_REVEALED = "row_revealed"
    CASHOUT_PENDING = "cashout_pending"
    COMPLETED_CASHOUT = "completed_cashout"
    COMPLETED_TOP_ROW = "completed_top_row"
    FAILED_MINE = "failed_mine"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


class BoxeTransitionEvent(StrEnum):
    START_ROUND = "start_round"
    PLATFORM_OPEN_SUCCESS = "platform_open_success"
    SAFE_PICK_NON_TOP_ROW = "safe_pick_non_top_row"
    MINE_PICK = "mine_pick"
    MANUAL_COLLECT = "manual_collect"
    SETTLEMENT_SUCCESS = "settlement_success"
    SAFE_PICK_TOP_ROW = "safe_pick_top_row"
    RECOVERY_AUTO_CASHOUT = "recovery_auto_cashout"
    RECOVERY_EXPIRE_ZERO_SAFE = "recovery_expire_zero_safe"
    IRRECOVERABLE_INCONSISTENCY = "irrecoverable_inconsistency"


TERMINAL_STATUSES = frozenset(
    {
        BoxeRoundStatus.COMPLETED_CASHOUT,
        BoxeRoundStatus.COMPLETED_TOP_ROW,
        BoxeRoundStatus.FAILED_MINE,
        BoxeRoundStatus.EXPIRED,
        BoxeRoundStatus.QUARANTINED,
    }
)

LEGAL_TRANSITIONS: dict[tuple[BoxeRoundStatus | None, BoxeTransitionEvent], BoxeRoundStatus] = {
    (None, BoxeTransitionEvent.START_ROUND): BoxeRoundStatus.CREATED,
    (BoxeRoundStatus.CREATED, BoxeTransitionEvent.PLATFORM_OPEN_SUCCESS): BoxeRoundStatus.ACTIVE,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW): BoxeRoundStatus.ROW_REVEALED,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW): BoxeRoundStatus.ROW_REVEALED,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.MINE_PICK): BoxeRoundStatus.FAILED_MINE,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.MINE_PICK): BoxeRoundStatus.FAILED_MINE,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.MANUAL_COLLECT): BoxeRoundStatus.CASHOUT_PENDING,
    (BoxeRoundStatus.CASHOUT_PENDING, BoxeTransitionEvent.SETTLEMENT_SUCCESS): BoxeRoundStatus.COMPLETED_CASHOUT,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.SAFE_PICK_TOP_ROW): BoxeRoundStatus.COMPLETED_TOP_ROW,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.SAFE_PICK_TOP_ROW): BoxeRoundStatus.COMPLETED_TOP_ROW,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.RECOVERY_AUTO_CASHOUT): BoxeRoundStatus.COMPLETED_CASHOUT,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.RECOVERY_AUTO_CASHOUT): BoxeRoundStatus.COMPLETED_CASHOUT,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.RECOVERY_EXPIRE_ZERO_SAFE): BoxeRoundStatus.EXPIRED,
    (BoxeRoundStatus.CREATED, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY): BoxeRoundStatus.QUARANTINED,
    (BoxeRoundStatus.ACTIVE, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY): BoxeRoundStatus.QUARANTINED,
    (BoxeRoundStatus.ROW_REVEALED, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY): BoxeRoundStatus.QUARANTINED,
    (BoxeRoundStatus.CASHOUT_PENDING, BoxeTransitionEvent.IRRECOVERABLE_INCONSISTENCY): BoxeRoundStatus.QUARANTINED,
}


class BoxeStateTransitionError(ValueError):
    def __init__(
        self,
        *,
        from_status: BoxeRoundStatus | None,
        event: BoxeTransitionEvent,
        reason: str,
    ) -> None:
        self.from_status = from_status
        self.event = event
        self.reason = reason
        super().__init__(
            f"Illegal BOXE transition from {from_status} using {event}: {reason}"
        )


@dataclass(frozen=True)
class BoxeTransition:
    from_status: BoxeRoundStatus | None
    event: BoxeTransitionEvent
    to_status: BoxeRoundStatus
    terminal: bool


def normalize_status(status: BoxeRoundStatus | str | None) -> BoxeRoundStatus | None:
    if status is None:
        return None
    if isinstance(status, BoxeRoundStatus):
        return status
    return BoxeRoundStatus(status)


def normalize_event(event: BoxeTransitionEvent | str) -> BoxeTransitionEvent:
    if isinstance(event, BoxeTransitionEvent):
        return event
    return BoxeTransitionEvent(event)


def is_terminal(status: BoxeRoundStatus | str) -> bool:
    return normalize_status(status) in TERMINAL_STATUSES


def transition(
    from_status: BoxeRoundStatus | str | None,
    event: BoxeTransitionEvent | str,
) -> BoxeTransition:
    normalized_from = normalize_status(from_status)
    normalized_event = normalize_event(event)
    to_status = LEGAL_TRANSITIONS.get((normalized_from, normalized_event))
    if to_status is None:
        _log_illegal_transition(normalized_from, normalized_event)
        raise BoxeStateTransitionError(
            from_status=normalized_from,
            event=normalized_event,
            reason="transition_not_allowed_by_spec",
        )
    return BoxeTransition(
        from_status=normalized_from,
        event=normalized_event,
        to_status=to_status,
        terminal=to_status in TERMINAL_STATUSES,
    )


def transition_to_expired_with_auto_cashout(
    current_status: BoxeRoundStatus | str,
) -> BoxeTransition:
    """Recovery-engine dependency interface for scenario #2.

    The recovery engine is out of scope for WP-BOXE-2B; this function only
    exposes the state transition it must request while settlement remains owned
    by the future recovery/platform workflow.
    """

    return transition(current_status, BoxeTransitionEvent.RECOVERY_AUTO_CASHOUT)


def validate_pick_attempt(
    *,
    status: BoxeRoundStatus | str | None,
    current_step: int,
    requested_step: int,
    same_idempotency_key: bool = False,
) -> None:
    normalized_status = normalize_status(status)
    if normalized_status in {None, BoxeRoundStatus.CREATED}:
        _raise_illegal(normalized_status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, "pick_before_start")
    if normalized_status in TERMINAL_STATUSES:
        _raise_illegal(normalized_status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, "reveal_after_terminal")
    if normalized_status not in {BoxeRoundStatus.ACTIVE, BoxeRoundStatus.ROW_REVEALED}:
        _raise_illegal(normalized_status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, "pick_not_allowed")
    if current_step > 0 and requested_step == current_step and same_idempotency_key:
        return
    if requested_step <= current_step:
        _raise_illegal(normalized_status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, "pick_previous_row")
    if requested_step != current_step + 1:
        _raise_illegal(normalized_status, BoxeTransitionEvent.SAFE_PICK_NON_TOP_ROW, "pick_future_row")


def validate_collect_attempt(
    *,
    status: BoxeRoundStatus | str,
    safe_picks_count: int,
) -> BoxeRoundStatus | None:
    normalized_status = BoxeRoundStatus(status)
    if normalized_status == BoxeRoundStatus.FAILED_MINE:
        return normalized_status
    if normalized_status == BoxeRoundStatus.COMPLETED_TOP_ROW:
        return normalized_status
    if normalized_status in TERMINAL_STATUSES:
        return normalized_status
    if safe_picks_count <= 0:
        _raise_illegal(normalized_status, BoxeTransitionEvent.MANUAL_COLLECT, "collect_before_safe_pick")
    if normalized_status != BoxeRoundStatus.ROW_REVEALED:
        _raise_illegal(normalized_status, BoxeTransitionEvent.MANUAL_COLLECT, "collect_not_allowed")
    return None


def _raise_illegal(
    from_status: BoxeRoundStatus | None,
    event: BoxeTransitionEvent,
    reason: str,
) -> None:
    _log_illegal_transition(from_status, event)
    raise BoxeStateTransitionError(
        from_status=from_status,
        event=event,
        reason=reason,
    )


def _log_illegal_transition(
    from_status: BoxeRoundStatus | None,
    event: BoxeTransitionEvent,
) -> None:
    logger.warning(
        "boxe_illegal_state_transition",
        extra={
            "from_status": from_status.value if from_status else None,
            "event": event.value,
        },
    )
