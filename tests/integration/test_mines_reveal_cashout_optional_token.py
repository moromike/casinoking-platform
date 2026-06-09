"""B1 oracolo: reveal/cashout real funzionano senza X-Game-Launch-Token.

Ownership resta garantita da bearer + user_id nel WHERE di _get_session_for_update.
Demo invariato (token ancora richiesto).
Start invariato (token ancora richiesto).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


def _start_real_round(
    *,
    client,
    auth_headers,
    player,
    title_code: str,
    bet_amount: str = "1.000000",
    grid_size: int = 9,
    mine_count: int = 1,
) -> dict[str, str]:
    """Create access/table sessions and start a real round (token required on start)."""
    headers_with_token = auth_headers(player["access_token"], title_code=title_code)

    access_resp = client.post(
        "/access-sessions",
        headers=headers_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_resp.status_code == 200, access_resp.text
    access_session_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
            "title_code": title_code,
        },
    )
    assert table_resp.status_code == 200, table_resp.text
    table_session_id = table_resp.json()["data"]["id"]

    start_resp = client.post(
        "/games/mines/start",
        headers={
            **headers_with_token,
            "Idempotency-Key": f"opt-token-start-{uuid4().hex}",
        },
        json={
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
            "bet_amount": bet_amount,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    return {
        "access_session_id": access_session_id,
        "table_session_id": table_session_id,
        "game_session_id": game_session_id,
    }


def test_reveal_real_without_launch_token(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
    db_helpers,
) -> None:
    """Real reveal works without X-Game-Launch-Token when bearer + ownership are valid."""
    player = create_authenticated_player(prefix="reveal-no-token")
    published_title = create_published_mines_variant(display_name="Reveal No Token")
    title_code = str(published_title["title_code"])

    ids = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
        title_code=title_code,
    )

    headers_no_token = auth_headers(
        player["access_token"], include_game_launch_token=False
    )

    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(9) if index not in mine_positions)

    reveal_resp = client.post(
        "/games/mines/reveal",
        headers=headers_no_token,
        json={"game_session_id": ids["game_session_id"], "cell_index": safe_cell},
    )
    assert reveal_resp.status_code == 200, reveal_resp.text
    data = reveal_resp.json()["data"]
    assert data["result"] == "safe"  # safe by construction
    assert Decimal(data["potential_payout"]) > Decimal("0")


def test_cashout_real_without_launch_token(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
    db_helpers,
) -> None:
    """Real cashout works without X-Game-Launch-Token when bearer + ownership are valid."""
    player = create_authenticated_player(prefix="cashout-no-token")
    published_title = create_published_mines_variant(display_name="Cashout No Token")
    title_code = str(published_title["title_code"])

    ids = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
        title_code=title_code,
    )

    headers_no_token = auth_headers(
        player["access_token"], include_game_launch_token=False
    )

    # Do one safe reveal first (cashout requires at least one safe reveal).
    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(9) if index not in mine_positions)
    reveal_resp = client.post(
        "/games/mines/reveal",
        headers=headers_no_token,
        json={"game_session_id": ids["game_session_id"], "cell_index": safe_cell},
    )
    assert reveal_resp.status_code == 200, reveal_resp.text
    potential_payout = Decimal(reveal_resp.json()["data"]["potential_payout"])

    balance_before = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))

    cashout_resp = client.post(
        "/games/mines/cashout",
        headers={
            **headers_no_token,
            "Idempotency-Key": f"opt-token-cashout-{uuid4().hex}",
        },
        json={"game_session_id": ids["game_session_id"]},
    )
    assert cashout_resp.status_code == 200, cashout_resp.text
    data = cashout_resp.json()["data"]
    assert data["status"] == "won"
    payout = Decimal(str(data["payout_amount"]))
    assert payout == potential_payout

    balance_after = Decimal(db_helpers.get_wallet_balance(str(player["user_id"])))
    assert balance_after == balance_before + payout
    assert (
        db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash")["drift"]
        == "0.000000"
    )


def test_reveal_real_other_user_session_rejected_without_token(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
    db_helpers,
) -> None:
    """Reveal on another user's session is rejected (403) even without token."""
    player_a = create_authenticated_player(prefix="reveal-owner-a")
    player_b = create_authenticated_player(prefix="reveal-owner-b")
    published_title = create_published_mines_variant(display_name="Reveal Ownership")
    title_code = str(published_title["title_code"])

    ids_a = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player_a,
        title_code=title_code,
    )

    headers_b_no_token = auth_headers(
        player_b["access_token"], include_game_launch_token=False
    )

    mine_positions = set(db_helpers.get_mine_positions(ids_a["game_session_id"]))
    safe_cell = next(index for index in range(9) if index not in mine_positions)

    reveal_resp = client.post(
        "/games/mines/reveal",
        headers=headers_b_no_token,
        json={"game_session_id": ids_a["game_session_id"], "cell_index": safe_cell},
    )
    assert reveal_resp.status_code == 403, reveal_resp.text
    assert "ownership" in reveal_resp.json()["error"]["message"].lower()


def test_cashout_real_other_user_session_rejected_without_token(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
) -> None:
    """Cashout on another user's session is rejected (409) even without token."""
    player_a = create_authenticated_player(prefix="cashout-owner-a")
    player_b = create_authenticated_player(prefix="cashout-owner-b")
    published_title = create_published_mines_variant(display_name="Cashout Ownership")
    title_code = str(published_title["title_code"])

    ids_a = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player_a,
        title_code=title_code,
    )

    headers_b_no_token = auth_headers(
        player_b["access_token"], include_game_launch_token=False
    )

    cashout_resp = client.post(
        "/games/mines/cashout",
        headers={
            **headers_b_no_token,
            "Idempotency-Key": f"opt-token-cashout-b-{uuid4().hex}",
        },
        json={"game_session_id": ids_a["game_session_id"]},
    )
    assert cashout_resp.status_code == 409, cashout_resp.text
    assert "not active" in cashout_resp.json()["error"]["message"].lower()
