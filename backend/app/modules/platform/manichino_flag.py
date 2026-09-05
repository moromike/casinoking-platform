"""L'interruttore del manichino, e il codice che lo identifica — lato PIATTAFORMA.

PERCHE' STA QUI E NON DENTRO IL MODULO DI GIOCO. Il manichino nasce per ridurre la
dipendenza della piattaforma dai giochi. Tenere l'interruttore dentro
`app.modules.games.manichino` costringeva cinque file di piattaforma
(`api/router.py`, `game_codes.py`, `game_runtime_descriptors.py`,
`settings/service.py`, `session_force_close.py`) a importare un modulo di gioco per
sapere se accendersi: **l'attrezzo contro l'accoppiamento lo aumentava di cinque
punti.** L'ha pescato il cricchetto di MAN-07 al primo colpo, sul lavoro appena fatto.

Qui la piattaforma chiede a se' stessa se la cavia e' accesa, e nessuno deve importare
un gioco per saperlo.
"""

from __future__ import annotations

import os

from app.core import config as _config

GAME_CODE_MANICHINO = "manichino"
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
