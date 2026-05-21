import os

import pytest

from app.modules.games.boxe.math import DIFFICULTIES, SUPPORTED_ROWS
from app.modules.games.boxe.randomness import derive_boxe_board


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_BOXE_STRESS") != "1",
    reason="BOXE stress tests are on-demand; set RUN_BOXE_STRESS=1",
)


@pytest.mark.parametrize("rows", SUPPORTED_ROWS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_boxe_safe_path_invariant_100k_boards(rows, difficulty):
    samples = int(os.getenv("BOXE_SAFE_PATH_STRESS_BOARDS", "100000"))
    for nonce in range(samples):
        board = derive_boxe_board(
            rows=rows,
            difficulty=difficulty,
            server_seed=f"stress-server-{rows}-{difficulty}",
            client_seed=f"stress-client-{rows}-{difficulty}",
            nonce=nonce,
        )
        assert all(row.safe_count >= 1 for row in board)
        assert all(row.mine_count >= 1 for row in board)
