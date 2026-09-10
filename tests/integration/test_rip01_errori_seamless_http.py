from __future__ import annotations
"""RIP-01: i rifiuti HTTP seamless non invitano il provider a ritentare."""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import Client

from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]

PROVIDER_CODE = "ck_collaudo"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, **extra: object) -> dict[str, object]:
    return {
        "user_id": user_id,
        "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE,
        "currency": "CHIP",
        "game_code": "manichino",
        "wallet_type": "cash",
        "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": uuid4().hex,
        **extra,
    }


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(route, content=body, headers={
        "x-provider-id": PROVIDER_CODE,
        "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
        "Content-Type": "application/json",
    })


def _assert_rejection_without_retry_or_balance_change(response, before: str, after: str) -> None:
    assert 400 <= response.status_code < 500, response.text
    assert after == before
    assert response.json()["error"]["retryable"] is False


def _reserve(client: Client, user_id: str) -> tuple[str, str]:
    game_session_id = str(uuid4())
    reserve_tx_id = f"rip01-reserve-{uuid4().hex}"
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=game_session_id, tx_id=reserve_tx_id, amount="10.00"
    ))
    assert response.status_code == 200, response.text
    return game_session_id, reserve_tx_id


def test_reserve_identica_restituisce_la_prima_risposta_senza_seconda_trattenuta(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="rip01-reserve-replay")
    user_id = str(player["user_id"])
    payload = _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"rip01-reserve-replay-{uuid4().hex}",
        amount="10.00",
    )

    first = _post(client, "/seamless/wallet/reserve", payload)
    assert first.status_code == 200, first.text
    balance_after_first = db_helpers.get_wallet_balance(user_id)
    replay = _post(client, "/seamless/wallet/reserve", payload)

    assert replay.status_code == 200, replay.text
    assert first.json()["already_exists"] is False
    assert replay.json()["already_exists"] is True
    assert db_helpers.get_wallet_balance(user_id) == balance_after_first
    first_body = dict(first.json())
    replay_body = dict(replay.json())
    first_body.pop("already_exists")
    replay_body.pop("already_exists")
    assert replay_body == first_body


def test_rifiuti_seamless_non_ritentabili_non_muovono_saldo(client, create_player, db_helpers) -> None:
    """Tre rotte, tre cause: provider non proprietario, round chiuso, round assente."""
    player = create_player(prefix="rip01-http-errors")
    user_id = str(player["user_id"])

    before_reserve = db_helpers.get_wallet_balance(user_id)
    wrong_provider = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"rip01-wrong-provider-{uuid4().hex}",
        amount="10.00", game_code="mines",
    ))
    _assert_rejection_without_retry_or_balance_change(
        wrong_provider, before_reserve, db_helpers.get_wallet_balance(user_id)
    )

    game_session_id, reserve_tx_id = _reserve(client, user_id)
    commit_tx_id = f"rip01-close-{uuid4().hex}"
    closed = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id, tx_id=commit_tx_id,
        reserve_tx_id=reserve_tx_id, amount="25.00", is_win=True,
    ))
    assert closed.status_code == 200, closed.text
    before_commit = db_helpers.get_wallet_balance(user_id)
    closed_again = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=game_session_id, tx_id=commit_tx_id,
        reserve_tx_id=reserve_tx_id, amount="25.00", is_win=True,
    ))
    assert closed_again.status_code == 200, closed_again.text
    assert db_helpers.get_wallet_balance(user_id) == before_commit
    assert closed.json()["already_exists"] is False
    assert closed_again.json()["already_exists"] is True

    before_rollback = db_helpers.get_wallet_balance(user_id)
    missing_round = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"rip01-missing-{uuid4().hex}",
        reserve_tx_id=f"rip01-missing-reserve-{uuid4().hex}",
    ))
    _assert_rejection_without_retry_or_balance_change(
        missing_round, before_rollback, db_helpers.get_wallet_balance(user_id)
    )


