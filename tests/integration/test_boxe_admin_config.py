from __future__ import annotations

from copy import deepcopy
from uuid import uuid4


def _seed_boxe_title(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
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
                title_code,
                engine_code,
                display_name,
                status,
                is_master,
                source_title_code
            )
            VALUES
                ('boxe', 'boxe', 'BOXE Master', 'active', true, NULL),
                (%s, 'boxe', 'BOXE Config Test', 'active', false, 'boxe')
            ON CONFLICT (title_code) DO UPDATE
            SET engine_code = EXCLUDED.engine_code,
                display_name = EXCLUDED.display_name,
                status = 'active',
                is_master = EXCLUDED.is_master,
                source_title_code = EXCLUDED.source_title_code,
                updated_at = NOW()
            """,
            (title_code,),
        )
        cursor.execute(
            """
            INSERT INTO site_titles (
                site_code,
                title_code,
                position,
                status,
                lobby_visibility,
                demo_enabled,
                real_enabled,
                lobby_display_name,
                lobby_description,
                featured
            )
            VALUES
                ('casinoking', 'boxe', 900, 'active', 'hidden', false, false, 'BOXE Master', 'Master BOXE', false),
                ('casinoking', %s, 901, 'active', 'visible', true, true, 'BOXE', 'BOXE test title', false)
            ON CONFLICT (site_code, title_code) DO UPDATE
            SET status = 'active',
                lobby_visibility = EXCLUDED.lobby_visibility,
                demo_enabled = EXCLUDED.demo_enabled,
                real_enabled = EXCLUDED.real_enabled,
                lobby_display_name = EXCLUDED.lobby_display_name,
                lobby_description = EXCLUDED.lobby_description,
                featured = EXCLUDED.featured,
                updated_at = NOW()
            """,
            (title_code,),
        )


def _cleanup_boxe_title(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM admin_audit_log WHERE resource_id = %s", (title_code,))
        cursor.execute("DELETE FROM boxe_picks WHERE round_id IN (SELECT id FROM boxe_rounds WHERE title_code = %s)", (title_code,))
        cursor.execute("DELETE FROM boxe_idempotency_keys WHERE round_id IN (SELECT id FROM boxe_rounds WHERE title_code = %s)", (title_code,))
        cursor.execute("DELETE FROM boxe_idempotency_keys WHERE session_id IN (SELECT id FROM boxe_sessions WHERE title_code = %s)", (title_code,))
        cursor.execute("DELETE FROM boxe_rounds WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM boxe_sessions WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM boxe_admin_config WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def _boxe_admin_payload() -> dict[str, object]:
    copy = {
        locale: {
            "game.title": f"BOXE {locale.upper()}",
            "actions.bet": "Bet",
            "actions.collect": "Collect",
            "round.won_notice": "You won {{amount}}.",
            "round.lost_notice": "You picked a mine.",
            "rules.bet_collect": "Bet, pick, collect.",
            "errors.insufficient_balance": "Insufficient balance.",
            "errors.round_closed": "Round closed.",
            "errors.network_retry": "Retry the same action.",
        }
        for locale in ("it", "en", "de", "es")
    }
    rules_html = {
        locale: {"bet_collect": f"<p>Rules for {locale}.</p>"}
        for locale in ("it", "en", "de", "es")
    }
    return {
        "rows_enabled": [4, 8],
        "default_rows": 4,
        "difficulty_enabled": ["easy", "hard"],
        "default_difficulty": "hard",
        "copy": copy,
        "rules_html": rules_html,
    }


def test_admin_can_save_publish_and_read_boxe_config(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-boxe-admin-config")
    title_code = f"boxe_cfg_{uuid4().hex[:8]}"
    _seed_boxe_title(db_connection, title_code)

    try:
        headers = auth_headers(admin_user["access_token"])
        get_response = client.get(
            "/admin/games/boxe/config",
            params={"title_code": title_code},
            headers=headers,
        )
        assert get_response.status_code == 200
        initial = get_response.json()["data"]
        assert initial["game_code"] == "boxe"
        assert initial["draft"]["rows_enabled"] == [4, 5, 6, 7, 8]
        assert initial["has_unpublished_changes"] is False

        payload = _boxe_admin_payload()
        draft_response = client.put(
            "/admin/games/boxe/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=payload,
        )
        assert draft_response.status_code == 200, draft_response.text
        draft = draft_response.json()["data"]
        assert draft["draft"]["rows_enabled"] == [4, 8]
        assert draft["draft"]["default_difficulty"] == "hard"
        assert draft["draft"]["copy"]["it"]["game.title"] == "BOXE IT"
        assert draft["draft_updated_by_admin_user_id"] == admin_user["user_id"]
        assert draft["has_unpublished_changes"] is True

        public_before = client.get("/games/boxe/config", params={"title_code": title_code})
        assert public_before.status_code == 200
        assert public_before.json()["data"]["rows_enabled"] == [4, 5, 6, 7, 8]

        publish_response = client.post(
            "/admin/games/boxe/config/publish",
            params={"title_code": title_code},
            headers=headers,
        )
        assert publish_response.status_code == 200, publish_response.text
        published = publish_response.json()["data"]
        assert published["published"]["rows_enabled"] == [4, 8]
        assert published["published"]["default_rows"] == 4
        assert published["has_unpublished_changes"] is False

        public_after = client.get("/games/boxe/config", params={"title_code": title_code})
        assert public_after.status_code == 200
        public_payload = public_after.json()["data"]
        assert public_payload["rows_enabled"] == [4, 8]
        assert public_payload["default_difficulty"] == "hard"
        assert public_payload["presentation_config"]["copy"]["it"]["game.title"] == "BOXE IT"

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT action_kind, resource_kind, payload_json
                FROM admin_audit_log
                WHERE resource_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (title_code,),
            )
            audit_row = cursor.fetchone()
        assert audit_row is not None
        assert audit_row["action_kind"] == "title_config_publish"
        assert audit_row["resource_kind"] == "title"
        assert audit_row["payload_json"]["engine_code"] == "boxe"
    finally:
        _cleanup_boxe_title(db_connection, title_code)


def test_boxe_config_validation_rejects_invalid_rows_defaults_and_missing_locale(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-boxe-admin-validation")
    title_code = f"boxe_cfg_{uuid4().hex[:8]}"
    _seed_boxe_title(db_connection, title_code)
    headers = auth_headers(admin_user["access_token"])

    try:
        invalid_rows = _boxe_admin_payload()
        invalid_rows["rows_enabled"] = [3, 8]
        response = client.put(
            "/admin/games/boxe/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=invalid_rows,
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

        invalid_default = _boxe_admin_payload()
        invalid_default["default_difficulty"] = "medium"
        response = client.put(
            "/admin/games/boxe/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=invalid_default,
        )
        assert response.status_code == 422

        missing_locale = deepcopy(_boxe_admin_payload())
        del missing_locale["copy"]["de"]
        response = client.put(
            "/admin/games/boxe/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=missing_locale,
        )
        assert response.status_code == 422
        assert "copy.de" in response.json()["error"]["message"]
    finally:
        _cleanup_boxe_title(db_connection, title_code)


def test_boxe_publish_during_active_round_affects_only_future_rounds(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-boxe-active-admin")
    player = create_authenticated_player(prefix="integration-boxe-active-player")
    title_code = f"boxe_cfg_{uuid4().hex[:8]}"
    _seed_boxe_title(db_connection, title_code)
    admin_headers = auth_headers(admin_user["access_token"])
    player_headers = auth_headers(player["access_token"])

    try:
        start_response = client.post(
            "/games/boxe/start",
            headers={**player_headers, "Idempotency-Key": f"boxe-active-start-{uuid4()}"},
            json={
                "title_code": title_code,
                "rows": 4,
                "difficulty": "hard",
                "bet_amount": "5.000000",
                "wallet_source": "demo",
            },
        )
        assert start_response.status_code == 200, start_response.text
        active_round_id = start_response.json()["data"]["round_id"]

        new_payload = _boxe_admin_payload()
        new_payload["rows_enabled"] = [8]
        new_payload["default_rows"] = 8
        new_payload["difficulty_enabled"] = ["easy"]
        new_payload["default_difficulty"] = "easy"
        draft_response = client.put(
            "/admin/games/boxe/config/draft",
            params={"title_code": title_code},
            headers=admin_headers,
            json=new_payload,
        )
        assert draft_response.status_code == 200, draft_response.text
        publish_response = client.post(
            "/admin/games/boxe/config/publish",
            params={"title_code": title_code},
            headers=admin_headers,
        )
        assert publish_response.status_code == 200, publish_response.text

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rows_count, difficulty, config_snapshot_json
                FROM boxe_rounds
                WHERE id = %s
                """,
                (active_round_id,),
            )
            active_round = cursor.fetchone()
        assert active_round["rows_count"] == 4
        assert active_round["difficulty"] == "hard"
        assert active_round["config_snapshot_json"]["rows"] == 4

        disabled_response = client.post(
            "/games/boxe/start",
            headers={**player_headers, "Idempotency-Key": f"boxe-disabled-start-{uuid4()}"},
            json={
                "title_code": title_code,
                "rows": 4,
                "difficulty": "hard",
                "bet_amount": "5.000000",
                "wallet_source": "demo",
            },
        )
        assert disabled_response.status_code == 400
        assert disabled_response.json()["error"]["code"] == "BAD_CONFIG"

        enabled_response = client.post(
            "/games/boxe/start",
            headers={**player_headers, "Idempotency-Key": f"boxe-enabled-start-{uuid4()}"},
            json={
                "title_code": title_code,
                "rows": 8,
                "difficulty": "easy",
                "bet_amount": "5.000000",
                "wallet_source": "demo",
            },
        )
        assert enabled_response.status_code == 200, enabled_response.text
    finally:
        _cleanup_boxe_title(db_connection, title_code)
