from __future__ import annotations
import pytest

from decimal import Decimal
from uuid import uuid4

from tests.integration.helpers import (
    apri_partita_cavia,
    chiudi_partita_cavia,
    create_game_access_session,
)


def test_table_session_rejects_game_code_unknown_to_catalog(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-unknown-game")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "slots",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
        },
    )

    assert create_response.status_code == 422, create_response.text


def test_table_session_reserves_and_consumes_loss(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-loss")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    cavia = apri_partita_cavia(
        client,
        headers,
        bet_amount="4.000000",
        table_budget_amount="10.000000",
        prefisso_idempotenza="gts-loss",
    )
    assert cavia["game_launch_token"]
    assert cavia["access_session_id"]
    assert cavia["game_session_id"]
    assert cavia["table_session_id"]
    table_session_id = cavia["table_session_id"]

    reserved_response = client.get(f"/table-sessions/{table_session_id}", headers=headers)
    assert reserved_response.status_code == 200
    reserved_session = reserved_response.json()["data"]
    assert reserved_session["table_balance_amount"] == "6.000000"
    assert reserved_session["loss_reserved_amount"] == "4.000000"
    assert reserved_session["loss_consumed_amount"] == "0.000000"
    assert reserved_session["loss_remaining_amount"] == "6.000000"

    loss_response = chiudi_partita_cavia(
        client,
        headers,
        game_launch_token=cavia["game_launch_token"],
        game_session_id=cavia["game_session_id"],
        esito="perdita",
        prefisso_idempotenza="gts-loss",
    )
    assert loss_response.status_code == 200, loss_response.text

    consumed_response = client.get(f"/table-sessions/{table_session_id}", headers=headers)
    assert consumed_response.status_code == 200
    consumed_session = consumed_response.json()["data"]
    assert consumed_session["table_balance_amount"] == "6.000000"
    assert consumed_session["loss_reserved_amount"] == "0.000000"
    assert consumed_session["loss_consumed_amount"] == "4.000000"
    assert consumed_session["loss_remaining_amount"] == "6.000000"


def test_table_session_releases_reserved_amount_on_cashout(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-cashout")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    cavia = apri_partita_cavia(
        client,
        headers,
        bet_amount="4.000000",
        table_budget_amount="10.000000",
        prefisso_idempotenza="gts-win",
    )
    assert cavia["game_launch_token"]
    assert cavia["access_session_id"]
    assert cavia["game_session_id"]
    assert cavia["table_session_id"]
    table_session_id = cavia["table_session_id"]

    cashout_response = chiudi_partita_cavia(
        client,
        headers,
        game_launch_token=cavia["game_launch_token"],
        game_session_id=cavia["game_session_id"],
        esito="vincita",
        payout_amount="5.000000",
        prefisso_idempotenza="gts-win",
    )
    assert cashout_response.status_code == 200, cashout_response.text
    payout_amount = Decimal(cashout_response.json()["data"]["payout_amount"])

    released_response = client.get(f"/table-sessions/{table_session_id}", headers=headers)
    assert released_response.status_code == 200
    released_session = released_response.json()["data"]
    expected_table_balance = Decimal("6.000000") + payout_amount
    assert released_session["table_balance_amount"] == f"{expected_table_balance:.6f}"
    assert released_session["loss_reserved_amount"] == "0.000000"
    assert released_session["loss_consumed_amount"] == "0.000000"
    assert released_session["loss_remaining_amount"] == "10.000000"


def test_table_session_rejects_bet_over_remaining_limit(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-limit")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    launch_response = client.post(
        "/games/manichino/launch-token", headers=headers, json={}
    )
    assert launch_response.status_code == 200, launch_response.text
    game_launch_token = launch_response.json()["data"]["game_launch_token"]
    access_session_id = create_game_access_session(
        client, headers, game_code="manichino", title_code="manichino_test"
    )

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "wallet_type": "cash",
            "table_budget_amount": "3.000000",
            "access_session_id": access_session_id,
        },
    )
    assert create_response.status_code == 200, create_response.text
    table_session = create_response.json()["data"]

    start_response = client.post(
        "/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"gts-limit-{uuid4().hex}",
        },
        json={
            "bet_amount": "4.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
            "table_session_id": table_session["id"],
        },
    )
    assert start_response.status_code == 422
    assert start_response.json()["error"]["message"] == "Table session limit exceeded"


