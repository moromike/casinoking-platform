"""POR-07 e REG-02 — il seamless eredita i controlli di casa senza bloccare sessioni aperte."""

from __future__ import annotations

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
GAME_CODE = "manichino"
WALLET_TYPE = "cash"


def _payload(*, user_id: str, game_session_id: str, tx_id: str, amount: str | None = None,
             currency: str = "EUR", is_win: bool | None = None,
             reserve_tx_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "user_id": user_id, "game_session_id": game_session_id,
        "provider_code": PROVIDER_CODE, "currency": currency, "game_code": GAME_CODE,
        "wallet_type": WALLET_TYPE, "tx_id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "nonce": uuid4().hex,
    }
    if amount is not None:
        payload["amount"] = amount
    if is_win is not None:
        payload["is_win"] = is_win
    # LA TRATTENUTA CHE LA CHIUSURA CHIUDE (POR-02): obbligatoria su commit e
    # rollback, assente sulla reserve, che non chiude niente.
    if reserve_tx_id is not None:
        payload["reserve_tx_id"] = reserve_tx_id
    return payload


def _post(client: Client, route: str, payload: dict[str, object]):
    secret = get_provider_secret(PROVIDER_CODE)
    assert secret is not None, "CK_COLLAUDO_SECRET_KEY non configurata per il collaudo seamless"
    body = json.dumps(payload, separators=(",", ":")).encode()
    return client.post(route, content=body, headers={
        "x-provider-id": PROVIDER_CODE,
        "x-signature-hmac": hmac.new(secret, body, hashlib.sha256).hexdigest(),
        "Content-Type": "application/json",
    })


def _assert_rejected_without_balance_change(response, before: str, after: str) -> None:
    assert 400 <= response.status_code < 500, response.text
    assert after == before, "Il rifiuto ha modificato il saldo del giocatore"
    # Un rifiuto non e' un guasto: non deve mai dire al fornitore di riprovare.
    # Aggiunto l'8/09: era il danno raccontato nelle motivazioni di RIP-01 e non
    # provato da nessun comando.
    corpo = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    assert corpo.get("error", {}).get("retryable") is not True, (
        "Un rifiuto 4xx porta retryable:true: dice a un fornitore esterno di ripetere "
        "all'infinito una chiamata che non riuscira' mai. " + response.text
    )


