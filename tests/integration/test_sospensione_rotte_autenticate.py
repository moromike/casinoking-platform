"""REG-02 — authenticated player routes must not strand a suspended player's money."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from tests.integration.test_mines_reveal_cashout_optional_token import _start_real_round


def _suspend(db_connection, user_id: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("UPDATE users SET status = 'suspended' WHERE id = %s", (user_id,))


@pytest.mark.integration
@pytest.mark.parametrize(
    ("path", "payload", "launch_path", "launch_payload"),
    [
        ("/games/mines/start", {"bet_amount": "1.000000", "grid_size": 9, "mine_count": 1, "wallet_type": "cash"}, None, None),
        ("/games/boxe/start", {"title_code": "boxe001", "rows": 4, "difficulty": "easy", "bet_amount": "1.000000", "wallet_source": "cash"}, "/games/boxe/launch-token", {"game_code": "boxe", "title_code": "boxe001"}),
        ("/games/hi-lo/start", {"title_code": "hilo001", "bet_amount": "1.000000", "wallet_source": "cash"}, "/games/hi-lo/launch-token", {"game_code": "hi_lo", "title_code": "hilo001"}),
        ("/games/manichino/start", {"bet_amount": "1.000000", "wallet_type": "cash"}, "/games/manichino/launch-token", {}),
    ],
    ids=("mines", "boxe", "hi_lo", "manichino"),
)
def test_suspended_player_cannot_open_any_authenticated_game(
    client, create_authenticated_player, auth_headers, db_connection, db_helpers,
    path, payload, launch_path, launch_payload,
) -> None:
    player = create_authenticated_player(prefix="reg02-auth-start")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    active_headers = auth_headers(
        player["access_token"], include_game_launch_token=launch_path is None
    )
    if launch_path is None:
        launch_token = active_headers["X-Game-Launch-Token"]
    else:
        issued = client.post(launch_path, headers=active_headers, json=launch_payload)
        assert issued.status_code == 200, issued.text
        launch_token = str(issued.json()["data"]["game_launch_token"])
    _suspend(db_connection, user_id)

    response = client.post(
        path,
        headers={
            **active_headers,
            "Idempotency-Key": f"reg02-auth-start-{uuid4().hex}",
            "X-Game-Launch-Token": launch_token,
        },
        json=payload,
    )

    assert response.status_code == 403, response.text
    assert db_helpers.get_wallet_balance(user_id) == before


def test_suspended_mines_player_can_reveal_cashout_and_close_access_session(
    client, create_authenticated_player, auth_headers, create_published_mines_variant,
    db_connection, db_helpers
) -> None:
    player = create_authenticated_player(prefix="reg02-auth-close")
    user_id = str(player["user_id"])
    title = create_published_mines_variant(display_name="REG-02 authenticated closure")
    ids = _start_real_round(
        client=client, auth_headers=auth_headers, player=player, title_code=str(title["title_code"])
    )
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    balance_after_open = Decimal(db_helpers.get_wallet_balance(user_id))
    _suspend(db_connection, user_id)

    mines = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(cell for cell in range(9) if cell not in mines)
    reveal = client.post("/games/mines/reveal", headers=headers, json={
        "game_session_id": ids["game_session_id"], "cell_index": safe_cell,
    })
    assert reveal.status_code == 200, reveal.text
    payout = Decimal(reveal.json()["data"]["potential_payout"])

    cashout = client.post("/games/mines/cashout", headers={
        **headers, "Idempotency-Key": f"reg02-auth-cashout-{uuid4().hex}",
    }, json={"game_session_id": ids["game_session_id"]})
    assert cashout.status_code == 200, cashout.text
    assert Decimal(db_helpers.get_wallet_balance(user_id)) == balance_after_open + payout

    close = client.post(f"/access-sessions/{ids['access_session_id']}/close", headers=headers)
    assert close.status_code == 200, close.text
