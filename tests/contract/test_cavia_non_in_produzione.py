from __future__ import annotations
"""PRV-04 — la cavia non puo' diventare una superficie di produzione."""

# Queste quattro difese sono indipendenti: togliendone una il collaudo diventa rosso
# su quella e solo su quella.


from dataclasses import replace
import importlib
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.router as api_router_module
from app.api.errors import register_error_handlers
from app.core import config as config_module
from app.modules.platform.access_sessions.service import (
    AccessSessionValidationError,
    create_access_session,
)
from app.modules.platform.catalog.library_service import get_site_game_library
from app.modules.platform.catalog.service import get_published_title_for_launch
from app.modules.platform.game_launch.service import (
    GameLaunchTokenValidationError,
    _ensure_title_launch_mode_allowed,
    issue_game_launch_token,
)
from app.modules.platform.manichino_flag import (
    TITLE_CODE_MANICHINO_TEST,
    ambiente_di_produzione,
    manichino_attivo,
)


@pytest.fixture
def _router_ripristinato():
    # Come MAN-05: il router si compone all'import, quindi va ricaricato anche al teardown.
    yield
    importlib.reload(api_router_module)


def _app_con_router_corrente() -> TestClient:
    importlib.reload(api_router_module)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api_router_module.api_router, prefix="/api/v1")
    return TestClient(app)


def _simula_produzione(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CK_MANICHINO", "1")
    monkeypatch.setattr(
        config_module,
        "settings",
        replace(config_module.settings, app_env="production"),
    )


def test_ambiente_di_produzione_riconosce_forme_operativamente_equivalenti(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for app_env in ("production", "PRODUCTION", "Production", "  production  ", "prod", "PROD"):
        monkeypatch.setattr(
            config_module,
            "settings",
            replace(config_module.settings, app_env=app_env),
        )
        assert ambiente_di_produzione() is True

    # Il negativo impedisce che una funzione sempre vera mascheri ambienti non produttivi.
    for app_env in ("development", "staging"):
        monkeypatch.setattr(
            config_module,
            "settings",
            replace(config_module.settings, app_env=app_env),
        )
        assert ambiente_di_produzione() is False


def _crea_titolo_di_prova(db_connection) -> str:
    title_code = f"prv04_test_{uuid4().hex[:12]}"
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_titles (
                title_code, engine_code, display_name, status, is_test, is_master, source_title_code
            )
            VALUES (%s, 'mines', 'Titolo di prova PRV-04', 'active', true, false, 'mines_classic')
            """,
            (title_code,),
        )
        cursor.execute(
            """
            INSERT INTO site_titles (
                site_code, title_code, position, status, lobby_visibility, demo_enabled, real_enabled
            )
            VALUES ('casinoking', %s, 999, 'active', 'visible', false, true)
            """,
            (title_code,),
        )
    return title_code


def _cancella_titolo_di_prova(db_connection, title_code: str) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM site_titles WHERE site_code = 'casinoking' AND title_code = %s", (title_code,))
        cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def test_d1_interruttore_non_espone_cavia_ne_emette_gettoni_in_produzione(
    _router_ripristinato, monkeypatch: pytest.MonkeyPatch
) -> None:
    _simula_produzione(monkeypatch)
    assert manichino_attivo() is False

    client = _app_con_router_corrente()
    for path in ("/api/v1/games/manichino/start", "/api/v1/games/manichino/settle"):
        response = client.post(path, json={})
        assert response.status_code == 404, f"{path} risponde in produzione"

    with pytest.raises(GameLaunchTokenValidationError, match="Manichino is not active"):
        issue_game_launch_token(
            player_id="player-prv04",
            role="player",
            game_code="manichino",
            title_code=TITLE_CODE_MANICHINO_TEST,
            site_code="casinoking",
            mode="real",
        )


def test_d1b_rotta_gettone_cavia_non_esiste_in_produzione(
    _router_ripristinato, monkeypatch: pytest.MonkeyPatch
) -> None:
    _simula_produzione(monkeypatch)

    client = _app_con_router_corrente()
    response = client.post("/api/v1/games/manichino/launch-token", json={})

    assert response.status_code == 404, "La rotta di emissione della cavia risponde in produzione"


def test_d2_vetrina_esclude_tutti_i_titoli_di_prova_in_produzione(
    monkeypatch: pytest.MonkeyPatch, db_connection
) -> None:
    _simula_produzione(monkeypatch)
    title_code = _crea_titolo_di_prova(db_connection)
    try:
        title_codes = {
            str(title["title_code"])
            for title in get_site_game_library(site_code="casinoking")["titles"]
        }
        # Senza una vetrina reale, le sole assenze sotto passerebbero anche se un guasto
        # avesse svuotato il catalogo invece di filtrare correttamente i titoli di prova.
        assert title_codes
        assert "mines001" in title_codes
        assert TITLE_CODE_MANICHINO_TEST not in title_codes
        # Non e' un'eccezione per nome: anche una Mines qualsiasi marcata test sparisce.
        assert title_code not in title_codes
    finally:
        _cancella_titolo_di_prova(db_connection, title_code)


def test_d3_lancio_rifiuta_qualunque_titolo_di_prova_in_produzione(
    monkeypatch: pytest.MonkeyPatch, db_connection
) -> None:
    _simula_produzione(monkeypatch)
    title_code = _crea_titolo_di_prova(db_connection)
    try:
        title = get_published_title_for_launch(site_code="casinoking", title_code=title_code)
        with pytest.raises(
            GameLaunchTokenValidationError,
            match="Test titles cannot be launched in production",
        ):
            _ensure_title_launch_mode_allowed(title=title, mode="real")
    finally:
        _cancella_titolo_di_prova(db_connection, title_code)


def test_d4_sessione_accesso_rifiuta_qualunque_titolo_di_prova_in_produzione(
    monkeypatch: pytest.MonkeyPatch, db_connection
) -> None:
    _simula_produzione(monkeypatch)
    title_code = _crea_titolo_di_prova(db_connection)
    try:
        with pytest.raises(
            AccessSessionValidationError,
            match="Test titles cannot be launched in production",
        ):
            create_access_session(
                user_id="player-prv04",
                game_code="mines",
                title_code=title_code,
                site_code="casinoking",
            )
    finally:
        _cancella_titolo_di_prova(db_connection, title_code)