def _set_player_status(db_connection, user_id: str, status: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("UPDATE users SET status = %s WHERE id = %s", (status, user_id))


def _set_wallet_balance(db_connection, user_id: str, balance: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE wallet_accounts
            SET balance_snapshot = %s
            WHERE user_id = %s
              AND wallet_type = %s
            """,
            (balance, user_id, WALLET_TYPE),
        )


def _open_reserve(client: Client, user_id: str, game_session_id: str) -> str:
    """Restituisce il tx_id della trattenuta aperta.

    Prima lo buttava via. Con reserve_tx_id obbligatorio su commit e rollback
    (POR-02) chi chiude deve dire QUALE trattenuta sta chiudendo, e quel dato
    puo' arrivare solo da qui.
    """
    tx_id = f"controlli-reserve-{uuid4().hex}"
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=game_session_id,
        tx_id=tx_id, amount="10.00",
    ))
    assert response.status_code == 200, response.text
    return tx_id


def test_valuta_diversa_da_quella_del_conto_rifiutata_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-currency")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"wrong-currency-{uuid4().hex}",
        amount="10.00", currency="USD",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_limite_sessione_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    # Il tetto della sessione tavolo, non il saldo: l'importo supera TABLE_SESSION_MAX_CHIPS.
    # Il nome di questo collaudo e' stato corretto l'8/09 (RIP-04) perche' diceva
    # "saldo insufficiente" e provava questo. Anche il prefisso e il tx_id sono stati
    # corretti: portavano ancora il nome sbagliato dentro il corpo.
    player = create_player(prefix="seamless-house-session-limit")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"session-limit-{uuid4().hex}", amount="1000.01",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_saldo_insufficiente_rifiutato_saldo_invariato(
    client, create_player, db_connection, db_helpers
) -> None:
    """Il giocatore non ha abbastanza soldi: la richiesta va rifiutata, il saldo non si tocca.

    Scritto l'8/09/2026 per RIP-04 e RIFATTO la stessa notte, dopo che la revisione
    indipendente ha respinto la prima versione.

    La prima versione usava monkeypatch per iniettare `table_session_id` dentro il
    modulo della rotta. Ma la rotta vera quel parametro **non lo passa mai** (compare
    zero volte in `api/v1/seamless/router.py`): quella versione provava una rotta che
    in produzione non esiste, e sarebbe diventata verde dichiarando una proprieta' che
    il prodotto non ha.

    Questa versione interroga la rotta vera e **non presume nulla sul codice d'errore**,
    perche' oggi il prodotto segnala il saldo insufficiente con l'etichetta di un'altra
    cosa (`TableSessionLimitExceededError`) e come separare le due cause e' una
    decisione di prodotto ancora da prendere. Pretende quindi soltanto cio' che deve
    essere vero **comunque** la si prenda: rifiutata, e saldo invariato.
    """
    player = create_player(prefix="seamless-house-insufficient-balance")
    user_id = str(player["user_id"])
    _set_wallet_balance(db_connection, user_id, "5.00")
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id,
        game_session_id=str(uuid4()),
        tx_id=f"insufficient-balance-{uuid4().hex}",
        amount="10.00",
    ))
    _assert_rejected_without_balance_change(
        response, before, db_helpers.get_wallet_balance(user_id)
    )


def test_importo_sotto_minimo_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-minimum")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"below-minimum-{uuid4().hex}", amount="0.00",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_importo_sopra_massimo_rifiutato_saldo_invariato(client, create_player, db_helpers) -> None:
    player = create_player(prefix="seamless-house-maximum")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    response = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=str(uuid4()), tx_id=f"above-maximum-{uuid4().hex}", amount="999.99",
    ))
    _assert_rejected_without_balance_change(response, before, db_helpers.get_wallet_balance(user_id))


def test_reg02_sospensione_non_blocca_sessione_aperta_ma_blocca_sessione_nuova(
    client, create_player, db_connection, db_helpers
) -> None:
    """I casi 1--4 sono sequenziali per rendere verificabile il legame fra le due sessioni."""
    player = create_player(prefix="seamless-reg02")
    user_id = str(player["user_id"])
    existing_game_session_id = str(uuid4())

    # Caso 1: trattenuta aperta, poi sospensione: la commit deve ancora passare.
    reserve_tx_id = _open_reserve(client, user_id, existing_game_session_id)
    _set_player_status(db_connection, user_id, "suspended")
    commit = _post(client, "/seamless/wallet/commit", _payload(
        user_id=user_id, game_session_id=existing_game_session_id,
        reserve_tx_id=reserve_tx_id,
        tx_id=f"reg02-commit-open-session-{uuid4().hex}", amount="25.00", is_win=True,
    ))
    assert commit.status_code == 200, commit.text

    # Caso 2: STESSA game_session_id del caso 1; una nuova trattenuta deve passare.
    same_game_session_id = existing_game_session_id
    assert same_game_session_id == existing_game_session_id
    reserve_in_existing_session = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=same_game_session_id,
        tx_id=f"reg02-reserve-existing-session-{uuid4().hex}", amount="10.00",
    ))
    assert reserve_in_existing_session.status_code == 200, reserve_in_existing_session.text

    # Caso 3: trattenuta aperta, giocatore sospeso, rollback deve passare.
    rollback_game_session_id = str(uuid4())
    _set_player_status(db_connection, user_id, "active")
    rollback_reserve_tx_id = _open_reserve(client, user_id, rollback_game_session_id)
    _set_player_status(db_connection, user_id, "suspended")
    rollback = _post(client, "/seamless/wallet/rollback", _payload(
        user_id=user_id, game_session_id=rollback_game_session_id,
        reserve_tx_id=rollback_reserve_tx_id,
        tx_id=f"reg02-rollback-open-session-{uuid4().hex}",
    ))
    assert rollback.status_code == 200, rollback.text

    # Caso 4: game_session_id DIVERSO: una sessione nuova e' rifiutata e non muove saldo.
    new_game_session_id = str(uuid4())
    assert new_game_session_id != existing_game_session_id
    before = db_helpers.get_wallet_balance(user_id)
    new_session = _post(client, "/seamless/wallet/reserve", _payload(
        user_id=user_id, game_session_id=new_game_session_id,
        tx_id=f"reg02-reserve-new-session-{uuid4().hex}", amount="10.00",
    ))
    after = db_helpers.get_wallet_balance(user_id)
    _assert_rejected_without_balance_change(new_session, before, after)
