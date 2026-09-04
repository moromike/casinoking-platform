"""Il manichino: una cavia contabile, non un gioco.

PERCHE' ESISTE: decine di test della piattaforma non testano i giochi — usano
un gioco per PRODURRE una transazione e poi verificano contabilita', sessioni
e registro. Il manichino muove soldi veri attraverso le tubature vere
(`platform_rounds`, `ledger_transactions`, wallet) con l'esito deciso da chi
chiama, cosi' quei test hanno di nuovo una cavia.

PERCHE' E' IN QUESTO FILE E BASTA: l'interruttore deve essere importabile da
`platform/game_codes.py` e da `app/api/router.py` senza trascinare il resto
del modulo (adapter, servizi, DB): qui non si importa nulla del modulo
stesso, cosi' non ci sono cicli di import.
"""

from __future__ import annotations

import os

from app.core import config as _config

GAME_CODE_MANICHINO = "manichino"

# Titolo tecnico usato dai round del manichino. NON viene pubblicato in
# catalogo/lobby: la riga in `game_titles` serve solo a soddisfare la FK di
# `platform_rounds.title_code` e va creata con lo stesso meccanismo delle
# fixture di test (INSERT diretta, niente `site_titles`).
TITLE_CODE_MANICHINO_TEST = "manichino_test"


def manichino_attivo() -> bool:
    # PERCHE': il manichino muove denaro VERO nel registro contabile. Se fosse
    # raggiungibile in produzione sarebbe un modo per accreditarsi vincite senza
    # giocare. Si chiude, non si apre: in produzione e' spento e basta.
    # `config.settings` va letto attraverso il modulo (non `from ... import
    # settings`): i test di contratto sostituiscono l'istanza per simulare
    # APP_ENV=production, e un riferimento copiato all'import non la vedrebbe.
    if _config.settings.app_env in ("production", "prod"):
        return False
    return os.environ.get("CK_MANICHINO", "").lower() in ("1", "true", "si")
