from decimal import Decimal

from tools.boxe_rtp_verify import (
    EXACT_GATE_TOLERANCE,
    RTP_DISCREPANCY_THRESHOLD,
    verify_all,
    verify_combo,
)


def test_boxe_rtp_verify_covers_all_rows_and_difficulties():
    report = verify_all(importance_rounds=10_000, include_naive=False)

    assert report.exact_gate_pass is True
    assert report.importance_gate_pass is True
    assert len(report.combos) == 15
    assert {(combo.rows, combo.difficulty) for combo in report.combos} == {
        (4, "easy"),
        (4, "medium"),
        (4, "hard"),
        (5, "easy"),
        (5, "medium"),
        (5, "hard"),
        (6, "easy"),
        (6, "medium"),
        (6, "hard"),
        (7, "easy"),
        (7, "medium"),
        (7, "hard"),
        (8, "easy"),
        (8, "medium"),
        (8, "hard"),
    }


def test_boxe_rtp_verify_checks_early_typical_and_top_strategies():
    combo = verify_combo(rows=8, difficulty="hard", importance_rounds=10_000)

    assert [strategy.strategy for strategy in combo.strategies] == ["early", "typical", "top"]
    assert [strategy.cashout_step for strategy in combo.strategies] == [1, 3, 8]
    for strategy in combo.strategies:
        assert abs(Decimal(strategy.exact_rtp) - Decimal("0.98")) <= EXACT_GATE_TOLERANCE
        assert abs(Decimal(strategy.importance_observed_rtp) - Decimal("0.98")) <= Decimal(
            "0.001"
        )
        assert abs(Decimal(strategy.importance_observed_rtp) - Decimal("0.98")) <= (
            RTP_DISCREPANCY_THRESHOLD
        )


def test_boxe_rtp_verify_naive_is_report_only():
    report = verify_all(importance_rounds=10_000, naive_rounds=1_000, include_naive=True)

    assert report.exact_gate_pass is True
    assert report.importance_gate_pass is True
    assert len(report.naive_monte_carlo) == 15
    assert {
        item.report_only_reason for item in report.naive_monte_carlo
    } == {
        "Naive Monte Carlo is informational only; exact and importance gates decide fix/no-fix."
    }
