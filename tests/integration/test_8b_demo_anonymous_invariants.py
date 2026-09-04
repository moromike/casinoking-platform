from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
import pytest


@pytest.fixture(scope="module", autouse=True)
def boxe_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        _seed_boxe_catalog(connection)
        yield


@pytest.fixture(scope="module", autouse=True)
def hi_lo_schema(database_url: str):
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
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


def _get_demo_launch_token(*, client, game_code: str, title_code: str) -> str:
    """Obtain an anonymous demo launch token (no user created)."""
    token_resp = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.88.0.{uuid4().int % 250 + 1}"},
    )
    assert token_resp.status_code == 200, token_resp.text
    anonymous_token = token_resp.json()["data"]["anonymous_token"]

    launch_resp = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anonymous_token},
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": "casinoking",
        },
    )
    assert launch_resp.status_code == 200, launch_resp.text
    return launch_resp.json()["data"]["game_launch_token"]


def test_demo_anonymous_boxe_does_not_create_user(
    client,
    db_connection,
):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        users_before = int(cursor.fetchone()["count"])

    demo_token = _get_demo_launch_token(
        client=client,
        game_code="boxe",
        title_code="boxe001",
    )

    start_resp = client.post(
        "/games/boxe/start",
        headers={
            "Idempotency-Key": f"demo-anon-boxe-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "boxe001",
            "rows": 4,
            "difficulty": "easy",
            "bet_amount": "1.00",
            "wallet_source": "demo",
            "client_seed": "anon-seed",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    data = start_resp.json()["data"]
    assert data["status"] == "active"

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        users_after = int(cursor.fetchone()["count"])

    assert users_after == users_before, "Anonymous demo must not create a user row"


def test_demo_anonymous_hi_lo_does_not_create_user(
    client,
    db_connection,
):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        users_before = int(cursor.fetchone()["count"])

    demo_token = _get_demo_launch_token(
        client=client,
        game_code="hi_lo",
        title_code="hilo001",
    )

    start_resp = client.post(
        "/games/hi-lo/start",
        headers={
            "Idempotency-Key": f"demo-anon-hilo-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "hilo001",
            "bet_amount": "1",
            "wallet_source": "demo",
            "client_seed": "anon-seed",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    data = start_resp.json()["data"]
    assert data["wallet_source"] == "demo"

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        users_after = int(cursor.fetchone()["count"])

    assert users_after == users_before, "Anonymous demo must not create a user row"


def test_demo_anonymous_boxe_no_platform_round_or_ledger(
    client,
    db_connection,
):
    demo_token = _get_demo_launch_token(
        client=client,
        game_code="boxe",
        title_code="boxe001",
    )

    start_resp = client.post(
        "/games/boxe/start",
        headers={
            "Idempotency-Key": f"demo-anon-boxe-ledger-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "boxe001",
            "rows": 4,
            "difficulty": "easy",
            "bet_amount": "1.00",
            "wallet_source": "demo",
            "client_seed": "anon-seed",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    round_id = start_resp.json()["data"]["round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS count FROM platform_rounds WHERE id = %s",
            (round_id,),
        )
        assert cursor.fetchone()["count"] == 0, "Demo round must not write platform_rounds"

        cursor.execute(
            """
            SELECT COUNT(*) AS count FROM ledger_transactions lt
            JOIN ledger_entries le ON le.transaction_id = lt.id
            WHERE lt.reference_id = %s
            """,
            (round_id,),
        )
        assert cursor.fetchone()["count"] == 0, "Demo round must not write ledger"


def test_demo_anonymous_hi_lo_no_platform_round_or_ledger(
    client,
    db_connection,
):
    demo_token = _get_demo_launch_token(
        client=client,
        game_code="hi_lo",
        title_code="hilo001",
    )

    start_resp = client.post(
        "/games/hi-lo/start",
        headers={
            "Idempotency-Key": f"demo-anon-hilo-ledger-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "hilo001",
            "bet_amount": "1",
            "wallet_source": "demo",
            "client_seed": "anon-seed",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    round_id = start_resp.json()["data"]["round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS count FROM platform_rounds WHERE id = %s",
            (round_id,),
        )
        assert cursor.fetchone()["count"] == 0, "Demo round must not write platform_rounds"

        cursor.execute(
            """
            SELECT COUNT(*) AS count FROM ledger_transactions lt
            JOIN ledger_entries le ON le.transaction_id = lt.id
            WHERE lt.reference_id = %s
            """,
            (round_id,),
        )
        assert cursor.fetchone()["count"] == 0, "Demo round must not write ledger"


def test_demo_launch_token_cannot_start_real_boxe(
    client,
    create_authenticated_player,
    auth_headers,
):
    player = create_authenticated_player(prefix="demo-real-iso-boxe")
    demo_token = _get_demo_launch_token(
        client=client,
        game_code="boxe",
        title_code="boxe001",
    )

    start_resp = client.post(
        "/games/boxe/start",
        headers={
            "Idempotency-Key": f"demo-real-iso-boxe-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "boxe001",
            "rows": 4,
            "difficulty": "easy",
            "bet_amount": "1.00",
            "wallet_source": "cash",
            "client_seed": "iso-seed",
        },
    )
    assert start_resp.status_code == 422, start_resp.text
    assert start_resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_demo_launch_token_cannot_start_real_hi_lo(
    client,
    create_authenticated_player,
    auth_headers,
):
    player = create_authenticated_player(prefix="demo-real-iso-hilo")
    demo_token = _get_demo_launch_token(
        client=client,
        game_code="hi_lo",
        title_code="hilo001",
    )

    start_resp = client.post(
        "/games/hi-lo/start",
        headers={
            "Idempotency-Key": f"demo-real-iso-hilo-{uuid4().hex}",
            "X-Game-Launch-Token": demo_token,
        },
        json={
            "title_code": "hilo001",
            "bet_amount": "1",
            "wallet_source": "cash",
            "client_seed": "iso-seed",
        },
    )
    assert start_resp.status_code == 422, start_resp.text
    assert start_resp.json()["error"]["code"] == "VALIDATION_ERROR"