def test_codici_specifici_per_round_valuta_e_importi(client, create_player, db_helpers) -> None:
    """I quattro rifiuti richiedono correzioni diverse dal provider.

    Non basta che siano tutti 4xx: un integratore deve poter distinguere un
    round assente da una valuta errata e dai due limiti dell'importo.
    """
    player = create_player(prefix="rip01-specific-codes")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)

    cases = (
        (
            "/seamless/wallet/rollback",
            _payload(
                user_id=user_id,
                game_session_id=str(uuid4()),
                tx_id=f"rip01-round-missing-{uuid4().hex}",
                reserve_tx_id=f"rip01-round-reserve-{uuid4().hex}",
            ),
            "CK.SEAMLESS.ROUND_NOT_FOUND",
        ),
        (
            "/seamless/wallet/reserve",
            _payload(
                user_id=user_id,
                game_session_id=str(uuid4()),
                tx_id=f"rip01-currency-{uuid4().hex}",
                amount="10.00",
                currency="USD",
            ),
            "CK.SEAMLESS.CURRENCY_MISMATCH",
        ),
        (
            "/seamless/wallet/reserve",
            _payload(
                user_id=user_id,
                game_session_id=str(uuid4()),
                tx_id=f"rip01-minimum-{uuid4().hex}",
                amount="0.00",
            ),
            "CK.SEAMLESS.AMOUNT_BELOW_MINIMUM",
        ),
        (
            "/seamless/wallet/reserve",
            _payload(
                user_id=user_id,
                game_session_id=str(uuid4()),
                tx_id=f"rip01-maximum-{uuid4().hex}",
                amount="1000.01",
            ),
            "CK.SEAMLESS.AMOUNT_ABOVE_MAXIMUM",
        ),
    )

    for route, payload, expected_code in cases:
        response = _post(client, route, payload)
        _assert_rejection_without_retry_or_balance_change(
            response, before, db_helpers.get_wallet_balance(user_id)
        )
        assert response.json()["error"]["code"] == expected_code


def test_commit_e_rollback_rifiutano_valuta_diversa(client, create_player, db_helpers) -> None:
    """RIP-03 vale su tutte le rotte denaro, non soltanto sulla reserve."""
    player = create_player(prefix="rip01-settlement-currency")
    user_id = str(player["user_id"])

    commit_round, commit_reserve_tx = _reserve(client, user_id)
    before_commit = db_helpers.get_wallet_balance(user_id)
    commit = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id,
        game_session_id=commit_round,
        tx_id=f"rip01-commit-currency-{uuid4().hex}",
        reserve_tx_id=commit_reserve_tx,
        amount="25.00",
        is_win=True,
        currency="USD",
    ))
    _assert_rejection_without_retry_or_balance_change(
        commit, before_commit, db_helpers.get_wallet_balance(user_id)
    )
    assert commit.json()["error"]["code"] == "CK.SEAMLESS.CURRENCY_MISMATCH"

    rollback_round, rollback_reserve_tx = _reserve(client, user_id)
    before_rollback = db_helpers.get_wallet_balance(user_id)
    rollback = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id,
        game_session_id=rollback_round,
        tx_id=f"rip01-rollback-currency-{uuid4().hex}",
        reserve_tx_id=rollback_reserve_tx,
        currency="USD",
    ))
    _assert_rejection_without_retry_or_balance_change(
        rollback, before_rollback, db_helpers.get_wallet_balance(user_id)
    )
    assert rollback.json()["error"]["code"] == "CK.SEAMLESS.CURRENCY_MISMATCH"


