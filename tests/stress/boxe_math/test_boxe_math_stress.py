import os
from decimal import Decimal

import pytest

from app.modules.games.boxe.math import DIFFICULTIES, SUPPORTED_ROWS, simulate_top_strategy


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_BOXE_STRESS") != "1",
    reason="BOXE stress tests are on-demand; set RUN_BOXE_STRESS=1",
)


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_boxe_stress_rtp(rows, difficulty):
    rounds = int(os.getenv("BOXE_STRESS_ROUNDS", "1000000"))
    summary = simulate_top_strategy(rows=rows, difficulty=difficulty, rounds=rounds)
    assert Decimal("0.9790") <= summary.empirical_rtp <= Decimal("0.9810")
