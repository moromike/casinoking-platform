from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.modules.games.mines.runtime import get_runtime_config
from app.modules.auth.security import hash_password


HOUSE_ACCOUNT_CODES = (
    "HOUSE_CASH",
    "HOUSE_BONUS",
    "GAME_PNL_MINES",
    "PROMO_RESERVE",
)


def _set_admin_profile(
    db_connection,
    *,
    user_id: str,
    areas: list[str],
    is_superadmin: bool = False,
) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO admin_profiles (user_id, is_superadmin, areas)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
                SET is_superadmin = EXCLUDED.is_superadmin,
                    areas = EXCLUDED.areas
            """,
            (user_id, is_superadmin, areas),
        )


def _create_area_admin(
    db_connection,
    *,
    prefix: str,
    areas: list[str],
    is_superadmin: bool = False,
) -> dict[str, object]:
    email = f"{prefix}-{uuid4().hex[:12]}@example.com"
    password = f"StrongPass-{uuid4().hex[:12]}"
    user_id = str(uuid4())
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (id, email, role, status)
            VALUES (%s, %s, 'admin', 'active')
            """,
            (user_id, email),
        )
        cursor.execute(
            """
            INSERT INTO user_credentials (user_id, password_hash)
            VALUES (%s, %s)
            """,
            (user_id, hash_password(password)),
        )
    _set_admin_profile(
        db_connection,
        user_id=user_id,
        areas=areas,
        is_superadmin=is_superadmin,
    )
    return {
        "email": email,
        "password": password,
        "user_id": user_id,
    }


def _login_area_admin(
    client,
    db_connection,
    *,
    prefix: str,
    areas: list[str],
    is_superadmin: bool = False,
) -> dict[str, object]:
    admin_user = _create_area_admin(
        db_connection,
        prefix=prefix,
        areas=areas,
        is_superadmin=is_superadmin,
    )
    login_response = client.post(
        "/admin/auth/login",
        json={
            "email": str(admin_user["email"]),
            "password": str(admin_user["password"]),
        },
    )
    assert login_response.status_code == 200, login_response.text
    admin_user["access_token"] = login_response.json()["data"]["access_token"]
    return admin_user


def _create_access_session(client, auth_headers, *, access_token: str) -> str:
    response = client.post(
        "/access-sessions",
        headers=auth_headers(access_token),
        json={"game_code": "mines"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _publish_mines_configuration(
    client,
    db_connection,
    auth_headers,
) -> dict[str, int]:
    runtime = get_runtime_config()
    grid_size = 25 if 25 in runtime["supported_grid_sizes"] else runtime["supported_grid_sizes"][0]
    supported_mine_counts = runtime["supported_mine_counts"][str(grid_size)]
    mine_count = 3 if 3 in supported_mine_counts else supported_mine_counts[0]

    mines_admin = _create_area_admin(
        db_connection,
        prefix="integration-financial-mines-publisher",
        areas=["mines"],
    )
    login_response = client.post(
        "/admin/auth/login",
        json={
            "email": str(mines_admin["email"]),
            "password": str(mines_admin["password"]),
        },
    )
    assert login_response.status_code == 200, login_response.text
    mines_admin["access_token"] = login_response.json()["data"]["access_token"]
    payload = {
        "rules_sections": {
            "ways_to_win": "<p>Pick a safe cell and cash out.</p>",
            "payout_display": "<p>Current payout is server authoritative.</p>",
            "settings_menu": "<p>Grid and mine count are configured before the round.</p>",
            "bet_collect": "<p>Bet starts the round and Collect settles a win.</p>",
            "balance_display": "<p>All balances are shown in CHIP.</p>",
            "general": "<p>Mines remains server authoritative.</p>",
            "history": "<p>Completed rounds are available in history.</p>",
        },
        "published_grid_sizes": [grid_size],
        "published_mine_counts": {str(grid_size): [mine_count]},
        "default_mine_counts": {str(grid_size): mine_count},
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
        headers=auth_headers(str(mines_admin["access_token"])),
        json=payload,
    )
    assert draft_response.status_code == 200, draft_response.text
    publish_response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(str(mines_admin["access_token"])),
    )
    assert publish_response.status_code == 200, publish_response.text
    return {"grid_size": grid_size, "mine_count": mine_count}


def _start_round(
    client,
    auth_headers,
    *,
    access_token: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    wallet_type: str = "cash",
    access_session_id: str | None = None,
    bet_amount: str = "5.000000",
) -> str:
    payload: dict[str, object] = {
        "grid_size": grid_size,
        "mine_count": mine_count,
        "bet_amount": bet_amount,
        "wallet_type": wallet_type,
    }
    if access_session_id is not None:
        payload["access_session_id"] = access_session_id

    response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(access_token),
            "Idempotency-Key": idempotency_key,
        },
        json=payload,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["game_session_id"]


