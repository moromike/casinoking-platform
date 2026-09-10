from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]

from decimal import Decimal
from uuid import uuid4

from tests.integration.helpers import apri_partita_cavia, chiudi_partita_cavia, create_game_access_session




MINES_BET_AMOUNT = Decimal("10.000000")
MANICHINO_BET_AMOUNT = Decimal("7.000000")


def _published_round_setup(client) -> tuple[int, int, Decimal]:
    response = client.get("/games/mines/config")
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    presentation = payload.get("presentation_config") or {}
    grid_sizes = presentation.get("published_grid_sizes") or payload["supported_grid_sizes"]
    grid_size = 25 if 25 in grid_sizes else grid_sizes[0]
    mine_counts = (
        presentation.get("published_mine_counts", {}).get(str(grid_size))
        or payload["supported_mine_counts"][str(grid_size)]
    )
    default_mine_count = presentation.get("default_mine_counts", {}).get(str(grid_size))
    mine_count = default_mine_count if default_mine_count in mine_counts else mine_counts[len(mine_counts) // 2]
    multiplier = Decimal(payload["payout_ladders"][str(grid_size)][str(mine_count)][0])
    return grid_size, mine_count, multiplier


def test_financial_report_groups_house_result_by_game(
    client,
    create_admin_user,
    create_authenticated_player,
    mines_auth_headers,
    db_helpers, mines_db_helpers,
) -> None:
    """Mines vinta: casa incassa la puntata e paga la vincita; manichino perso: incassa solo."""
    finance_admin = create_admin_user(prefix="rib-report-admin")
    mines_player = create_authenticated_player(prefix="rib-report-mines")
    manichino_player = create_authenticated_player(prefix="rib-report-manichino")
    grid_size, mine_count, first_safe_multiplier = _published_round_setup(client)

    mines_headers = mines_auth_headers(mines_player["access_token"])
    mines_title_code = mines_auth_headers.implicit_title_code() or "mines_auth_default"
    mines_access_session_id = create_game_access_session(
        client, mines_headers, game_code="mines", title_code=mines_title_code
    )
    mines_start = client.post(
        "/games/mines/start",
        headers={**mines_headers, "Idempotency-Key": f"rib-report-mines-start-{uuid4().hex}"},
        json={
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": f"{MINES_BET_AMOUNT:.6f}",
            "wallet_type": "cash",
            "access_session_id": mines_access_session_id,
        },
    )
    assert mines_start.status_code == 200, mines_start.text
    mines_session_id = mines_start.json()["data"]["game_session_id"]
    mine_positions = set(mines_db_helpers.get_mine_positions(mines_session_id))
    safe_cell = next(cell for cell in range(grid_size) if cell not in mine_positions)
    mines_reveal = client.post(
        "/games/mines/reveal",
        headers=mines_headers,
        json={"game_session_id": mines_session_id, "cell_index": safe_cell},
    )
    assert mines_reveal.status_code == 200, mines_reveal.text
    mines_cashout = client.post(
        "/games/mines/cashout",
        headers={**mines_headers, "Idempotency-Key": f"rib-report-mines-cashout-{uuid4().hex}"},
        json={"game_session_id": mines_session_id},
    )
    assert mines_cashout.status_code == 200, mines_cashout.text

    manichino_headers = mines_auth_headers(manichino_player["access_token"], include_game_launch_token=False)
    manichino_round = apri_partita_cavia(
        client,
        manichino_headers,
        bet_amount=f"{MANICHINO_BET_AMOUNT:.6f}",
        prefisso_idempotenza=f"rib-man-{uuid4().hex[:8]}",
    )
    chiudi_partita_cavia(
        client,
        manichino_headers,
        game_launch_token=manichino_round["game_launch_token"],
        game_session_id=manichino_round["game_session_id"],
        esito="perdita",
        prefisso_idempotenza=f"rib-man-{uuid4().hex[:8]}",
    )

    report_response = client.get(
        "/admin/reports/financial/sessions",
        params={"email_query": "rib-report-"},
        headers=mines_auth_headers(finance_admin["access_token"]),
    )
    assert report_response.status_code == 200, report_response.text
    results = {row["game_code"]: row for row in report_response.json()["data"]["game_results"]}

    # Confronti numerici: la vincita Mines e' un costo della casa, la perdita manichino un ricavo.
    assert set(results) == {"mines", "manichino"}
    assert Decimal(results["mines"]["bank_delta"]) == MINES_BET_AMOUNT - (
        MINES_BET_AMOUNT * first_safe_multiplier
    )
    assert Decimal(results["manichino"]["bank_delta"]) == MANICHINO_BET_AMOUNT
