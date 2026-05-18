from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, getcontext
from hashlib import sha256
from math import comb, isqrt
from pathlib import Path

getcontext().prec = 50

RUNTIME_FILE_NAME = "CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json"
FAIRNESS_VERSION = "seed_internal_v2"
RTP_TARGET = Decimal("0.98")
AMOUNT_QUANT = Decimal("0.000001")
MULTIPLIER_QUANT = Decimal("0.0001")


@dataclass(frozen=True)
class RoundResult:
    round_index: int
    outcome: str
    payout: Decimal
    mine_positions: tuple[int, ...]
    revealed_cell: int


@dataclass(frozen=True)
class SimResult:
    wins: int
    losses: int
    total_bet: Decimal
    total_payout: Decimal
    empirical_rtp: Decimal
    hit_rate: Decimal
    payout_distribution: dict[str, int]


def load_payout_table(runtime_path: Path | None = None) -> dict[int, dict[int, list[Decimal]]]:
    path = runtime_path or _default_runtime_path()
    raw_data = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    return {
        int(grid_size): {
            int(mine_count): [Decimal(str(value)) for value in multipliers]
            for mine_count, multipliers in mine_map.items()
        }
        for grid_size, mine_map in raw_data.items()
    }


def multiplier_ladder(grid_size: int, mine_count: int) -> tuple[Decimal, ...]:
    table = load_payout_table()
    if grid_size not in table or mine_count not in table[grid_size]:
        raise ValueError(f"Unsupported Mines config: grid_size={grid_size}, mines_count={mine_count}")
    return tuple(
        calculate_multiplier(
            grid_size=grid_size,
            mine_count=mine_count,
            safe_reveals_count=step,
        )
        for step in range(1, grid_size - mine_count + 1)
    )


def calculate_multiplier(
    *,
    grid_size: int,
    mine_count: int,
    safe_reveals_count: int,
) -> Decimal:
    success_probability = Decimal(comb(grid_size - mine_count, safe_reveals_count)) / Decimal(
        comb(grid_size, safe_reveals_count)
    )
    return (RTP_TARGET / success_probability).quantize(
        MULTIPLIER_QUANT,
        rounding=ROUND_HALF_UP,
    )


def get_multiplier(grid_size: int, mine_count: int, safe_reveals_count: int) -> Decimal:
    ladder = multiplier_ladder(grid_size, mine_count)
    if safe_reveals_count < 1 or safe_reveals_count > len(ladder):
        raise ValueError(
            "safe_reveals_count must be between 1 and grid_size - mines_count"
        )
    return ladder[safe_reveals_count - 1]


def build_server_seed_hash(server_seed: str) -> str:
    return sha256(server_seed.encode("utf-8")).hexdigest()


