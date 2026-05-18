import os
from decimal import Decimal

import pytest

from tools.mines_math_simulator import load_payout_table, simulate


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_MINES_STRESS") != "1",
    reason="Mines stress tests are on-demand; set RUN_MINES_STRESS=1",
)


def _all_supported_configs() -> list[tuple[int, int]]:
    table = load_payout_table()
    return [
        (grid_size, mine_count)
        for grid_size, mine_map in sorted(table.items())
        for mine_count in sorted(mine_map)
    ]


@pytest.mark.parametrize(("grid_size", "mine_count"), _all_supported_configs())
def test_mines_stress_first_safe_cashout_rtp(grid_size, mine_count):
    rounds = int(os.getenv("MINES_STRESS_ROUNDS", "1000000"))
    summary = simulate(
        grid_size=grid_size,
        mine_count=mine_count,
        bet=Decimal("1.000000"),
        rounds=rounds,
        seed=f"mines-stress-{grid_size}-{mine_count}",
        cashout_step=1,
    )
    assert Decimal("0.9790") <= summary.empirical_rtp <= Decimal("0.9810")
