"""RIP-01, contrappeso 1: l'elenco delle traduzioni e' CHIUSO.

Scritto dall'orchestratore PRIMA che la riparazione cominciasse, e non da chi
ripara: il contratto di Fase 9 lo impone con una ragione precisa — «chi e'
limitato non si scrive da solo il limite».

Cosa vincola. RIP-01 traduce le eccezioni di dominio in rifiuti 4xx al confine
delle rotte seamless. La scorciatoia peggiore possibile e' tradurre TUTTO: cosi'
il collaudo diventa verde e ogni guasto vero — un errore di programmazione, un
database irraggiungibile — viene consegnato al fornitore come «colpa tua, non
riprovare», e nessuno si accorge piu' di niente.

Quindi: cio' che NON e' in elenco deve continuare a diventare 500.
"""
from __future__ import annotations

import pytest

from app.api.v1.seamless.errors import (
    SEAMLESS_ERROR_TRANSLATIONS,
    translate_seamless_error,
)


class EccezioneMaiVistaPrima(Exception):
    """Un guasto che nessuno ha previsto. Non deve essere tradotto."""


def test_elenco_non_vuoto_e_fatto_di_eccezioni() -> None:
    assert SEAMLESS_ERROR_TRANSLATIONS, "l'elenco delle traduzioni non puo' essere vuoto"
    for eccezione in SEAMLESS_ERROR_TRANSLATIONS:
        assert isinstance(eccezione, type) and issubclass(eccezione, Exception), (
            f"{eccezione!r} non e' una classe di eccezione: l'elenco deve essere "
            "fatto di nomi di eccezioni, non di stringhe o di pattern"
        )


def test_ogni_traduzione_e_un_4xx() -> None:
    for eccezione, traduzione in SEAMLESS_ERROR_TRANSLATIONS.items():
        stato = traduzione[0]
        assert 400 <= stato < 500, (
            f"{eccezione.__name__} e' tradotta in {stato}: l'elenco serve a produrre "
            "rifiuti del chiamante, non altri stati"
        )


@pytest.mark.parametrize(
    "guasto",
    [
        EccezioneMaiVistaPrima("il database e' sparito"),
        RuntimeError("errore di programmazione"),
        ZeroDivisionError("division by zero"),
        KeyError("chiave assente"),
    ],
    ids=["eccezione-nuova", "runtime", "divisione-per-zero", "chiave-assente"],
)
def test_cio_che_non_e_in_elenco_non_viene_tradotto(guasto: Exception) -> None:
    """None significa: non tradurre, lascia che diventi 500 e che urli."""
    assert translate_seamless_error(guasto) is None, (
        f"{type(guasto).__name__} e' stato tradotto in un rifiuto 4xx. "
        "Un guasto vero consegnato al fornitore come 'colpa tua' e' il modo "
        "esatto in cui RIP-01 si chiude barando."
    )


def test_l_elenco_non_contiene_exception_ne_baseexception() -> None:
    """Mettere Exception in elenco tradurrebbe tutto, aggirando questo collaudo."""
    for vietata in (Exception, BaseException):
        assert vietata not in SEAMLESS_ERROR_TRANSLATIONS, (
            f"{vietata.__name__} in elenco traduce qualunque cosa: e' l'elenco "
            "aperto travestito da elenco chiuso"
        )


def test_l_elenco_contiene_solo_eccezioni_di_dominio_nostre() -> None:
    """Il buco che `Exception` da sola non chiude.

    Segnalato dalla sfida al piano dell'8/09: si puo' tradurre mezza codebase
    senza scrivere mai `Exception`, mettendo in elenco una base larga —
    `ValueError`, `LookupError`, o l'eccezione radice del driver del database.
    Formalmente conforme, sostanzialmente un elenco aperto.

    Il criterio che non si aggira: ogni voce dell'elenco deve essere
    un'eccezione **definita da noi**, cioe' dichiarata dentro `app.`. Se serve
    distinguere due cause che oggi condividono la stessa eccezione, la strada e'
    **separare l'eccezione** — come e' stato fatto per il saldo insufficiente
    delle sessioni tavolo — non allargare la maglia.
    """
    intrusi = [
        f"{eccezione.__module__}.{eccezione.__name__}"
        for eccezione in SEAMLESS_ERROR_TRANSLATIONS
        if not (eccezione.__module__ or "").startswith("app.")
    ]
    assert not intrusi, (
        "queste voci non sono eccezioni di dominio nostre e catturano molto piu' "
        f"di cio' che dichiarano: {intrusi}"
    )


def test_le_eccezioni_in_elenco_vengono_tradotte() -> None:
    """Il contrappeso non deve poter essere superato svuotando l'elenco."""
    for eccezione in SEAMLESS_ERROR_TRANSLATIONS:
        try:
            istanza = eccezione("caso di prova")
        except Exception:  # pragma: no cover - eccezioni con firma non standard
            continue
        assert translate_seamless_error(istanza) is not None, (
            f"{eccezione.__name__} e' in elenco ma non viene tradotta"
        )
