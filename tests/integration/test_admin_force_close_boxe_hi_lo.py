from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
import pytest

from tests.integration.helpers import (
    BOXE_SCHEMA_DOWN_SQL,
    HI_LO_SCHEMA_DOWN_SQL,
    apply_boxe_schema_migrations,
    apply_hi_lo_schema_migrations,
)


@pytest.fixture(scope="module", autouse=True)
def boxe_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(BOXE_SCHEMA_DOWN_SQL)
        apply_boxe_schema_migrations(connection)
        _seed_boxe_catalog(connection)
        yield


@pytest.fixture(scope="module", autouse=True)
def hi_lo_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(HI_LO_SCHEMA_DOWN_SQL)
        apply_hi_lo_schema_migrations(connection)
        _seed_hi_lo_catalog(connection)
        yield


def _seed_boxe_catalog(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
            VALUES ('boxe', 'BOXE', 'app.modules.games.boxe', 'active')
            ON CONFLICT (engine_code) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                runtime_module = EXCLUDED.runtime_module,
                status = 'active'
            """
        )
        cursor.execute(
            """
            INSERT INTO game_titles (
                title_code, engine_code, display_name, status, is_master, source_title_code
            )
            VALUES ('boxe001', 'boxe', 'BOXE 001', 'active', false, 'boxe')
            ON CONFLICT (title_code) DO UPDATE
            SET engine_code = EXCLUDED.engine_code,
                display_name = EXCLUDED.display_name,
                status = 'active'
            """
        )


def _seed_hi_lo_catalog(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
            VALUES ('hi_lo', 'HI-LO', 'app.modules.games.hi_lo', 'active')
            ON CONFLICT (engine_code) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                runtime_module = EXCLUDED.runtime_module,
                status = 'active'
            """
        )
        cursor.execute(
            """
            INSERT INTO game_titles (
                title_code, engine_code, display_name, status, is_master, source_title_code
            )
            VALUES ('hilo001', 'hi_lo', 'HI-LO 001', 'active', false, 'hi_lo')
            ON CONFLICT (title_code) DO UPDATE
            SET engine_code = EXCLUDED.engine_code,
                display_name = EXCLUDED.display_name,
                status = 'active'
            """
        )


def _create_minimal_active_session(
    db_connection,
    player,
    game_code: str,
    title_code: str,
    bet_amount: str = "5.000000",
    table_budget_amount: str = "20.000000",
) -> dict[str, str]:
    user_id = str(player["user_id"])
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, balance_snapshot, ledger_account_id
            FROM wallet_accounts
            WHERE user_id = %s AND wallet_type = 'cash'
            """,
            (user_id,),
        )
        wallet = cursor.fetchone()
        wallet_id = str(wallet["id"])
        wallet_balance = Decimal(wallet["balance_snapshot"])

        access_session_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO game_access_sessions (id, user_id, game_code, status, title_code, site_code)
            VALUES (%s, %s, %s, 'active', %s, 'casinoking')
            """,
            (access_session_id, user_id, game_code, title_code),
        )

        table_session_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO game_table_sessions (
                id, access_session_id, user_id, game_code, wallet_account_id,
                wallet_type, table_budget_amount, loss_limit_amount,
                loss_reserved_amount, loss_consumed_amount, table_balance_amount,
                status, title_code, site_code
            )
            VALUES (%s, %s, %s, %s, %s, 'cash', %s, %s, %s, 0, %s, 'active', %s, 'casinoking')
            """,
            (
                table_session_id,
                access_session_id,
                user_id,
                game_code,
                wallet_id,
                table_budget_amount,
                table_budget_amount,
                bet_amount,
                str(Decimal(table_budget_amount) - Decimal(bet_amount)),
                title_code,
            ),
        )

        start_tx_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO ledger_transactions (
                id, user_id, transaction_type, reference_type, reference_id,
                idempotency_key, metadata_json
            )
            VALUES (%s, %s, 'bet', 'platform_round', %s, %s, '{}')
            """,
            (start_tx_id, user_id, str(uuid4()), f"start-tx-{uuid4().hex[:8]}"),
        )

        platform_round_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO platform_rounds (
                id, user_id, game_code, wallet_account_id, wallet_type,
                bet_amount, status, payout_amount, start_ledger_transaction_id,
                wallet_balance_after_start, table_session_id, title_code, site_code,
                idempotency_key, request_fingerprint, created_at
            )
            VALUES (
                %s, %s, %s, %s, 'cash',
                %s, 'active', 0, %s,
                %s, %s, %s, 'casinoking',
                %s, %s, now()
            )
            """,
            (
                platform_round_id,
                user_id,
                game_code,
                wallet_id,
                bet_amount,
                start_tx_id,
                str(wallet_balance - Decimal(bet_amount)),
                table_session_id,
                title_code,
                f"idemp-{uuid4().hex[:8]}",
                f"fp-{uuid4().hex[:8]}",
            ),
        )

        return {
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
            "platform_round_id": platform_round_id,
            "wallet_id": wallet_id,
        }


def _create_boxe_round(db_connection, player, platform_round_id: str, access_session_id: str, table_session_id: str):
    user_id = str(player["user_id"])
    with db_connection.cursor() as cursor:
        boxe_round_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO boxe_rounds (
                id, platform_round_id, player_id, title_code, site_code,
                status, rows_count, difficulty, current_step, safe_picks_count,
                bet_amount, multiplier_current, payout_current, config_snapshot_json,
                multiplier_table_json, fairness_version, server_seed, server_seed_hash,
                client_seed, nonce, start_idempotency_key, request_fingerprint,
                access_session_id, table_session_id
            )
            VALUES (
                %s, %s, %s, 'boxe001', 'casinoking',
                'active', 4, 'easy', 0, 0,
                5.000000, 1.0000, 0, '{}',
                '{}', 'v1', 'seed', 'hash',
                'client', 0, %s, %s,
                %s, %s
            )
            """,
            (
                boxe_round_id,
                platform_round_id,
                user_id,
                f"start-{uuid4().hex[:8]}",
                f"fp-{uuid4().hex[:8]}",
                access_session_id,
                table_session_id,
            ),
        )
        return boxe_round_id