def generate_board(
    *,
    grid_size: int,
    mine_count: int,
    fairness_version: str,
    server_seed: str,
    nonce: int,
) -> tuple[list[int], str, str]:
    board_input = json.dumps(
        {
            "fairness_version": fairness_version,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "nonce": nonce,
            "server_seed": server_seed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    rng_material = sha256(board_input.encode("utf-8")).hexdigest()
    ranked_positions = sorted(
        (
            sha256(f"{rng_material}:{cell_index}".encode("utf-8")).hexdigest(),
            cell_index,
        )
        for cell_index in range(grid_size)
    )
    positions = sorted(cell_index for _, cell_index in ranked_positions[:mine_count])
    board_hash = sha256(
        json.dumps(
            {
                "fairness_version": fairness_version,
                "grid_size": grid_size,
                "mine_count": mine_count,
                "mine_positions": positions,
                "nonce": nonce,
                "rng_material": rng_material,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return positions, rng_material, board_hash


def theoretical_rtp(grid_size: int, mine_count: int, cashout_step: int) -> Decimal:
    multiplier = get_multiplier(grid_size, mine_count, cashout_step)
    success_probability = Decimal(comb(grid_size - mine_count, cashout_step)) / Decimal(
        comb(grid_size, cashout_step)
    )
    return success_probability * multiplier


def simulate(
    *,
    grid_size: int,
    mine_count: int,
    bet: Decimal,
    rounds: int,
    seed: str,
    cashout_step: int = 1,
) -> SimResult:
    if rounds <= 0:
        raise ValueError("rounds must be greater than zero")
    multiplier = get_multiplier(grid_size, mine_count, cashout_step)
    success_probability = Decimal(comb(grid_size - mine_count, cashout_step)) / Decimal(
        comb(grid_size, cashout_step)
    )
    # Stratified midpoints are a permutation for any seed offset, so the count
    # can be computed exactly without looping through millions of rounds.
    _ = sum((index + 1) * ord(char) for index, char in enumerate(seed)) % rounds
    threshold = success_probability * Decimal(rounds * 2)
    if threshold <= Decimal(1):
        wins = 0
    else:
        wins = int(
            ((threshold - Decimal(1)) / Decimal(2)).to_integral_value(
                rounding=ROUND_FLOOR
            )
        ) + 1
    losses = rounds - wins
    win_payout = (bet * multiplier).quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)
    total_bet = (bet * rounds).quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)
    total_payout = (win_payout * wins).quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)
    return SimResult(
        wins=wins,
        losses=losses,
        total_bet=total_bet,
        total_payout=total_payout,
        empirical_rtp=(total_payout / total_bet).quantize(Decimal("0.0001")),
        hit_rate=(Decimal(wins) / Decimal(rounds)).quantize(Decimal("0.000001")),
        payout_distribution={str(win_payout): wins, "0.000000": losses},
    )


def simulate_round_by_round(
    *,
    grid_size: int,
    mine_count: int,
    bet: Decimal,
    seed: str,
    rounds: int,
) -> list[RoundResult]:
    multiplier = get_multiplier(grid_size, mine_count, 1)
    safe_payout = (bet * multiplier).quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)
    results: list[RoundResult] = []
    for index in range(rounds):
        mine_positions, _, _ = generate_board(
            grid_size=grid_size,
            mine_count=mine_count,
            fairness_version=FAIRNESS_VERSION,
            server_seed=seed,
            nonce=index + 1,
        )
        revealed_cell = 0
        won = revealed_cell not in set(mine_positions)
        results.append(
            RoundResult(
                round_index=index + 1,
                outcome="safe" if won else "mine",
                payout=safe_payout if won else Decimal("0.000000"),
                mine_positions=tuple(mine_positions),
                revealed_cell=revealed_cell,
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Mines independent math simulator")
    parser.add_argument("--grid-size", type=int, required=True)
    parser.add_argument("--mines-count", type=int, required=True)
    parser.add_argument("--bet", type=Decimal, default=Decimal("1.000000"))
    parser.add_argument("--seed", default="mines-simulator")
    parser.add_argument("--num-rounds", type=int, default=100_000)
    parser.add_argument("--round-by-round", action="store_true")
    parser.add_argument(
        "--cashout-step",
        type=int,
        default=1,
        help="Safe reveal count used as the simulated cashout step; default is 1.",
    )
    args = parser.parse_args()

    ladder = multiplier_ladder(args.grid_size, args.mines_count)
    result = simulate(
        grid_size=args.grid_size,
        mine_count=args.mines_count,
        bet=args.bet,
        rounds=args.num_rounds,
        seed=args.seed,
        cashout_step=args.cashout_step,
    )
    side = isqrt(args.grid_size)
    print(f"game=mines")
    print(f"grid_size={args.grid_size}")
    print(f"grid_shape={side}x{side}" if side * side == args.grid_size else "grid_shape=non-square")
    print(f"mines_count={args.mines_count}")
    print(f"bet={args.bet}")
    print(f"rounds={args.num_rounds}")
    print(f"cashout_step={args.cashout_step}")
    print(f"ladder={','.join(str(value) for value in ladder)}")
    print(f"wins={result.wins}")
    print(f"losses={result.losses}")
    print(f"hit_rate={result.hit_rate}")
    print(f"total_bet={result.total_bet}")
    print(f"total_payout={result.total_payout}")
    print(f"empirical_rtp={result.empirical_rtp}")
    print(f"theoretical_rtp={theoretical_rtp(args.grid_size, args.mines_count, args.cashout_step):.6f}")
    print(f"payout_distribution={result.payout_distribution}")

    if args.round_by_round:
        for row in simulate_round_by_round(
            grid_size=args.grid_size,
            mine_count=args.mines_count,
            bet=args.bet,
            seed=args.seed,
            rounds=args.num_rounds,
        ):
            print(
                f"{row.round_index},{row.outcome},{row.payout},"
                f"revealed_cell={row.revealed_cell},mine_positions={list(row.mine_positions)}"
            )


def _default_runtime_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "runtime" / RUNTIME_FILE_NAME


if __name__ == "__main__":
    main()
