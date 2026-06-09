from __future__ import annotations

from uuid import uuid4

from app.modules.platform.game_launch.service import validate_game_launch_token


def test_gmp3_mock_non_casinoking_host_can_launch_boxe_demo(
    client,
    db_connection,
) -> None:
    site_code = f"gmp3host_{uuid4().hex[:8]}"
    _publish_boxe_on_site(db_connection=db_connection, site_code=site_code)

    try:
        demo_launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": _demo_token(client)},
            json={
                "game_code": "boxe",
                "title_code": "boxe001",
                "site_code": site_code,
                "host_code": "mockhost",
                "brand_code": site_code,
                "return_url": "https://arcade.example/return",
                "locale": "en",
                "embed_origin": "https://arcade.example",
                "correlation_id": "gmp3-correlation",
            },
        )
        assert demo_launch_response.status_code == 200, demo_launch_response.text
        payload = demo_launch_response.json()["data"]

        assert payload["game_code"] == "boxe"
        assert payload["title_code"] == "boxe001"
        assert payload["site_code"] == site_code
        assert payload["host_code"] == "mockhost"
        assert payload["brand_code"] == site_code
        assert payload["mode"] == "demo"

        launch_descriptor = payload["launch_descriptor"]
        storage_descriptor = payload["storage_descriptor"]
        embed_descriptor = payload["embed_descriptor"]
        replay_descriptor = payload["replay_descriptor"]

        assert launch_descriptor["site_code"] == site_code
        assert launch_descriptor["host_code"] == "mockhost"
        assert launch_descriptor["brand_code"] == site_code
        assert launch_descriptor["locale"] == "en"
        assert launch_descriptor["return_url"] == "https://arcade.example/return"
        assert launch_descriptor["correlation_id"] == "gmp3-correlation"
        assert launch_descriptor["storage_namespace"] == f"host.{site_code}.game.boxe"
        assert storage_descriptor["namespace"] == f"host.{site_code}.game.boxe"
        assert "casinoking" not in storage_descriptor["namespace"]
        assert embed_descriptor["protocol"] == "ck-game-embed-v1"
        assert replay_descriptor["player_replay_endpoint"] == "/games/boxe/round/{roundRef}/replay"

        launch_context = validate_game_launch_token(
            game_launch_token=str(payload["game_launch_token"]),
        )
        assert launch_context["site_code"] == site_code
        assert launch_context["host_code"] == "mockhost"
        assert launch_context["brand_code"] == site_code
        assert launch_context["locale"] == "en"

        config_response = client.get(
            "/games/boxe/config",
            params={"title_code": "boxe001", "site_code": site_code},
        )
        assert config_response.status_code == 200, config_response.text
        config_payload = config_response.json()["data"]
        assert config_payload["game_code"] == "boxe"
        assert config_payload["title_code"] == "boxe001"
        assert config_payload["site_code"] == site_code
    finally:
        _cleanup_mock_site(db_connection=db_connection, site_code=site_code)


def test_gmp3_boxe_demo_launch_does_not_fallback_to_casinoking_publication(client) -> None:
    missing_site_code = f"gmp3missing_{uuid4().hex[:8]}"

    response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": _demo_token(client)},
        json={
            "game_code": "boxe",
            "title_code": "boxe001",
            "site_code": missing_site_code,
            "host_code": "mockhost",
            "brand_code": missing_site_code,
        },
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "Title is not published on this site" in error["message"]


def _demo_token(client) -> str:
    response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.77.0.{uuid4().int % 250 + 1}"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["anonymous_token"]


def _publish_boxe_on_site(*, db_connection, site_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO sites (site_code, display_name, base_url, status)
            VALUES (%s, 'GMP3 Mock Host', 'https://arcade.example', 'active')
            ON CONFLICT (site_code) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                base_url = EXCLUDED.base_url,
                status = 'active',
                updated_at = NOW()
            """,
            (site_code,),
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
            VALUES (
                %s,
                'boxe001',
                1,
                'active',
                'visible',
                true,
                false,
                'BOXE',
                'BOXE demo on a non-CasinoKing host.',
                false
            )
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
            (site_code,),
        )


def _cleanup_mock_site(*, db_connection, site_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM site_titles WHERE site_code = %s", (site_code,))
        cursor.execute("DELETE FROM sites WHERE site_code = %s", (site_code,))
