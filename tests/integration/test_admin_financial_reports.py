from __future__ import annotations
import pytest

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.modules.auth.security import hash_password
from tests.integration.helpers import apri_partita_cavia, chiudi_partita_cavia


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


def _round_cavia(
    client,
    auth_headers,
    *,
    access_token: str,
    prefisso_idempotenza: str,
    esito: str,
    payout_amount: str | None = None,
    bet_amount: str = "5.000000",
) -> dict[str, str]:
    """Esegue un round piattaforma senza dipendere dalla matematica di un gioco."""
    headers = auth_headers(access_token, include_game_launch_token=False)
    round_ids = apri_partita_cavia(
        client,
        headers,
        bet_amount=bet_amount,
        prefisso_idempotenza=prefisso_idempotenza,
    )
    assert round_ids["access_session_id"]
    assert round_ids["game_session_id"]
    assert round_ids["game_launch_token"]
    assert round_ids["table_session_id"]
    settle_response = chiudi_partita_cavia(
        client,
        headers,
        game_launch_token=round_ids["game_launch_token"],
        game_session_id=round_ids["game_session_id"],
        esito=esito,
        payout_amount=payout_amount,
        prefisso_idempotenza=prefisso_idempotenza,
    )
    assert settle_response.status_code == 200, settle_response.text
    assert round_ids["access_session_id"] != round_ids["game_session_id"]
    assert round_ids["game_launch_token"] != round_ids["game_session_id"]
    return round_ids


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
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-player")

    winning_round = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-access",
        esito="vincita",
        payout_amount="6.000000",
    )
    access_session_id = winning_round["access_session_id"]

    legacy_round = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-legacy",
        esito="vincita",
        payout_amount="6.000000",
    )
    legacy_session_round_id = legacy_round["game_session_id"]
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

    # Render the round legacy at DB level (real start without access_session is forbidden)
    with db_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE platform_rounds SET access_session_id = NULL WHERE id = %s",
            (legacy_session_round_id,),
        )
        assert cursor.rowcount == 1
        cursor.execute(
            "SELECT access_session_id FROM platform_rounds WHERE id = %s",
            (legacy_session_round_id,),
        )
        row = cursor.fetchone()
        assert row is not None and row["access_session_id"] is None

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
    assert session["game_code"] == "manichino"
    assert session["title_code"] == "manichino_test"
    assert session["site_code"] == "casinoking"
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
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-filters-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-filters-player")

    winning_round = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-fil-win",
        esito="vincita",
        payout_amount="6.000000",
    )
    winning_access_session_id = winning_round["access_session_id"]
    winning_round_id = winning_round["game_session_id"]
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
        headers=auth_headers(str(player["access_token"]), include_game_launch_token=False),
    )
    assert close_winning_access_response.status_code == 200, close_winning_access_response.text

    losing_round = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-fil-loss",
        esito="perdita",
    )
    losing_access_session_id = losing_round["access_session_id"]
    losing_round_id = losing_round["game_session_id"]
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
    finance_admin = _login_area_admin(
        client,
        db_connection,
        prefix="integration-finance-report-pagination-admin",
        areas=["finance"],
    )
    player = create_authenticated_player(prefix="integration-finance-report-pagination-player")

    created_session_ids: list[str] = []
    for index in range(26):
        round_ids = _round_cavia(
            client,
            auth_headers,
            access_token=str(player["access_token"]),
            prefisso_idempotenza=f"fin-page-{index}",
            esito="perdita",
        )
        access_session_id = round_ids["access_session_id"]
        created_session_ids.append(access_session_id)
        close_response = client.post(
            f"/access-sessions/{access_session_id}/close",
            headers=auth_headers(str(player["access_token"]), include_game_launch_token=False),
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
        "total_items": 26,
        "total_pages": 1,
    }
    assert len(default_payload["sessions"]) == 26

    page_one_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "page": "1",
            "limit": "25",
        },
    )
    assert page_one_response.status_code == 200, page_one_response.text
    page_one_payload = page_one_response.json()["data"]
    assert page_one_payload["pagination"] == {
        "page": 1,
        "limit": 25,
        "total_items": 26,
        "total_pages": 2,
    }
    assert len(page_one_payload["sessions"]) == 25

    page_two_response = client.get(
        "/admin/reports/financial/sessions",
        headers=auth_headers(str(finance_admin["access_token"])),
        params={
            "user_id": str(player["user_id"]),
            "page": "2",
            "limit": "25",
        },
    )
    assert page_two_response.status_code == 200, page_two_response.text
    page_two_payload = page_two_response.json()["data"]
    assert page_two_payload["pagination"] == {
        "page": 2,
        "limit": 25,
        "total_items": 26,
        "total_pages": 2,
    }
    assert len(page_two_payload["sessions"]) == 1

    page_one_session_ids = {session["session_id"] for session in page_one_payload["sessions"]}
    page_two_session_ids = {session["session_id"] for session in page_two_payload["sessions"]}
    assert page_one_session_ids | page_two_session_ids == set(created_session_ids)
    assert page_one_session_ids.isdisjoint(page_two_session_ids)

    for page_size in (50, 100):
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
        assert page_size_payload["pagination"]["total_items"] == 26
        assert len(page_size_payload["sessions"]) == 26

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
    round_ids = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-detail",
        esito="vincita",
        payout_amount="6.000000",
    )
    access_session_id = round_ids["access_session_id"]
    round_id = round_ids["game_session_id"]

    detail_response = client.get(
        f"/admin/reports/financial/sessions/{access_session_id}",
        headers=auth_headers(str(finance_admin["access_token"])),
    )
    assert detail_response.status_code == 200, detail_response.text

    payload = detail_response.json()["data"]
    assert payload["session_id"] == access_session_id
    assert payload["is_legacy"] is False
    assert payload["game_code"] == "manichino"
    assert payload["title_code"] == "manichino_test"
    assert payload["site_code"] == "casinoking"
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
    round_ids = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-ended",
        esito="vincita",
        payout_amount="6.000000",
    )
    access_session_id = round_ids["access_session_id"]
    round_id = round_ids["game_session_id"]
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
    round_ids = _round_cavia(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        prefisso_idempotenza="fin-rbac",
        esito="perdita",
    )
    access_session_id = round_ids["access_session_id"]

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
