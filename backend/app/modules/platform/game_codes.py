GAME_CODE_MINES = "mines"
GAME_CODE_BOXE = "boxe"
GAME_CODE_HI_LO = "hi_lo"
ALLOWED_GAME_CODES = (GAME_CODE_MINES, GAME_CODE_BOXE, GAME_CODE_HI_LO)
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
