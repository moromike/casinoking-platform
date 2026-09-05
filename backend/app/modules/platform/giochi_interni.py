"""L'interruttore dei giochi interni — la prova generale dell'estrazione.

PERCHE' ESISTE. I giochi (Mines, Boxe, Hi-Lo) vivono dentro questa piattaforma. Il
piano e' portarli fuori, ma il tentativo del 3-4 settembre 2026 e' fallito: togliendoli
sono morti oltre trecento test, perche' decine di collaudi di CONTABILITA' e SESSIONI
usavano un gioco come veicolo per far muovere dei soldi. Si era portato via il
ponteggio da un edificio ancora in costruzione.

Questo interruttore permette di **provare l'estrazione senza farla**: con
`CK_GIOCHI_INTERNI=off` le rotte dei giochi non vengono montate e rispondono 404,
esattamente come il giorno in cui i giochi se ne andranno davvero. Se in quella
configurazione i test di contabilita' e sessioni restano verdi, la rete regge.

**Non e' l'unica prova che serve, e va detto.** Questo spegne le ROTTE. Che il codice
della piattaforma non IMPORTI piu' i moduli dei giochi e' un'altra cosa, e la misura
`tests/contract/test_confine_piattaforma_giochi.py`. Due prove per due problemi:
spegnere una rotta e' facile, districare un import no.

Acceso per difetto: in sviluppo e in produzione i giochi ci sono. Si spegne solo per
lanciare la prova.
"""

from __future__ import annotations

import os


def giochi_interni_attivi() -> bool:
    return os.environ.get("CK_GIOCHI_INTERNI", "on").strip().lower() not in (
        "off",
        "0",
        "false",
        "no",
    )
