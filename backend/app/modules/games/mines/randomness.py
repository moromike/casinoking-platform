from hashlib import sha256
import json


def build_server_seed_hash(server_seed: str) -> str:
    return sha256(server_seed.encode("utf-8")).hexdigest()


def generate_board(
    *,
    grid_size: int,
    mine_count: int,
    fairness_version: str,
    server_seed: str,
    nonce: int,
) -> tuple[list[int], str, str]:
    board_input = json.dumps(
        {
            "fairness_version": fairness_version,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "nonce": nonce,
            "server_seed": server_seed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    rng_material = sha256(board_input.encode("utf-8")).hexdigest()
    ranked_positions = sorted(
        (
            sha256(f"{rng_material}:{cell_index}".encode("utf-8")).hexdigest(),
            cell_index,
        )
        for cell_index in range(grid_size)
    )
    positions = sorted(cell_index for _, cell_index in ranked_positions[:mine_count])
    board_hash = sha256(
        json.dumps(
            {
                "fairness_version": fairness_version,
                "grid_size": grid_size,
                "mine_count": mine_count,
                "mine_positions": positions,
                "nonce": nonce,
                "rng_material": rng_material,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return positions, rng_material, board_hash
