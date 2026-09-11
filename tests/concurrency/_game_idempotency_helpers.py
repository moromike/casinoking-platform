from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Callable

import httpx


def auth_headers(access_token: str, *, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def open_real_table(
    *,
    api_base_url: str,
    access_token: str,
    game_code: str,
    title_code: str,
) -> tuple[str, str, str]:
    headers = auth_headers(access_token)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        access = client.post(
            "/access-sessions",
            headers=headers,
            json={"game_code": game_code, "title_code": title_code, "site_code": "casinoking"},
        )
        assert access.status_code == 200, access.text
        access_session_id = access.json()["data"]["id"]
        table = client.post(
            "/table-sessions",
            headers=headers,
            json={
                "game_code": game_code,
                "title_code": title_code,
                "site_code": "casinoking",
                "wallet_type": "cash",
                "table_budget_amount": "20.000000",
                "access_session_id": access_session_id,
            },
        )
        assert table.status_code == 200, table.text
        route = "hi-lo" if game_code == "hi_lo" else game_code
        launch = client.post(
            f"/games/{route}/launch-token",
            headers=headers,
            json={"game_code": game_code, "title_code": title_code, "site_code": "casinoking", "mode": "real"},
        )
        assert launch.status_code == 200, launch.text
    return access_session_id, table.json()["data"]["id"], launch.json()["data"]["game_launch_token"]


def parallel_posts(
    *,
    api_base_url: str,
    path: str,
    headers: dict[str, str],
    payload: dict[str, object],
) -> list[httpx.Response]:
    barrier = Barrier(2)

    def post() -> httpx.Response:
        barrier.wait(timeout=10)
        with httpx.Client(base_url=api_base_url, timeout=20.0) as client:
            return client.post(path, headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(post) for _ in range(2)]
        return [future.result() for future in futures]


def controlled_double_call(call: Callable[[], object]) -> list[tuple[str, object]]:
    """Run two service calls and retain exceptions as assertion evidence."""
    def capture() -> tuple[str, object]:
        try:
            return "ok", call()
        except Exception as exc:  # the current race is expected to surface here
            return "error", f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(capture) for _ in range(2)]
        return [future.result() for future in futures]

