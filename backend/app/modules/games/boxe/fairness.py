from __future__ import annotations

from app.modules.games.boxe.math import FAIRNESS_VERSION
from app.modules.games.boxe.randomness import (
    build_round_path_hash,
    build_server_seed_hash,
    generate_step_outcome,
)

GAME_CODE = "boxe"
RANDOM_SOURCE = "internal_seed_engine"


def create_fairness_artifacts(
    *,
    rows: int,
    difficulty: str,
    selected_box_indexes: list[int],
    server_seed: str,
    client_seed: str,
    nonce: int,
) -> dict[str, object]:
    outcomes = []
    for step, selected_box_index in enumerate(selected_box_indexes, start=1):
        outcome = generate_step_outcome(
            rows=rows,
            difficulty=difficulty,
            step=step,
            selected_box_index=selected_box_index,
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
        )
        outcomes.append(outcome)
        if not outcome.safe:
            break

    return {
        "game_code": GAME_CODE,
        "fairness_version": FAIRNESS_VERSION,
        "random_source": RANDOM_SOURCE,
        "nonce": nonce,
        "server_seed_hash": build_server_seed_hash(server_seed),
        "client_seed": client_seed,
        "round_path_hash": build_round_path_hash(outcomes=outcomes, nonce=nonce),
        "outcomes": [
            {
                "step": outcome.step,
                "selected_box_index": outcome.selected_box_index,
                "safe": outcome.safe,
                "success_probability": str(outcome.success_probability),
                "rng_material": outcome.rng_material,
            }
            for outcome in outcomes
        ],
        "user_verifiable": False,
    }


def verify_fairness_artifacts(
    *,
    artifacts: dict[str, object],
    rows: int,
    difficulty: str,
    selected_box_indexes: list[int],
    server_seed: str,
    client_seed: str,
    nonce: int,
) -> dict[str, object]:
    recomputed = create_fairness_artifacts(
        rows=rows,
        difficulty=difficulty,
        selected_box_indexes=selected_box_indexes,
        server_seed=server_seed,
        client_seed=client_seed,
        nonce=nonce,
    )
    return {
        "server_seed_hash_match": artifacts.get("server_seed_hash")
        == recomputed["server_seed_hash"],
        "round_path_hash_match": artifacts.get("round_path_hash")
        == recomputed["round_path_hash"],
        "verified": artifacts.get("server_seed_hash") == recomputed["server_seed_hash"]
        and artifacts.get("round_path_hash") == recomputed["round_path_hash"],
        "computed": recomputed,
    }
