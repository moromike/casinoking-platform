"""G2 — Ogni rotta rifiuta le richieste anonime, tranne quelle dichiarate pubbliche.

L'onere e' rovesciato di proposito: NON si cercano le rotte che dichiarano di essere
protette. Una rotta che se ne dimentica non dichiara nulla, ed e' esattamente cosi'
che cms_v2.py e' rimasto raggiungibile senza credenziali. Qui si guardano TUTTE le
rotte, e chi ne vuole una pubblica deve scriverlo nell'elenco qui sotto, di suo pugno.

Questo file contiene solo le prove in LETTURA, che non modificano nulla e possono
girare sempre. Le prove sui metodi che scrivono stanno altrove: su una rotta davvero
aperta la richiesta arriva al gestore, e una DELETE cancella per davvero.
"""

import httpx
import pytest

# Rotte legittimamente pubbliche. Ogni riga deve avere un perche' scritto accanto.
# Aggiungere una riga qui e' una decisione di sicurezza, non un modo di far passare
# il test.
ROTTE_PUBBLICHE: set[tuple[str, str]] = {
    # --- sonde di servizio: non espongono dati
    ("GET", "/api/v1/health/live"),
    ("GET", "/api/v1/health/ready"),

    # --- il sito pubblico: un visitatore non ancora registrato deve poterlo vedere
    ("GET", "/api/v1/site/home"),
    ("GET", "/api/v1/site-v3/sites/{site_code}/manifest"),
    ("GET", "/api/v1/site-v3/sites/{site_code}/navigation"),
    ("GET", "/api/v1/site-v3/sites/{site_code}/pages/{page_code}"),
    ("GET", "/api/v1/admin/cms-v2/sites/{site_code}/pages/{page_code}/public"),

    # --- vetrina dei giochi: serve a mostrare il catalogo prima dell'accesso
    ("GET", "/api/v1/games/library"),
    ("GET", "/api/v1/catalog/sites/{site_code}/titles"),
    ("GET", "/api/v1/catalog/titles/{title_code}"),
    ("GET", "/api/v1/titles/{title_code}/theme"),
    ("GET", "/api/v1/game-modules/{game_code}/manifest"),

    # --- configurazione dei giochi: la interfaccia la legge per disegnare il tavolo
    #     DA RIVEDERE: verificare che non esponga nulla di sensibile.
    ("GET", "/api/v1/games/boxe/config"),
    ("GET", "/api/v1/games/hi-lo/config"),
    ("GET", "/api/v1/games/mines/config"),

    # --- correttezza verificabile: pubblica per progetto, e' il suo scopo
    #     DA RIVEDERE insieme a SIC-08 (il seme non deve stare in chiaro).
    ("GET", "/api/v1/games/mines/fairness/current"),
    ("GET", "/api/v1/games/mines/verify"),
}

SEGNAPOSTO = "00000000-0000-0000-0000-000000000000"


def _percorso_concreto(path: str) -> str:
    while "{" in path:
        inizio = path.index("{")
        fine = path.index("}", inizio)
        path = path[:inizio] + SEGNAPOSTO + path[fine + 1:]
    return path


@pytest.fixture(scope="module")
def server_base_url(api_base_url: str) -> str:
    """La radice del server, senza il prefisso delle API.

    api_base_url termina con /api/v1, mentre lo schema OpenAPI sta alla radice e i
    percorsi che contiene sono gia' completi di prefisso: usare il client delle API
    lo duplicherebbe. Lo slash finale si toglie prima, altrimenti la rimozione del
    suffisso non aggancia.
    """
    return api_base_url.rstrip("/").removesuffix("/api/v1").rstrip("/")


@pytest.fixture(scope="module")
def server_client(server_base_url: str):
    with httpx.Client(base_url=server_base_url, timeout=15.0) as sessione:
        yield sessione


@pytest.fixture(scope="module")
def rotte(server_client: httpx.Client) -> list[tuple[str, str]]:
    risposta = server_client.get("/openapi.json")
    risposta.raise_for_status()
    return sorted(
        (metodo.upper(), percorso)
        for percorso, operazioni in risposta.json().get("paths", {}).items()
        for metodo in operazioni
        if metodo.upper() == "GET"
    )


def test_lo_schema_contiene_abbastanza_rotte(rotte: list[tuple[str, str]]) -> None:
    """Se lo schema torna quasi vuoto, il test sotto passerebbe a vuoto."""
    assert len(rotte) >= 30, (
        f"Trovate solo {len(rotte)} rotte in lettura: lo schema o l'indirizzo sono "
        "sbagliati, non e' che il progetto ne ha poche."
    )


def test_le_rotte_pubbliche_dichiarate_esistono(rotte: list[tuple[str, str]]) -> None:
    """Una riga dell'elenco che non corrisponde a niente e' un elenco invecchiato."""
    esistenti = set(rotte)
    fantasma = sorted(f"{m} {p}" for m, p in ROTTE_PUBBLICHE if (m, p) not in esistenti)
    assert not fantasma, (
        "Rotte dichiarate pubbliche che non esistono piu':\n  " + "\n  ".join(fantasma)
    )


def test_le_rotte_in_lettura_rifiutano_le_richieste_anonime(
    server_client: httpx.Client,
    rotte: list[tuple[str, str]],
) -> None:
    aperte: list[str] = []
    for metodo, percorso in rotte:
        if (metodo, percorso) in ROTTE_PUBBLICHE:
            continue
        risposta = server_client.request(metodo, _percorso_concreto(percorso))
        if risposta.status_code in (401, 403):
            continue
        aperte.append(f"{metodo} {percorso} -> {risposta.status_code}")

    assert not aperte, (
        f"{len(aperte)} rotte in lettura rispondono a una richiesta anonima e non "
        "sono dichiarate pubbliche:\n  " + "\n  ".join(aperte)
    )
