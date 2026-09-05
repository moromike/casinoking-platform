from __future__ import annotations
import pytest

from uuid import uuid4


def _issue_manichino_launch_token(client, headers: dict[str, str]) -> str:
    """La porta e' comune, ma il gettone deve autorizzare proprio il manichino."""
    response = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["game_launch_token"])


def test_wallet_detail_matches_materialized_snapshot_before_and_after_manichino_start(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-wallet-detail")

    def _wallet_rows() -> dict[str, dict[str, object]]:
        response = client.get(
            "/wallets",
            headers=auth_headers(player["access_token"]),
        )
        assert response.status_code == 200
        return {
            row["wallet_type"]: row
            for row in response.json()["data"]
        }

    def _wallet_detail(wallet_type: str) -> dict[str, object]:
        response = client.get(
            f"/wallets/{wallet_type}",
            headers=auth_headers(player["access_token"]),
        )
        assert response.status_code == 200
        return response.json()["data"]

    initial_rows = _wallet_rows()
    assert _wallet_detail("cash") == initial_rows["cash"]
    assert _wallet_detail("bonus") == initial_rows["bonus"]

    headers = auth_headers(player["access_token"])
    game_launch_token = _issue_manichino_launch_token(client, headers)

    # MAN-03: Mines era solo il mezzo per far scendere il saldo di 5 euro; cio'
    # che si verifica e' la coerenza fra /wallets e /wallets/{type}. Ora il
    # mezzo e' il manichino, e le asserzioni (compresi i saldi attesi) sono
    # identiche. La sessione d'accesso, obbligatoria per Mines, qui e'
    # facoltativa e non serve.
    start_response = client.post(
        "/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"integration-wallet-detail-manichino-start-{uuid4().hex}",
        },
        json={
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200

    cash_detail = _wallet_detail("cash")
    bonus_detail = _wallet_detail("bonus")
    updated_rows = _wallet_rows()

    assert cash_detail == updated_rows["cash"]
    assert bonus_detail == updated_rows["bonus"]
    assert cash_detail["balance_snapshot"] == "995.000000"
    assert bonus_detail["balance_snapshot"] == "0.000000"
    assert db_helpers.get_wallet_balance(str(player["user_id"]), "cash") == "995.000000"
    assert db_helpers.get_wallet_balance(str(player["user_id"]), "bonus") == "0.000000"