def _win_round(
    client,
    auth_headers,
    db_helpers,
    *,
    access_token: str,
    start_idempotency_key: str,
    cashout_idempotency_key: str,
    grid_size: int,
    mine_count: int,
    wallet_type: str = "cash",
    access_session_id: str | None = None,
    bet_amount: str = "5.000000",
) -> str:
    session_id = _start_round(
        client,
        auth_headers,
        access_token=access_token,
        idempotency_key=start_idempotency_key,
        grid_size=grid_size,
        mine_count=mine_count,
        wallet_type=wallet_type,
        access_session_id=access_session_id,
        bet_amount=bet_amount,
    )
    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(grid_size) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(access_token),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(access_token),
            "Idempotency-Key": cashout_idempotency_key,
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    return session_id


def _lose_round(
    client,
    auth_headers,
    db_helpers,
    *,
    access_token: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    wallet_type: str = "cash",
    access_session_id: str | None = None,
    bet_amount: str = "5.000000",
) -> str:
    session_id = _start_round(
        client,
        auth_headers,
        access_token=access_token,
        idempotency_key=idempotency_key,
        grid_size=grid_size,
        mine_count=mine_count,
        wallet_type=wallet_type,
        access_session_id=access_session_id,
        bet_amount=bet_amount,
    )
    mine_cell = db_helpers.get_mine_positions(session_id)[0]
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(access_token),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text
    assert reveal_response.json()["data"]["result"] == "mine"
    return session_id


def _grant_bonus(
    client,
    auth_headers,
    *,
    admin_access_token: str,
    target_user_id: str,
    amount: str,
    idempotency_key: str,
) -> None:
    response = client.post(
        f"/admin/users/{target_user_id}/bonus-grants",
        headers={
            **auth_headers(admin_access_token),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "amount": amount,
            "reason": "integration bonus funding",
        },
    )
    assert response.status_code == 200, response.text


def _set_transaction_created_at(
    db_connection,
    *,
    session_id: str,
    transaction_type: str,
    created_at: datetime,
) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ledger_transactions
            SET created_at = %s
            WHERE reference_type = 'game_session'
              AND reference_id = %s
              AND transaction_type = %s
            """,
            (created_at, session_id, transaction_type),
        )


def _manual_round_only_bank_delta(
    db_connection,
    *,
    user_id: str,
) -> Decimal:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            WITH round_transaction_links AS (
                SELECT pr.start_ledger_transaction_id AS ledger_transaction_id
                FROM platform_rounds pr
                WHERE pr.user_id = %s

                UNION ALL

                SELECT lt.id AS ledger_transaction_id
                FROM platform_rounds pr
                JOIN ledger_transactions lt
                  ON lt.reference_type = 'game_session'
                 AND lt.reference_id = pr.id
                 AND lt.transaction_type = 'win'
                WHERE pr.user_id = %s
            )
            SELECT COALESCE(
                SUM(
                    CASE
                        WHEN le.entry_side = 'credit' THEN le.amount
                        ELSE -le.amount
                    END
                ),
                0
            ) AS bank_delta
            FROM round_transaction_links rtl
            JOIN ledger_entries le ON le.transaction_id = rtl.ledger_transaction_id
            JOIN ledger_accounts la ON la.id = le.ledger_account_id
            WHERE la.account_code IN (%s, %s, %s, %s)
            """,
            (user_id, user_id, *HOUSE_ACCOUNT_CODES),
        )
        row = cursor.fetchone()
    assert row is not None
    return row["bank_delta"]


