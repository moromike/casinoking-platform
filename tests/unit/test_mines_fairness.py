from __future__ import annotations

from app.modules.games.mines.randomness import build_server_seed_hash, generate_board


def test_seeded_board_generation_is_deterministic() -> None:
    first = generate_board(
        grid_size=25,
        mine_count=3,
        fairness_version="seed_internal_v2",
        server_seed="unit-test-seed",
        nonce=17,
    )
    second = generate_board(
        grid_size=25,
        mine_count=3,
        fairness_version="seed_internal_v2",
        server_seed="unit-test-seed",
        nonce=17,
    )

    assert first == second


def test_seeded_board_generation_changes_when_nonce_changes() -> None:
    first = generate_board(
        grid_size=25,
        mine_count=3,
        fairness_version="seed_internal_v2",
        server_seed="unit-test-seed",
        nonce=17,
    )
    second = generate_board(
        grid_size=25,
        mine_count=3,
        fairness_version="seed_internal_v2",
        server_seed="unit-test-seed",
        nonce=18,
    )

    assert first[1] != second[1]
    assert first[2] != second[2]


def test_server_seed_hash_is_stable() -> None:
    assert build_server_seed_hash("unit-test-seed") == build_server_seed_hash(
        "unit-test-seed"
    )
