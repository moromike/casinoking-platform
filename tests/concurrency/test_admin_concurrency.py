from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import httpx


def test_duplicate_admin_bonus_grant_same_idempotency_key_creates_one_action(
    api_base_url,
    create_admin_user,
    create_player,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="concurrency-admin")
    target_user = create_player(prefix="concurrency-admin-target")
    headers = {
        "Authorization": f"Bearer {admin_user['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": "concurrency-admin-bonus-key",
    }
    payload = {
        "amount": "20.000000",
        "reason": "manual promotional credit",
    }

    def do_bonus_grant() -> httpx.Response:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
            return client.post(
                f"/admin/users/{target_user['user_id']}/bonus-grants",
                headers=headers,
                json=payload,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: do_bonus_grant(), range(2)))

    assert all(response.status_code == 200 for response in responses)
    action_ids = {response.json()["data"]["admin_action_id"] for response in responses}
    assert len(action_ids) == 1

    admin_action_rows = db_helpers.fetchall(
        """
        SELECT id
        FROM admin_actions
        WHERE target_user_id = %s
          AND action_type = 'bonus_grant'
        """,
        (target_user["user_id"],),
    )
    assert len(admin_action_rows) == 1
    assert db_helpers.get_wallet_balance(str(target_user["user_id"]), "bonus") == "20.000000"
