from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28

GAME_CODE = "hi_lo"
FAIRNESS_VERSION = "hi_lo_seed_v1"
RTP_TARGET = Decimal("0.98")
RANKS = tuple(range(1, 14))
SUITS = ("clubs", "spades", "hearts", "diamonds")
BLACK_SUITS = frozenset({"clubs", "spades"})
RED_SUITS = frozenset({"hearts", "diamonds"})
PREDICTION_ACTIONS = ("black", "red", "down", "up")

_CENT = Decimal("0.01")
_MULTIPLIER_QUANTUM = Decimal("0.0001")
_PROBABILITY_QUANTUM = Decimal("0.000000000001")


@dataclass(frozen=True)
class Card:
    rank: int
    suit: str

    @property
    def rank_label(self) -> str:
        return rank_label(self.rank)

    @property
    def color(self) -> str:
        return card_color(self.suit)


@dataclass(frozen=True)
class PredictionQuote:
    action: str
    label: str
    probability: Decimal
    probability_percent: Decimal
    cumulative_probability_after_success: Decimal
    multiplier: Decimal


def rank_label(rank: int) -> str:
    rank = validate_rank(rank)
    labels = {
        1: "A",
        11: "J",
        12: "Q",
        13: "K",
    }
    return labels.get(rank, str(rank))


def validate_rank(rank: int) -> int:
    if rank not in RANKS:
        raise ValueError(f"Unsupported HI-LO rank: {rank}")
    return rank


def validate_suit(suit: str) -> str:
    normalized = suit.strip().lower()
    if normalized not in SUITS:
        raise ValueError(f"Unsupported HI-LO suit: {suit}")
    return normalized


def validate_card(card: Card) -> Card:
    return Card(rank=validate_rank(card.rank), suit=validate_suit(card.suit))


def card_color(suit: str) -> str:
    suit = validate_suit(suit)
    if suit in BLACK_SUITS:
        return "black"
    return "red"


def card_from_index(card_index: int) -> Card:
    if card_index < 0 or card_index >= 52:
        raise ValueError(f"Unsupported HI-LO card index: {card_index}")
    suit = SUITS[card_index // 13]
    rank = (card_index % 13) + 1
    return Card(rank=rank, suit=suit)


def card_to_index(card: Card) -> int:
    card = validate_card(card)
    return SUITS.index(card.suit) * 13 + (card.rank - 1)


def get_action_probability(*, current_rank: int, action: str) -> Decimal:
    current_rank = validate_rank(current_rank)
    normalized_action = normalize_action(action)
    if normalized_action in {"black", "red"}:
        return Decimal(1) / Decimal(2)
    if normalized_action == "down":
        if current_rank == 1:
            return Decimal(1) / Decimal(13)
        if current_rank == 13:
            return Decimal(12) / Decimal(13)
        return Decimal(current_rank) / Decimal(13)
    if current_rank == 13:
        return Decimal(1) / Decimal(13)
    if current_rank == 1:
        return Decimal(12) / Decimal(13)
    return Decimal(14 - current_rank) / Decimal(13)


def get_action_label(*, current_rank: int, action: str) -> str:
    current_rank = validate_rank(current_rank)
    normalized_action = normalize_action(action)
    if normalized_action == "black":
        return "BLACK"
    if normalized_action == "red":
        return "RED"
    if normalized_action == "down":
        if current_rank == 1:
            return "SAME"
        if current_rank == 13:
            return "LOWER"
        return "LOWER_OR_SAME"
    if current_rank == 13:
        return "SAME"
    if current_rank == 1:
        return "HIGHER"
    return "HIGHER_OR_SAME"


def normalize_action(action: str) -> str:
    normalized = action.strip().lower()
    if normalized not in PREDICTION_ACTIONS:
        raise ValueError(f"Unsupported HI-LO prediction action: {action}")
    return normalized


def get_prediction_quotes(
    *,
    current_rank: int,
    current_cumulative_probability: Decimal = Decimal("1"),
) -> tuple[PredictionQuote, ...]:
    current_rank = validate_rank(current_rank)
    current_cumulative_probability = validate_probability(
        current_cumulative_probability,
        field_name="current_cumulative_probability",
    )
    return tuple(
        get_prediction_quote(
            current_rank=current_rank,
            action=action,
            current_cumulative_probability=current_cumulative_probability,
        )
        for action in PREDICTION_ACTIONS
    )


def get_prediction_quote(
    *,
    current_rank: int,
    action: str,
    current_cumulative_probability: Decimal = Decimal("1"),
) -> PredictionQuote:
    current_rank = validate_rank(current_rank)
    normalized_action = normalize_action(action)
    current_cumulative_probability = validate_probability(
        current_cumulative_probability,
        field_name="current_cumulative_probability",
    )
    action_probability = get_action_probability(
        current_rank=current_rank,
        action=normalized_action,
    )
    cumulative_after_success = current_cumulative_probability * action_probability
    return PredictionQuote(
        action=normalized_action,
        label=get_action_label(current_rank=current_rank, action=normalized_action),
        probability=action_probability,
        probability_percent=(action_probability * Decimal(100)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        ),
        cumulative_probability_after_success=cumulative_after_success,
        multiplier=calculate_multiplier(
            cumulative_success_probability=cumulative_after_success,
        ),
    )


def is_prediction_success(*, current_card: Card, action: str, next_card: Card) -> bool:
    current_card = validate_card(current_card)
    next_card = validate_card(next_card)
    normalized_action = normalize_action(action)
    if normalized_action == "black":
        return next_card.color == "black"
    if normalized_action == "red":
        return next_card.color == "red"
    if normalized_action == "down":
        if current_card.rank == 1:
            return next_card.rank == 1
        if current_card.rank == 13:
            return next_card.rank < 13
        return next_card.rank <= current_card.rank
    if current_card.rank == 13:
        return next_card.rank == 13
    if current_card.rank == 1:
        return next_card.rank > 1
    return next_card.rank >= current_card.rank


def calculate_raw_multiplier(*, cumulative_success_probability: Decimal) -> Decimal:
    probability = validate_probability(
        cumulative_success_probability,
        field_name="cumulative_success_probability",
    )
    return RTP_TARGET / probability


def calculate_multiplier(*, cumulative_success_probability: Decimal) -> Decimal:
    return calculate_raw_multiplier(
        cumulative_success_probability=cumulative_success_probability,
    ).quantize(_MULTIPLIER_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_payout(*, bet_amount: Decimal, multiplier: Decimal) -> Decimal:
    if bet_amount <= 0:
        raise ValueError("bet_amount must be positive")
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    return (bet_amount * multiplier).quantize(_CENT, rounding=ROUND_HALF_UP)


def calculate_theoretical_rtp(*, cumulative_success_probability: Decimal) -> Decimal:
    probability = validate_probability(
        cumulative_success_probability,
        field_name="cumulative_success_probability",
    )
    return (probability * calculate_multiplier(cumulative_success_probability=probability)).quantize(
        _PROBABILITY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def validate_probability(value: Decimal, *, field_name: str) -> Decimal:
    probability = Decimal(value)
    if probability <= 0 or probability > 1:
        raise ValueError(f"{field_name} must be in the interval (0, 1]")
    return probability