def test_financial_sessions_report_returns_paginated_structure_and_excludes_legacy_by_default(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-player")

    access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    _win_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        start_idempotency_key="integration-financial-access-start",
        cashout_idempotency_key="integration-financial-access-cashout",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
        access_session_id=access_session_id,
    )

    legacy_session_round_id = _win_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        start_idempotency_key="integration-financial-legacy-start",
        cashout_idempotency_key="integration-financial-legacy-cashout",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
    )
    _set_transaction_created_at(
        db_connection,
        session_id=legacy_session_round_id,
        transaction_type="bet",
        created_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC),
    )
    _set_transaction_created_at(
        db_connection,
        session_id=legacy_session_round_id,
        transaction_type="win",
        created_at=datetime(2026, 1, 15, 10, 5, 0, tzinfo=UTC),
    )

    _grant_bonus(
        client,
        auth_headers,
        admin_access_token=str(finance_admin["access_token"]),
        target_user_id=str(player["user_id"]),
        amount="50.000000",
        idempotency_key="integration-financial-report-bonus",
    )

    report_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={"user_id": str(player["user_id"])} ,
    )
    assert report_response.status_code == 200, report_response.text

    payload = report_response.json()["data"]
    sessions = payload["sessions"]
    assert payload["pagination"] == {
        "page": 1,
        "limit": 50,
        "total_items": 1,
        "total_pages": 1,
    }
    assert len(sessions) == 1
    assert all(session["is_legacy"] is False for session in sessions)

    session = sessions[0]
    assert session["session_id"] == access_session_id
    assert session["user_id"] == str(player["user_id"])
    assert session["user_email"] == str(player["email"])
    assert session["game_code"] == "mines"
    assert payload["page_totals"]["bank_delta"] == session["bank_delta"]
    assert payload["summary"]["total_bank_delta_period"] == session["bank_delta"]
    assert session["session_id"] != f"legacy-{player['user_id']}-2026-01-15"


def test_financial_sessions_report_filters_by_email_date_transaction_type_and_bank_delta(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-filters-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-filters-player")

    winning_access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    winning_round_id = _win_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        start_idempotency_key="integration-financial-filters-win-start",
        cashout_idempotency_key="integration-financial-filters-win-cashout",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
        access_session_id=winning_access_session_id,
    )
    _set_transaction_created_at(
        db_connection,
        session_id=winning_round_id,
        transaction_type="bet",
        created_at=datetime(2026, 2, 2, 10, 0, 0, tzinfo=UTC),
    )
    _set_transaction_created_at(
        db_connection,
        session_id=winning_round_id,
        transaction_type="win",
        created_at=datetime(2026, 2, 2, 10, 5, 0, tzinfo=UTC),
    )
    close_winning_access_response = client.post(
        f"/access-sessions/{winning_access_session_id}/close",
        headers=auth_headers(str(player["access_token"])),
    )
    assert close_winning_access_response.status_code == 200, close_winning_access_response.text

    losing_access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    losing_round_id = _lose_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        idempotency_key="integration-financial-filters-lose-start",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
        access_session_id=losing_access_session_id,
    )
    _set_transaction_created_at(
        db_connection,
        session_id=losing_round_id,
        transaction_type="bet",
        created_at=datetime(2026, 2, 3, 11, 0, 0, tzinfo=UTC),
    )

    win_filter_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "transaction_type": "win",
        },
    )
    assert win_filter_response.status_code == 200, win_filter_response.text
    win_sessions = win_filter_response.json()["data"]["sessions"]
    assert [session["session_id"] for session in win_sessions] == [winning_access_session_id]

    min_delta_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "min_delta": "1.000000",
        },
    )
    assert min_delta_response.status_code == 200, min_delta_response.text
    min_delta_sessions = min_delta_response.json()["data"]["sessions"]
    assert [session["session_id"] for session in min_delta_sessions] == [losing_access_session_id]
    assert Decimal(min_delta_sessions[0]["bank_delta"]) > Decimal("0.000000")

    max_delta_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "max_delta": "0.000000",
        },
    )
    assert max_delta_response.status_code == 200, max_delta_response.text
    max_delta_sessions = max_delta_response.json()["data"]["sessions"]
    assert [session["session_id"] for session in max_delta_sessions] == [winning_access_session_id]
    assert Decimal(max_delta_sessions[0]["bank_delta"]) <= Decimal("0.000000")

    date_filter_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "date_from": "2026-02-03",
            "date_to": "2026-02-03",
        },
    )
    assert date_filter_response.status_code == 200, date_filter_response.text
    date_filter_sessions = date_filter_response.json()["data"]["sessions"]
    assert [session["session_id"] for session in date_filter_sessions] == [losing_access_session_id]

    email_filter_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "email": str(player["email"]).split("@")[0],
        },
    )
    assert email_filter_response.status_code == 200, email_filter_response.text
    email_filter_payload = email_filter_response.json()["data"]
    assert email_filter_payload["pagination"]["total_items"] == 2
    assert {session["session_id"] for session in email_filter_payload["sessions"]} == {
        winning_access_session_id,
        losing_access_session_id,
    }
    assert all(
        session["user_email"] == str(player["email"])
        for session in email_filter_payload["sessions"]
    )


