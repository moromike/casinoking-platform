"""RIP-01, contrappeso 2: nessun rifiuto 4xx dice al fornitore di riprovare.

Scritto dall'orchestratore PRIMA della riparazione, come il contrappeso 1.

Cosa vincola, e perche' e' il danno vero. Un fornitore che riceve
`retryable: true` ripete: e' l'unica cosa che puo' fare. Se la richiesta era
sbagliata e noi gli diciamo di riprovare, gli abbiamo chiesto di ritentare in
eterno su un percorso che muove denaro. Nella prima stesura del contratto questo
danno era raccontato nelle motivazioni e non era provato da niente.
"""
from __future__ import annotations

from app.api.errors import lookup_error_definition
from app.api.v1.seamless.errors import SEAMLESS_ERROR_TRANSLATIONS


def test_nessuna_traduzione_dichiara_retryable() -> None:
    colpevoli: list[str] = []
    for eccezione, traduzione in SEAMLESS_ERROR_TRANSLATIONS.items():
        # La traduzione puo' portare con se' un retryable esplicito: se c'e',
        # deve essere falso. Un 4xx ritentabile e' una contraddizione.
        for pezzo in traduzione:
            if pezzo is True:
                colpevoli.append(eccezione.__name__)
    assert not colpevoli, (
        "queste traduzioni dichiarano retryable=True su un rifiuto 4xx: "
        f"{colpevoli}. Un rifiuto del chiamante non si ritenta."
    )


def test_ogni_codice_tradotto_e_non_ritentabile_nel_registro() -> None:
    """Il codice d'errore porta con se' `retryable` dal registro centrale.

    Non basta che la rotta non scriva `retryable: true` a mano: se il codice
    scelto e' registrato come ritentabile, la risposta lo diventa comunque.
    """
    colpevoli: list[str] = []
    sconosciuti: list[str] = []
    for eccezione, traduzione in SEAMLESS_ERROR_TRANSLATIONS.items():
        codici = [pezzo for pezzo in traduzione if isinstance(pezzo, str)]
        for codice in codici:
            definizione = lookup_error_definition(codice)
            if definizione is None:
                # Buco trovato dalla revisione dell'8/09: senza questo, un codice
                # inventato che nel registro non esiste passava il collaudo, e
                # `retryable` finiva deciso dal ripiego invece che dal registro.
                sconosciuti.append(f"{eccezione.__name__} -> {codice}")
            elif definizione.retryable:
                colpevoli.append(f"{eccezione.__name__} -> {codice}")
    assert not sconosciuti, (
        "questi codici non esistono nel registro degli errori: nessuno garantisce "
        f"che siano non ritentabili, e chi ci integra non li trova documentati: {sconosciuti}"
    )
    assert not colpevoli, (
        "questi codici sono registrati come ritentabili ma vengono usati per "
        f"rifiutare il chiamante: {colpevoli}"
    )
