"""B1 network evidence: real reveal/cashout work without X-Game-Launch-Token.

This script plays a full real round and a full demo round via HTTP,
verifying that:
1. Start real still sends X-Game-Launch-Token.
2. Reveal/cashout real do NOT send X-Game-Launch-Token (backend accepts them).
3. Reveal/cashout demo DO send X-Game-Launch-Token (unchanged).
4. End-to-end: wallet is updated correctly in both modes.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import httpx

API_BASE = "http://localhost:8000/api/v1"
client = httpx.Client(base_url=API_BASE, timeout=10.0)


def _register_and_login(prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid4().hex[:8]}@example.com"
    pwd = "StrongPass123!"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": pwd,
            "site_access_password": "change-me",
            "first_name": "T",
            "last_name": "T",
            "fiscal_code": "FC12345678901234",
            "phone_number": "+391234567890",
        },
    )
    login_resp = client.post("/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["data"]["access_token"]
    user_id = login_resp.json()["data"]["user_id"]
    return token, str(user_id)


def _create_published_title() -> str:
    """Create a published mines variant via backend helper (used by tests)."""
    # We need to call a helper; since we are in test context, we rely on
    # the variant mines001b already existing from seed, or we create one
    # via direct DB. For simplicity, assume mines001b exists.
    return "mines001b"


def _get_wallet_balance(user_id: str) -> Decimal:
    wallets = client.get("/wallets", headers={"Authorization": f"Bearer {_token}"}).json()["data"]
    cash = next((w for w in wallets if w["wallet_type"] == "cash"), None)
    return Decimal(cash["balance_snapshot"] if cash else "0")


def _get_title_code() -> str:
    # Try to reuse an existing published title.
    # If mines001b doesn't exist, the start will fail and we catch it.
    return "mines001b"


_token = ""


def test_real_round_reveal_and_cashout_without_token() -> None:
    """Full real round: start WITH token, reveal/cashout WITHOUT token."""
    global _token
    _token, user_id = _register_and_login("net-real")
    title_code = _get_title_code()

    headers = {"Authorization": f"Bearer {_token}"}

    # 1. Get launch token (start still requires it)
    lt_resp = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={"title_code": title_code, "mode": "real"},
    )
    assert lt_resp.status_code == 200, lt_resp.text
    launch_token = lt_resp.json()["data"]["game_launch_token"]
    headers_with_token = {**headers, "X-Game-Launch-Token": launch_token}

    # 2. Access + table sessions
    access_resp = client.post(
        "/access-sessions",
        headers=headers_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_resp.status_code == 200, access_resp.text
    access_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_id,
            "title_code": title_code,
        },
    )
    assert table_resp.status_code == 200, table_resp.text
    table_id = table_resp.json()["data"]["id"]

    # 3. Start round — MUST include token
    start_resp = client.post(
        "/games/mines/start",
        headers={**headers_with_token, "Idempotency-Key": f"net-start-{uuid4().hex}"},
        json={
            "access_session_id": access_id,
            "table_session_id": table_id,
            "bet_amount": "1.000000",
            "grid_size": 9,
            "mine_count": 1,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    balance_after_start = _get_wallet_balance(user_id)

    # 4. Reveal — WITHOUT token
    reveal_resp = client.post(
        "/games/mines/reveal",
        headers=headers,  # NO X-Game-Launch-Token
        json={"game_session_id": game_session_id, "cell_index": 0},
    )
    assert reveal_resp.status_code == 200, reveal_resp.text
    reveal_data = reveal_resp.json()["data"]

    # If cell 0 was a mine, try others until safe
    if reveal_data["result"] == "mine":
        for i in range(1, 9):
            reveal_resp = client.post(
                "/games/mines/reveal",
                headers=headers,
                json={"game_session_id": game_session_id, "cell_index": i},
            )
            reveal_data = reveal_resp.json()["data"]
            if reveal_data["result"] == "safe":
                break

    assert reveal_data["result"] == "safe", "Could not find a safe cell"
    potential_payout = Decimal(reveal_data["potential_payout"])

    # 5. Cashout — WITHOUT token
    balance_before_cashout = _get_wallet_balance(user_id)
    cashout_resp = client.post(
        "/games/mines/cashout",
        headers={**headers, "Idempotency-Key": f"net-cashout-{uuid4().hex}"},
        json={"game_session_id": game_session_id},
    )
    assert cashout_resp.status_code == 200, cashout_resp.text
    cashout_data = cashout_resp.json()["data"]
    assert cashout_data["status"] == "won"
    payout = Decimal(str(cashout_data["payout_amount"]))
    assert payout == potential_payout

    balance_after_cashout = _get_wallet_balance(user_id)
    assert balance_after_cashout == balance_before_cashout + payout

    print("[PASS] Real round: start with token, reveal/cashout without token, wallet correct.")


def test_demo_round_reveal_and_cashout_with_token() -> None:
    """Full demo round: start/reveal/cashout ALL with token (unchanged)."""
    # 1. Demo anon token
    demo_token_resp = client.post("/demo/token", json={})
    assert demo_token_resp.status_code == 200, demo_token_resp.text
    anon_token = demo_token_resp.json()["data"]["anonymous_token"]

    # 2. Demo launch
    demo_launch_resp = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anon_token},
        json={"title_code": "mines001b"},
    )
    assert demo_launch_resp.status_code == 200, demo_launch_resp.text
    launch_token = demo_launch_resp.json()["data"]["game_launch_token"]

    # 3. Demo start
    start_resp = client.post(
        "/games/mines/start",
        headers={
            "X-Game-Launch-Token": launch_token,
            "Idempotency-Key": f"net-demo-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "demo",
            "title_code": "mines001b",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    # 4. Demo reveal WITH token
    reveal_resp = client.post(
        "/games/mines/reveal",
        headers={"X-Game-Launch-Token": launch_token},
        json={"game_session_id": game_session_id, "cell_index": 0},
    )
    reveal_data = reveal_resp.json()["data"]
    if reveal_data["result"] == "mine":
        for i in range(1, 9):
            reveal_resp = client.post(
                "/games/mines/reveal",
                headers={"X-Game-Launch-Token": launch_token},
                json={"game_session_id": game_session_id, "cell_index": i},
            )
            reveal_data = reveal_resp.json()["data"]
            if reveal_data["result"] == "safe":
                break
    assert reveal_data["result"] == "safe"

    # 5. Demo cashout WITH token
    cashout_resp = client.post(
        "/games/mines/cashout",
        headers={
            "X-Game-Launch-Token": launch_token,
            "Idempotency-Key": f"net-demo-cashout-{uuid4().hex}",
        },
        json={"game_session_id": game_session_id},
    )
    assert cashout_resp.status_code == 200, cashout_resp.text
    cashout_data = cashout_resp.json()["data"]
    assert cashout_data["status"] == "won"

    print("[PASS] Demo round: start/reveal/cashout all with token, unchanged.")


def test_real_read_session_fairness_replay_without_token() -> None:
    """Real session/fairness/replay reads work without X-Game-Launch-Token."""
    token, user_id = _register_and_login("net-read")
    title_code = _get_title_code()
    headers = {"Authorization": f"Bearer {token}"}

    lt_resp = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={"title_code": title_code, "mode": "real"},
    )
    assert lt_resp.status_code == 200, lt_resp.text
    launch_token = lt_resp.json()["data"]["game_launch_token"]
    headers_with_token = {**headers, "X-Game-Launch-Token": launch_token}

    access_resp = client.post(
        "/access-sessions",
        headers=headers_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_resp.status_code == 200, access_resp.text
    access_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_id,
            "title_code": title_code,
        },
    )
    assert table_resp.status_code == 200, table_resp.text
    table_id = table_resp.json()["data"]["id"]

    start_resp = client.post(
        "/games/mines/start",
        headers={**headers_with_token, "Idempotency-Key": f"net-read-start-{uuid4().hex}"},
        json={
            "access_session_id": access_id,
            "table_session_id": table_id,
            "bet_amount": "1.000000",
            "grid_size": 9,
            "mine_count": 1,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    # 1. GET session without token
    session_resp = client.get(
        f"/games/mines/session/{game_session_id}",
        headers=headers,  # NO token
    )
    assert session_resp.status_code == 200, session_resp.text
    assert session_resp.json()["data"]["game_session_id"] == game_session_id

    # 2. GET fairness without token
    fairness_resp = client.get(
        f"/games/mines/session/{game_session_id}/fairness",
        headers=headers,  # NO token
    )
    assert fairness_resp.status_code == 200, fairness_resp.text
    assert fairness_resp.json()["data"]["game_session_id"] == game_session_id

    # 3. GET replay without token
    replay_resp = client.get(
        f"/games/mines/session/{game_session_id}/replay",
        headers=headers,  # NO token
    )
    assert replay_resp.status_code == 200, replay_resp.text
    assert replay_resp.json()["data"]["game_session_id"] == game_session_id

    print("[PASS] Real reads (session/fairness/replay) without token.")


def test_real_read_other_user_session_rejected_without_token() -> None:
    """Reading another user's session is rejected without token."""
    token_a, _ = _register_and_login("net-read-owner-a")
    token_b, _ = _register_and_login("net-read-owner-b")
    title_code = _get_title_code()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    lt_resp = client.post(
        "/games/mines/launch-token",
        headers=headers_a,
        json={"title_code": title_code, "mode": "real"},
    )
    launch_token = lt_resp.json()["data"]["game_launch_token"]
    headers_a_with_token = {**headers_a, "X-Game-Launch-Token": launch_token}

    access_resp = client.post(
        "/access-sessions",
        headers=headers_a_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    access_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_a_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_id,
            "title_code": title_code,
        },
    )
    table_id = table_resp.json()["data"]["id"]

    start_resp = client.post(
        "/games/mines/start",
        headers={**headers_a_with_token, "Idempotency-Key": f"net-read-own-start-{uuid4().hex}"},
        json={
            "access_session_id": access_id,
            "table_session_id": table_id,
            "bet_amount": "1.000000",
            "grid_size": 9,
            "mine_count": 1,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )
    game_session_id = start_resp.json()["data"]["game_session_id"]

    for endpoint in [
        f"/games/mines/session/{game_session_id}",
        f"/games/mines/session/{game_session_id}/fairness",
        f"/games/mines/session/{game_session_id}/replay",
    ]:
        resp = client.get(endpoint, headers=headers_b)  # NO token
        assert resp.status_code in (403, 404), (
            f"Expected 403/404 for {endpoint}, got {resp.status_code}: {resp.text}"
        )

    print("[PASS] Real reads other user session rejected without token.")


def test_demo_read_session_replay_with_token() -> None:
    """Demo session/replay reads still require and work with token."""
    demo_token_resp = client.post("/demo/token", json={})
    assert demo_token_resp.status_code == 200, demo_token_resp.text
    anon_token = demo_token_resp.json()["data"]["anonymous_token"]

    demo_launch_resp = client.post(
        "/demo/launch",
        headers={"X-Demo-Token": anon_token},
        json={"title_code": "mines001b"},
    )
    assert demo_launch_resp.status_code == 200, demo_launch_resp.text
    launch_token = demo_launch_resp.json()["data"]["game_launch_token"]

    start_resp = client.post(
        "/games/mines/start",
        headers={
            "X-Game-Launch-Token": launch_token,
            "Idempotency-Key": f"net-demo-read-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "demo",
            "title_code": "mines001b",
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    session_resp = client.get(
        f"/games/mines/session/{game_session_id}",
        headers={"X-Game-Launch-Token": launch_token},
    )
    assert session_resp.status_code == 200, session_resp.text

    replay_resp = client.get(
        f"/games/mines/session/{game_session_id}/replay",
        headers={"X-Game-Launch-Token": launch_token},
    )
    assert replay_resp.status_code == 200, replay_resp.text

    print("[PASS] Demo reads (session/replay) with token, unchanged.")


def test_real_access_sessions_latest_without_token() -> None:
    """/access-sessions/latest real works without token and scopes to user."""
    token_a, user_id_a = _register_and_login("net-latest-a")
    token_b, user_id_b = _register_and_login("net-latest-b")
    title_code = _get_title_code()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Player A starts a round to create an access session
    lt_resp = client.post(
        "/games/mines/launch-token",
        headers=headers_a,
        json={"title_code": title_code, "mode": "real"},
    )
    launch_token = lt_resp.json()["data"]["game_launch_token"]
    headers_a_with_token = {**headers_a, "X-Game-Launch-Token": launch_token}

    access_resp = client.post(
        "/access-sessions",
        headers=headers_a_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    access_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_a_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_id,
            "title_code": title_code,
        },
    )
    table_id = table_resp.json()["data"]["id"]

    client.post(
        "/games/mines/start",
        headers={**headers_a_with_token, "Idempotency-Key": f"net-latest-start-{uuid4().hex}"},
        json={
            "access_session_id": access_id,
            "table_session_id": table_id,
            "bet_amount": "1.000000",
            "grid_size": 9,
            "mine_count": 1,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )

    # Player A fetches latest WITHOUT token — must see their own session
    latest_a = client.get(
        f"/games/mines/access-sessions/latest?title_code={title_code}",
        headers=headers_a,
    )
    assert latest_a.status_code == 200, latest_a.text
    sessions_a = latest_a.json()["data"]
    assert len(sessions_a) > 0
    assert all(s["title_code"] == title_code for s in sessions_a)

    # Player B fetches latest WITHOUT token — must NOT see A's session
    latest_b = client.get(
        f"/games/mines/access-sessions/latest?title_code={title_code}",
        headers=headers_b,
    )
    assert latest_b.status_code == 200, latest_b.text
    sessions_b = latest_b.json()["data"]
    assert all(s["access_session_id"] != access_id for s in sessions_b)

    print("[PASS] /access-sessions/latest real without token, scoped per user.")


if __name__ == "__main__":
    test_real_round_reveal_and_cashout_without_token()
    test_demo_round_reveal_and_cashout_with_token()
    test_real_read_session_fairness_replay_without_token()
    test_real_read_other_user_session_rejected_without_token()
    test_demo_read_session_replay_with_token()
    test_real_access_sessions_latest_without_token()
    print("\nAll network evidence tests passed.")
