from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext

getcontext().prec = 28

SUPPORTED_ROWS = (4, 5, 6, 7, 8)
DIFFICULTIES = ("easy", "medium", "hard")
RTP_TARGET = Decimal("0.98")
CENT = Decimal("0.01")
MULTIPLIER_QUANTUM = Decimal("0.0001")
TARGET_SAFE_PROBABILITIES = {
    "easy": Decimal("0.60"),
    "medium": Decimal("0.50"),
    "hard": Decimal("0.40"),
}


@dataclass(frozen=True)
class SimResult:
    wins: int
    total_bet: Decimal
    total_payout: Decimal
    empirical_rtp: Decimal
    hit_rate: Decimal


def multiplier_ladder(rows: int, difficulty: str) -> tuple[Decimal, ...]:
    cumulative = Decimal("1")
    values: list[Decimal] = []
    for row in range(rows):
        cumulative *= row_success_probability(rows, difficulty, row)
        values.append((RTP_TARGET / cumulative).quantize(MULTIPLIER_QUANTUM, rounding=ROUND_HALF_UP))
    return tuple(values)


def simulate(rows: int, difficulty: str, bet: Decimal, rounds: int, seed: str) -> SimResult:
    ladder = multiplier_ladder(rows, difficulty)
    top_multiplier = ladder[-1]
    win_probability = cumulative_success_probability(rows, difficulty, rows)
    offset = sum((index + 1) * ord(char) for index, char in enumerate(seed)) % rounds
    wins = 0
    for index in range(rounds):
        uniform = Decimal(((index + offset) % rounds) * 2 + 1) / Decimal(rounds * 2)
        if uniform < win_probability:
            wins += 1
    total_bet = (bet * rounds).quantize(CENT, rounding=ROUND_HALF_UP)
    total_payout = (bet * top_multiplier * wins).quantize(CENT, rounding=ROUND_HALF_UP)
    return SimResult(
        wins=wins,
        total_bet=total_bet,
        total_payout=total_payout,
        empirical_rtp=(total_payout / total_bet).quantize(Decimal("0.0001")),
        hit_rate=(Decimal(wins) / Decimal(rounds)).quantize(Decimal("0.000001")),
    )


def cells_for_row(rows: int, row: int) -> int:
    return rows - row + 1


def safe_count_for_row(rows: int, difficulty: str, row: int) -> int:
    cell_count = cells_for_row(rows, row)
    raw_count = TARGET_SAFE_PROBABILITIES[difficulty] * Decimal(cell_count)
    safe_count = int(raw_count.to_integral_value(rounding=ROUND_HALF_EVEN))
    return max(1, min(cell_count - 1, safe_count))


def row_success_probability(rows: int, difficulty: str, row: int) -> Decimal:
    return Decimal(safe_count_for_row(rows, difficulty, row)) / Decimal(cells_for_row(rows, row))


def cumulative_success_probability(rows: int, difficulty: str, step: int) -> Decimal:
    probability = Decimal("1")
    for row in range(step):
        probability *= row_success_probability(rows, difficulty, row)
    return probability


def main() -> None:
    parser = argparse.ArgumentParser(description="BOXE independent math simulator")
    parser.add_argument("--rows", type=int, choices=SUPPORTED_ROWS, required=True)
    parser.add_argument("--difficulty", choices=DIFFICULTIES, required=True)
    parser.add_argument("--bet", type=Decimal, default=Decimal("1.00"))
    parser.add_argument("--seed", default="boxe-simulator")
    parser.add_argument("--num-rounds", type=int, default=100_000)
    parser.add_argument("--round-by-round", action="store_true")
    args = parser.parse_args()

    ladder = multiplier_ladder(args.rows, args.difficulty)
    result = simulate(args.rows, args.difficulty, args.bet, args.num_rounds, args.seed)
    print(f"rows={args.rows}")
    print(f"difficulty={args.difficulty}")
    print(f"bet={args.bet}")
    print(f"rounds={args.num_rounds}")
    print(f"ladder={','.join(str(value) for value in ladder)}")
    print(
        "safe_counts="
        + ",".join(str(safe_count_for_row(args.rows, args.difficulty, row)) for row in range(args.rows))
    )
    print(
        "row_probabilities="
        + ",".join(str(row_success_probability(args.rows, args.difficulty, row)) for row in range(args.rows))
    )
    print(f"wins={result.wins}")
    print(f"hit_rate={result.hit_rate}")
    print(f"total_bet={result.total_bet}")
    print(f"total_payout={result.total_payout}")
    print(f"empirical_rtp={result.empirical_rtp}")

    if args.round_by_round:
        top_multiplier = ladder[-1]
        win_probability = cumulative_success_probability(args.rows, args.difficulty, args.rows)
        offset = sum((index + 1) * ord(char) for index, char in enumerate(args.seed)) % args.num_rounds
        for index in range(args.num_rounds):
            uniform = Decimal(((index + offset) % args.num_rounds) * 2 + 1) / Decimal(
                args.num_rounds * 2
            )
            won = uniform < win_probability
            payout = args.bet * top_multiplier if won else Decimal("0.00")
            print(f"{index + 1},{'win' if won else 'loss'},{payout.quantize(CENT)}")


if __name__ == "__main__":
    main()
