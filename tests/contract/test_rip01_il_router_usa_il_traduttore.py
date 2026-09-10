from __future__ import annotations
"""RIP-01, contrappeso 3: il confine deve USARE l'elenco, non solo averlo.

Aggiunto dall'orchestratore dopo la sfida al piano dell'8/09, che ha trovato il
buco nei primi due contrappesi: verificavano che l'elenco fosse chiuso e non
ritentabile, ma **nessuno obbligava il router a passare di li'**. Si poteva
consegnare una mappa impeccabile e ignorata, con gli `except` duplicati ancora
al loro posto: tutti i collaudi verdi, riparazione inesistente.
"""

import ast
import inspect
from pathlib import Path

from app.api.v1.seamless import router as seamless_router

ROTTE_DEL_DENARO = ("reserve_funds", "commit_funds", "rollback_funds")


def _albero() -> ast.Module:
    sorgente = Path(inspect.getfile(seamless_router)).read_text(encoding="utf-8")
    return ast.parse(sorgente)


def _funzione(nome: str) -> ast.FunctionDef:
    for nodo in ast.walk(_albero()):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nome:
            return nodo
    raise AssertionError(f"la rotta {nome} non esiste piu' nel router seamless")


def test_ogni_rotta_del_denaro_passa_dal_traduttore() -> None:
    mancanti = []
    for nome in ROTTE_DEL_DENARO:
        chiamate = {
            n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
            for n in ast.walk(_funzione(nome))
            if isinstance(n, ast.Call)
        }
        if "translate_seamless_error" not in chiamate:
            mancanti.append(nome)
    assert not mancanti, (
        f"queste rotte non chiamano il traduttore: {mancanti}. Un elenco che "
        "nessuno consulta non e' una riparazione, e' un file in piu'."
    )


def test_nessuna_rotta_del_denaro_cattura_exception_a_mano() -> None:
    """Un `except Exception` nel corpo della rotta rimette tutto in un sacco solo."""
    colpevoli = []
    for nome in ROTTE_DEL_DENARO:
        for nodo in ast.walk(_funzione(nome)):
            if not isinstance(nodo, ast.ExceptHandler):
                continue
            tipo = nodo.type
            nomi = []
            if isinstance(tipo, ast.Name):
                nomi = [tipo.id]
            elif isinstance(tipo, ast.Tuple):
                nomi = [e.id for e in tipo.elts if isinstance(e, ast.Name)]
            elif tipo is None:
                nomi = ["<except nudo>"]
            for n in nomi:
                if n in {"Exception", "BaseException", "<except nudo>"}:
                    colpevoli.append(f"{nome}: except {n}")
    assert not colpevoli, (
        f"catture troppo larghe dentro le rotte del denaro: {colpevoli}"
    )
