from __future__ import annotations

from uuid import uuid4


def _published_round_setup(client) -> dict[str, int]:
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

    return {"grid_size": grid_size, "mine_count": mine_count}


def test_catalog_endpoints_expose_seeded_engine_title_site(client) -> None:
    title_response = client.get("/catalog/titles/mines_classic")
    assert title_response.status_code == 200
    title_payload = title_response.json()["data"]
    assert title_payload["title_code"] == "mines_classic"
    assert title_payload["engine_code"] == "mines"
    assert title_payload["engine"]["engine_code"] == "mines"

    site_response = client.get("/catalog/sites/casinoking/titles")
    assert site_response.status_code == 200
    site_payload = site_response.json()["data"]
    assert site_payload["site"]["site_code"] == "casinoking"
    assert [title["title_code"] for title in site_payload["titles"]] == ["mines_classic"]
    assert site_payload["titles"][0]["site_title_status"] == "active"


def test_launch_token_is_title_and_site_aware_and_rejects_demo(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-title-launch")

    issue_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
        json={
            "title_code": "mines_classic",
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert issue_response.status_code == 200
    issue_payload = issue_response.json()["data"]
    assert issue_payload["game_code"] == "mines"
    assert issue_payload["title_code"] == "mines_classic"
    assert issue_payload["site_code"] == "casinoking"
    assert issue_payload["mode"] == "real"

    validate_response = client.post(
        "/games/mines/launch/validate",
        json={"game_launch_token": issue_payload["game_launch_token"]},
    )
    assert validate_response.status_code == 200
    validate_payload = validate_response.json()["data"]
    assert validate_payload["title_code"] == "mines_classic"
    assert validate_payload["site_code"] == "casinoking"
    assert validate_payload["mode"] == "real"

    demo_response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
        json={
            "title_code": "mines_classic",
            "site_code": "casinoking",
            "mode": "demo",
        },
    )
    assert demo_response.status_code == 501
    assert demo_response.json()["error"]["message"] == (
        "Demo launch mode is not available until Phase 6"
    )


def test_title_and_site_code_are_persisted_for_access_table_and_rounds(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    round_setup = _published_round_setup(client)
    player = create_authenticated_player(prefix="integration-title-propagation")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)

    access_response = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "title_code": "mines_classic",
            "site_code": "casinoking",
        },
    )
    assert access_response.status_code == 200
    access_payload = access_response.json()["data"]
    assert access_payload["title_code"] == "mines_classic"
    assert access_payload["site_code"] == "casinoking"

    table_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "title_code": "mines_classic",
            "site_code": "casinoking",
            "wallet_type": "cash",
            "table_budget_amount": "5.000000",
            "access_session_id": access_payload["id"],
        },
    )
    assert table_response.status_code == 200
    table_payload = table_response.json()["data"]
    assert table_payload["title_code"] == "mines_classic"
    assert table_payload["site_code"] == "casinoking"

    launch_response = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={
            "title_code": "mines_classic",
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert launch_response.status_code == 200
    game_launch_token = launch_response.json()["data"]["game_launch_token"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"integration-title-propagation-{uuid4()}",
        },
        json={
            "grid_size": round_setup["grid_size"],
            "mine_count": round_setup["mine_count"],
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": access_payload["id"],
            "table_session_id": table_payload["id"],
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()["data"]
    assert start_payload["title_code"] == "mines_classic"
    assert start_payload["site_code"] == "casinoking"

    platform_round = db_helpers.fetchone(
        """
        SELECT title_code, site_code
        FROM platform_rounds
        WHERE id = %s
        """,
        (start_payload["game_session_id"],),
    )
    mines_round = db_helpers.fetchone(
        """
        SELECT title_code, site_code
        FROM mines_game_rounds
        WHERE id = %s
        """,
        (start_payload["game_session_id"],),
    )
    assert platform_round == {"title_code": "mines_classic", "site_code": "casinoking"}
    assert mines_round == {"title_code": "mines_classic", "site_code": "casinoking"}
