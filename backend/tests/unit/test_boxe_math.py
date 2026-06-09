from decimal import Decimal

import pytest

from app.modules.games.boxe.math import (
    DIFFICULTIES,
    RTP_TARGET,
    SUPPORTED_ROWS,
    calculate_payout,
    cells_for_row,
    get_all_multiplier_ladders,
    get_multiplier,
    get_multiplier_ladder,
    get_mine_count_for_row,
    get_safe_count_for_row,
    get_theoretical_rtp,
    simulate_top_strategy,
)
from tools.boxe_math_simulator import multiplier_ladder as simulator_ladder
from tools.boxe_math_simulator import simulate as simulator_simulate


@pytest.mark.parametrize(
    ("rows", "difficulty", "step", "expected"),
    [
        (4, "easy", 1, Decimal("1.6333")),
        (4, "hard", 1, Decimal("2.4500")),
        (4, "hard", 4, Decimal("29.4000")),
        (8, "easy", 1, Decimal("1.7640")),
        (8, "easy", 8, Decimal("74.0880")),
        (8, "hard", 8, Decimal("1234.8000")),
    ],
)
def test_boxe_wave6_recalibrated_anchors_match(rows, difficulty, step, expected):
    assert get_multiplier(rows=rows, difficulty=difficulty, step=step) == expected


def test_boxe_ladders_are_complete_and_increasing():
    ladders = get_all_multiplier_ladders()
    assert sorted(ladders) == list(SUPPORTED_ROWS)
    for rows in SUPPORTED_ROWS:
        for difficulty in DIFFICULTIES:
            ladder = get_multiplier_ladder(rows=rows, difficulty=difficulty)
            assert len(ladder) == rows
            assert all(ladder[index] < ladder[index + 1] for index in range(len(ladder) - 1))


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_boxe_safe_counts_preserve_path_and_mine_in_every_row(rows, difficulty):
    for row in range(rows):
        safe_count = get_safe_count_for_row(row=row, rows=rows, difficulty=difficulty)
        mine_count = get_mine_count_for_row(row=row, rows=rows, difficulty=difficulty)
        assert safe_count >= 1
        assert mine_count >= 1
        assert safe_count + mine_count == cells_for_row(row, rows)


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_boxe_theoretical_rtp_is_98_after_ladder_recalibration(rows, difficulty):
    for step in range(1, rows + 1):
        assert abs(
            get_theoretical_rtp(rows=rows, difficulty=difficulty, step=step) - RTP_TARGET
        ) <= Decimal("0.0001")


def test_boxe_payout_uses_backend_decimal_rounding():
    assert calculate_payout(
        bet_amount=Decimal("2.50"),
        rows=4,
        difficulty="hard",
        step=4,
    ) == Decimal("73.50")


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
