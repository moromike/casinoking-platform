from decimal import Decimal

import pytest

from app.modules.games.boxe.math import (
    DIFFICULTIES,
    SUPPORTED_ROWS,
    calculate_payout,
    get_all_multiplier_ladders,
    get_multiplier,
    get_multiplier_ladder,
    simulate_top_strategy,
)
from tools.boxe_math_simulator import multiplier_ladder as simulator_ladder
from tools.boxe_math_simulator import simulate as simulator_simulate


@pytest.mark.parametrize(
    ("rows", "difficulty", "step", "expected"),
    [
        (4, "easy", 1, Decimal("1.37")),
        (4, "hard", 1, Decimal("2.94")),
        (4, "hard", 4, Decimal("36.58")),
        (8, "easy", 1, Decimal("1.76")),
        (8, "easy", 8, Decimal("9.87")),
        (8, "hard", 8, Decimal("548.80")),
    ],
)
def test_boxe_observed_anchors_match(rows, difficulty, step, expected):
    assert get_multiplier(rows=rows, difficulty=difficulty, step=step) == expected


def test_boxe_ladders_are_complete_and_increasing():
    ladders = get_all_multiplier_ladders()
    assert sorted(ladders) == list(SUPPORTED_ROWS)
    for rows in SUPPORTED_ROWS:
        for difficulty in DIFFICULTIES:
            ladder = get_multiplier_ladder(rows=rows, difficulty=difficulty)
            assert len(ladder) == rows
            assert all(ladder[index] < ladder[index + 1] for index in range(len(ladder) - 1))


def test_boxe_payout_uses_backend_decimal_rounding():
    assert calculate_payout(
        bet_amount=Decimal("2.50"),
        rows=4,
        difficulty="hard",
        step=4,
    ) == Decimal("91.45")


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_boxe_ci_sized_rtp_validation(rows, difficulty):
    summary = simulate_top_strategy(rows=rows, difficulty=difficulty, rounds=100_000)
    assert Decimal("0.9750") <= summary.empirical_rtp <= Decimal("0.9850")


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_external_simulator_matches_backend_math(rows, difficulty):
    backend_ladder = get_multiplier_ladder(rows=rows, difficulty=difficulty)
    external_ladder = simulator_ladder(rows, difficulty)
    assert external_ladder == backend_ladder

    backend_summary = simulate_top_strategy(
        rows=rows,
        difficulty=difficulty,
        rounds=10_000,
        seed="fixed-validation",
    )
    external_summary = simulator_simulate(
        rows,
        difficulty,
        Decimal("1.00"),
        10_000,
        "fixed-validation",
    )
    assert external_summary.empirical_rtp == backend_summary.empirical_rtp
    assert external_summary.hit_rate == backend_summary.hit_rate
