from __future__ import annotations

from collections.abc import Callable


LiquidazioneHandler = Callable[..., dict[str, object] | None]

_LIQUIDAZIONI: dict[str, LiquidazioneHandler] = {}


def registra_liquidazione(game_code: str, handler: LiquidazioneHandler) -> None:
    esistente = _LIQUIDAZIONI.get(game_code)
    if esistente is not None and esistente is not handler:
        raise RuntimeError(
            f"Liquidazione gia' registrata con un handler diverso per {game_code}"
        )
    _LIQUIDAZIONI[game_code] = handler


def cerca_liquidazione(game_code: str) -> LiquidazioneHandler | None:
    return _LIQUIDAZIONI.get(game_code)


def giochi_iscritti() -> frozenset[str]:
    return frozenset(_LIQUIDAZIONI)
