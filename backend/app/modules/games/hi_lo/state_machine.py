from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HiLoRoundStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    CASHOUT_PENDING = "cashout_pending"
    COMPLETED_CASHOUT = "completed_cashout"
    FAILED_PREDICTION = "failed_prediction"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


class HiLoTransitionEvent(str, Enum):
    START_ROUND = "start_round"
    PLATFORM_OPEN_SUCCESS = "platform_open_success"
    ACTIVE_SKIP = "active_skip"
    PREDICTION_SUCCESS = "prediction_success"
    PREDICTION_FAILURE = "prediction_failure"
    MANUAL_CASHOUT = "manual_cashout"
    SETTLEMENT_SUCCESS = "settlement_success"
    RECOVERY_EXPIRE = "recovery_expire"
    IRRECOVERABLE_INCONSISTENCY = "irrecoverable_inconsistency"


TERMINAL_STATUSES = frozenset(
    {
        HiLoRoundStatus.COMPLETED_CASHOUT,
        HiLoRoundStatus.FAILED_PREDICTION,
        HiLoRoundStatus.EXPIRED,
        HiLoRoundStatus.QUARANTINED,
    }
)


class HiLoStateTransitionError(RuntimeError):
    def __init__(
        self,
        *,
        from_status: HiLoRoundStatus | None,
        event: HiLoTransitionEvent | str,
        reason: str,
    ) -> None:
        self.from_status = from_status
        self.event = HiLoTransitionEvent(event)
        self.reason = reason
        super().__init__(f"Invalid HI-LO transition {from_status} -> {self.event}: {reason}")


@dataclass(frozen=True)
class HiLoStateTransition:
    from_status: HiLoRoundStatus | None
    event: HiLoTransitionEvent
    to_status: HiLoRoundStatus
    terminal: bool


def is_terminal(status: HiLoRoundStatus | str) -> bool:
    return HiLoRoundStatus(status) in TERMINAL_STATUSES


def transition(
    from_status: HiLoRoundStatus | str | None,
    event: HiLoTransitionEvent | str,
) -> HiLoStateTransition:
    normalized_from = HiLoRoundStatus(from_status) if from_status is not None else None
    normalized_event = HiLoTransitionEvent(event)
    to_status = _TRANSITIONS.get((normalized_from, normalized_event))
    if to_status is None:
        reason = "transition_after_terminal" if normalized_from and is_terminal(normalized_from) else "illegal_transition"
        raise HiLoStateTransitionError(
            from_status=normalized_from,
            event=normalized_event,
            reason=reason,
        )
    return HiLoStateTransition(
        from_status=normalized_from,
        event=normalized_event,
        to_status=to_status,
        terminal=is_terminal(to_status),
    )


def validate_prediction_attempt(*, status: HiLoRoundStatus | str) -> None:
    normalized = HiLoRoundStatus(status)
    if normalized == HiLoRoundStatus.ACTIVE:
        return
    reason = "prediction_after_terminal" if is_terminal(normalized) else "prediction_before_start"
    raise HiLoStateTransitionError(
        from_status=normalized,
        event=HiLoTransitionEvent.PREDICTION_SUCCESS,
        reason=reason,
    )


def validate_skip_attempt(*, status: HiLoRoundStatus | str, active_skip_count: int, active_skip_limit: int) -> None:
    normalized = HiLoRoundStatus(status)
    if normalized != HiLoRoundStatus.ACTIVE:
        reason = "skip_after_terminal" if is_terminal(normalized) else "skip_before_start"
        raise HiLoStateTransitionError(
            from_status=normalized,
            event=HiLoTransitionEvent.ACTIVE_SKIP,
            reason=reason,
        )
    if active_skip_count >= active_skip_limit:
        raise HiLoStateTransitionError(
            from_status=normalized,
            event=HiLoTransitionEvent.ACTIVE_SKIP,
            reason="active_skip_limit_reached",
        )


def validate_cashout_attempt(*, status: HiLoRoundStatus | str, correct_predictions_count: int) -> None:
    normalized = HiLoRoundStatus(status)
    if normalized == HiLoRoundStatus.ACTIVE and correct_predictions_count > 0:
        return
    if is_terminal(normalized):
        reason = "cashout_after_terminal"
    elif correct_predictions_count <= 0:
        reason = "cashout_before_prediction"
    else:
        reason = "cashout_before_start"
    raise HiLoStateTransitionError(
        from_status=normalized,
        event=HiLoTransitionEvent.MANUAL_CASHOUT,
        reason=reason,
    )


_TRANSITIONS: dict[tuple[HiLoRoundStatus | None, HiLoTransitionEvent], HiLoRoundStatus] = {
    (None, HiLoTransitionEvent.START_ROUND): HiLoRoundStatus.CREATED,
    (HiLoRoundStatus.CREATED, HiLoTransitionEvent.PLATFORM_OPEN_SUCCESS): HiLoRoundStatus.ACTIVE,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.ACTIVE_SKIP): HiLoRoundStatus.ACTIVE,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.PREDICTION_SUCCESS): HiLoRoundStatus.ACTIVE,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.PREDICTION_FAILURE): HiLoRoundStatus.FAILED_PREDICTION,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.MANUAL_CASHOUT): HiLoRoundStatus.CASHOUT_PENDING,
    (HiLoRoundStatus.CASHOUT_PENDING, HiLoTransitionEvent.SETTLEMENT_SUCCESS): HiLoRoundStatus.COMPLETED_CASHOUT,
    (HiLoRoundStatus.CREATED, HiLoTransitionEvent.RECOVERY_EXPIRE): HiLoRoundStatus.EXPIRED,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.RECOVERY_EXPIRE): HiLoRoundStatus.EXPIRED,
    (HiLoRoundStatus.CREATED, HiLoTransitionEvent.IRRECOVERABLE_INCONSISTENCY): HiLoRoundStatus.QUARANTINED,
    (HiLoRoundStatus.ACTIVE, HiLoTransitionEvent.IRRECOVERABLE_INCONSISTENCY): HiLoRoundStatus.QUARANTINED,
    (HiLoRoundStatus.CASHOUT_PENDING, HiLoTransitionEvent.IRRECOVERABLE_INCONSISTENCY): HiLoRoundStatus.QUARANTINED,
}
