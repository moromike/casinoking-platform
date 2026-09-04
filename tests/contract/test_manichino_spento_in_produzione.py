"""MAN-05: in produzione il manichino non esiste, qualunque cosa dica l'interruttore.

PERCHE' IL RELOAD: la registrazione delle rotte avviene all'import di
`app.api.router` (`if manichino_attivo(): include_router(...)`). Per provare
l'interruttore senza rilanciare il processo, il test ricarica quel modulo con
l'ambiente simulato e costruisce un'app nuova; a fine test il modulo viene
ricaricato di nuovo con l'ambiente reale, cosi' gli altri test della sessione
trovano il router nello stato giusto.
"""

from __future__ import annotations

from dataclasses import replace
import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.router as api_router_module
from app.api.errors import register_error_handlers
from app.core import config as config_module
from app.modules.games.manichino import manichino_attivo


@pytest.fixture
def _router_ripristinato():
    # Il teardown di questo fixture gira DOPO quello di monkeypatch (ordine
    # inverso di setup: va dichiarato prima in firma), quindi il reload finale
    # vede di nuovo l'ambiente reale.
    yield
    importlib.reload(api_router_module)


def _app_con_router_corrente() -> TestClient:
    importlib.reload(api_router_module)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api_router_module.api_router, prefix="/api/v1")
    return TestClient(app)


def test_manichino_spento_in_produzione_anche_con_interruttore_attivo(
    _router_ripristinato,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # CK_MANICHINO=1 ma APP_ENV=production: il modulo non si registra e basta.
    monkeypatch.setenv("CK_MANICHINO", "1")
    monkeypatch.setattr(
        config_module,
        "settings",
        replace(config_module.settings, app_env="production"),
    )
    assert manichino_attivo() is False

    client = _app_con_router_corrente()
    for path in ("/api/v1/games/manichino/start", "/api/v1/games/manichino/settle"):
        response = client.post(path, json={})
        assert response.status_code == 404, f"{path} risponde in produzione"


def test_manichino_spento_senza_interruttore(
    _router_ripristinato,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Spento di default: fuori produzione ma senza CK_MANICHINO, niente rotte.
    monkeypatch.delenv("CK_MANICHINO", raising=False)
    assert manichino_attivo() is False

    client = _app_con_router_corrente()
    response = client.post("/api/v1/games/manichino/start", json={})
    assert response.status_code == 404


def test_manichino_attivo_con_interruttore_fuori_produzione(
    _router_ripristinato,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Controllo positivo: con l'interruttore attivo la rotta esiste — risponde
    # 401 (manca il bearer) invece di 404. La dipendenza di autenticazione
    # scatta prima del corpo del handler, quindi il 401 e' la prova che la
    # rotta e' registrata e non anonima.
    monkeypatch.setenv("CK_MANICHINO", "1")
    assert manichino_attivo() is True

    client = _app_con_router_corrente()
    response = client.post(
        "/api/v1/games/manichino/start",
        json={"bet_amount": "1.000000", "wallet_type": "cash"},
    )
    assert response.status_code == 401
