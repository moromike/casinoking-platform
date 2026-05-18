from __future__ import annotations

from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
BOXE_ASSET_DIR = REPO_ROOT / "assets" / "Games" / "boxe"
BOXE_GAME_CARD = BOXE_ASSET_DIR / "boxe_icon001_512px.webp"
BOXE_SAFE_SYMBOL = BOXE_ASSET_DIR / "diamond_green_v001.png"
BOXE_MINE_SYMBOL = BOXE_ASSET_DIR / "mine_fucsia_002.png"


def test_boxe_assets_upload_preview_delete_and_theme_publish(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    title_code = f"boxe_assets_{uuid4().hex[:8]}"
    admin_user = create_admin_user(prefix="integration-boxe-assets")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)
    _seed_boxe_title_with_theme_config(db_connection, title_code)

    try:
        uploaded_card = _upload_asset(
            client,
            headers=headers,
            title_code=title_code,
            asset_kind="game_card",
            file_path=BOXE_GAME_CARD,
            mime="image/webp",
        )
        assert uploaded_card["asset_kind"] == "game_card"
        assert uploaded_card["byte_size"] == BOXE_GAME_CARD.stat().st_size
        assert uploaded_card["public_url"].startswith(f"/static/games/{title_code}/game_card/")

        uploaded_safe = _upload_asset(
            client,
            headers=headers,
            title_code=title_code,
            asset_kind="symbol_safe",
            file_path=BOXE_SAFE_SYMBOL,
            mime="image/png",
        )
        uploaded_mine = _upload_asset(
            client,
            headers=headers,
            title_code=title_code,
            asset_kind="symbol_mine",
            file_path=BOXE_MINE_SYMBOL,
            mime="image/png",
        )
        assert uploaded_safe["byte_size"] <= 150 * 1024
        assert uploaded_mine["byte_size"] <= 150 * 1024

        list_response = client.get(
            f"/admin/titles/{title_code}/assets",
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        assert {
            asset["asset_kind"]
            for asset in list_response.json()["data"]
        } == {"game_card", "symbol_safe", "symbol_mine"}

        delete_response = client.delete(
            f"/admin/titles/{title_code}/assets/symbol_mine",
            headers=headers,
        )
        assert delete_response.status_code == 200, delete_response.text
        assert delete_response.json()["data"]["status"] == "deleted"

        draft_theme = client.put(
            f"/admin/titles/{title_code}/theme",
            headers=headers,
            json={
                "tokens": {
                    "--ck-bg": "#0f172a",
                    "--ck-surface": "#111827",
                    "--ck-surface-strong": "#1f2937",
                    "--ck-fg": "#f8fafc",
                    "--ck-muted": "#cbd5e1",
                    "--ck-accent": "#22c55e",
                    "--ck-danger": "#fb7185",
                    "--ck-radius-cell": "10px",
                }
            },
        )
        assert draft_theme.status_code == 200, draft_theme.text
        assert draft_theme.json()["data"]["has_unpublished_changes"] is True

        publish_theme = client.post(
            f"/admin/titles/{title_code}/theme/publish",
            headers=headers,
        )
        assert publish_theme.status_code == 200, publish_theme.text
        assert publish_theme.json()["data"]["published"]["tokens"]["--ck-accent"] == "#22c55e"

        public_theme = client.get(f"/titles/{title_code}/theme")
        assert public_theme.status_code == 200
        public_payload = public_theme.json()["data"]
        assert public_payload["tokens"]["--ck-bg"] == "#0f172a"
        assert public_payload["assets"]["game_card"] == uploaded_card["public_url"]

        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT action_kind, resource_id
                FROM admin_audit_log
                WHERE resource_id = %s
                   OR resource_id LIKE %s
                ORDER BY created_at ASC
                """,
                (title_code, f"{title_code}:%"),
            )
            audit_rows = cursor.fetchall()

        action_pairs = {(row["action_kind"], row["resource_id"]) for row in audit_rows}
        assert ("title_asset_upload", f"{title_code}:game_card") in action_pairs
        assert ("title_asset_upload", f"{title_code}:symbol_safe") in action_pairs
        assert ("title_asset_upload", f"{title_code}:symbol_mine") in action_pairs
        assert ("title_asset_delete", f"{title_code}:symbol_mine") in action_pairs
        assert ("theme_publish", title_code) in action_pairs
    finally:
        _cleanup_boxe_title(db_connection, title_code)


def test_boxe_asset_validation_rejects_invalid_format_and_oversize(
    client,
    create_admin_user,
    auth_headers,
    db_connection,
) -> None:
    title_code = f"boxe_assets_bad_{uuid4().hex[:8]}"
    admin_user = create_admin_user(prefix="integration-boxe-assets-bad")
    headers = auth_headers(admin_user["access_token"], include_game_launch_token=False)
    _seed_boxe_title_with_theme_config(db_connection, title_code)

    try:
        unsupported_response = client.post(
            f"/admin/titles/{title_code}/assets",
            headers=headers,
            data={"asset_kind": "symbol_safe"},
            files={"file": ("safe.txt", b"not an image", "text/plain")},
        )
        assert unsupported_response.status_code == 422
        assert unsupported_response.json()["error"]["message"] == "Asset MIME type is not supported"

        oversized_response = client.post(
            f"/admin/titles/{title_code}/assets",
            headers=headers,
            data={"asset_kind": "game_card"},
            files={"file": ("card.png", _oversized_png_payload(), "image/png")},
        )
        assert oversized_response.status_code == 422
        assert oversized_response.json()["error"]["message"] == "Game card asset file is too large"
    finally:
        _cleanup_boxe_title(db_connection, title_code)


def _upload_asset(
    client,
    *,
    headers: dict[str, str],
    title_code: str,
    asset_kind: str,
    file_path: Path,
    mime: str,
) -> dict[str, object]:
    response = client.post(
        f"/admin/titles/{title_code}/assets",
        headers=headers,
        data={"asset_kind": asset_kind},
        files={"file": (file_path.name, file_path.read_bytes(), mime)},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _oversized_png_payload() -> bytes:
    png_header = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x02\x00\x00\x00\x02\x00"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    )
    return png_header + (b"x" * (301 * 1024))


def _seed_boxe_title_with_theme_config(db_connection, title_code: str) -> None:
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
                (%s, 'boxe', 'BOXE Asset Test', 'active', false, 'boxe')
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
                ('casinoking', %s, 901, 'active', 'visible', true, true, 'BOXE', 'BOXE asset test', false)
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
        cursor.execute(
            """
            INSERT INTO title_configs (
                title_code,
                rules_sections_json,
                ui_labels_json,
                theme_tokens_json,
                draft_rules_sections_json,
                draft_ui_labels_json,
                draft_theme_tokens_json
            )
            VALUES (
                %s,
                '{}'::jsonb,
                '{}'::jsonb,
                NULL,
                '{}'::jsonb,
                '{}'::jsonb,
                NULL
            )
            ON CONFLICT (title_code) DO NOTHING
            """,
            (title_code,),
        )


def _cleanup_boxe_title(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM admin_audit_log WHERE resource_id = %s OR resource_id LIKE %s",
            (title_code, f"{title_code}:%"),
        )
        cursor.execute("DELETE FROM title_assets WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))
