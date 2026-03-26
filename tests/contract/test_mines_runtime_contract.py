from __future__ import annotations


def test_mines_config_contract_shape(client) -> None:
    response = client.get("/games/mines/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["game_code"] == "mines"
    assert payload["data"]["supported_grid_sizes"] == [9, 16, 25, 36, 49]
    assert payload["data"]["supported_mine_counts"]["25"][:5] == [1, 2, 3, 4, 5]
    assert payload["data"]["payout_ladders"]["25"]["3"][:3] == [
        "1.0229",
        "1.169",
        "1.3444",
    ]
    assert payload["data"]["payout_runtime_file"].endswith(".json")
    assert payload["data"]["fairness_version"] == "seed_internal_v2"


def test_mines_fairness_current_contract_shape(client) -> None:
    response = client.get("/games/mines/fairness/current")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == {
        "game_code": "mines",
        "fairness_version": "seed_internal_v2",
        "fairness_phase": "B",
        "random_source": "internal_seed_engine",
        "board_hash_persisted": True,
        "server_seed_hash_persisted": True,
        "payout_runtime_file": "CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json",
        "user_verifiable": False,
        "active_server_seed_hash": payload["data"]["active_server_seed_hash"],
        "seed_activated_at": payload["data"]["seed_activated_at"],
    }
    assert len(payload["data"]["active_server_seed_hash"]) == 64
    assert payload["data"]["seed_activated_at"]


def test_mines_fairness_current_never_exposes_plaintext_seed(client) -> None:
    response = client.get("/games/mines/fairness/current")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["user_verifiable"] is False
    assert "server_seed" not in payload
    assert "previous_server_seed" not in payload
    assert "revealed_at" not in payload
    assert "client_seed" not in payload
