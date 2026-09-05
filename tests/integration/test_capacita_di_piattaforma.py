"""CAP-01/CAP-02: capacita' platform che devono sopravvivere ai runtime interni."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import settings
from app.modules.platform.manichino_flag import manichino_attivo
from tests.integration.helpers import apri_partita_cavia, create_game_access_session


def _apri_partita_mines(
    client,
    headers,
    *,
    title_code: str,
    idempotency_key: str,
) -> dict[str, object]:
    access_session_id = create_game_access_session(
        client,
        headers,
        game_code="mines",
        title_code=title_code,
    )
    response = client.post(
        "/games/mines/start",
        headers={**headers, "Idempotency-Key": idempotency_key},
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.skipif(
    not manichino_attivo(), reason="manichino spento: serve CK_MANICHINO=1"
)
def test_platform_round_reads_a_cavia_round(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="cap-platform-cavia")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    cavia = apri_partita_cavia(
        client,
        headers,
        bet_amount="2.000000",
        prefisso_idempotenza="cap-platform-cavia",
    )

    response = client.get(f"/platform/rounds/{cavia['game_session_id']}", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["game_session_id"] == cavia["game_session_id"]
    assert data["game_code"] == "manichino"
    assert data["status"] == "active"
    assert data["wallet_type"] == "cash"
    assert data["bet_amount"] == "2.000000"
    assert data["payout_amount"] == "0.000000"
    assert isinstance(data["ledger_transaction_id"], str)
    assert data["wallet_balance_after_start"].count(".") == 1
    assert data["created_at"]
    assert data["closed_at"] is None


def test_platform_round_matches_legacy_mines_session(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
) -> None:
    player = create_authenticated_player(prefix="cap-platform-mines")
    title = create_published_mines_variant(display_name="CAP Platform Mines")
    # PERCHE' COL GETTONE, e per QUESTO titolo: /games/mines/start lo pretende, e il
    # gettone deve essere emesso per lo stesso titolo su cui si apre la partita.
    headers = auth_headers(player["access_token"], title_code=str(title["title_code"]))
    started = _apri_partita_mines(
        client,
        headers,
        title_code=str(title["title_code"]),
        idempotency_key="cap-platform-mines-start",
    )

    legacy_response = client.get(
        f"/games/mines/session/{started['game_session_id']}", headers=headers
    )
    platform_response = client.get(
        f"/platform/rounds/{started['game_session_id']}", headers=headers
    )

    assert legacy_response.status_code == 200, legacy_response.text
    assert platform_response.status_code == 200, platform_response.text
    legacy = legacy_response.json()["data"]
    platform = platform_response.json()["data"]
    for field in (
        "game_session_id",
        "status",
        "wallet_type",
        "bet_amount",
        "ledger_transaction_id",
        "wallet_balance_after_start",
        "created_at",
        "closed_at",
    ):
        # PERCHE' si stampa: questa parita' e' una PROVA da depositare, e una prova che
        # dice solo "verde" non permette a nessuno di controllare cosa e' stato
        # confrontato. I valori finiscono in artifacts/fase8b/lettura-sessione-parita.txt.
        print(f"  {field:28} gioco={legacy[field]!s:44} piattaforma={platform[field]!s}")
        assert platform[field] == legacy[field]
    assert platform["game_code"] == "mines"
    assert platform["payout_amount"] == "0.000000"


def test_player_cannot_read_another_players_platform_round(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    owner = create_authenticated_player(prefix="cap-platform-owner")
    other_player = create_authenticated_player(prefix="cap-platform-other")
    # PERCHE' LA CAVIA E NON MINES: questa e' una regola di PIATTAFORMA — nessuno legge la
    # partita di un altro — e deve reggere anche quando i giochi veri non ci sono. Con
    # Mines come veicolo, a giochi spenti il collaudo morirebbe sul preparativo invece che
    # verificare la regola. Il veicolo non e' cio' che si sta verificando.
    owner_headers = auth_headers(owner["access_token"], include_game_launch_token=False)
    started = apri_partita_cavia(
        client, owner_headers, prefisso_idempotenza=f"capp-{uuid4().hex[:8]}"
    )

    response = client.get(
        f"/platform/rounds/{started['game_session_id']}",
        headers=auth_headers(other_player["access_token"], include_game_launch_token=False),
    )

    assert response.status_code == 403


def test_missing_platform_round_returns_not_found(
    client, create_authenticated_player, auth_headers
) -> None:
    player = create_authenticated_player(prefix="cap-platform-missing")

    response = client.get(
        f"/platform/rounds/{uuid4()}",
        headers=auth_headers(player["access_token"], include_game_launch_token=False),
    )

    assert response.status_code == 404


def test_platform_launch_validation_accepts_valid_token_and_rejects_invalid_cases(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="cap-platform-launch")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    # PERCHE' IL GETTONE DELLA CAVIA: la validazione e' una capacita' di PIATTAFORMA, e
    # va provata dove serve — cioe' anche a giochi spenti. Chiedere il gettone alla rotta
    # di Mines legherebbe la prova proprio a cio' da cui vogliamo renderci indipendenti.
    issued = client.post(
        "/games/manichino/launch-token",
        headers=headers,
        json={},
    )
    assert issued.status_code == 200, issued.text
    valid_token = str(issued.json()["data"]["game_launch_token"])

    accepted = client.post(
        "/platform/launch/validate", json={"game_launch_token": valid_token}
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["data"]["game_code"] == "manichino"

    claims = jwt.decode(valid_token, options={"verify_signature": False})
    other_game_claims = {**claims, "game_code": "boxe"}
    other_game_token = jwt.encode(other_game_claims, settings.jwt_secret, algorithm="HS256")
    expired_token = jwt.encode(
        {**claims, "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    badly_signed_token = jwt.encode(claims, "wrong-signing-key", algorithm="HS256")

    rejected_other_game = client.post(
        "/platform/launch/validate", json={"game_launch_token": other_game_token}
    )
    rejected_expired = client.post(
        "/platform/launch/validate", json={"game_launch_token": expired_token}
    )
    rejected_bad_signature = client.post(
        "/platform/launch/validate", json={"game_launch_token": badly_signed_token}
    )

    assert rejected_other_game.status_code == 403
    assert rejected_expired.status_code == 401
    assert rejected_bad_signature.status_code == 401
    assert (
        rejected_other_game.json()["error"]["message"]
        == "Game launch token game code is not valid"
    )
    assert rejected_expired.json()["error"]["message"] == "Game launch token has expired"
    assert rejected_bad_signature.json()["error"]["message"] == "Game launch token is not valid"


@pytest.mark.skipif(
    not manichino_attivo(), reason="manichino spento: serve CK_MANICHINO=1"
)
def test_chiave_di_idempotenza_troppo_lunga_viene_rifiutata_non_esplode(
    client, create_authenticated_player, auth_headers
) -> None:
    """Un input del chiamante non deve mai produrre un errore di sistema.

    PERCHE' ESISTE. La chiave di idempotenza viene messa in uno spazio da 128 caratteri
    dopo essere stata allungata con il codice del gioco e l'identificativo del giocatore.
    Una chiave lunga arrivava fino alla scrittura, e la banca dati rispondeva con un
    troncamento che diventava un 500 — cioe' "e' colpa nostra" per un input sbagliato di
    chi chiama. Trovato il 5/09/2026 con una chiave di 138 caratteri, mentre si provava
    tutt'altro. Adesso deve essere un rifiuto che dice cosa non va.
    """
    player = create_authenticated_player(prefix="cap-chiave-lunga")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    gettone = client.post("/games/manichino/launch-token", headers=headers, json={})
    assert gettone.status_code == 200, gettone.text
    launch_token = str(gettone.json()["data"]["game_launch_token"])

    risposta = client.post(
        "/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": launch_token,
            "Idempotency-Key": "x" * 200,
        },
        json={"bet_amount": "1.000000", "wallet_type": "cash"},
    )

    assert risposta.status_code == 422, risposta.text
    assert "too long" in risposta.json()["error"]["message"]


def test_i_giochi_restano_iscritti_alla_liquidazione_anche_a_rotte_spente() -> None:
    """CAP-03, criterio di prodotto: spegnere le rotte non spegne i soldi.

    `CK_GIOCHI_INTERNI=off` toglie le rotte dei giochi, non il dovere di liberare una
    puntata gia' trattenuta. Un round di Mines rimasto aperto deve potersi liquidare
    anche il giorno in cui la sua rotta non risponde piu': se le iscrizioni seguissero
    l'interruttore delle rotte, quel denaro resterebbe fermo senza che nessuno se ne
    accorga. Qui si verifica proprio questo, e vale in entrambe le configurazioni.
    """
    from app.modules.platform.access_sessions.bootstrap_liquidazione import (
        assicura_iscrizioni,
    )
    from app.modules.platform.access_sessions.registro_liquidazione import giochi_iscritti
    from app.modules.platform.game_codes import (
        GAME_CODE_BOXE,
        GAME_CODE_HI_LO,
        GAME_CODE_MINES,
    )

    assicura_iscrizioni()
    iscritti = giochi_iscritti()

    for game_code in (GAME_CODE_MINES, GAME_CODE_BOXE, GAME_CODE_HI_LO):
        assert game_code in iscritti, (
            f"{game_code} non e' iscritto alla liquidazione d'ufficio: un suo round "
            "rimasto aperto resterebbe aperto, con la puntata trattenuta."
        )
