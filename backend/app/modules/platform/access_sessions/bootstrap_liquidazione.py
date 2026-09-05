from __future__ import annotations

from app.modules.platform.manichino_flag import manichino_attivo


_iscrizioni_assicurate = False


def assicura_iscrizioni() -> None:
    global _iscrizioni_assicurate
    if _iscrizioni_assicurate:
        return

    # Radice di composizione: questo e' l'unico punto che elenca per nome i giochi
    # installati. I giochi interni si iscrivono anche con CK_GIOCHI_INTERNI=off:
    # quel flag spegne le rotte, non il dovere di liberare denaro gia' trattenuto.
    from app.modules.games.boxe import autoliquidazione as _boxe_autoliquidazione  # noqa: F401
    from app.modules.games.hi_lo import autoliquidazione as _hi_lo_autoliquidazione  # noqa: F401
    from app.modules.games.mines import autoliquidazione as _mines_autoliquidazione  # noqa: F401

    if manichino_attivo():
        from app.modules.games.manichino import (  # noqa: F401
            autoliquidazione as _manichino_autoliquidazione,
        )

    _iscrizioni_assicurate = True
