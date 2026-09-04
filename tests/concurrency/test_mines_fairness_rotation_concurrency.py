from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import httpx


def test_duplicate_fairness_rotate_same_idempotency_key_creates_one_active_hash(
    api_base_url,
    create_admin_user,
) -> None:
    admin_user = create_admin_user(prefix="concurrency-fairness-rotate-admin")
    headers = {
        "Authorization": f"Bearer {admin_user['access_token']}",
        "Idempotency-Key": "concurrency-fairness-rotate-key",
    }

    def do_rotate() -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post("/games/mines/fairness/rotate", headers=headers)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: do_rotate(), range(2)))

    assert all(response.status_code == 200 for response in responses)
    hashes = {response.json()["data"]["active_server_seed_hash"] for response in responses}
    assert len(hashes) == 1
