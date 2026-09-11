GAME_CODE_MINES = "mines"
GAME_CODE_BOXE = "boxe"
GAME_CODE_HI_LO = "hi_lo"
# Coins e' il gioco esterno di M&M Games: non ha un runtime dentro la
# piattaforma, ma il game_code deve superare gli stessi controlli (sessioni,
# round economici) perche' il suo denaro passa dal ledger come gli altri.
GAME_CODE_COINS = "coins"

# PERCHE' il manichino sta nella lista solo quando e' attivo: `game_code` e'
# il controllo che lascia passare un gioco attraverso sessioni tavolo, sessioni
# d'accesso e round economici. Un codice presente ma spento sarebbe un gioco
# raggiungibile a interruttore chiuso.
from app.modules.platform.manichino_flag import GAME_CODE_MANICHINO, manichino_attivo

_BASE_GAME_CODES = (GAME_CODE_MINES, GAME_CODE_BOXE, GAME_CODE_HI_LO, GAME_CODE_COINS)

# La lista e' decisa all'import del processo: CK_MANICHINO si legge
# all'avvio, non a ogni richiesta — un interruttore che cambia a meta'
# processo renderebbe i test intermittenti.
ALLOWED_GAME_CODES = (
    _BASE_GAME_CODES + (GAME_CODE_MANICHINO,)
    if manichino_attivo()
    else _BASE_GAME_CODES
)
DEFAULT_GAME_CODE = GAME_CODE_MINES


def normalize_game_code(raw_value: str | None, *, required_message: str) -> str:
    if raw_value is None:
        raise ValueError(required_message)
    normalized = raw_value.strip().lower()
    if not normalized:
        raise ValueError(required_message)
    return normalized


def is_allowed_game_code(game_code: str) -> bool:
    return game_code in ALLOWED_GAME_CODES
