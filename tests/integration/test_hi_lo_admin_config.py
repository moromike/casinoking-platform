from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

HI_LO_COPY_KEYS = (
    "game.title",
    "how_to_play.title",
    "how_to_play.intro",
    "how_to_play.card_1_title",
    "how_to_play.card_1_text",
    "how_to_play.card_2_title",
    "how_to_play.card_2_text",
    "how_to_play.card_3_title",
    "how_to_play.card_3_text",
    "how_to_play.continue",
    "rules.dialog_aria",
    "rules.header_title",
    "rules.intro",
    "rules.close_aria",
    "rules.rules_tab",
    "rules.replay_tab",
    "rules.replay_loading",
    "rules.replay_unavailable",
    "rules.bet_predict_collect",
    "rules.bet_predict_collect_heading",
    "rules.probability_display",
    "rules.payout_rules",
    "rules.fairness_explain",
    "rules.card_deck_mechanics",
    "rules.skip_semantics",
    "rules.edge_rank_behavior",
)
HI_LO_RULE_SECTION_KEYS = (
    "bet_predict_collect",
    "probability_display",
    "payout_rules",
    "fairness_explain",
    "card_deck_mechanics",
    "skip_semantics",
    "edge_rank_behavior",
)


def _seed_hi_lo_title(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
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
                title_code,
                engine_code,
                display_name,
                status,
                is_master,
                source_title_code
            )
            VALUES
                ('hi_lo', 'hi_lo', 'HI-LO Master', 'active', true, NULL),
                (%s, 'hi_lo', 'HI-LO Config Test', 'active', false, 'hi_lo')
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
                ('casinoking', 'hi_lo', 910, 'active', 'hidden', false, false, 'HI-LO Master', 'Master HI-LO', false),
                ('casinoking', %s, 911, 'active', 'visible', true, true, 'HI-LO', 'HI-LO test title', false)
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


def _cleanup_hi_lo_title(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM admin_audit_log WHERE resource_id = %s", (title_code,))
        cursor.execute("DELETE FROM title_assets WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def _hi_lo_admin_payload() -> dict[str, object]:
    copy = {
        locale: {
            key: _copy_value(locale=locale, key=key)
            for key in HI_LO_COPY_KEYS
        }
        for locale in ("it", "en", "de", "es")
    }
    rules_html = {
        locale: {
            key: f"<p><strong>{key}</strong> HI-LO rules for {locale}.</p><ul><li>Server owned.</li></ul>"
            for key in HI_LO_RULE_SECTION_KEYS
        }
        for locale in ("it", "en", "de", "es")
    }
    return {
        "default_locale": "en",
        "copy": copy,
        "rules_html": rules_html,
    }


def _copy_value(*, locale: str, key: str) -> str:
    if key == "rules.dialog_aria":
        return f"Game info {{{{gameTitle}}}} {locale}"
    if key == "rules.header_title":
        return f"GAME INFO - {{{{gameTitle}}}} {locale}"
    if key == "game.title":
        return f"HI-LO {locale.upper()}"
    return f"{key} {locale}"


def test_admin_can_save_publish_and_read_hi_lo_config(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-hi-lo-admin-config")
    title_code = f"hilo_cfg_{uuid4().hex[:8]}"
    _seed_hi_lo_title(db_connection, title_code)

    try:
        headers = auth_headers(admin_user["access_token"])
        get_response = client.get(
            "/admin/games/hi-lo/config",
            params={"title_code": title_code},
            headers=headers,
        )
        assert get_response.status_code == 200
        initial = get_response.json()["data"]
        assert initial["game_code"] == "hi_lo"
        assert initial["draft"]["default_locale"] == "it"
        assert initial["has_unpublished_changes"] is False

        payload = _hi_lo_admin_payload()
        draft_response = client.put(
            "/admin/games/hi-lo/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=payload,
        )
        assert draft_response.status_code == 200, draft_response.text
        draft = draft_response.json()["data"]
        assert draft["draft"]["default_locale"] == "en"
        assert draft["draft"]["copy"]["it"]["game.title"] == "HI-LO IT"
        assert draft["draft"]["copy"]["en"]["rules.dialog_aria"].startswith("Game info")
        assert set(draft["draft"]["rules_html"]["en"]) == set(HI_LO_RULE_SECTION_KEYS)
        assert "<ul>" in draft["draft"]["rules_html"]["en"]["fairness_explain"]
        assert draft["draft_updated_by_admin_user_id"] == admin_user["user_id"]
        assert draft["has_unpublished_changes"] is True

        public_before = client.get("/games/hi-lo/config", params={"title_code": title_code})
        assert public_before.status_code == 200
        assert public_before.json()["data"]["presentation_config"]["default_locale"] == "it"

        publish_response = client.post(
            "/admin/games/hi-lo/config/publish",
            params={"title_code": title_code},
            headers=headers,
        )
        assert publish_response.status_code == 200, publish_response.text
        published = publish_response.json()["data"]
        assert published["published"]["default_locale"] == "en"
        assert published["has_unpublished_changes"] is False

        public_after = client.get("/games/hi-lo/config", params={"title_code": title_code})
        assert public_after.status_code == 200
        public_payload = public_after.json()["data"]
        assert public_payload["presentation_config"]["default_locale"] == "en"
        assert public_payload["presentation_config"]["copy"]["it"]["game.title"] == "HI-LO IT"
        assert set(public_payload["presentation_config"]["rules_html"]["en"]) == set(HI_LO_RULE_SECTION_KEYS)

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
        assert audit_row["payload_json"]["engine_code"] == "hi_lo"
    finally:
        _cleanup_hi_lo_title(db_connection, title_code)


def test_hi_lo_config_validation_rejects_missing_locale_and_placeholders(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    admin_user = create_admin_user(prefix="integration-hi-lo-admin-validation")
    title_code = f"hilo_cfg_{uuid4().hex[:8]}"
    _seed_hi_lo_title(db_connection, title_code)
    headers = auth_headers(admin_user["access_token"])

    try:
        invalid_locale = _hi_lo_admin_payload()
        invalid_locale["default_locale"] = "fr"
        response = client.put(
            "/admin/games/hi-lo/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=invalid_locale,
        )
        assert response.status_code == 422
        assert "default_locale" in response.json()["error"]["message"]

        missing_rule = deepcopy(_hi_lo_admin_payload())
        del missing_rule["rules_html"]["en"]["edge_rank_behavior"]
        response = client.put(
            "/admin/games/hi-lo/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=missing_rule,
        )
        assert response.status_code == 422
        assert "rules_html.en.edge_rank_behavior" in response.json()["error"]["message"]

        missing_placeholder = deepcopy(_hi_lo_admin_payload())
        missing_placeholder["copy"]["it"]["rules.header_title"] = "Game info"
        response = client.put(
            "/admin/games/hi-lo/config/draft",
            params={"title_code": title_code},
            headers=headers,
            json=missing_placeholder,
        )
        assert response.status_code == 422
        assert "gameTitle" in response.json()["error"]["message"]
    finally:
        _cleanup_hi_lo_title(db_connection, title_code)
