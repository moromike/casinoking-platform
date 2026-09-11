"""3bC — Collaudo incrociato: il client Coins VERO produce richieste valide.

Si istanzia il SeamlessWalletClient reale di m-and-m-games con un trasporto
finto, si catturano le tre richieste (reserve/commit/rollback) e si validano:
- i corpi coi modelli Pydantic VERI della piattaforma (ReserveRequest, ecc.)
- la firma col verificatore VERO (firma_valida da providers/auth.py)

PERCHE' DENTRO IL GATE E NON A PARTE: un collaudo che gira separatamente
puo' essere dimenticato. Dentro il gate della piattaforma, il rosso e'
visibile a ogni esecuzione.

FALLISCE, NON SALTA, se il repository fratello manca: pytest.fail() rende
il test ROSSO, non skippato. Un test skippato e' un test che non prova
niente, e il gate non lo conta come fallimento.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

# --- Individuare il repository fratello ---
# Dentro Docker: CK_REPO_FRATELLO=/repo-fratello/src (montato da ck-test.sh)
# Sulla macchina: percorso relativo al repository della piattaforma
_PERCORSO_FRATELLO = os.environ.get("CK_REPO_FRATELLO")
if not _PERCORSO_FRATELLO:
    _radice = Path(__file__).resolve().parents[2]
    _candidato = _radice.parent / "m-and-m-games" / "src"
    if _candidato.is_dir():
        _PERCORSO_FRATELLO = str(_candidato)

if not _PERCORSO_FRATELLO or not Path(_PERCORSO_FRATELLO).is_dir():
    pytest.fail(
        "3bC: il repository fratello m-and-m-games non e' raggiungibile. "
        "Il collaudo incrociato non puo' girare senza il client Coins reale. "
        "Clonare m-and-m-games accanto a casinoking-platform, oppure impostare "
        "CK_REPO_FRATELLO al percorso del suo src/."
    )

# M&M config.py pretende MANDM_SECRET_KEY in ambiente
if "MANDM_SECRET_KEY" not in os.environ:
    os.environ["MANDM_SECRET_KEY"] = "mandm-collaudo"

sys.path.insert(0, _PERCORSO_FRATELLO)

from games.coins.platform_client import SeamlessWalletClient  # noqa: E402

from app.api.v1.seamless.router import (  # noqa: E402
    CommitRequest,
    ReserveRequest,
    RollbackRequest,
)
from app.modules.providers.auth import firma_valida  # noqa: E402


PROVIDER_ID = "m-and-m-games"
CHIAVE_PROVA = b"mandm-collaudo"
CONTESTO_ATTRS = {
    "user_id": "user-incrociato",
    "game_session_id": "session-incrociata",
    "game_code": "coins",
    "wallet_type": "cash",
    "currency": "EUR",
    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
}


class _LaunchContextStub:
    """Uno stub con gli stessi attributi di LaunchContext, senza dipendenze M&M."""

    def __init__(self) -> None:
        for k, v in CONTESTO_ATTRS.items():
            setattr(self, k, v)


class _RequestCapture:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json={"status": "success"}, request=request)


def _make_client(capture: _RequestCapture) -> SeamlessWalletClient:
    return SeamlessWalletClient(
        platform_url="http://piattaforma.test/api/v1/seamless",
        provider_id=PROVIDER_ID,
        secret_key=CHIAVE_PROVA,
        transport=httpx.MockTransport(capture),
    )


# --- 1. reserve produce una ReserveRequest valida ---


def test_reserve_produces_valid_reserve_request() -> None:
    capture = _RequestCapture()
    client = _make_client(capture)
    contesto = _LaunchContextStub()

    client.reserve(tx_id="tx-riserva-1", amount=10, launch_context=contesto)

    assert len(capture.requests) == 1
    richiesta = capture.requests[0]
    corpo = json.loads(richiesta.content)

    parsed = ReserveRequest.model_validate(corpo)
    assert parsed.user_id == "user-incrociato"
    assert parsed.game_session_id == "session-incrociata"
    assert parsed.game_code == "coins"
    assert parsed.wallet_type == "cash"
    assert parsed.currency == "EUR"
    assert parsed.tx_id == "tx-riserva-1"
    assert parsed.provider_code == PROVIDER_ID
    assert parsed.amount == 10
    assert parsed.timestamp
    assert parsed.nonce

    firma = richiesta.headers.get("x-signature-hmac", "")
    assert firma_valida(PROVIDER_ID, richiesta.content, firma), (
        "La firma del client M&M non e' verificata da firma_valida"
    )
    assert richiesta.headers.get("x-provider-id") == PROVIDER_ID


# --- 2. commit produce una CommitRequest valida con reserve_tx_id ---


def test_commit_produces_valid_commit_request() -> None:
    capture = _RequestCapture()
    client = _make_client(capture)
    contesto = _LaunchContextStub()

    client.commit(
        tx_id="tx-commit-1",
        amount=20,
        is_win=True,
        reserve_tx_id="tx-riserva-1",
        launch_context=contesto,
    )

    assert len(capture.requests) == 1
    richiesta = capture.requests[0]
    corpo = json.loads(richiesta.content)

    parsed = CommitRequest.model_validate(corpo)
    assert parsed.reserve_tx_id == "tx-riserva-1"
    assert parsed.is_win is True
    assert parsed.user_id == "user-incrociato"
    assert parsed.provider_code == PROVIDER_ID

    firma = richiesta.headers.get("x-signature-hmac", "")
    assert firma_valida(PROVIDER_ID, richiesta.content, firma)


# --- 3. rollback produce una RollbackRequest valida con reserve_tx_id ---


def test_rollback_produces_valid_rollback_request() -> None:
    capture = _RequestCapture()
    client = _make_client(capture)
    contesto = _LaunchContextStub()

    client.rollback(
        tx_id="tx-rollback-1",
        reserve_tx_id="tx-riserva-1",
        launch_context=contesto,
    )

    assert len(capture.requests) == 1
    richiesta = capture.requests[0]
    corpo = json.loads(richiesta.content)

    parsed = RollbackRequest.model_validate(corpo)
    assert parsed.reserve_tx_id == "tx-riserva-1"
    assert parsed.user_id == "user-incrociato"
    assert parsed.provider_code == PROVIDER_ID

    firma = richiesta.headers.get("x-signature-hmac", "")
    assert firma_valida(PROVIDER_ID, richiesta.content, firma)
