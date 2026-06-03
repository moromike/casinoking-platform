from __future__ import annotations

from uuid import uuid4


def test_gmp5_public_manifest_and_mock_host_demo_launch_contract(
    client,
    db_connection,
) -> None:
    site_code = f"gmp5host_{uuid4().hex[:8]}"
    _publish_boxe_on_site(db_connection=db_connection, site_code=site_code)

    try:
        manifest_response = client.get("/game-modules/boxe/manifest")
        assert manifest_response.status_code == 200, manifest_response.text
        manifest = manifest_response.json()["data"]

        assert manifest["game_code"] == "boxe"
        assert manifest["runtime"]["entry"] == "/runtime/boxe"
        assert manifest["runtime"]["embed_protocol"] == "ck-game-embed-v1"
        assert manifest["host_integration"]["selected_target"] == "same_repo_manifest_first"
        assert manifest["host_integration"]["physical_split"] == "none"
        assert manifest["admin"]["arbitrary_code_allowed"] is False

        launch_response = client.post(
            "/demo/launch",
            headers={"X-Demo-Token": _demo_token(client)},
            json={
                "game_code": "boxe",
                "title_code": "boxe001",
                "site_code": site_code,
                "host_code": "mockhost",
                "brand_code": site_code,
                "return_url": "https://mockhost.example/return",
                "locale": "en",
                "embed_origin": "https://mockhost.example",
                "correlation_id": "gmp5-correlation",
            },
        )
        assert launch_response.status_code == 200, launch_response.text
        launch = launch_response.json()["data"]

        assert launch["game_code"] == manifest["game_code"]
        assert launch["launch_descriptor"]["site_code"] == site_code
        assert launch["launch_descriptor"]["host_code"] == "mockhost"
        assert launch["launch_descriptor"]["brand_code"] == site_code
        assert launch["launch_descriptor"]["locale"] == "en"
        assert launch["launch_descriptor"]["return_url"] == "https://mockhost.example/return"
        assert launch["storage_descriptor"]["namespace"] == f"host.{site_code}.game.boxe"
        assert "casinoking" not in launch["storage_descriptor"]["namespace"]
        assert launch["storage_descriptor"]["allowed_uses"] == manifest["storage"]["allowed_uses"]
        assert launch["embed_descriptor"]["protocol"] == manifest["runtime"]["embed_protocol"]
        assert (
            launch["replay_descriptor"]["player_replay_endpoint"]
            == manifest["reporting"]["player_replay_endpoint"]
        )
        assert (
            launch["replay_descriptor"]["admin_replay_endpoint"]
            == manifest["reporting"]["admin_replay_endpoint"]
        )
    finally:
        _cleanup_mock_site(db_connection=db_connection, site_code=site_code)


def test_gmp5_manifest_endpoint_has_no_unknown_game_fallback(client) -> None:
    response = client.get("/game-modules/unknown/manifest")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert "unknown" in error["message"]


def _demo_token(client) -> str:
    response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.88.0.{uuid4().int % 250 + 1}"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["anonymous_token"]


def _publish_boxe_on_site(*, db_connection, site_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO sites (site_code, display_name, base_url, status)
            VALUES (%s, 'GMP5 Mock Host', 'https://mockhost.example', 'active')
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
                'BOXE demo on a GMP5 mock host.',
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
