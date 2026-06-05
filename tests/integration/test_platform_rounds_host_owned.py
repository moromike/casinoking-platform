from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.modules.platform.rounds.service import open_game_round

from tests.integration.helpers import create_game_access_session


def test_open_game_round_writes_platform_rounds_legacy_equivalent_rows_for_all_games(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="platform-host-owned")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    mines_title = create_published_mines_variant(
        display_name="Mines Platform Host-Owned",
        lobby_visibility="visible",
        demo_enabled=True,
        real_enabled=True,
    )
    _publish_existing_title_for_real_play(
        db_connection,
        title_code="boxe001",
        site_code="casinoking",
    )
    _publish_existing_title_for_real_play(
        db_connection,
        title_code="hilo001",
        site_code="casinoking",
    )

    cases = [
        {
            "game_code": "mines",
            "title_code": mines_title["title_code"],
            "site_code": mines_title["site_code"],
            "grid_size": 9,
            "mine_count": 1,
            "config": {"grid_size": 9, "mine_count": 1},
        },
        {
            "game_code": "boxe",
            "title_code": "boxe001",
            "site_code": "casinoking",
            "grid_size": 4,
            "mine_count": 1,
            "config": {"rows": 4, "difficulty": "easy"},
        },
        {
            "game_code": "hi_lo",
            "title_code": "hilo001",
            "site_code": "casinoking",
            "grid_size": 52,
            "mine_count": 1,
            "config": {"deck": "standard_52"},
        },
    ]

    for case in cases:
        access_session_id = create_game_access_session(
            client,
            headers,
            game_code=str(case["game_code"]),
            title_code=str(case["title_code"]),
            site_code=str(case["site_code"]),
        )
        table_session = _create_table_session(
            client,
            headers,
            game_code=str(case["game_code"]),
            title_code=str(case["title_code"]),
            site_code=str(case["site_code"]),
            access_session_id=access_session_id,
        )
        platform_round_id = str(uuid4())
        idempotency_key = f"platform-host-owned-{case['game_code']}-{uuid4().hex}"
        request_fingerprint = f"fingerprint:{case['game_code']}:{uuid4().hex}"
        bet_amount = Decimal("1.250000")

        with db_connection.transaction():
            with db_connection.cursor() as cursor:
                result = open_game_round(
                    cursor=cursor,
                    game_code=str(case["game_code"]),
                    user_id=str(player["user_id"]),
                    game_session_id=platform_round_id,
                    idempotency_key=idempotency_key,
                    grid_size=int(case["grid_size"]),
                    mine_count=int(case["mine_count"]),
                    bet_amount=bet_amount,
                    wallet_type="cash",
                    table_session_id=table_session["id"],
                    access_session_id=access_session_id,
                    title_code=str(case["title_code"]),
                    site_code=str(case["site_code"]),
                    game_config_payload=dict(case["config"]),
                    request_fingerprint=request_fingerprint,
                )
                cursor.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        game_code,
                        title_code,
                        site_code,
                        access_session_id,
                        wallet_account_id,
                        wallet_type,
                        bet_amount,
                        status,
                        payout_amount,
                        start_ledger_transaction_id,
                        wallet_balance_after_start,
                        table_session_id,
                        idempotency_key,
                        request_fingerprint,
                        settlement_ledger_transaction_id,
                        closed_at
                    FROM platform_rounds
                    WHERE id = %s
                    """,
                    (platform_round_id,),
                )
                row = cursor.fetchone()

        assert row is not None
        assert str(row["id"]) == platform_round_id
        assert result["platform_round_id"] == platform_round_id
        assert str(row["user_id"]) == str(player["user_id"])
        assert row["game_code"] == case["game_code"]
        assert row["title_code"] == case["title_code"]
        assert row["site_code"] == case["site_code"]
        assert str(row["access_session_id"]) == access_session_id
        assert str(row["wallet_account_id"]) == str(result["wallet_account_id"])
        assert row["wallet_type"] == "cash"
        assert Decimal(row["bet_amount"]) == bet_amount
        assert row["status"] == "active"
        assert Decimal(row["payout_amount"]) == Decimal("0.000000")
        assert str(row["start_ledger_transaction_id"]) == str(result["ledger_transaction_id"])
        assert Decimal(row["wallet_balance_after_start"]) == Decimal(
            result["wallet_balance_after_start"]
        )
        assert str(row["table_session_id"]) == str(result["table_session_id"]) == table_session["id"]
        assert row["idempotency_key"] == idempotency_key
        assert row["request_fingerprint"] == request_fingerprint
        assert row["settlement_ledger_transaction_id"] is None
        assert row["closed_at"] is None


def _create_table_session(
    client,
    headers,
    *,
    game_code: str,
    title_code: str,
    site_code: str,
    access_session_id: str,
) -> dict[str, object]:
    response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _publish_existing_title_for_real_play(db_connection, *, title_code: str, site_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE site_titles
            SET lobby_visibility = 'visible',
                demo_enabled = true,
                real_enabled = true,
                updated_at = NOW()
            WHERE site_code = %s
              AND title_code = %s
            """,
            (site_code, title_code),
        )
