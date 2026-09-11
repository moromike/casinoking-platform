from __future__ import annotations

"""PASSO 3-bis, sottopasso 3bA — contratto di lancio Coins lato piattaforma.

Inchioda quattro cose (CONTRATTO-3bis, 11/09/2026):
1. Coins entra nel catalogo (motore, fornitore, titolo lanciabile);
2. il launch-token porta `wallet_type` e `currency` decisi dalla piattaforma,
   mai dal client;
3. `POST /providers/launch/introspect` risponde solo a un fornitore
   autenticato (schema HMAC esistente: 422 intestazione assente, 401 provider
   ignoto o firma falsa) e solo per token del SUO gioco (403 altrimenti);
4. la risposta di introspezione non contiene segreti.
"""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.modules.platform.game_codes import ALLOWED_GAME_CODES
from app.modules.providers.auth import get_provider_secret


pytestmark = [pytest.mark.integration]

PROVIDER_MANDM = "m-and-m-games"
PROVIDER_COLLAUDO = "ck_collaudo"
GAME_CODE = "coins"
TITLE_CODE = "coins001"
INTROSPECT_ROUTE = "/providers/launch/introspect"


def _firma_headers(provider_id: str, body: bytes, *, method: str = "POST",
                    route: str = INTROSPECT_ROUTE) -> dict[str, str]:
    from tests.integration._firma_operazione import token_da_percorso, firma_operazione

    secret = get_provider_secret(provider_id)
    assert secret is not None, (
        f"Chiave del provider {provider_id} non configurata per il collaudo"
    )
    token_op = token_da_percorso(route)
    return {
        "x-provider-id": provider_id,
        "x-signature-hmac": firma_operazione(secret, method, token_op, body),
        "Content-Type": "application/json",
    }


def _introspect(client, launch_token: str, provider_id: str = PROVIDER_MANDM):
    body = json.dumps({"launch_token": launch_token}, separators=(",", ":")).encode()
    return client.post(
        INTROSPECT_ROUTE, content=body, headers=_firma_headers(provider_id, body)
    )


