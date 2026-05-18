from app.modules.games.boxe.fairness import (
    create_fairness_artifacts,
    verify_fairness_artifacts,
)
from app.modules.games.boxe.randomness import generate_step_outcome


def test_boxe_step_outcome_is_deterministic_for_same_seed_material():
    first = generate_step_outcome(
        rows=8,
        difficulty="hard",
        step=3,
        selected_box_index=2,
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
    )
    second = generate_step_outcome(
        rows=8,
        difficulty="hard",
        step=3,
        selected_box_index=2,
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=42,
    )
    assert second == first


def test_boxe_fairness_artifacts_verify_against_recomputed_path():
    artifacts = create_fairness_artifacts(
        rows=6,
        difficulty="medium",
        selected_box_indexes=[0, 1, 1, 2, 0, 0],
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=7,
    )
    verification = verify_fairness_artifacts(
        artifacts=artifacts,
        rows=6,
        difficulty="medium",
        selected_box_indexes=[0, 1, 1, 2, 0, 0],
        server_seed="server-seed",
        client_seed="client-seed",
        nonce=7,
    )
    assert verification["verified"] is True
    assert verification["server_seed_hash_match"] is True
    assert verification["round_path_hash_match"] is True