def test_table_session_cannot_be_used_by_another_player(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    owner = create_authenticated_player(prefix="integration-table-owner")
    other = create_authenticated_player(prefix="integration-table-other")
    owner_headers = auth_headers(owner["access_token"], include_game_launch_token=False)
    other_headers = auth_headers(other["access_token"], include_game_launch_token=False)

    launch_response = client.post(
        "/games/manichino/launch-token", headers=other_headers, json={}
    )
    assert launch_response.status_code == 200, launch_response.text
    game_launch_token = launch_response.json()["data"]["game_launch_token"]
    other_access_session_id = create_game_access_session(
        client, other_headers, game_code="manichino", title_code="manichino_test"
    )

    create_response = client.post(
        "/table-sessions",
        headers=owner_headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
        },
    )
    assert create_response.status_code == 200, create_response.text
    table_session = create_response.json()["data"]

    other_read_response = client.get(
        f"/table-sessions/{table_session['id']}",
        headers=other_headers,
    )
    assert other_read_response.status_code == 404

    start_response = client.post(
        "/games/manichino/start",
        headers={
            **other_headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"gts-cross-{uuid4().hex}",
        },
        json={
            "bet_amount": "4.000000",
            "wallet_type": "cash",
            "access_session_id": other_access_session_id,
            "table_session_id": table_session["id"],
        },
    )
    assert start_response.status_code == 422
    assert start_response.json()["error"]["message"] == "Table session not found"

    table_row = db_helpers.fetchone(
        """
        SELECT table_balance_amount, loss_reserved_amount, loss_consumed_amount
        FROM game_table_sessions
        WHERE id = %s
        """,
        (table_session["id"],),
    )
    assert table_row is not None
    assert f"{table_row['table_balance_amount']:.6f}" == "10.000000"
    assert f"{table_row['loss_reserved_amount']:.6f}" == "0.000000"
    assert f"{table_row['loss_consumed_amount']:.6f}" == "0.000000"


def test_table_session_limits_do_not_default_to_full_wallet_balance(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="integration-table-safe-default")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE wallet_accounts
            SET balance_snapshot = 37.000000
            WHERE user_id = %s
              AND wallet_type = 'cash'
            """,
            (player["user_id"],),
        )

    limits_response = client.get("/table-sessions/limits?wallet_type=cash", headers=headers)

    assert limits_response.status_code == 200, limits_response.text
    limits = limits_response.json()["data"]
    assert limits["wallet_balance_available"] == "37.000000"
    assert limits["max_table_amount"] == "37.000000"
    assert limits["default_table_amount"] == "0.000000"


def test_table_session_limits_default_to_maximum_when_balance_can_cover_it(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-max-default")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    limits_response = client.get("/table-sessions/limits?wallet_type=cash", headers=headers)

    assert limits_response.status_code == 200, limits_response.text
    limits = limits_response.json()["data"]
    assert limits["wallet_balance_available"] == "1000.000000"
    assert limits["max_table_amount"] == "100.000000"
    assert limits["default_table_amount"] == "100.000000"


def test_table_session_rejects_full_wallet_balance_as_budget(
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    player = create_authenticated_player(prefix="integration-table-no-all-in")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE wallet_accounts
            SET balance_snapshot = 37.000000
            WHERE user_id = %s
              AND wallet_type = 'cash'
            """,
            (player["user_id"],),
        )

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "wallet_type": "cash",
            "table_budget_amount": "37.000000",
        },
    )

    assert create_response.status_code == 409
    assert create_response.json()["error"]["code"] == "TABLE_LIMIT_EXCEEDED"
    assert (
        create_response.json()["error"]["message"]
        == "Table session amount must be lower than available balance"
    )
