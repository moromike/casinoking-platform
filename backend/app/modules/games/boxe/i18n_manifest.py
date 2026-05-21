from __future__ import annotations

from dataclasses import dataclass
from typing import Final


ALLOWED_LOCALES: Final[tuple[str, ...]] = ("it", "en", "de", "es")
DEFAULT_LOCALE: Final[str] = "it"


@dataclass(frozen=True)
class BoxeCopyDefinition:
    key: str
    required: bool
    max_length: int
    placeholders: tuple[str, ...] = ()


BOXE_COPY_MANIFEST: Final[tuple[BoxeCopyDefinition, ...]] = (
    BoxeCopyDefinition("game.title", required=True, max_length=80),
    BoxeCopyDefinition("actions.bet", required=True, max_length=32),
    BoxeCopyDefinition("actions.bet_loading", required=True, max_length=32),
    BoxeCopyDefinition("actions.collect", required=True, max_length=32),
    BoxeCopyDefinition("actions.collect_loading", required=True, max_length=32),
    BoxeCopyDefinition("actions.back_to_site_aria", required=True, max_length=80),
    BoxeCopyDefinition("actions.fullscreen", required=True, max_length=80),
    BoxeCopyDefinition("actions.game_info", required=True, max_length=32),
    BoxeCopyDefinition("round.won_notice", required=True, max_length=160, placeholders=("amount",)),
    BoxeCopyDefinition("round.lost_notice", required=True, max_length=120),
    BoxeCopyDefinition("rules.bet_collect", required=True, max_length=160),
    BoxeCopyDefinition("rules.replay_loading", required=True, max_length=80),
    BoxeCopyDefinition("rules.replay_tab", required=True, max_length=32),
    BoxeCopyDefinition("rules.replay_unavailable", required=True, max_length=120),
    BoxeCopyDefinition("errors.insufficient_balance", required=True, max_length=140),
    BoxeCopyDefinition("errors.round_closed", required=True, max_length=120),
    BoxeCopyDefinition("errors.network_retry", required=True, max_length=180),
)

BOXE_COPY_KEYS: Final[tuple[str, ...]] = tuple(
    definition.key for definition in BOXE_COPY_MANIFEST
)

BOXE_DEFAULT_COPY: Final[dict[str, dict[str, str]]] = {
    "it": {
        "game.title": "BOXE",
        "actions.bet": "Punta",
        "actions.bet_loading": "Punto...",
        "actions.collect": "Incassa",
        "actions.collect_loading": "Incasso...",
        "actions.back_to_site_aria": "Torna al sito",
        "actions.fullscreen": "Fullscreen",
        "actions.game_info": "Info gioco",
        "round.won_notice": "Hai vinto {{amount}}.",
        "round.lost_notice": "Hai scelto una mina.",
        "rules.bet_collect": "Punta, scegli una casella per riga e incassa dopo una scelta sicura.",
        "rules.replay_loading": "Caricamento replay...",
        "rules.replay_tab": "REPLAY",
        "rules.replay_unavailable": "Replay non ancora disponibile.",
        "errors.insufficient_balance": "Saldo insufficiente.",
        "errors.round_closed": "La mano e' gia' conclusa.",
        "errors.network_retry": "Connessione instabile. Riprova con la stessa azione.",
    },
    "en": {
        "game.title": "BOXE",
        "actions.bet": "Bet",
        "actions.bet_loading": "Betting...",
        "actions.collect": "Collect",
        "actions.collect_loading": "Collecting...",
        "actions.back_to_site_aria": "Back to site",
        "actions.fullscreen": "Fullscreen",
        "actions.game_info": "Game info",
        "round.won_notice": "You won {{amount}}.",
        "round.lost_notice": "You picked a mine.",
        "rules.bet_collect": "Bet, pick one box per row, and collect after a safe pick.",
        "rules.replay_loading": "Loading replay...",
        "rules.replay_tab": "REPLAY",
        "rules.replay_unavailable": "Replay not available yet.",
        "errors.insufficient_balance": "Insufficient balance.",
        "errors.round_closed": "The round is already closed.",
        "errors.network_retry": "Connection is unstable. Retry the same action.",
    },
    "de": {
        "game.title": "BOXE",
        "actions.bet": "Setzen",
        "actions.bet_loading": "Setze...",
        "actions.collect": "Auszahlen",
        "actions.collect_loading": "Zahle aus...",
        "actions.back_to_site_aria": "Zurueck zur Seite",
        "actions.fullscreen": "Fullscreen",
        "actions.game_info": "Spielinfo",
        "round.won_notice": "Du hast {{amount}} gewonnen.",
        "round.lost_notice": "Du hast eine Mine gewaehlt.",
        "rules.bet_collect": "Setze, waehle ein Feld pro Reihe und zahle nach einem sicheren Treffer aus.",
        "rules.replay_loading": "Replay wird geladen...",
        "rules.replay_tab": "REPLAY",
        "rules.replay_unavailable": "Replay noch nicht verfuegbar.",
        "errors.insufficient_balance": "Guthaben reicht nicht aus.",
        "errors.round_closed": "Die Runde ist bereits beendet.",
        "errors.network_retry": "Verbindung instabil. Wiederhole dieselbe Aktion.",
    },
    "es": {
        "game.title": "BOXE",
        "actions.bet": "Apostar",
        "actions.bet_loading": "Apostando...",
        "actions.collect": "Cobrar",
        "actions.collect_loading": "Cobrando...",
        "actions.back_to_site_aria": "Volver al sitio",
        "actions.fullscreen": "Fullscreen",
        "actions.game_info": "Info juego",
        "round.won_notice": "Ganaste {{amount}}.",
        "round.lost_notice": "Elegiste una mina.",
        "rules.bet_collect": "Apuesta, elige una caja por fila y cobra tras una eleccion segura.",
        "rules.replay_loading": "Cargando replay...",
        "rules.replay_tab": "REPLAY",
        "rules.replay_unavailable": "Replay aun no disponible.",
        "errors.insufficient_balance": "Saldo insuficiente.",
        "errors.round_closed": "La ronda ya esta cerrada.",
        "errors.network_retry": "Conexion inestable. Reintenta la misma accion.",
    },
}


def validate_default_copy_catalog() -> list[str]:
    errors: list[str] = []
    for locale in ALLOWED_LOCALES:
        copy_payload = BOXE_DEFAULT_COPY.get(locale, {})
        for definition in BOXE_COPY_MANIFEST:
            value = copy_payload.get(definition.key, "")
            if definition.required and not value.strip():
                errors.append(f"{locale}.{definition.key} is required")
            if len(value) > definition.max_length:
                errors.append(
                    f"{locale}.{definition.key} exceeds {definition.max_length} characters"
                )
            placeholders = _extract_placeholders(value)
            for placeholder in placeholders:
                if placeholder not in definition.placeholders:
                    errors.append(
                        f"{locale}.{definition.key} contains unknown placeholder {placeholder}"
                    )
            for placeholder in definition.placeholders:
                if placeholder not in placeholders:
                    errors.append(f"{locale}.{definition.key} is missing placeholder {placeholder}")
    return errors


def _extract_placeholders(value: str) -> set[str]:
    placeholders: set[str] = set()
    cursor = 0
    while True:
        start = value.find("{{", cursor)
        if start == -1:
            return placeholders
        end = value.find("}}", start + 2)
        if end == -1:
            return placeholders
        placeholders.add(value[start + 2 : end].strip())
        cursor = end + 2
