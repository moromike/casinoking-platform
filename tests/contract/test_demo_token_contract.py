from __future__ import annotations

from uuid import UUID
from uuid import uuid4

import jwt

from app.api.routes import demo as demo_routes
from app.core.config import settings
from app.modules.platform.game_launch.service import GAME_LAUNCH_AUDIENCE, GAME_LAUNCH_ISSUER


def test_demo_token_emits_signed_jwt(client) -> None:
    demo_routes._token_requests_by_ip.clear()

    response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.10.1.{uuid4().int % 250 + 1}"},
    )

    assert response.status_code == 200
    token = response.json()["data"]["anonymous_token"]
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=demo_routes.DEMO_ANON_AUDIENCE,
        issuer=demo_routes.DEMO_ANON_ISSUER,
    )
    assert payload["kind"] == "demo_anon"
    UUID(payload["sub"])


def test_demo_token_rejects_tampered_signature(client) -> None:
    demo_routes._token_requests_by_ip.clear()

    token_response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.10.2.{uuid4().int % 250 + 1}"},
    )
    token = token_response.json()["data"]["anonymous_token"]
    header, payload, _signature = token.split(".")
    tampered = f"{header}.{payload}.invalidsignature"

    response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": tampered},
        json={"title_code": "mines_classic"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_demo_launch_emits_game_launch_token(
    client,
    create_published_mines_variant,
) -> None:
    demo_routes._token_requests_by_ip.clear()
    published_title = create_published_mines_variant(
        display_name="Mines Demo Token Contract Variant",
        cleanup=False,
    )
    title_code = str(published_title["title_code"])

    token_response = client.post(
        "/demo/token",
        headers={"X-Forwarded-For": f"10.10.3.{uuid4().int % 250 + 1}"},
    )
    anonymous_token = token_response.json()["data"]["anonymous_token"]
    anonymous_payload = jwt.decode(
        anonymous_token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=demo_routes.DEMO_ANON_AUDIENCE,
        issuer=demo_routes.DEMO_ANON_ISSUER,
    )

    launch_response = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anonymous_token},
        json={"title_code": title_code},
    )

    assert launch_response.status_code == 200
    launch_payload = launch_response.json()["data"]
    assert launch_payload["mode"] == "demo"
    assert launch_payload["anonymous_id"] == anonymous_payload["sub"]
    game_payload = jwt.decode(
        launch_payload["game_launch_token"],
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=GAME_LAUNCH_AUDIENCE,
        issuer=GAME_LAUNCH_ISSUER,
    )
    assert game_payload["mode"] == "demo"
    assert game_payload["anonymous_id"] == anonymous_payload["sub"]
    assert game_payload["title_code"] == title_code


def test_demo_token_rate_limit(client) -> None:
    demo_routes._token_requests_by_ip.clear()

    test_ip = f"10.10.4.{uuid4().int % 250 + 1}"
    responses = [
        client.post("/demo/token", headers={"X-Forwarded-For": test_ip})
        for _ in range(11)
    ]

    assert [response.status_code for response in responses[:10]] == [200] * 10
    assert responses[10].status_code == 429