def test_financial_sessions_report_supports_default_and_allowed_page_sizes(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-pagination-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-pagination-player")

    created_session_ids: list[str] = []
    for index in range(21):
        access_session_id = _create_access_session(
            client,
            auth_headers,
            access_token=str(player["access_token"]),
        )
        created_session_ids.append(access_session_id)
        _lose_round(
            client,
            auth_headers,
            db_helpers,
            access_token=str(player["access_token"]),
            idempotency_key=f"integration-financial-pagination-round-{index}",
            grid_size=round_setup["grid_size"],
            mine_count=round_setup["mine_count"],
            access_session_id=access_session_id,
        )
        close_response = client.post(
            f"/access-sessions/{access_session_id}/close",
            headers=auth_headers(str(player["access_token"])),
        )
        assert close_response.status_code == 200, close_response.text

    default_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={"user_id": str(player["user_id"])} ,
    )
    assert default_response.status_code == 200, default_response.text
    default_payload = default_response.json()["data"]
    assert default_payload["pagination"] == {
        "page": 1,
        "limit": 50,
        "total_items": 21,
        "total_pages": 1,
    }
    assert len(default_payload["sessions"]) == 21

    page_one_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "page": "1",
            "limit": "20",
        },
    )
    assert page_one_response.status_code == 200, page_one_response.text
    page_one_payload = page_one_response.json()["data"]
    assert page_one_payload["pagination"] == {
        "page": 1,
        "limit": 20,
        "total_items": 21,
        "total_pages": 2,
    }
    assert len(page_one_payload["sessions"]) == 20

    page_two_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "page": "2",
            "limit": "20",
        },
    )
    assert page_two_response.status_code == 200, page_two_response.text
    page_two_payload = page_two_response.json()["data"]
    assert page_two_payload["pagination"] == {
        "page": 2,
        "limit": 20,
        "total_items": 21,
        "total_pages": 2,
    }
    assert len(page_two_payload["sessions"]) == 1

    page_one_session_ids = {session["session_id"] for session in page_one_payload["sessions"]}
    page_two_session_ids = {session["session_id"] for session in page_two_payload["sessions"]}
    assert page_one_session_ids | page_two_session_ids == set(created_session_ids)
    assert page_one_session_ids.isdisjoint(page_two_session_ids)

    for page_size in (100, 500):
        page_size_response = client.get(
            "/admin/reports/financial/sessions",
            headers=auth_headers(str(finance_admin["access_token"])),
            params={
                "user_id": str(player["user_id"]),
                "limit": str(page_size),
            },
        )
        assert page_size_response.status_code == 200, page_size_response.text
        page_size_payload = page_size_response.json()["data"]
        assert page_size_payload["pagination"]["limit"] == page_size
        assert page_size_payload["pagination"]["total_items"] == 21
        assert len(page_size_payload["sessions"]) == 21

    assert Decimal(default_payload["page_totals"]["bank_delta"]) == sum(
        Decimal(session["bank_delta"]) for session in default_payload["sessions"]
    )
    assert Decimal(page_one_payload["page_totals"]["bank_delta"]) == sum(
        Decimal(session["bank_delta"]) for session in page_one_payload["sessions"]
    )
    assert Decimal(page_two_payload["page_totals"]["bank_delta"]) == sum(
        Decimal(session["bank_delta"]) for session in page_two_payload["sessions"]
    )


def test_financial_session_detail_returns_bet_and_win_events_for_access_session(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _create_area_admin(
        db_connection,
        prefix="integration-financial-detail-admin",
        areas=["finance"],
    )
    finance_login = client.post(
        "/admin/auth/login",
        json={
            "email": str(finance_admin["email"]),
            "password": str(finance_admin["password"]),
        },
    )
    assert finance_login.status_code == 200, finance_login.text
    finance_admin["access_token"] = finance_login.json()["data"]["access_token"]
    player = create_authenticated_player(prefix="integration-financial-detail-player")
    access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )

    round_id = _win_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        start_idempotency_key="integration-financial-detail-start",
        cashout_idempotency_key="integration-financial-detail-cashout",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
        access_session_id=access_session_id,
    )

    detail_response = client.get(
        f"/admin/reports/financial/sessions/{access_session_id}",
        headers=auth_headers(str(finance_admin["access_token"])),
    )
    assert detail_response.status_code == 200, detail_response.text

    payload = detail_response.json()["data"]
    assert payload["session_id"] == access_session_id
    assert payload["is_legacy"] is False
    assert payload["game_code"] == "mines"
    assert len(payload["events"]) == 2
    assert [event["transaction_type"] for event in payload["events"]] == ["bet", "win"]
    assert {event["platform_round_id"] for event in payload["events"]} == {round_id}
    assert payload["events"][0]["bank_credit"] == "5.000000"
    assert payload["events"][0]["bank_debit"] == "0.000000"
    assert payload["events"][1]["bank_credit"] == "0.000000"
    assert Decimal(payload["events"][1]["bank_debit"]) > Decimal("0.000000")
    assert payload["events"][0]["game_enrichment"] != ""
    assert payload["events"][1]["game_enrichment"] != ""