def test_commit_e_rollback_rifiutano_la_reserve_di_un_altro_round(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="rip01-reserve-link")
    user_id = str(player["user_id"])
    first_round, _first_reserve_tx = _reserve(client, user_id)
    _other_round, other_reserve_tx = _reserve(client, user_id)

    before = db_helpers.get_wallet_balance(user_id)
    commit = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=f"rip01-wrong-reserve-commit-{uuid4().hex}",
        reserve_tx_id=other_reserve_tx,
        amount="25.00",
        is_win=True,
    ))
    _assert_rejection_without_retry_or_balance_change(
        commit, before, db_helpers.get_wallet_balance(user_id)
    )
    assert commit.json()["error"]["code"] == "CK.SEAMLESS.RESERVE_TRANSACTION_MISMATCH"

    rollback = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=f"rip01-wrong-reserve-rollback-{uuid4().hex}",
        reserve_tx_id=other_reserve_tx,
    ))
    _assert_rejection_without_retry_or_balance_change(
        rollback, before, db_helpers.get_wallet_balance(user_id)
    )
    assert rollback.json()["error"]["code"] == "CK.SEAMLESS.RESERVE_TRANSACTION_MISMATCH"


def test_replay_divergente_non_riusa_la_risposta_di_un_altra_operazione(
    client, create_player, db_helpers
) -> None:
    player = create_player(prefix="rip01-replay-divergent")
    user_id = str(player["user_id"])
    first_round, first_reserve_tx = _reserve(client, user_id)
    second_round, second_reserve_tx = _reserve(client, user_id)

    commit_tx_id = f"rip01-replay-win-{uuid4().hex}"
    first_commit = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=commit_tx_id,
        reserve_tx_id=first_reserve_tx,
        amount="25.00",
        is_win=True,
    ))
    assert first_commit.status_code == 200, first_commit.text
    before = db_helpers.get_wallet_balance(user_id)

    wrong_reserve_replay = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=commit_tx_id,
        reserve_tx_id=second_reserve_tx,
        amount="25.00",
        is_win=True,
    ))
    _assert_rejection_without_retry_or_balance_change(
        wrong_reserve_replay, before, db_helpers.get_wallet_balance(user_id)
    )

    wrong_currency_replay = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=commit_tx_id,
        reserve_tx_id=first_reserve_tx,
        amount="25.00",
        is_win=True,
        currency="USD",
    ))
    _assert_rejection_without_retry_or_balance_change(
        wrong_currency_replay, before, db_helpers.get_wallet_balance(user_id)
    )

    rollback_tx_id = f"rip01-replay-rollback-{uuid4().hex}"
    first_rollback = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id,
        game_session_id=second_round,
        tx_id=rollback_tx_id,
        reserve_tx_id=second_reserve_tx,
    ))
    assert first_rollback.status_code == 200, first_rollback.text
    before_rollback_replay = db_helpers.get_wallet_balance(user_id)
    cross_round_replay = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id,
        game_session_id=first_round,
        tx_id=rollback_tx_id,
        reserve_tx_id=first_reserve_tx,
    ))
    _assert_rejection_without_retry_or_balance_change(
        cross_round_replay,
        before_rollback_replay,
        db_helpers.get_wallet_balance(user_id),
    )
    assert cross_round_replay.json()["error"]["code"] == "CK.LEDGER.IDEMPOTENCY_CONFLICT"


def test_commit_vincita_rifiuta_importi_fuori_limite(client, create_player, db_helpers) -> None:
    """I limiti RIP-03 proteggono anche l'accredito, non solo la trattenuta."""
    player = create_player(prefix="rip01-settlement-amount")
    user_id = str(player["user_id"])

    for amount, expected_code in (
        ("1000.01", "CK.SEAMLESS.AMOUNT_ABOVE_MAXIMUM"),
    ):
        game_session_id, reserve_tx_id = _reserve(client, user_id)
        before = db_helpers.get_wallet_balance(user_id)
        response = _post(client, "/seamless/wallet/commit", _payload(
            user_id=user_id,
            game_session_id=game_session_id,
            tx_id=f"rip01-commit-amount-{uuid4().hex}",
            reserve_tx_id=reserve_tx_id,
            amount=amount,
            is_win=True,
        ))
        _assert_rejection_without_retry_or_balance_change(
            response, before, db_helpers.get_wallet_balance(user_id)
        )
        assert response.json()["error"]["code"] == expected_code
