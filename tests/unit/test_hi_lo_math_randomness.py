from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.modules.games.hi_lo import fairness, math, randomness


def test_first_step_probabilities_and_multipliers_match_math_spec() -> None:
    expected_rank_slots = {
        1: ("SAME", Decimal(1) / Decimal(13), Decimal("12.7400"), "HIGHER", Decimal(12) / Decimal(13), Decimal("1.0617")),
        2: ("LOWER_OR_SAME", Decimal(2) / Decimal(13), Decimal("6.3700"), "HIGHER_OR_SAME", Decimal(12) / Decimal(13), Decimal("1.0617")),
        3: ("LOWER_OR_SAME", Decimal(3) / Decimal(13), Decimal("4.2467"), "HIGHER_OR_SAME", Decimal(11) / Decimal(13), Decimal("1.1582")),
        4: ("LOWER_OR_SAME", Decimal(4) / Decimal(13), Decimal("3.1850"), "HIGHER_OR_SAME", Decimal(10) / Decimal(13), Decimal("1.2740")),
        5: ("LOWER_OR_SAME", Decimal(5) / Decimal(13), Decimal("2.5480"), "HIGHER_OR_SAME", Decimal(9) / Decimal(13), Decimal("1.4156")),
        6: ("LOWER_OR_SAME", Decimal(6) / Decimal(13), Decimal("2.1233"), "HIGHER_OR_SAME", Decimal(8) / Decimal(13), Decimal("1.5925")),
        7: ("LOWER_OR_SAME", Decimal(7) / Decimal(13), Decimal("1.8200"), "HIGHER_OR_SAME", Decimal(7) / Decimal(13), Decimal("1.8200")),
        8: ("LOWER_OR_SAME", Decimal(8) / Decimal(13), Decimal("1.5925"), "HIGHER_OR_SAME", Decimal(6) / Decimal(13), Decimal("2.1233")),
        9: ("LOWER_OR_SAME", Decimal(9) / Decimal(13), Decimal("1.4156"), "HIGHER_OR_SAME", Decimal(5) / Decimal(13), Decimal("2.5480")),
        10: ("LOWER_OR_SAME", Decimal(10) / Decimal(13), Decimal("1.2740"), "HIGHER_OR_SAME", Decimal(4) / Decimal(13), Decimal("3.1850")),
        11: ("LOWER_OR_SAME", Decimal(11) / Decimal(13), Decimal("1.1582"), "HIGHER_OR_SAME", Decimal(3) / Decimal(13), Decimal("4.2467")),
        12: ("LOWER_OR_SAME", Decimal(12) / Decimal(13), Decimal("1.0617"), "HIGHER_OR_SAME", Decimal(2) / Decimal(13), Decimal("6.3700")),
        13: ("LOWER", Decimal(12) / Decimal(13), Decimal("1.0617"), "SAME", Decimal(1) / Decimal(13), Decimal("12.7400")),
    }

    for rank, (down_label, down_probability, down_multiplier, up_label, up_probability, up_multiplier) in expected_rank_slots.items():
        quotes = {quote.action: quote for quote in math.get_prediction_quotes(current_rank=rank)}
        assert quotes["black"].label == "BLACK"
        assert quotes["black"].probability == Decimal(1) / Decimal(2)
        assert quotes["black"].multiplier == Decimal("1.9600")
        assert quotes["red"].label == "RED"
        assert quotes["red"].probability == Decimal(1) / Decimal(2)
        assert quotes["red"].multiplier == Decimal("1.9600")
        assert quotes["down"].label == down_label
        assert quotes["down"].probability == down_probability
        assert quotes["down"].multiplier == down_multiplier
        assert quotes["up"].label == up_label
        assert quotes["up"].probability == up_probability
        assert quotes["up"].multiplier == up_multiplier


def test_edge_rank_predictions_avoid_guaranteed_buttons() -> None:
    ace = math.Card(rank=1, suit="clubs")
    king = math.Card(rank=13, suit="hearts")
    two = math.Card(rank=2, suit="spades")
    queen = math.Card(rank=12, suit="diamonds")

    assert math.is_prediction_success(current_card=ace, action="down", next_card=ace)
    assert not math.is_prediction_success(current_card=ace, action="down", next_card=two)
    assert math.is_prediction_success(current_card=ace, action="up", next_card=two)
    assert not math.is_prediction_success(current_card=ace, action="up", next_card=ace)

    assert math.is_prediction_success(current_card=king, action="down", next_card=queen)
    assert not math.is_prediction_success(current_card=king, action="down", next_card=king)
    assert math.is_prediction_success(current_card=king, action="up", next_card=king)
    assert not math.is_prediction_success(current_card=king, action="up", next_card=queen)