def test_financial_session_detail_uses_latest_transaction_timestamp_for_active_session_ended_at(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _create_area_admin(
        db_connection,
        prefix="integration-financial-ended-at-admin",
        areas=["finance"],
    )
    finance_login = client.post(
        "/admin/auth/login",
        json={
            "email": str(finance_admin["email"]),
            "password": str(finance_admin["password"]),
        },
    )
    assert finance_login.status_code == 200, finance_login.text
    finance_admin["access_token"] = finance_login.json()["data"]["access_token"]

    player = create_authenticated_player(prefix="integration-financial-ended-at-player")
    access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    round_id = _win_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        start_idempotency_key="integration-financial-ended-at-start",
        cashout_idempotency_key="integration-financial-ended-at-cashout",
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
        access_session_id=access_session_id,
    )
    _set_transaction_created_at(
        db_connection,
        session_id=round_id,
        transaction_type="bet",
        created_at=datetime(2026, 2, 20, 9, 0, 0, tzinfo=UTC),
    )
    _set_transaction_created_at(
        db_connection,
        session_id=round_id,
        transaction_type="win",
        created_at=datetime(2026, 2, 20, 9, 7, 0, tzinfo=UTC),
    )

    detail_response = client.get(
        f"/admin/reports/financial/sessions/{access_session_id}",
        headers=auth_headers(str(finance_admin["access_token"])),
    )
    assert detail_response.status_code == 200, detail_response.text

    payload = detail_response.json()["data"]
    assert payload["started_at"] != ""
    assert payload["ended_at"] == "2026-02-20T09:07:00+00:00"
    assert [event["timestamp"] for event in payload["events"]] == [
        "2026-02-20T09:00:00+00:00",
        "2026-02-20T09:07:00+00:00",
    ]


def test_financial_sessions_endpoints_require_finance_area(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
    db_helpers,
) -> None:
    round_setup = _publish_mines_configuration(
        client,
        db_connection,
        auth_headers,
    )
    finance_admin = _create_area_admin(
        db_connection,
        prefix="integration-financial-rbac-finance",
        areas=["finance"],
    )
    finance_login = client.post(
        "/admin/auth/login",
        json={
            "email": str(finance_admin["email"]),
            "password": str(finance_admin["password"]),
        },
    )
    assert finance_login.status_code == 200, finance_login.text
    finance_admin["access_token"] = finance_login.json()["data"]["access_token"]
    end_user_admin = _create_area_admin(
        db_connection,
        prefix="integration-financial-rbac-end-user",
        areas=["end_user"],
    )
    end_user_login = client.post(
        "/admin/auth/login",
        json={
            "email": str(end_user_admin["email"]),
            "password": str(end_user_admin["password"]),
        },
    )
    assert end_user_login.status_code == 200, end_user_login.text
    end_user_admin["access_token"] = end_user_login.json()["data"]["access_token"]
    player = create_authenticated_player(prefix="integration-financial-rbac-player")
    access_session_id = _create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    _lose_round(
        client,
        auth_headers,
        db_helpers,
        access_token=str(player["access_token"]),
        idempotency_key="integration-financial-rbac-round",
        access_session_id=access_session_id,
        grid_size=round_setup["grid_size"],
        mine_count=round_setup["mine_count"],
    )

    finance_list_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={"user_id": str(player["user_id"])} ,
    )
    assert finance_list_response.status_code == 200, finance_list_response.text

    end_user_list_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(end_user_admin["access_token"])),
        params={"user_id": str(player["user_id"])} ,
    )
    assert end_user_list_response.status_code == 403, end_user_list_response.text

    end_user_detail_response = client.get(
        f"/admin/reports/financial/sessions/{access_session_id}",
        headers=auth_headers(str(end_user_admin["access_token"])),
    )
    assert end_user_detail_response.status_code == 403, end_user_detail_response.text
