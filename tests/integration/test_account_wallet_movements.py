from __future__ import annotations

from decimal import Decimal
from urllib.parse import quote
from uuid import uuid4


def test_player_wallet_movements_expose_signed_amount_and_balance_after(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-account-movements-admin")
    player = create_authenticated_player(prefix="integration-account-movements")
    player_headers = auth_headers(
        player["access_token"],
        include_game_launch_token=False,
    )
    admin_headers = auth_headers(
        admin_user["access_token"],
        include_game_launch_token=False,
    )

    bonus_response = client.post(
        f"/admin/users/{player['user_id']}/bonus-grants",
        headers={
            **admin_headers,
            "Idempotency-Key": f"account-movements-bonus-{uuid4()}",
        },
        json={
            "amount": "50.000000",
            "reason": "account movements test bonus",
        },
    )
    assert bonus_response.status_code == 200, bonus_response.text

    debit_response = client.post(
        f"/admin/users/{player['user_id']}/adjustments",
        headers={
            **admin_headers,
            "Idempotency-Key": f"account-movements-debit-{uuid4()}",
        },
        json={
            "wallet_type": "cash",
            "direction": "debit",
            "amount": "10.000000",
            "reason": "account_movements_test_debit",
        },
    )
    assert debit_response.status_code == 200, debit_response.text

    response = client.get(
        "/account/wallet-movements?limit=10",
        headers=player_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["limit"] == 10

    movements = body["data"]
    movement_by_type_wallet = {
        (movement["transaction_type"], movement["wallet_type"]): movement
        for movement in movements
    }

    assert movement_by_type_wallet[("signup_credit", "cash")]["amount"] == "1000.000000"
    assert movement_by_type_wallet[("signup_credit", "cash")]["balance_after"] == "1000.000000"
    assert movement_by_type_wallet[("signup_credit", "cash")]["direction"] == "credit"

    assert movement_by_type_wallet[("admin_adjustment", "cash")]["amount"] == "-10.000000"
    assert movement_by_type_wallet[("admin_adjustment", "cash")]["balance_after"] == "990.000000"
    assert movement_by_type_wallet[("admin_adjustment", "cash")]["direction"] == "debit"

    assert movement_by_type_wallet[("bonus_grant", "bonus")]["amount"] == "50.000000"
    assert movement_by_type_wallet[("bonus_grant", "bonus")]["balance_after"] == "50.000000"
    assert movement_by_type_wallet[("bonus_grant", "bonus")]["direction"] == "credit"

    assert "idempotency_key" not in movements[0]


def test_player_wallet_movements_are_cursor_paginated(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-account-cursor-admin")
    player = create_authenticated_player(prefix="integration-account-cursor")
    player_headers = auth_headers(
        player["access_token"],
        include_game_launch_token=False,
    )
    admin_headers = auth_headers(
        admin_user["access_token"],
        include_game_launch_token=False,
    )

    for index in range(2):
        response = client.post(
            f"/admin/users/{player['user_id']}/adjustments",
            headers={
                **admin_headers,
                "Idempotency-Key": f"account-cursor-{index}-{uuid4()}",
            },
            json={
                "wallet_type": "cash",
                "direction": "credit",
                "amount": "1.000000",
                "reason": "account_cursor_test_credit",
            },
        )
        assert response.status_code == 200, response.text

    first_page = client.get(
        "/account/wallet-movements?limit=1",
        headers=player_headers,
    )
    assert first_page.status_code == 200, first_page.text
    first_body = first_page.json()
    assert len(first_body["data"]) == 1
    assert first_body["meta"]["next_cursor"]

    second_page = client.get(
        f"/account/wallet-movements?limit=10&cursor={first_body['meta']['next_cursor']}",
        headers=player_headers,
    )
    assert second_page.status_code == 200, second_page.text
    second_body = second_page.json()
    assert second_body["data"]

    first_ids = {movement["id"] for movement in first_body["data"]}
    second_ids = {movement["id"] for movement in second_body["data"]}
    assert first_ids.isdisjoint(second_ids)


def test_player_wallet_movements_reject_invalid_cursor(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-account-bad-cursor")
    response = client.get(
        "/account/wallet-movements?cursor=not-a-cursor",
        headers=auth_headers(
            player["access_token"],
            include_game_launch_token=False,
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_player_statement_movements_expose_cash_statement_and_separate_bonus(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-statement-admin")
    player = create_authenticated_player(prefix="integration-statement")
    player_headers = auth_headers(
        player["access_token"],
        include_game_launch_token=False,
    )
    admin_headers = auth_headers(
        admin_user["access_token"],
        include_game_launch_token=False,
    )

    bonus_response = client.post(
        f"/admin/users/{player['user_id']}/bonus-grants",
        headers={
            **admin_headers,
            "Idempotency-Key": f"statement-bonus-{uuid4()}",
        },
        json={
            "amount": "50.000000",
            "reason": "statement test bonus",
        },
    )
    assert bonus_response.status_code == 200, bonus_response.text

    debit_response = client.post(
        f"/admin/users/{player['user_id']}/adjustments",
        headers={
            **admin_headers,
            "Idempotency-Key": f"statement-cash-debit-{uuid4()}",
        },
        json={
            "wallet_type": "cash",
            "direction": "debit",
            "amount": "10.000000",
            "reason": "statement_test_debit",
        },
    )
    assert debit_response.status_code == 200, debit_response.text

    cash_response = client.get(
        "/account/statement-movements",
        headers=player_headers,
    )
    assert cash_response.status_code == 200, cash_response.text
    cash_body = cash_response.json()
    assert cash_body["meta"]["category"] == "all"
    assert cash_body["meta"]["wallet_type"] == "cash"
    assert cash_body["meta"]["period"] == "last_30_days"
    assert cash_body["meta"]["balance_disclaimer"] is None

    cash_items = cash_body["data"]
    assert all(item["wallet_type"] == "cash" for item in cash_items)
    assert not any(item["movement_family"] == "bonus" for item in cash_items)

    cash_by_type = {item["movement_type"]: item for item in cash_items}
    assert cash_by_type["admin_adjustment"]["id"].startswith("adjustment:")
    assert cash_by_type["admin_adjustment"]["debit_amount"] == "10.000000"
    assert cash_by_type["admin_adjustment"]["credit_amount"] == "0.000000"
    assert cash_by_type["admin_adjustment"]["net_amount"] == "-10.000000"
    assert cash_by_type["admin_adjustment"]["balance_after"] == "990.000000"
    assert cash_by_type["admin_adjustment"]["contains_adjustments"] is True

    adjustment_detail_response = client.get(
        f"/account/statement-movements/{quote(cash_by_type['admin_adjustment']['id'], safe='')}"
        "?wallet_type=cash",
        headers=player_headers,
    )
    assert adjustment_detail_response.status_code == 200, adjustment_detail_response.text
    adjustment_detail_body = adjustment_detail_response.json()
    assert adjustment_detail_body["data"]["movement_id"] == cash_by_type["admin_adjustment"]["id"]
    assert adjustment_detail_body["data"]["movement_family"] == "adjustment"
    assert adjustment_detail_body["meta"]["next_cursor"] is None
    adjustment_detail_items = adjustment_detail_body["data"]["items"]
    assert len(adjustment_detail_items) == 1
    assert adjustment_detail_items[0]["transaction_type"] == "admin_adjustment"
    assert adjustment_detail_items[0]["debit_amount"] == "10.000000"
    assert adjustment_detail_items[0]["balance_after"] == "990.000000"
    assert "reason" not in adjustment_detail_items[0]

    bonus_response = client.get(
        "/account/statement-movements?wallet_type=bonus&category=bonus",
        headers=player_headers,
    )
    assert bonus_response.status_code == 200, bonus_response.text
    bonus_body = bonus_response.json()
    assert bonus_body["meta"]["balance_disclaimer"] == (
        "Il saldo riflette il wallet, non solo le righe filtrate."
    )
    bonus_items = bonus_body["data"]
    assert len(bonus_items) == 1
    bonus_item = bonus_items[0]
    assert bonus_item["id"].startswith("bonus:")
    assert bonus_item["wallet_type"] == "bonus"
    assert bonus_item["movement_family"] == "bonus"
    assert bonus_item["credit_amount"] == "50.000000"
    assert bonus_item["balance_after"] == "50.000000"
    assert bonus_item["show_detail_count"] is False

    bonus_detail_response = client.get(
        f"/account/statement-movements/{quote(bonus_item['id'], safe='')}?wallet_type=bonus",
        headers=player_headers,
    )
    assert bonus_detail_response.status_code == 200, bonus_detail_response.text
    bonus_detail_body = bonus_detail_response.json()
    assert bonus_detail_body["data"]["movement_id"] == bonus_item["id"]
    assert bonus_detail_body["data"]["movement_family"] == "bonus"
    assert bonus_detail_body["data"]["items"][0]["transaction_type"] == "bonus_grant"
    assert bonus_detail_body["data"]["items"][0]["credit_amount"] == "50.000000"
    assert bonus_detail_body["data"]["items"][0]["balance_after"] == "50.000000"
    assert "reason" not in bonus_detail_body["data"]["items"][0]

    invalid_wallet_response = client.get(
        "/account/statement-movements?wallet_type=all",
        headers=player_headers,
    )
    assert invalid_wallet_response.status_code == 422
    assert invalid_wallet_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_player_statement_movements_aggregate_game_session_by_access_session(
    client,
    create_authenticated_player,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-statement-game")
    published_title = create_published_mines_variant(display_name="Statement Game")
    title_code = str(published_title["title_code"])
    player_headers = auth_headers(player["access_token"], title_code=title_code)

    access_response = client.post(
        "/access-sessions",
        headers=player_headers,
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_response.status_code == 200, access_response.text
    access_session_id = access_response.json()["data"]["id"]

    won_start_response = client.post(
        "/games/mines/start",
        headers={
            **player_headers,
            "Idempotency-Key": f"statement-game-win-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert won_start_response.status_code == 200, won_start_response.text
    won_session_id = won_start_response.json()["data"]["game_session_id"]
    mine_positions = set(db_helpers.get_mine_positions(won_session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=player_headers,
        json={
            "game_session_id": won_session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **player_headers,
            "Idempotency-Key": f"statement-game-cashout-{uuid4().hex}",
        },
        json={"game_session_id": won_session_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    won_payout = cashout_response.json()["data"]["payout_amount"]

    lost_start_response = client.post(
        "/games/mines/start",
        headers={
            **player_headers,
            "Idempotency-Key": f"statement-game-loss-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert lost_start_response.status_code == 200, lost_start_response.text
    lost_session_id = lost_start_response.json()["data"]["game_session_id"]
    mine_cell = db_helpers.get_mine_positions(lost_session_id)[0]

    loss_reveal_response = client.post(
        "/games/mines/reveal",
        headers=player_headers,
        json={
            "game_session_id": lost_session_id,
            "cell_index": mine_cell,
        },
    )
    assert loss_reveal_response.status_code == 200, loss_reveal_response.text

    statement_response = client.get(
        "/account/statement-movements?category=game",
        headers=player_headers,
    )
    assert statement_response.status_code == 200, statement_response.text
    statement_body = statement_response.json()
    assert statement_body["meta"]["balance_disclaimer"] == (
        "Il saldo riflette il wallet, non solo le righe filtrate."
    )

    game_items = statement_body["data"]
    assert len(game_items) == 1
    game_item = game_items[0]
    assert game_item["id"] == f"game:{access_session_id}"
    assert game_item["movement_family"] == "game"
    assert game_item["movement_label"] == "Sessione gioco"
    assert game_item["description"] == "Mines"
    assert game_item["detail_count"] == 2
    assert game_item["show_detail_count"] is True
    assert game_item["debit_amount"] == "3.000000"
    assert game_item["credit_amount"] == won_payout
    assert game_item["net_amount"] == f"{Decimal(won_payout) - Decimal('3.000000'):.6f}"
    assert game_item["balance_after"] == f"{Decimal('1000.000000') + Decimal(won_payout) - Decimal('3.000000'):.6f}"
    assert game_item["show_competency_at"] is True

    first_detail_page = client.get(
        f"/account/statement-movements/{quote(game_item['id'], safe='')}?wallet_type=cash&limit=1",
        headers=player_headers,
    )
    assert first_detail_page.status_code == 200, first_detail_page.text
    first_detail_body = first_detail_page.json()
    assert first_detail_body["data"]["movement_id"] == game_item["id"]
    assert first_detail_body["data"]["movement_family"] == "game"
    assert first_detail_body["meta"]["wallet_type"] == "cash"
    assert len(first_detail_body["data"]["items"]) == 1
    assert first_detail_body["meta"]["next_cursor"]
    first_round_detail = first_detail_body["data"]["items"][0]
    assert first_round_detail["item_type"] == "game_round"
    assert first_round_detail["round_code"].startswith("RND-")
    assert first_round_detail["platform_round_id"] in {won_session_id, lost_session_id}
    assert first_round_detail["wallet_type"] == "cash"
    assert first_round_detail["debit_amount"] in {"1.000000", "2.000000"}
    assert "reason" not in first_round_detail

    second_detail_page = client.get(
        "/account/statement-movements/"
        f"{quote(game_item['id'], safe='')}?wallet_type=cash&limit=10"
        f"&cursor={first_detail_body['meta']['next_cursor']}",
        headers=player_headers,
    )
    assert second_detail_page.status_code == 200, second_detail_page.text
    second_detail_body = second_detail_page.json()
    assert second_detail_body["data"]["items"]

    first_detail_ids = {item["id"] for item in first_detail_body["data"]["items"]}
    second_detail_ids = {item["id"] for item in second_detail_body["data"]["items"]}
    assert first_detail_ids.isdisjoint(second_detail_ids)


def test_player_statement_movements_are_cursor_paginated_and_reject_bad_cursor(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-statement-cursor-admin")
    player = create_authenticated_player(prefix="integration-statement-cursor")
    player_headers = auth_headers(
        player["access_token"],
        include_game_launch_token=False,
    )
    admin_headers = auth_headers(
        admin_user["access_token"],
        include_game_launch_token=False,
    )

    for index in range(2):
        response = client.post(
            f"/admin/users/{player['user_id']}/adjustments",
            headers={
                **admin_headers,
                "Idempotency-Key": f"statement-cursor-{index}-{uuid4()}",
            },
            json={
                "wallet_type": "cash",
                "direction": "credit",
                "amount": "1.000000",
                "reason": "statement_cursor_test_credit",
            },
        )
        assert response.status_code == 200, response.text

    first_page = client.get(
        "/account/statement-movements?category=adjustments&limit=1",
        headers=player_headers,
    )
    assert first_page.status_code == 200, first_page.text
    first_body = first_page.json()
    assert len(first_body["data"]) == 1
    assert first_body["meta"]["next_cursor"]

    second_page = client.get(
        "/account/statement-movements"
        f"?category=adjustments&limit=10&cursor={first_body['meta']['next_cursor']}",
        headers=player_headers,
    )
    assert second_page.status_code == 200, second_page.text
    second_body = second_page.json()
    assert second_body["data"]

    first_ids = {item["id"] for item in first_body["data"]}
    second_ids = {item["id"] for item in second_body["data"]}
    assert first_ids.isdisjoint(second_ids)

    bad_cursor = client.get(
        "/account/statement-movements?cursor=not-a-cursor",
        headers=player_headers,
    )
    assert bad_cursor.status_code == 422
    assert bad_cursor.json()["error"]["code"] == "VALIDATION_ERROR"

    detail_bad_cursor = client.get(
        f"/account/statement-movements/{quote(first_body['data'][0]['id'], safe='')}?cursor=not-a-cursor",
        headers=player_headers,
    )
    assert detail_bad_cursor.status_code == 422
    assert detail_bad_cursor.json()["error"]["code"] == "VALIDATION_ERROR"