def _create_hi_lo_round(db_connection, player, platform_round_id: str):
    user_id = str(player["user_id"])
    with db_connection.cursor() as cursor:
        hi_lo_round_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO hi_lo_rounds (
                id, platform_round_id, player_id, title_code, site_code,
                status, wallet_source, bet_amount, current_card_rank,
                current_card_suit, current_draw_index, correct_predictions_count,
                active_skip_count, cumulative_success_probability, multiplier_current,
                payout_current, fairness_version, server_seed, server_seed_hash,
                client_seed, round_nonce, start_idempotency_key, request_fingerprint
            )
            VALUES (
                %s, %s, %s, 'hilo001', 'casinoking',
                'active', 'cash', 5.000000, 7,
                'hearts', 0, 0,
                0, 1, 1.0000,
                0, 'v1', 'seed', 'hash',
                'client', 0, %s, %s
            )
            """,
            (
                hi_lo_round_id,
                platform_round_id,
                user_id,
                f"start-{uuid4().hex[:8]}",
                f"fp-{uuid4().hex[:8]}",
            ),
        )
        return hi_lo_round_id


def _cleanup_rounds(db_connection, platform_round_id: str, game_round_id: str | None = None, table_name: str | None = None):
    with db_connection.cursor() as cursor:
        if table_name:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (game_round_id,))
        cursor.execute("DELETE FROM platform_rounds WHERE id = %s", (platform_round_id,))


def test_admin_force_close_boxe_coherence(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_connection,
    request,
):
    player = create_authenticated_player(prefix="admin-force-close-boxe")
    admin = create_admin_user(prefix="admin-force-close-boxe-admin")
    session_data = _create_minimal_active_session(
        db_connection=db_connection,
        player=player,
        game_code="boxe",
        title_code="boxe001",
    )
    boxe_round_id = _create_boxe_round(
        db_connection=db_connection,
        player=player,
        platform_round_id=session_data["platform_round_id"],
        access_session_id=session_data["access_session_id"],
        table_session_id=session_data["table_session_id"],
    )
    request.addfinalizer(
        lambda: _cleanup_rounds(
            db_connection,
            session_data["platform_round_id"],
            boxe_round_id,
            "boxe_rounds",
        )
    )

    response = client.post(
        f"/admin/users/{player['user_id']}/sessions/force-close",
        headers=auth_headers(str(admin["access_token"])),
        json={
            "game_code": "boxe",
            "reason": "integration test",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert len(payload["voided_rounds"]) == 1
    assert payload["voided_rounds"][0]["round_id"] == session_data["platform_round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM platform_rounds WHERE id = %s",
            (session_data["platform_round_id"],),
        )
        pr = cursor.fetchone()
        assert pr["status"] == "cancelled"

        cursor.execute(
            "SELECT status, outcome, terminal_reason FROM boxe_rounds WHERE id = %s",
            (boxe_round_id,),
        )
        br = cursor.fetchone()
        assert br["status"] == "cancelled"
        assert br["outcome"] == "admin_force_close"
        assert br["terminal_reason"] == "admin_force_close"


def test_admin_force_close_hi_lo_coherence(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    db_connection,
    request,
):
    player = create_authenticated_player(prefix="admin-force-close-hi-lo")
    admin = create_admin_user(prefix="admin-force-close-hi-lo-admin")
    session_data = _create_minimal_active_session(
        db_connection=db_connection,
        player=player,
        game_code="hi_lo",
        title_code="hilo001",
    )
    hi_lo_round_id = _create_hi_lo_round(
        db_connection=db_connection,
        player=player,
        platform_round_id=session_data["platform_round_id"],
    )
    request.addfinalizer(
        lambda: _cleanup_rounds(
            db_connection,
            session_data["platform_round_id"],
            hi_lo_round_id,
            "hi_lo_rounds",
        )
    )

    response = client.post(
        f"/admin/users/{player['user_id']}/sessions/force-close",
        headers=auth_headers(str(admin["access_token"])),
        json={
            "game_code": "hi_lo",
            "reason": "integration test",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert len(payload["voided_rounds"]) == 1
    assert payload["voided_rounds"][0]["round_id"] == session_data["platform_round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM platform_rounds WHERE id = %s",
            (session_data["platform_round_id"],),
        )
        pr = cursor.fetchone()
        assert pr["status"] == "cancelled"

        cursor.execute(
            "SELECT status, outcome, terminal_reason FROM hi_lo_rounds WHERE id = %s",
            (hi_lo_round_id,),
        )
        hlr = cursor.fetchone()
        assert hlr["status"] == "cancelled"
        assert hlr["outcome"] == "admin_force_close"
        assert hlr["terminal_reason"] == "admin_force_close"
