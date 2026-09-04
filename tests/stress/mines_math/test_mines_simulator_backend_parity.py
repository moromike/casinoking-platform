from decimal import Decimal

from app.modules.games.mines.randomness import generate_board as backend_generate_board
from app.modules.games.mines.runtime import (
    FAIRNESS_VERSION,
    get_multiplier as backend_get_multiplier,
    get_payout_table as backend_get_payout_table,
)
from tools.mines_math_simulator import (
    generate_board as simulator_generate_board,
    get_multiplier as simulator_get_multiplier,
    load_payout_table,
)


def test_mines_simulator_payout_table_matches_backend_runtime():
    simulator_table = load_payout_table()
    backend_table = backend_get_payout_table()

    assert simulator_table.keys() == backend_table.keys()
    for grid_size, mine_map in backend_table.items():
        assert simulator_table[grid_size].keys() == mine_map.keys()
        for mine_count, backend_ladder in mine_map.items():
            assert simulator_table[grid_size][mine_count] == backend_ladder
            for step, expected_multiplier in enumerate(backend_ladder, start=1):
                assert simulator_get_multiplier(
                    grid_size, mine_count, step
                ) == backend_get_multiplier(
                    grid_size=grid_size,
                    mine_count=mine_count,
                    safe_reveals_count=step,
                )
                assert expected_multiplier == Decimal(str(expected_multiplier))


def test_mines_simulator_rng_matches_backend_for_fixed_seeds():
    seeds = ("mines-cert-a", "mines-cert-b", "mines-cert-c")
    configs = ((9, 1), (16, 4), (25, 3), (36, 12), (49, 24))

    for seed_index, seed in enumerate(seeds, start=1):
        for grid_size, mine_count in configs:
            nonce = seed_index * 1000 + grid_size + mine_count
            assert simulator_generate_board(
                grid_size=grid_size,
                mine_count=mine_count,
                fairness_version=FAIRNESS_VERSION,
                server_seed=seed,
                nonce=nonce,
            ) == backend_generate_board(
                grid_size=grid_size,
                mine_count=mine_count,
                fairness_version=FAIRNESS_VERSION,
                server_seed=seed,
                nonce=nonce,
            )