def _issue_coins_launch_token(client, headers: dict[str, str]) -> str:
    """Il gettone si chiede alla porta di lancio della piattaforma, come per
    ogni altro gioco. Nel corpo il client PROVA a scegliersi portafoglio e
    valuta: la piattaforma deve ignorarlo e metterci cio' che sa lei."""
    response = client.post(
        "/games/mines/launch-token",
        headers=headers,
        json={
            "game_code": GAME_CODE,
            "title_code": TITLE_CODE,
            "site_code": "casinoking",
            "mode": "real",
            # Provazione: se questi campi avessero effetto, il gettone
            # dichiarerebbe un portafoglio e una valuta che la piattaforma
            # non ha mai assegnato a questo giocatore.
            "wallet_type": "bonus",
            "currency": "USD",
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["game_launch_token"])


def test_coins_registrato_nel_catalogo(db_connection) -> None:
    assert GAME_CODE in ALLOWED_GAME_CODES
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ge.status AS engine_status, ge.provider_code, gp.status AS provider_status
            FROM game_engines ge
            JOIN game_providers gp ON gp.provider_code = ge.provider_code
            WHERE ge.engine_code = %s
            """,
            (GAME_CODE,),
        )
        engine = cursor.fetchone()
        assert engine is not None, "Il motore coins non e' nel catalogo"
        assert engine["engine_status"] == "active"
        assert engine["provider_code"] == PROVIDER_MANDM
        assert engine["provider_status"] == "active"

        cursor.execute(
            """
            SELECT gt.is_master, gt.is_test, st.lobby_visibility, st.real_enabled
            FROM site_titles st
            JOIN game_titles gt ON gt.title_code = st.title_code
            WHERE st.site_code = 'casinoking' AND st.title_code = %s
              AND gt.engine_code = %s AND gt.status = 'active' AND st.status = 'active'
            """,
            (TITLE_CODE, GAME_CODE),
        )
        title = cursor.fetchone()
        assert title is not None, "Il titolo coins001 non e' pubblicato sul sito"
        assert title["is_master"] is False
        assert title["is_test"] is False
        # Senza titolo visibile e abilitato al reale la piattaforma non puo'
        # emettere il gettone che M&M introspettera'.
        assert title["lobby_visibility"] == "visible"
        assert title["real_enabled"] is True


def test_launch_token_coins_porta_wallet_type_e_currency_della_piattaforma(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="3ba-coins-payload")
    token = _issue_coins_launch_token(client, auth_headers(player["access_token"]))
    claims = jwt.decode(token, options={"verify_signature": False})
    assert claims["game_code"] == GAME_CODE
    # Il giocatore ha provato a imporsi "bonus"/"USD": il gettone deve portare
    # il portafoglio reale che la piattaforma gli conosce (cash/CHIP).
    assert claims["wallet_type"] == "cash"
    assert claims["currency"] == "CHIP"


def test_introspezione_200_campi_del_contratto(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="3ba-introspect-ok")
    token = _issue_coins_launch_token(client, auth_headers(player["access_token"]))
    claims = jwt.decode(token, options={"verify_signature": False})

    response = _introspect(client, token)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == str(player["user_id"])
    assert data["game_session_id"] == claims["game_play_session_id"]
    assert data["game_code"] == GAME_CODE
    assert data["wallet_type"] == "cash"
    assert data["currency"] == "CHIP"
    # La scadenza e' quella del gettone, non una data inventata.
    assert data["expires_at"] == datetime.fromtimestamp(claims["exp"], tz=UTC).isoformat()


def test_introspezione_422_senza_intestazioni(client) -> None:
    body = json.dumps({"launch_token": "qualunque"}, separators=(",", ":")).encode()
    response = client.post(
        INTROSPECT_ROUTE, content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422, response.text


def test_introspezione_401_firma_falsa(client) -> None:
    body = json.dumps({"launch_token": "qualunque"}, separators=(",", ":")).encode()
    response = client.post(
        INTROSPECT_ROUTE,
        content=body,
        headers={
            "x-provider-id": PROVIDER_MANDM,
            "x-signature-hmac": "0" * 64,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401, response.text


def test_introspezione_401_provider_ignoto(client) -> None:
    body = json.dumps({"launch_token": "qualunque"}, separators=(",", ":")).encode()
    response = client.post(
        INTROSPECT_ROUTE,
        content=body,
        headers={
            "x-provider-id": "provider-che-non-esiste",
            "x-signature-hmac": hmac.new(b"qualsiasi", body, hashlib.sha256).hexdigest(),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401, response.text


def test_introspezione_403_token_scaduto(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="3ba-introspect-expired")
    token = _issue_coins_launch_token(client, auth_headers(player["access_token"]))
    claims = jwt.decode(token, options={"verify_signature": False})
    expired = jwt.encode(
        {**claims, "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    response = _introspect(client, expired)
    assert response.status_code == 403, response.text


def test_introspezione_403_token_firmato_da_altri(client) -> None:
    forged = jwt.encode(
        {
            "iss": "casinoking-platform",
            "aud": "casinoking-mines",
            "sub": "chiunque",
            "token_kind": "game_launch",
            "game_code": GAME_CODE,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "chiave-inventata",
        algorithm="HS256",
    )
    response = _introspect(client, forged)
    assert response.status_code == 403, response.text


def test_introspezione_403_token_di_un_altro_gioco(
    client, create_authenticated_player, auth_headers
) -> None:
    """Un gettone del manichino (del fornitore di collaudo) presentato da M&M:
    il gioco del token non appartiene a chi chiede."""
    player = create_authenticated_player(prefix="3ba-introspect-otherscope")
    response = client.post(
        "/games/manichino/launch-token",
        headers=auth_headers(player["access_token"]),
        json={},
    )
    assert response.status_code == 200, response.text
    manichino_token = str(response.json()["data"]["game_launch_token"])
    response = _introspect(client, manichino_token)
    assert response.status_code == 403, response.text


def test_introspezione_403_provider_diverso_da_quello_del_gioco(
    client, create_authenticated_player, auth_headers
) -> None:
    """Un gettone Coins presentato dal fornitore di collaudo: autenticato, ma
    Coins non e' suo."""
    player = create_authenticated_player(prefix="3ba-introspect-wrongprov")
    token = _issue_coins_launch_token(client, auth_headers(player["access_token"]))
    response = _introspect(client, token, provider_id=PROVIDER_COLLAUDO)
    assert response.status_code == 403, response.text


def test_lancio_rifiutato_con_due_portafogli_cash(
    client, create_authenticated_player, auth_headers, db_connection
) -> None:
    """Giro 1 (revisione agy, difetto 2): lo schema ammette piu' portafogli cash
    per lo stesso giocatore (unicita' su user_id+wallet_type+currency_code,
    migrazione 0002:40-41). Se succede, il lancio reale NON deve pescarne uno
    a caso: si rifiuta con un errore di dominio (422), mai una scelta
    arbitraria."""
    from decimal import Decimal
    from uuid import uuid4

    player = create_authenticated_player(prefix="3ba-due-cash")
    ledger_id = str(uuid4())
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ledger_accounts (
                id, account_code, account_type, owner_user_id, currency_code, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                ledger_id,
                f"PLAYER_CASH_EUR_{player['user_id']}",
                "player_cash",
                str(player["user_id"]),
                "EUR",
                "active",
            ),
        )
        cursor.execute(
            """
            INSERT INTO wallet_accounts (
                id, user_id, ledger_account_id, wallet_type, currency_code,
                balance_snapshot, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid4()),
                str(player["user_id"]),
                ledger_id,
                "cash",
                "EUR",
                Decimal("0.000000"),
                "active",
            ),
        )

    response = client.post(
        "/games/mines/launch-token",
        headers=auth_headers(player["access_token"]),
        json={
            "game_code": GAME_CODE,
            "title_code": TITLE_CODE,
            "site_code": "casinoking",
            "mode": "real",
        },
    )
    assert response.status_code == 422, response.text


def test_introspezione_nessun_segreto_nella_risposta(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="3ba-introspect-noleak")
    token = _issue_coins_launch_token(client, auth_headers(player["access_token"]))
    response = _introspect(client, token)
    assert response.status_code == 200, response.text
    # Ne' il segreto JWT, ne' le chiavi dei fornitori, ne' il gettone stesso.
    assert settings.jwt_secret not in response.text
    for provider_id in (PROVIDER_MANDM, PROVIDER_COLLAUDO):
        secret = get_provider_secret(provider_id)
        if secret:
            assert secret.decode() not in response.text
    assert token not in response.text
    # E la forma e' quella del contratto: sei campi, nient'altro.
    assert set(response.json().keys()) == {
        "user_id",
        "game_session_id",
        "game_code",
        "wallet_type",
        "currency",
        "expires_at",
    }