def test_sequence_multiplier_uses_single_edge_cumulative_rtp_model() -> None:
    cumulative = Decimal(1)
    cumulative *= math.get_action_probability(current_rank=7, action="red")
    assert math.calculate_multiplier(cumulative_success_probability=cumulative) == Decimal("1.9600")

    cumulative *= math.get_action_probability(current_rank=7, action="down")
    assert math.calculate_multiplier(cumulative_success_probability=cumulative) == Decimal("3.6400")
    assert math.calculate_theoretical_rtp(cumulative_success_probability=cumulative) == Decimal("0.980000000000")


def test_active_skip_is_ev_neutral_before_rounding_drift() -> None:
    current_cumulative_probability = Decimal("0.125")
    current_cashout_raw_multiplier = math.calculate_raw_multiplier(
        cumulative_success_probability=current_cumulative_probability,
    )

    for rank in math.RANKS:
        for action in math.PREDICTION_ACTIONS:
            action_probability = math.get_action_probability(current_rank=rank, action=action)
            next_cumulative_probability = current_cumulative_probability * action_probability
            next_raw_multiplier = math.calculate_raw_multiplier(
                cumulative_success_probability=next_cumulative_probability,
            )
            assert (
                abs(action_probability * next_raw_multiplier - current_cashout_raw_multiplier)
                < Decimal("0.000000000000000000000001")
            )


def test_no_hi_lo_specific_max_win_cap_branch_exists() -> None:
    source = Path("backend/app/modules/games/hi_lo/math.py").read_text(encoding="utf-8").lower()

    assert "5000" not in source
    assert "max_win" not in source
    assert "cap" not in source


def test_card_index_round_trip_and_colors() -> None:
    for card_index in range(52):
        card = math.card_from_index(card_index)
        assert math.card_to_index(card) == card_index

    assert math.Card(rank=1, suit="clubs").color == "black"
    assert math.Card(rank=13, suit="spades").color == "black"
    assert math.Card(rank=7, suit="hearts").color == "red"
    assert math.Card(rank=10, suit="diamonds").color == "red"


def test_draw_card_is_deterministic_and_material_changes_by_index() -> None:
    kwargs = {
        "server_seed": "server-seed",
        "client_seed": "client-seed",
        "round_nonce": 17,
        "draw_index": 3,
        "draw_purpose": "prediction_draw",
    }
    first = randomness.draw_card(**kwargs)
    second = randomness.draw_card(**kwargs)
    third = randomness.draw_card(**{**kwargs, "draw_index": 4})

    assert first == second
    assert first.rng_material != third.rng_material
    assert first.digest != third.digest
    assert 0 <= first.card_index < 52


def test_draw_card_smoke_distribution_is_uniform_enough() -> None:
    counts: Counter[int] = Counter()
    sample_size = 52_000
    for draw_index in range(sample_size):
        draw = randomness.draw_card(
            server_seed="uniform-server",
            client_seed="uniform-client",
            round_nonce=91,
            draw_index=draw_index,
            draw_purpose="prediction_draw",
        )
        counts[draw.card_index] += 1

    assert len(counts) == 52
    expected = sample_size / 52
    assert max(abs(count - expected) for count in counts.values()) < expected * 0.15


def test_replacement_model_allows_duplicate_cards_in_stream() -> None:
    cards = [
        randomness.draw_card(
            server_seed="replacement-server",
            client_seed="replacement-client",
            round_nonce=3,
            draw_index=draw_index,
            draw_purpose="active_skip_card",
        ).card_index
        for draw_index in range(53)
    ]

    assert len(set(cards)) < len(cards)


def test_fairness_artifacts_reconstruct_and_verify_draw_sequence() -> None:
    draw_requests = [
        fairness.DrawRequest(draw_index=0, draw_purpose="start_base_card"),
        fairness.DrawRequest(draw_index=1, draw_purpose="prediction_draw"),
        fairness.DrawRequest(draw_index=2, draw_purpose="active_skip_card"),
    ]
    artifacts = fairness.create_fairness_artifacts(
        server_seed="fair-server",
        client_seed="fair-client",
        round_nonce=42,
        draw_requests=draw_requests,
    )

    assert artifacts["game_code"] == "hi_lo"
    assert artifacts["server_seed_hash"] == randomness.build_server_seed_hash("fair-server")
    assert len(artifacts["draws"]) == 3

    verification = fairness.verify_fairness_artifacts(
        artifacts=artifacts,
        server_seed="fair-server",
        client_seed="fair-client",
        round_nonce=42,
        draw_requests=draw_requests,
    )
    assert verification["verified"] is True

    tampered = {**artifacts, "draw_sequence_hash": "not-the-real-hash"}
    tampered_verification = fairness.verify_fairness_artifacts(
        artifacts=tampered,
        server_seed="fair-server",
        client_seed="fair-client",
        round_nonce=42,
        draw_requests=draw_requests,
    )
    assert tampered_verification["verified"] is False
