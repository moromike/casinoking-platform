from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesSessionVoidedByOperatorError,
    MinesValidationError,
)


class MinesRoundStatus(str, Enum):
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class MinesTransitionEvent(str, Enum):
    START = "start"
    REVEAL_SAFE = "reveal_safe"
    REVEAL_MINE = "reveal_mine"
    CASHOUT = "cashout"


TERMINAL_STATUSES = frozenset({
    MinesRoundStatus.WON,
    MinesRoundStatus.LOST,
    MinesRoundStatus.CANCELLED,
})


@dataclass(frozen=True)
class MinesTransition:
    new_status: MinesRoundStatus
    terminal: bool


class MinesStateTransitionError(Exception):
    def __init__(self, from_status: MinesRoundStatus, event: MinesTransitionEvent, reason: str) -> None:
        self.from_status = from_status
        self.event = event
        self.reason = reason
        super().__init__(
            f"Invalid transition from {from_status.value} via {event.value}: {reason}"
        )


_LEGAL_TRANSITIONS: dict[MinesRoundStatus, dict[MinesTransitionEvent, MinesTransition]] = {
    MinesRoundStatus.ACTIVE: {
        MinesTransitionEvent.REVEAL_SAFE: MinesTransition(
            new_status=MinesRoundStatus.ACTIVE, terminal=False
        ),
        MinesTransitionEvent.REVEAL_MINE: MinesTransition(
            new_status=MinesRoundStatus.LOST, terminal=True
        ),
        MinesTransitionEvent.CASHOUT: MinesTransition(
            new_status=MinesRoundStatus.WON, terminal=True
        ),
    },
}


def transition(
    from_status: MinesRoundStatus,
    event: MinesTransitionEvent,
) -> MinesTransition:
    if from_status in TERMINAL_STATUSES:
        raise MinesStateTransitionError(
            from_status, event, "round is already in a terminal state"
        )
    transitions = _LEGAL_TRANSITIONS.get(from_status, {})
    if event not in transitions:
        raise MinesStateTransitionError(
            from_status, event, f"event {event.value} is not valid from {from_status.value}"
        )
    return transitions[event]


def is_terminal(status: MinesRoundStatus) -> bool:
    return status in TERMINAL_STATUSES


def validate_reveal_attempt(
    session: dict[str, object],
    cell_index: int,
) -> None:
    status = MinesRoundStatus(session["status"])
    if status == MinesRoundStatus.CANCELLED:
        raise MinesSessionVoidedByOperatorError("Game session was closed by an operator")
    if status != MinesRoundStatus.ACTIVE:
        raise MinesGameStateConflictError("Game session is not active")
    grid_size = int(session["grid_size"])
    if cell_index < 0 or cell_index >= grid_size:
        raise MinesValidationError("Cell index is not valid")
    revealed_cells = list(session["revealed_cells_json"])
    if cell_index in revealed_cells:
        raise MinesGameStateConflictError("Cell already revealed")


def validate_cashout_attempt(session: dict[str, object]) -> None:
    status = MinesRoundStatus(session["status"])
    if status == MinesRoundStatus.CANCELLED:
        raise MinesSessionVoidedByOperatorError("Game session was closed by an operator")
    if status != MinesRoundStatus.ACTIVE:
        raise MinesGameStateConflictError("Game session is not active")
    safe_reveals_count = int(session["safe_reveals_count"])
    if safe_reveals_count <= 0:
        raise MinesGameStateConflictError(
            "Cashout is not available before a safe reveal"
        )
