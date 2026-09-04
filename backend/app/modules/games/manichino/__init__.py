"""Il manichino: una cavia contabile, non un gioco.

PERCHE' ESISTE: decine di test della piattaforma non testano i giochi — usano
un gioco per PRODURRE una transazione e poi verificano contabilita', sessioni
e registro. Il manichino muove soldi veri attraverso le tubature vere
(`platform_rounds`, `ledger_transactions`, wallet) con l'esito deciso da chi
chiama, cosi' quei test hanno di nuovo una cavia.

DOVE STA L'INTERRUTTORE: nella piattaforma, non qui. Vedi il perche' sotto.
"""

from __future__ import annotations


# L'interruttore, il codice del gioco e il titolo tecnico vivono nella PIATTAFORMA
# (app/modules/platform/manichino_flag.py) e qui si riespongono soltanto. Cosi'
# nessun file di piattaforma deve importare un modulo di GIOCO per sapere se la
# cavia contabile e' accesa — che e' esattamente l'accoppiamento che il manichino
# esiste per ridurre, e che il cricchetto di MAN-07 ha pescato al primo colpo.
from app.modules.platform.manichino_flag import (  # noqa: F401
    GAME_CODE_MANICHINO,
    TITLE_CODE_MANICHINO_TEST,
    manichino_attivo,
)
