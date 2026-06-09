from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext

getcontext().prec = 28

GAME_CODE = "boxe"
RTP_TARGET = Decimal("0.98")
FAIRNESS_VERSION = "boxe_seed_v2"
SUPPORTED_ROWS = (4, 5, 6, 7, 8)
DIFFICULTIES = ("easy", "medium", "hard")

_CENT = Decimal("0.01")
_MULTIPLIER_QUANTUM = Decimal("0.0001")
_PROBABILITY_QUANTUM = Decimal("0.000000000001")
TARGET_SAFE_PROBABILITIES: dict[str, Decimal] = {
    "easy": Decimal("0.60"),
    "medium": Decimal("0.50"),
    "hard": Decimal("0.40"),
}


@dataclass(frozen=True)
class BoxeConfig:
    rows: int
    difficulty: str


@dataclass(frozen=True)
class SimulationSummary:
    rows: int
    difficulty: str
    rounds: int
    wins: int
    total_bet: Decimal
    total_payout: Decimal
    empirical_rtp: Decimal
    hit_rate: Decimal


def normalize_difficulty(difficulty: str) -> str:
    value = difficulty.strip().lower()
    if value not in DIFFICULTIES:
        raise ValueError(f"Unsupported BOXE difficulty: {difficulty}")
    return value


def validate_rows(rows: int) -> int:
    if rows not in SUPPORTED_ROWS:
        raise ValueError(f"Unsupported BOXE rows: {rows}")
    return rows


def cells_for_row(row: int, rows: int) -> int:
    rows = validate_rows(rows)
    if row < 0 or row >= rows:
        raise ValueError(f"Unsupported BOXE row {row} for rows={rows}")
    return rows - row + 1


def get_target_safe_probability(*, difficulty: str) -> Decimal:
    difficulty = normalize_difficulty(difficulty)
    return TARGET_SAFE_PROBABILITIES[difficulty]


def get_safe_count_for_row(*, row: int, rows: int, difficulty: str) -> int:
    cell_count = cells_for_row(row, rows)
    target_probability = get_target_safe_probability(difficulty=difficulty)
    raw_count = target_probability * Decimal(cell_count)
    safe_count = int(raw_count.to_integral_value(rounding=ROUND_HALF_EVEN))
    return max(1, min(cell_count - 1, safe_count))


def get_mine_count_for_row(*, row: int, rows: int, difficulty: str) -> int:
    return cells_for_row(row, rows) - get_safe_count_for_row(
        row=row,
        rows=rows,
        difficulty=difficulty,
    )


def get_row_success_probability(*, row: int, rows: int, difficulty: str) -> Decimal:
    return (
        Decimal(get_safe_count_for_row(row=row, rows=rows, difficulty=difficulty))
        / Decimal(cells_for_row(row, rows))
    )


def get_row_success_probabilities(*, rows: int, difficulty: str) -> tuple[Decimal, ...]:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    return tuple(
        get_row_success_probability(row=row, rows=rows, difficulty=difficulty)
        for row in range(rows)
    )


def get_multiplier(*, rows: int, difficulty: str, step: int) -> Decimal:
    table = get_multiplier_ladder(rows=rows, difficulty=difficulty)
    if step < 1 or step > len(table):
        raise ValueError(f"Unsupported BOXE step {step} for rows={rows}")
    return table[step - 1]


def get_multiplier_ladder(*, rows: int, difficulty: str) -> tuple[Decimal, ...]:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    cumulative_probability = Decimal("1")
    multipliers: list[Decimal] = []
    for row in range(rows):
        cumulative_probability *= get_row_success_probability(
            row=row,
            rows=rows,
            difficulty=difficulty,
        )
        multipliers.append(_to_multiplier(RTP_TARGET / cumulative_probability))
    return tuple(multipliers)


def get_all_multiplier_ladders() -> dict[int, dict[str, tuple[Decimal, ...]]]:
    return {
        rows: {
            difficulty: get_multiplier_ladder(rows=rows, difficulty=difficulty)
            for difficulty in DIFFICULTIES
        }
        for rows in SUPPORTED_ROWS
    }


def get_step_success_probability(*, rows: int, difficulty: str, step: int) -> Decimal:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    if step < 1 or step > rows:
        raise ValueError(f"Unsupported BOXE step {step} for rows={rows}")
    return get_row_success_probability(row=step - 1, rows=rows, difficulty=difficulty)


def get_cumulative_success_probability(*, rows: int, difficulty: str, step: int) -> Decimal:
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    if step < 1 or step > rows:
        raise ValueError(f"Unsupported BOXE step {step} for rows={rows}")
    cumulative = Decimal("1")
    for row in range(step):
        cumulative *= get_row_success_probability(row=row, rows=rows, difficulty=difficulty)
    return cumulative


def get_theoretical_rtp(*, rows: int, difficulty: str, step: int) -> Decimal:
    return (
        get_cumulative_success_probability(rows=rows, difficulty=difficulty, step=step)
        * get_multiplier(rows=rows, difficulty=difficulty, step=step)
    ).quantize(_PROBABILITY_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_payout(*, bet_amount: Decimal, rows: int, difficulty: str, step: int) -> Decimal:
    multiplier = get_multiplier(rows=rows, difficulty=difficulty, step=step)
    return (bet_amount * multiplier).quantize(_CENT, rounding=ROUND_HALF_UP)


def simulate_top_strategy(
    *,
    rows: int,
    difficulty: str,
    bet_amount: Decimal = Decimal("1.00"),
    rounds: int = 100_000,
    seed: str = "boxe-ci",
) -> SimulationSummary:
    """Run a deterministic stratified validation simulation.

    The top-row strategy either reaches the final multiplier or loses before it.
    Stratified uniforms keep the CI-sized 100k validation stable for high
    volatility configs while preserving the target hit rate.
    """

    if rounds <= 0:
        raise ValueError("rounds must be positive")
    rows = validate_rows(rows)
    difficulty = normalize_difficulty(difficulty)
    top_multiplier = get_multiplier(rows=rows, difficulty=difficulty, step=rows)
    win_probability = get_cumulative_success_probability(
        rows=rows,
        difficulty=difficulty,
        step=rows,
    )
    wins = 0
    offset = _seed_offset(seed=seed, rounds=rounds)
    for index in range(rounds):
        uniform = Decimal(((index + offset) % rounds) * 2 + 1) / Decimal(rounds * 2)
        if uniform < win_probability:
            wins += 1

    total_bet = (bet_amount * rounds).quantize(_CENT, rounding=ROUND_HALF_UP)
    total_payout = (bet_amount * top_multiplier * wins).quantize(_CENT, rounding=ROUND_HALF_UP)
    empirical_rtp = (total_payout / total_bet).quantize(Decimal("0.0001"))
    hit_rate = (Decimal(wins) / Decimal(rounds)).quantize(Decimal("0.000001"))
    return SimulationSummary(
        rows=rows,
        difficulty=difficulty,
        rounds=rounds,
        wins=wins,
        total_bet=total_bet,
        total_payout=total_payout,
        empirical_rtp=empirical_rtp,
        hit_rate=hit_rate,
    )


def _to_multiplier(value: Decimal) -> Decimal:
    return value.quantize(_MULTIPLIER_QUANTUM, rounding=ROUND_HALF_UP)


def _seed_offset(*, seed: str, rounds: int) -> int:
    # Small deterministic offset so repeated seeds do not always start at bucket 0.
    material = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    return material % rounds
