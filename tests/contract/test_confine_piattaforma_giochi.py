"""MAN-07 — Il cricchetto: la piattaforma non deve dipendere sempre di piu' dai giochi.

PERCHE' ESISTE, e perche' non bastava quello che c'era gia'.

`tests/contract/test_boundary_imports.py` verifica che il GIOCO non importi la
PIATTAFORMA. Utile, ma e' la direzione opposta a quella che conta per l'estrazione.
La direzione che conta — **la piattaforma non deve importare i giochi** — non la
misurava nessuno, ed e' la ragione fisica per cui la Fase 3 ha lasciato dietro di se'
file orfani e meta' suite spenta: si erano portati via i giochi da un edificio che li
aveva dentro i muri.

QUESTO TEST NON RIPARA NIENTE. Districare quei file e' l'estrazione vera, cioe' la
fase successiva. Qui si mette un cricchetto: l'elenco dei colpevoli e' scritto sotto,
per nome, e il test diventa rosso se ne compare uno nuovo. Puo' solo stringere.

E stringe in entrambi i versi: se un file **esce** dall'elenco senza che l'elenco
venga aggiornato, il test fallisce lo stesso. Un debito che si estingue va festeggiato
scrivendolo, non lasciato scadere in silenzio — altrimenti l'elenco resta pieno di
nomi che non significano piu' niente e nessuno se ne fida piu'.
"""

from __future__ import annotations

import ast
import pathlib

RADICE = pathlib.Path(__file__).resolve().parents[2] / "backend" / "app"

# Le rotte dei giochi: importano il proprio gioco per definizione, e se ne andranno
# insieme a lui. Non sono debito.
ROTTE_DEI_GIOCHI = {
    "api/routes/mines.py",
    "api/routes/boxe.py",
    "api/routes/hi_lo.py",
    # Il manichino e' una cavia, non un gioco, ma la sua rotta ha la stessa forma:
    # importa il proprio modulo e se ne andra' con lui. Quando l'estrazione sara'
    # fatta e la cavia non servira' piu', questa riga sparisce insieme alle altre.
    "api/routes/manichino.py",
}

# IL DEBITO VERO, misurato il 4/09/2026. Sono i file della piattaforma che sanno
# cosa sia un gioco specifico. Finche' esistono, i giochi non si possono portare via.
# Ogni riga che sparisce da qui e' un passo verso l'estrazione.
DEBITO_NOTO = {
    "api/routes/admin.py",
    "modules/admin/session_force_close.py",
    # 5/09/2026, CAP-03: il debito si e' SPOSTATO, non e' nato ne' sparito.
    # Prima stava in `modules/platform/access_sessions/service.py`, un file di 1182
    # righe che conteneva 426 righe di logica contabile dei tre giochi di casa e una
    # mappa con i loro nomi scritti a mano. Adesso quel file non importa piu' nessun
    # gioco e non ne nomina nessuno: i gestori vivono nei moduli dei loro giochi e si
    # iscrivono a un registro che di giochi non sa niente.
    #
    # Cio' che resta e' questo file, ed e' una RADICE DI COMPOSIZIONE: 26 righe cui
    # spetta, per mestiere, di elencare cosa e' installato. E' l'unico posto dove un
    # nome di gioco e' legittimo, allo stesso titolo delle rotte qui sopra.
    #
    # PERCHE' NON UN'ESENZIONE. Sarebbe stato piu' comodo aggiungerlo a
    # ROTTE_DEI_GIOCHI e far sparire la riga dal debito. Ma questa dipendenza e' vera
    # e il giorno dell'estrazione va tolta: un elenco di debiti da cui si esce
    # cambiando categoria e' un elenco di cui nessuno si fida. Resta debito, e si paga
    # in Fase 10 insieme agli altri.
    "modules/platform/access_sessions/bootstrap_liquidazione.py",
    "modules/platform/catalog/admin_title_service.py",
    "modules/platform/catalog/title_locale_service.py",
}


def _moduli_importati(sorgente: str) -> list[str]:
    albero = ast.parse(sorgente)
    moduli: list[str] = []
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Import):
            moduli.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            moduli.append(nodo.module)
    return moduli


def _chi_importa_un_gioco() -> set[str]:
    colpevoli: set[str] = set()
    for percorso in RADICE.rglob("*.py"):
        if "__pycache__" in percorso.parts:
            continue
        relativo = percorso.relative_to(RADICE).as_posix()
        if relativo.startswith("modules/games/"):
            continue  # un gioco che importa se stesso non e' un problema
        try:
            moduli = _moduli_importati(percorso.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        if any(m.startswith("app.modules.games.") for m in moduli):
            colpevoli.add(relativo)
    return colpevoli


def test_nessun_file_nuovo_della_piattaforma_importa_un_gioco() -> None:
    colpevoli = _chi_importa_un_gioco() - ROTTE_DEI_GIOCHI
    nuovi = colpevoli - DEBITO_NOTO
    assert not nuovi, (
        "Questi file della piattaforma hanno cominciato a importare un modulo di gioco: "
        f"{sorted(nuovi)}. Ogni dipendenza nuova rende l'estrazione dei giochi piu' "
        "difficile di quanto fosse ieri. Se e' voluta, va aggiunta a DEBITO_NOTO con "
        "una ragione scritta nel commit — non di nascosto."
    )


def test_il_debito_dichiarato_esiste_ancora_davvero() -> None:
    colpevoli = _chi_importa_un_gioco() - ROTTE_DEI_GIOCHI
    estinti = DEBITO_NOTO - colpevoli
    assert not estinti, (
        f"Questi file NON importano piu' un gioco: {sorted(estinti)}. E' una buona "
        "notizia: vanno tolti da DEBITO_NOTO in questo stesso commit, cosi' il "
        "cricchetto stringe. Un elenco pieno di nomi non piu' veri e' un elenco di cui "
        "nessuno si fida."
    )


def test_le_rotte_dei_giochi_sono_le_uniche_esentate() -> None:
    """Le tre esenzioni devono esistere: se una sparisce, l'elenco va aggiornato."""
    mancanti = [r for r in ROTTE_DEI_GIOCHI if not (RADICE / r).exists()]
    assert not mancanti, (
        f"Rotte di gioco dichiarate esenti ma inesistenti: {mancanti}. "
        "Se i giochi sono stati estratti, questo elenco va svuotato."
    )
