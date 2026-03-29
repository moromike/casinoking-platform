from __future__ import annotations


def _build_backoffice_payload() -> dict[str, object]:
    return {
        "rules_sections": {
            "ways_to_win": "<p>Pick at least one diamond, then collect.</p>",
            "payout_display": "<p>The highlighted multiplier is the payout available right now.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Authenticated players can inspect completed hands from account history.</p>",
        },
        "published_grid_sizes": [9, 16],
        "published_mine_counts": {
            "9": [1, 3, 5],
            "16": [1, 5, 8],
        },
        "default_mine_counts": {
            "9": 3,
            "16": 5,
        },
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
                "bet": "Place bet",
                "bet_loading": "Placing bet...",
                "collect": "Collect win",
                "collect_loading": "Collecting win...",
                "home": "Return home",
                "fullscreen": "Go fullscreen",
                "game_info": "Open game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }


def test_admin_can_save_mines_backoffice_draft_and_publish_it_explicitly(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-mines-backoffice-admin")

    get_response = client.get(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert get_response.status_code == 200
    initial_payload = get_response.json()["data"]
    assert initial_payload["game_code"] == "mines"
    assert "draft" in initial_payload
    assert "published" in initial_payload
    assert len(initial_payload["published"]["published_grid_sizes"]) >= 1

    update_payload = _build_backoffice_payload()
    update_payload["ui_labels"]["real"]["collect"] = "Collect win published marker"

    put_response = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
        json=update_payload,
    )
    assert put_response.status_code == 200
    draft_payload = put_response.json()["data"]
    assert draft_payload["draft"]["published_grid_sizes"] == [9, 16]
    assert draft_payload["draft"]["published_mine_counts"]["9"] == [1, 3, 5]
    assert draft_payload["draft"]["default_mine_counts"]["16"] == 5
    assert draft_payload["draft"]["ui_labels"]["real"]["bet"] == "Place bet"
    assert draft_payload["draft"]["ui_labels"]["real"]["collect"] == "Collect win published marker"
    assert draft_payload["draft_updated_by_admin_user_id"] == admin_user["user_id"]
    assert draft_payload["draft_updated_at"] is not None
    assert draft_payload["has_unpublished_changes"] is True

    public_runtime_before_publish = client.get("/games/mines/config")
    assert public_runtime_before_publish.status_code == 200
    public_payload_before_publish = public_runtime_before_publish.json()["data"]["presentation_config"]
    assert public_payload_before_publish["ui_labels"]["real"]["collect"] != "Collect win published marker"

    publish_response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200
    published_payload = publish_response.json()["data"]
    assert published_payload["published"]["published_grid_sizes"] == [9, 16]
    assert published_payload["published"]["ui_labels"]["real"]["collect"] == "Collect win published marker"
    assert published_payload["published_updated_by_admin_user_id"] == admin_user["user_id"]
    assert published_payload["published_at"] is not None
    assert published_payload["has_unpublished_changes"] is False

    public_runtime_after_publish = client.get("/games/mines/config")
    assert public_runtime_after_publish.status_code == 200
    public_payload_after_publish = public_runtime_after_publish.json()["data"]["presentation_config"]
    assert public_payload_after_publish["published_grid_sizes"] == [9, 16]
    assert public_payload_after_publish["rules_sections"]["ways_to_win"] == (
        "<p>Pick at least one diamond, then collect.</p>"
    )
    assert public_payload_after_publish["ui_labels"]["real"]["collect"] == "Collect win published marker"


def test_mines_start_rejects_configurations_not_published_by_backoffice(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-mines-backoffice-publish-admin")
    player = create_authenticated_player(prefix="integration-mines-backoffice-player")

    update_response = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
        json={
            **_build_backoffice_payload(),
            "published_grid_sizes": [9],
            "published_mine_counts": {
                "9": [1, 3, 5],
            },
            "default_mine_counts": {
                "9": 3,
            },
        },
    )
    assert update_response.status_code == 200

    publish_response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200

    blocked_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-unpublished-grid",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert blocked_start_response.status_code == 422
    assert blocked_start_response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "The selected grid_size and mine_count are not published",
        },
    }

    allowed_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-start-published-grid",
        },
        json={
            "grid_size": 9,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert allowed_start_response.status_code == 200
