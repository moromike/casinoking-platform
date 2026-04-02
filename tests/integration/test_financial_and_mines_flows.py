from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.modules.games.mines.runtime import get_multiplier


def _publish_mines_configuration(
    client,
    create_admin_user,
    auth_headers,
    *,
    published_grid_sizes: list[int],
    published_mine_counts: dict[str, list[int]],
    default_mine_counts: dict[str, int],
) -> None:
    admin_user = create_admin_user(prefix="integration-mines-publish-helper")
    payload = {
        "rules_sections": {
            "ways_to_win": "<p>Pick at least one diamond, then collect.</p>",
            "payout_display": "<p>The highlighted multiplier is the payout available right now.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Authenticated players can inspect completed hands from account history.</p>",
        },
        "published_grid_sizes": published_grid_sizes,
        "published_mine_counts": published_mine_counts,
        "default_mine_counts": default_mine_counts,
        "ui_labels": {
            "demo": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
            "real": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }
    draft_response = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
        json=payload,
    )
    assert draft_response.status_code == 200
    publish_response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200


def _published_round_setup(client) -> dict[str, int | Decimal]:
    runtime_response = client.get("/games/mines/config")
    assert runtime_response.status_code == 200
    runtime_payload = runtime_response.json()["data"]
    presentation_config = runtime_payload.get("presentation_config") or {}

    published_grid_sizes = (
        presentation_config.get("published_grid_sizes")
        or runtime_payload["supported_grid_sizes"]
    )
    grid_size = 25 if 25 in published_grid_sizes else published_grid_sizes[0]

    published_mine_counts = (
        presentation_config.get("published_mine_counts", {}).get(str(grid_size))
        or runtime_payload["supported_mine_counts"][str(grid_size)]
    )
    default_mine_count = presentation_config.get("default_mine_counts", {}).get(str(grid_size))
    mine_count = (
        default_mine_count
        if default_mine_count in published_mine_counts
        else published_mine_counts[len(published_mine_counts) // 2]
    )
    payout_ladder = runtime_payload["payout_ladders"][str(grid_size)][str(mine_count)]

    return {
        "grid_size": grid_size,
        "mine_count": mine_count,
        "first_safe_multiplier": Decimal(payout_ladder[0]),
    }


def _expected_wallet_balance_after_cashout(
    bet_amount: str,
    first_safe_multiplier: Decimal,
) -> str:
    quant = Decimal("0.000001")
    starting_balance = Decimal("1000.000000")
    bet = Decimal(bet_amount)
    payout = (bet * first_safe_multiplier).quantize(quant, rounding=ROUND_HALF_UP)
    final_balance = (starting_balance - bet + payout).quantize(
        quant,
        rounding=ROUND_HALF_UP,
    )
    return f"{final_balance:.6f}"


def test_register_creates_wallets_and_signup_ledger(
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-signup")

    user_row = db_helpers.fetchone(
        """
        SELECT email, role, status
        FROM users
        WHERE id = %s
        """,
        (player["user_id"],),
    )
    assert user_row == {
        "email": player["email"],
        "role": "player",
        "status": "active",
    }

    wallet_rows = db_helpers.fetchall(
        """
        SELECT wallet_type, balance_snapshot
        FROM wallet_accounts
        WHERE user_id = %s
        ORDER BY wallet_type
        """,
        (player["user_id"],),
    )
    assert [
        {
            "wallet_type": row["wallet_type"],
            "balance_snapshot": f"{row['balance_snapshot']:.6f}",
        }
        for row in wallet_rows
    ] == [
        {"wallet_type": "bonus", "balance_snapshot": "0.000000"},
        {"wallet_type": "cash", "balance_snapshot": "1000.000000"},
    ]

    transaction_rows = db_helpers.fetchall(
        """
        SELECT transaction_type, idempotency_key
        FROM ledger_transactions
        WHERE user_id = %s
        ORDER BY created_at
        """,
        (player["user_id"],),
    )
    assert transaction_rows == [
        {
            "transaction_type": "signup_credit",
            "idempotency_key": f"signup-{player['user_id']}",
        }
    ]


def test_demo_player_can_start_a_real_mines_round(
    client,
    auth_headers,
) -> None:
    round_setup = _published_round_setup(client)
    demo_response = client.post("/auth/demo")
    assert demo_response.status_code == 200
    demo_payload = demo_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(demo_payload["access_token"]),
            "Idempotency-Key": "integration-demo-start",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()["data"]
    assert start_payload["status"] == "active"
    assert start_payload["wallet_balance_after"] == "999.000000"


def test_game_launch_token_is_valid_for_mines_but_not_for_standard_player_bearer(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-game-launch-token")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    assert issue_response.status_code == 200
    game_launch_token = issue_response.json()["data"]["game_launch_token"]

    validate_response = client.post(
        "/games/mines/launch/validate",
        json={"game_launch_token": game_launch_token},
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["data"]["player_id"] == str(player["user_id"])

    forbidden_wallet_response = client.get(
        "/wallets",
        headers={"Authorization": f"Bearer {game_launch_token}"},
    )
    assert forbidden_wallet_response.status_code == 401
    assert forbidden_wallet_response.json() == {
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Invalid bearer token",
        },
    }


def test_mines_start_accepts_valid_game_launch_token_header(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-start-launch-token")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    assert issue_response.status_code == 200
    game_launch_token = issue_response.json()["data"]["game_launch_token"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-with-launch-token",
            "X-Game-Launch-Token": game_launch_token,
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200


def test_mines_start_rejects_mismatched_game_launch_token_header(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    round_setup = _published_round_setup(client)
    owner = create_authenticated_player(prefix="integration-launch-owner")
    other = create_authenticated_player(prefix="integration-launch-other")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(owner["access_token"]),
        json={"game_code": "mines"},
    )
    assert issue_response.status_code == 200
    game_launch_token = issue_response.json()["data"]["game_launch_token"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(other["access_token"]),
            "Idempotency-Key": "integration-start-with-mismatched-launch-token",
            "X-Game-Launch-Token": game_launch_token,
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 403
    assert start_response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Game launch token ownership is not valid",
        },
    }


def test_mines_start_rejects_invalid_game_launch_token_header(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-launch-invalid")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-invalid-launch-token",
            "X-Game-Launch-Token": "invalid-launch-token",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 401
    assert start_response.json() == {
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Game launch token is not valid",
        },
    }


def test_mines_reveal_rejects_mismatched_game_launch_token_header(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    owner = create_authenticated_player(prefix="integration-reveal-launch-owner")
    other = create_authenticated_player(prefix="integration-reveal-launch-other")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(owner["access_token"]),
            "Idempotency-Key": "integration-start-owner-for-reveal-token",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    owner_launch_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(owner["access_token"]),
        json={"game_code": "mines"},
    )
    assert owner_launch_response.status_code == 200
    game_launch_token = owner_launch_response.json()["data"]["game_launch_token"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(
        index for index in range(int(round_setup["grid_size"])) if index not in mine_positions
    )

    reveal_response = client.post(
        "/games/mines/reveal",
        headers={
            **auth_headers(other["access_token"]),
            "X-Game-Launch-Token": game_launch_token,
        },
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 403
    assert reveal_response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Game launch token ownership is not valid",
        },
    }


def test_mines_launch_token_supports_full_round_lifecycle(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-launch-lifecycle")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    assert issue_response.status_code == 200
    game_launch_token = issue_response.json()["data"]["game_launch_token"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-launch-lifecycle-start",
            "X-Game-Launch-Token": game_launch_token,
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(
        index for index in range(int(round_setup["grid_size"])) if index not in mine_positions
    )

    reveal_response = client.post(
        "/games/mines/reveal",
        headers={
            **auth_headers(player["access_token"]),
            "X-Game-Launch-Token": game_launch_token,
        },
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200
    assert reveal_response.json()["data"]["result"] == "safe"

    session_response = client.get(
        f"/games/mines/session/{session_id}",
        headers={
            **auth_headers(player["access_token"]),
            "X-Game-Launch-Token": game_launch_token,
        },
    )
    assert session_response.status_code == 200
    assert session_response.json()["data"]["status"] == "active"

    fairness_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers={
            **auth_headers(player["access_token"]),
            "X-Game-Launch-Token": game_launch_token,
        },
    )
    assert fairness_response.status_code == 200
    assert fairness_response.json()["data"]["game_session_id"] == session_id

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-launch-lifecycle-cashout",
            "X-Game-Launch-Token": game_launch_token,
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200
    assert cashout_response.json()["data"]["status"] == "won"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]


def test_mines_session_endpoints_reject_invalid_game_launch_token_header(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-invalid-session-launch-token")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-invalid-session-launch-token-start",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    session_response = client.get(
        f"/games/mines/session/{session_id}",
        headers={
            **auth_headers(player["access_token"]),
            "X-Game-Launch-Token": "invalid-launch-token",
        },
    )
    assert session_response.status_code == 401
    assert session_response.json() == {
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Game launch token is not valid",
        },
    }

    fairness_response = client.get(
        f"/games/mines/session/{session_id}/fairness",
        headers={
            **auth_headers(player["access_token"]),
            "X-Game-Launch-Token": "invalid-launch-token",
        },
    )
    assert fairness_response.status_code == 401
    assert fairness_response.json() == {
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Game launch token is not valid",
        },
    }


def test_mines_start_reveal_cashout_updates_wallet_and_ledger(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-win")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-win",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()["data"]
    session_id = start_payload["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(
        index for index in range(int(round_setup["grid_size"])) if index not in mine_positions
    )

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200
    assert reveal_response.json()["data"]["result"] == "safe"

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-win",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200
    cashout_payload = cashout_response.json()["data"]
    assert cashout_payload["status"] == "won"

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == _expected_wallet_balance_after_cashout(
        "5.000000",
        round_setup["first_safe_multiplier"],
    )

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]

    session_row = db_helpers.fetchone(
        """
        SELECT pr.status, pr.closed_at, mgr.safe_reveals_count
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
        WHERE pr.id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] == "won"
    assert session_row["closed_at"] is not None
    assert session_row["safe_reveals_count"] == 1

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    session_payload = session_snapshot.json()["data"]
    assert session_payload["status"] == "won"
    assert session_payload["closed_at"] is not None
    assert session_payload["revealed_cells"] == [safe_cell]
    assert "mine_positions" not in session_payload
    assert "mine_positions_json" not in session_payload


def test_mines_loss_does_not_create_win_credit(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    _publish_mines_configuration(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[9],
        published_mine_counts={"9": [1]},
        default_mine_counts={"9": 1},
    )
    player = create_authenticated_player(prefix="integration-loss")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-loss",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]
    mine_cell = db_helpers.get_mine_positions(session_id)[0]

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200
    assert reveal_response.json()["data"] == {
        "game_session_id": session_id,
        "status": "lost",
        "result": "mine",
        "safe_reveals_count": 0,
        "mine_positions": [mine_cell],
    }

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    assert session_snapshot.json()["data"]["potential_payout"] == "0.000000"

    assert db_helpers.get_wallet_balance(str(player["user_id"])) == "999.000000"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet"]

    session_row = db_helpers.fetchone(
        """
        SELECT pr.status, pr.closed_at, mgr.safe_reveals_count
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
        WHERE pr.id = %s
        """,
        (session_id,),
    )
    assert session_row is not None
    assert session_row["status"] == "lost"
    assert session_row["closed_at"] is not None
    assert session_row["safe_reveals_count"] == 0

    assert session_snapshot.json()["data"]["revealed_cells"] == [mine_cell]
    assert "mine_positions" not in session_snapshot.json()["data"]
    assert "mine_positions_json" not in session_snapshot.json()["data"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "999.000000",
        "ledger_balance": "999.000000",
        "drift": "0.000000",
    }


def test_reveal_after_won_session_returns_game_state_conflict_and_keeps_ledger_unchanged(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-reveal-after-won")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-reveal-after-won-start",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(
        index for index in range(int(round_setup["grid_size"])) if index not in mine_positions
    )

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-reveal-after-won-cashout",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200

    replay_reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": (safe_cell + 1) % int(round_setup["grid_size"]),
        },
    )
    assert replay_reveal_response.status_code == 409
    assert replay_reveal_response.json()["error"]["code"] == "GAME_STATE_CONFLICT"

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    session_payload = session_snapshot.json()["data"]
    assert session_payload["status"] == "won"
    assert session_payload["revealed_cells"] == [safe_cell]
    assert session_payload["safe_reveals_count"] == 1

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": _expected_wallet_balance_after_cashout(
            "5.000000",
            round_setup["first_safe_multiplier"],
        ),
        "ledger_balance": _expected_wallet_balance_after_cashout(
            "5.000000",
            round_setup["first_safe_multiplier"],
        ),
        "drift": "0.000000",
    }


def test_cashout_after_lost_session_returns_game_state_conflict_and_does_not_create_win(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    _publish_mines_configuration(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[9],
        published_mine_counts={"9": [1]},
        default_mine_counts={"9": 1},
    )
    player = create_authenticated_player(prefix="integration-cashout-after-lost")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-after-lost-start",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]
    mine_cell = db_helpers.get_mine_positions(session_id)[0]

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-after-lost-cashout",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 409
    assert cashout_response.json()["error"]["code"] == "GAME_STATE_CONFLICT"

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    assert session_snapshot.json()["data"]["status"] == "lost"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "999.000000",
        "ledger_balance": "999.000000",
        "drift": "0.000000",
    }


def test_cashout_replay_after_won_with_different_idempotency_key_is_rejected_without_extra_win(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-cashout-replay-after-won")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-replay-after-won-start",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(
        index for index in range(int(round_setup["grid_size"])) if index not in mine_positions
    )

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200

    first_cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-replay-after-won-a",
        },
        json={"game_session_id": session_id},
    )
    assert first_cashout_response.status_code == 200

    second_cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-cashout-replay-after-won-b",
        },
        json={"game_session_id": session_id},
    )
    assert second_cashout_response.status_code == 409
    assert second_cashout_response.json()["error"]["code"] == "GAME_STATE_CONFLICT"

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": _expected_wallet_balance_after_cashout(
            "5.000000",
            round_setup["first_safe_multiplier"],
        ),
        "ledger_balance": _expected_wallet_balance_after_cashout(
            "5.000000",
            round_setup["first_safe_multiplier"],
        ),
        "drift": "0.000000",
    }


def test_reveal_last_available_safe_cell_auto_finishes_round(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    _publish_mines_configuration(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[9],
        published_mine_counts={"9": [8]},
        default_mine_counts={"9": 8},
    )
    player = create_authenticated_player(prefix="integration-auto-finish-final-safe")
    expected_multiplier = get_multiplier(
        grid_size=9,
        mine_count=8,
        safe_reveals_count=1,
    )
    expected_payout = (Decimal("1.000000") * expected_multiplier).quantize(Decimal("0.000001"))

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-auto-finish-final-safe-start",
        },
        json={
            "grid_size": 9,
            "mine_count": 8,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(9) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200
    reveal_payload = reveal_response.json()["data"]
    assert reveal_payload["result"] == "safe"
    assert reveal_payload["status"] == "won"
    assert reveal_payload["safe_reveals_count"] == 1
    assert reveal_payload["multiplier_current"] == f"{expected_multiplier:.4f}"
    assert reveal_payload["potential_payout"] == f"{expected_payout:.6f}"
    assert reveal_payload["payout_amount"] == f"{expected_payout:.6f}"

    session_snapshot = client.get(
        f"/games/mines/session/{session_id}",
        headers=auth_headers(player["access_token"]),
    )
    assert session_snapshot.status_code == 200
    session_payload = session_snapshot.json()["data"]
    assert session_payload["status"] == "won"
    assert session_payload["revealed_cells"] == [safe_cell]
    assert session_payload["safe_reveals_count"] == 1

    game_transactions = db_helpers.get_game_transactions(session_id)
    assert [row["transaction_type"] for row in game_transactions] == ["bet", "win"]
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": f"{(Decimal('1000.000000') - Decimal('1.000000') + expected_payout):.6f}",
        "ledger_balance": f"{(Decimal('1000.000000') - Decimal('1.000000') + expected_payout):.6f}",
        "drift": "0.000000",
    }


def test_password_reset_updates_credentials_and_consumes_token(
    client,
    create_player,
    login_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-password-reset")
    new_password = "StrongPass-PasswordReset"

    forgot_response = client.post(
        "/auth/password/forgot",
        json={"email": player["email"]},
    )
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["data"]["reset_token"]
    assert isinstance(reset_token, str)

    reset_response = client.post(
        "/auth/password/reset",
        json={
            "token": reset_token,
            "new_password": new_password,
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["data"] == {"password_reset": True}

    old_login_response = client.post(
        "/auth/login",
        json={
            "email": player["email"],
            "password": player["password"],
        },
    )
    assert old_login_response.status_code == 401

    new_login_payload = login_player(
        email=str(player["email"]),
        password=new_password,
    )
    assert new_login_payload["token_type"] == "bearer"

    token_rows = db_helpers.fetchall(
        """
        SELECT consumed_at
        FROM password_reset_tokens
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (player["user_id"],),
    )
    assert len(token_rows) == 1
    assert token_rows[0]["consumed_at"] is not None

    replay_response = client.post(
        "/auth/password/reset",
        json={
            "token": reset_token,
            "new_password": "StrongPass-PasswordReset-Replay",
        },
    )
    assert replay_response.status_code == 409
    assert replay_response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Reset token is not valid or expired",
        },
    }
