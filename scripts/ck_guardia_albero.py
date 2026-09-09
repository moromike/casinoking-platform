"""Guardia dell'albero: impedisce i verdi falsi quando i collaudi girano da una copia
di lavoro diversa da quella che ha acceso lo stack.

PERCHE' ESISTE. Trovato da Codex gpt-5.6-sol il 9/09/2026 e RIPRODOTTO: si disfa la
riparazione D2 dentro un git worktree, si lancia il suo collaudo da li', e il collaudo
resta VERDE — mentre sullo stesso identico sabotaggio l'albero principale e' rosso.

LA CAUSA, che non e' un difetto del prodotto. I collaudi che passano dalla rete
interrogano `http://backend:8000`, cioe' il contenitore acceso da docker compose. Quel
contenitore monta il codice dell'albero PRINCIPALE. Quindi una modifica di prodotto fatta
in un worktree non viene mai eseguita: il collaudo giudica il codice di un altro albero e
risponde verde. E' il modo peggiore di sbagliare, perche' un revisore lo conta come
successo — la stessa malattia per cui esiste la Fase GATE.

PERCHE' UN MODULO QUI E NON UNA MODIFICA A tests/conftest.py. La missione in corso e'
`tipo: riparazione`, e durante una riparazione i collaudi non si toccano (GAT-04). Il
posto giusto per uno strumento di misura e' fra gli strumenti, non dentro cio' che
misura. Si carica con `-p ck_guardia_albero`.

QUANTI COLLAUDI RIGUARDA, OGGI: TUTTI. La proposta iniziale era di fermare solo i collaudi
che passano dalla rete e lasciar correre gli altri. [LETTO] tests/conftest.py: tre fixture
sono `autouse=True` — `wait_for_backend` (di sessione), `preserve_mines_backoffice_config`
e `preserve_site_bootstrap` — e le ultime due dipendono da `db_connection`. Si applicano a
ogni collaudo raccolto, quindi in questa suite NON ESISTE un collaudo indipendente dallo
stack, nemmeno in tests/unit. Verificato lanciando `tests/unit` da un worktree: fermato.
La distinzione resta scritta lo stesso, e non e' codice morto: se un domani nascera' un
collaudo davvero autonomo, girera' senza che nessuno debba ricordarsi di riabilitarlo.

PERCHE' SI GUARDANO LE FIXTURE E NON LE CARTELLE. Una regola per cartella e' una stima:
[GENERATO] i collaudi che parlano con lo stack stanno in tests/contract, tests/integration
e tests/concurrency, ma non tutti, e domani uno nuovo potrebbe stare altrove. La fixture
invece e' il fatto: chi chiede `client` o `db_connection` sta parlando con lo stack, e
pytest ci dice esattamente chi lo fa. Un collaudo nuovo e' coperto senza che nessuno si
ricordi di aggiungerlo a un elenco.
"""
import os

import pytest

# Le fixture RADICE che raggiungono lo stack acceso. Non serve elencare quelle derivate:
# `item.fixturenames` contiene la chiusura completa, quindi un collaudo che usa
# `create_player` risulta comunque dipendente da `client`.
FIXTURE_DELLO_STACK = frozenset({
    "api_base_url",
    "database_url",
    "client",
    "db_connection",
    "frontend_base_url",
    "public_edge_base_url",
    "site_v3_frontend_base_url",
    "site_access_password",
    "wait_for_backend",
    "wait_for_frontend",
    "wait_for_public_edge",
    "wait_for_site_v3_frontend",
})

USCITA_ALBERO_SBAGLIATO = 6


def _stesso_albero(a: str, b: str) -> bool:
    """Due percorsi indicano la stessa cartella?

    ROSSO FALSO segnalato da Codex sol e Antigravity, ottavo giro: il confronto era fra
    STRINGHE (`os.path.normpath`). Se si arriva all'albero giusto passando per un
    collegamento simbolico, la stringa e' diversa da quella canonica che riporta Docker, e
    la guardia fermava una corsa legittima. Un blocco su chi lavora bene e' il modo piu'
    rapido per farsi disattivare.

    Si confrontano quindi le cartelle vere. `os.path.samefile` guarda l'identita' reale
    (dispositivo e inode) e non si fa ingannare dai collegamenti; se uno dei due percorsi
    non esiste dentro il contenitore — cosa normale, il percorso dell'host non e' montato
    con lo stesso nome — si ripiega su `realpath`, che almeno scioglie i collegamenti.
    """
    try:
        return os.path.samefile(a, b)
    except OSError:
        return os.path.realpath(a) == os.path.realpath(b)


def pytest_collection_modifyitems(session, config, items):
    stack = os.environ.get("CK_ALBERO_STACK", "")
    corrente = os.environ.get("CK_ALBERO_CORRENTE", "")
    # Senza le due informazioni la guardia TACE. Non e' una svista: questo modulo puo'
    # essere caricato da un chiamante che non le sa (una corsa a mano, un altro script),
    # e una guardia che blocca cio' che non sa giudicare e' peggio di una che non c'e'.
    # Chi le fornisce e' ck-test.sh, che le legge dal contenitore vero.
    if not stack or not corrente or _stesso_albero(stack, corrente):
        return

    colpiti = [i for i in items if FIXTURE_DELLO_STACK & set(i.fixturenames)]
    if not colpiti:
        return

    esempi = "\n".join("         - %s" % i.nodeid for i in colpiti[:5])
    if len(colpiti) > 5:
        esempi += "\n         - ... e altri %d" % (len(colpiti) - 5)

    pytest.exit(
        "\n[STOP] Questi collaudi giudicherebbero il codice di un ALTRO albero.\n"
        "       Stai lanciando da:  %s\n"
        "       Lo stack acceso serve il codice di: %s\n"
        "       %d collaudi su %d dipendono dallo stack, quindi NON eseguirebbero le tue\n"
        "       modifiche di prodotto: risponderebbero verde su codice mai provato.\n"
        "%s\n"
        "       PERCHE' RIGUARDA TUTTI: tests/conftest.py ha tre fixture automatiche\n"
        "       (wait_for_backend, preserve_mines_backoffice_config, preserve_site_bootstrap)\n"
        "       che si applicano a ogni collaudo. In questa suite non c'e' un sottoinsieme\n"
        "       che si possa lanciare da qui in modo attendibile.\n"
        "       COSA FARE: lancia dall'albero principale,\n"
        "         %s\n"
        "       portandoci le tue modifiche. Uno stack separato per questo albero oggi non\n"
        "       e' previsto: userebbe le stesse porte e lo stesso database, che e' esclusivo.\n"
        % (corrente, stack, len(colpiti), len(items), esempi, stack),
        returncode=USCITA_ALBERO_SBAGLIATO,
    )
