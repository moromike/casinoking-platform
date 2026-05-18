from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
from math import exp, log

getcontext().prec = 28

SUPPORTED_ROWS = (4, 5, 6, 7, 8)
DIFFICULTIES = ("easy", "medium", "hard")
RTP_TARGET = Decimal("0.98")
CENT = Decimal("0.01")


@dataclass(frozen=True)
class SimResult:
    wins: int
    total_bet: Decimal
    total_payout: Decimal
    empirical_rtp: Decimal
    hit_rate: Decimal


def multiplier_ladder(rows: int, difficulty: str) -> tuple[Decimal, ...]:
    first = _first_multiplier(rows, difficulty)
    growth = _growth_factor(rows, difficulty)
    return tuple(
        Decimal(str(first * (growth ** (step - 1)))).quantize(CENT, rounding=ROUND_HALF_UP)
        for step in range(1, rows + 1)
    )


def simulate(rows: int, difficulty: str, bet: Decimal, rounds: int, seed: str) -> SimResult:
    ladder = multiplier_ladder(rows, difficulty)
    top_multiplier = ladder[-1]
    win_probability = RTP_TARGET / top_multiplier
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
    print(f"wins={result.wins}")
    print(f"hit_rate={result.hit_rate}")
    print(f"total_bet={result.total_bet}")
    print(f"total_payout={result.total_payout}")
    print(f"empirical_rtp={result.empirical_rtp}")

    if args.round_by_round:
        top_multiplier = ladder[-1]
        win_probability = RTP_TARGET / top_multiplier
        offset = sum((index + 1) * ord(char) for index, char in enumerate(args.seed)) % args.num_rounds
        for index in range(args.num_rounds):
            uniform = Decimal(((index + offset) % args.num_rounds) * 2 + 1) / Decimal(
                args.num_rounds * 2
            )
            won = uniform < win_probability
            payout = args.bet * top_multiplier if won else Decimal("0.00")
            print(f"{index + 1},{'win' if won else 'loss'},{payout.quantize(CENT)}")


def _first_multiplier(rows: int, difficulty: str) -> float:
    row_t = (rows - 4) / 4
    easy_first = _log_lerp(1.37, 1.76, row_t)
    hard_first = easy_first * (2.94 / 1.37)
    return _log_lerp(easy_first, hard_first, {"easy": 0.0, "medium": 0.5, "hard": 1.0}[difficulty])


def _growth_factor(rows: int, difficulty: str) -> float:
    row_t = (rows - 4) / 4
    weight = {"easy": 0.0, "medium": 0.5, "hard": 1.0}[difficulty]
    easy_growth = (9.87 / 1.76) ** (1 / 7)
    hard_growth_r4 = (36.58 / 2.94) ** (1 / 3)
    hard_first_r8 = 1.76 * (2.94 / 1.37)
    hard_growth_r8 = (548.80 / hard_first_r8) ** (1 / 7)
    hard_growth = _log_lerp(hard_growth_r4, hard_growth_r8, row_t)
    return _log_lerp(easy_growth, hard_growth, weight)


def _log_lerp(start: float, end: float, t: float) -> float:
    return exp(log(start) + (log(end) - log(start)) * t)


if __name__ == "__main__":
    main()
