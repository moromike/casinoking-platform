from app.modules.games.boxe.math import DIFFICULTIES, SUPPORTED_ROWS, get_safe_count_for_row
from app.modules.games.boxe.randomness import (
    derive_boxe_board,
    generate_pyramid_full_reveal,
    generate_step_outcome,
)


def test_boxe_step_outcome_uses_same_board_as_full_reveal():
    outcome = generate_step_outcome(
        rows=8,
        difficulty="hard",
        step=3,
        selected_box_index=2,
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
    )
    reveal = generate_pyramid_full_reveal(
        rows=8,
        difficulty="hard",
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
        picked_cells=[(2, 2)],
    )

    revealed_cell = reveal[2]["cells"][2]
    assert revealed_cell["picked"] is True
    assert revealed_cell["state"] == ("safe" if outcome.safe else "mine")


def test_boxe_derived_board_is_deterministic_for_same_seed_material():
    first = derive_boxe_board(
        rows=8,
        difficulty="hard",
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
    )
    second = derive_boxe_board(
        rows=8,
        difficulty="hard",
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
    )
    assert second == first


def test_boxe_derived_board_preserves_safe_path_and_counts_for_all_configs():
    for rows in SUPPORTED_ROWS:
        for difficulty in DIFFICULTIES:
            board = derive_boxe_board(
                rows=rows,
                difficulty=difficulty,
                server_seed=f"server-{rows}-{difficulty}",
                client_seed=f"client-{rows}-{difficulty}",
                nonce=rows,
            )
            assert len(board) == rows
            for row in board:
                expected_safe_count = get_safe_count_for_row(
                    row=row.row,
                    rows=rows,
                    difficulty=difficulty,
                )
                assert row.safe_count == expected_safe_count
                assert row.mine_count == len(row.cells) - expected_safe_count
                assert row.safe_count >= 1
                assert row.mine_count >= 1
