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

BOXE_RULE_SECTION_KEYS: Final[tuple[str, ...]] = (
    "bet_collect",
    "payout_display",
    "payout_rules",
    "fairness_explain",
    "board_mechanics",
    "difficulty_semantics",
    "max_win_cap",
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

BOXE_DEFAULT_RULES_HTML: Final[dict[str, dict[str, str]]] = {
    "it": {
        "bet_collect": (
            "<p>Punta, scegli una box per riga e incassa quando il moltiplicatore ti conviene.</p>"
            "<ul><li>La mano parte dalla base della piramide.</li><li>Ogni riga richiede una sola scelta.</li><li>Una mina chiude subito la mano in perdita.</li></ul>"
        ),
        "payout_display": (
            "<p>La ladder mostra i moltiplicatori della combinazione righe x difficolta scelta.</p>"
            "<ul><li>Il valore evidenziato e' quello incassabile ora.</li><li>Il valore successivo e' il premio potenziale della prossima riga.</li></ul>"
        ),
        "payout_rules": (
            "<p>Il payout e' calcolato dal backend come puntata iniziale per moltiplicatore corrente.</p>"
            "<ul><li>Perdita: payout zero.</li><li>Top row: pagamento automatico del moltiplicatore massimo.</li><li>Target matematico: RTP 98%.</li></ul>"
        ),
        "fairness_explain": (
            "<p>BOXE e' server-authoritative: seed, outcome, full reveal e payout arrivano dal server.</p>"
            "<ul><li>Il server seed hash permette audit.</li><li>Replay e round terminali usano lo stesso payload deterministico.</li></ul>"
        ),
        "board_mechanics": (
            "<p>La board e' una piramide bottom-to-top: con N righe, cells_for_row = rows - row + 1.</p>"
            "<ul><li>Le righe future restano coperte durante il round.</li><li>Su loss, cashout o top-row win viene rivelata tutta la piramide.</li></ul>"
        ),
        "difficulty_semantics": (
            "<p>La difficolta cambia rischio e ricompensa, non il flusso della mano.</p>"
            "<ul><li>EASY: rischio minore.</li><li>MEDIUM: profilo intermedio.</li><li>HARD: rischio e moltiplicatori maggiori.</li></ul>"
        ),
        "max_win_cap": (
            "<p>BOXE v1 non applica un max win cap prodotto dedicato.</p>"
            "<ul><li>Il limite effettivo resta dato da puntata, moltiplicatore e vincoli generali del tavolo.</li></ul>"
        ),
    },
    "en": {
        "bet_collect": (
            "<p>Bet, pick one box per row, and collect when the multiplier is right.</p>"
            "<ul><li>The hand starts at the pyramid base.</li><li>Each row requires exactly one pick.</li><li>A mine ends the hand immediately in loss.</li></ul>"
        ),
        "payout_display": (
            "<p>The ladder shows the multipliers for the selected rows x difficulty setup.</p>"
            "<ul><li>The highlighted value can be collected now.</li><li>The next value is the potential reward for the next row.</li></ul>"
        ),
        "payout_rules": (
            "<p>Payout is calculated by the backend as initial bet times current multiplier.</p>"
            "<ul><li>Loss: zero payout.</li><li>Top row: automatic payout of the maximum multiplier.</li><li>Math target: 98% RTP.</li></ul>"
        ),
        "fairness_explain": (
            "<p>BOXE is server-authoritative: seed, outcome, full reveal and payout come from the server.</p>"
            "<ul><li>The server seed hash supports audit.</li><li>Replay and terminal rounds use the same deterministic payload.</li></ul>"
        ),
        "board_mechanics": (
            "<p>The board is a bottom-to-top pyramid: with N rows, cells_for_row = rows - row + 1.</p>"
            "<ul><li>Future rows stay hidden during the round.</li><li>Loss, cashout and top-row win reveal the full pyramid.</li></ul>"
        ),
        "difficulty_semantics": (
            "<p>Difficulty changes risk and reward, not the hand flow.</p>"
            "<ul><li>EASY: lower risk.</li><li>MEDIUM: balanced profile.</li><li>HARD: higher risk and higher multipliers.</li></ul>"
        ),
        "max_win_cap": (
            "<p>BOXE v1 does not apply a dedicated product max win cap.</p>"
            "<ul><li>The effective limit remains driven by bet, multiplier and general table constraints.</li></ul>"
        ),
    },
    "de": {
        "bet_collect": (
            "<p>Setze, waehle eine Box pro Reihe und zahle aus, wenn der Multiplikator passt.</p>"
            "<ul><li>Die Runde startet an der Pyramidenbasis.</li><li>Jede Reihe braucht genau eine Wahl.</li><li>Eine Mine beendet die Runde sofort als Verlust.</li></ul>"
        ),
        "payout_display": (
            "<p>Die Leiste zeigt die Multiplikatoren fuer die gewaehlte Kombination Reihen x Schwierigkeit.</p>"
            "<ul><li>Der markierte Wert kann jetzt ausgezahlt werden.</li><li>Der naechste Wert ist der potenzielle Gewinn der naechsten Reihe.</li></ul>"
        ),
        "payout_rules": (
            "<p>Die Auszahlung wird vom Backend als Einsatz mal aktueller Multiplikator berechnet.</p>"
            "<ul><li>Verlust: Auszahlung null.</li><li>Top row: automatische Auszahlung des maximalen Multiplikators.</li><li>Matheziel: 98% RTP.</li></ul>"
        ),
        "fairness_explain": (
            "<p>BOXE ist server-authoritative: Seed, Ergebnis, Full Reveal und Auszahlung kommen vom Server.</p>"
            "<ul><li>Der Server-Seed-Hash unterstuetzt Audit.</li><li>Replay und terminale Runden nutzen denselben deterministischen Payload.</li></ul>"
        ),
        "board_mechanics": (
            "<p>Das Board ist eine Pyramide von unten nach oben: bei N Reihen gilt cells_for_row = rows - row + 1.</p>"
            "<ul><li>Zukuenftige Reihen bleiben waehrend der Runde verborgen.</li><li>Verlust, Cashout und Top-Row-Win decken die ganze Pyramide auf.</li></ul>"
        ),
        "difficulty_semantics": (
            "<p>Schwierigkeit aendert Risiko und Gewinn, nicht den Ablauf.</p>"
            "<ul><li>EASY: weniger Risiko.</li><li>MEDIUM: ausgewogenes Profil.</li><li>HARD: hoeheres Risiko und hoehere Multiplikatoren.</li></ul>"
        ),
        "max_win_cap": (
            "<p>BOXE v1 nutzt keinen eigenen Produkt-Max-Win-Cap.</p>"
            "<ul><li>Das effektive Limit kommt weiter aus Einsatz, Multiplikator und allgemeinen Tischgrenzen.</li></ul>"
        ),
    },
    "es": {
        "bet_collect": (
            "<p>Apuesta, elige una caja por fila y cobra cuando el multiplicador convenga.</p>"
            "<ul><li>La mano empieza en la base de la piramide.</li><li>Cada fila requiere exactamente una eleccion.</li><li>Una mina termina la mano inmediatamente en perdida.</li></ul>"
        ),
        "payout_display": (
            "<p>La escala muestra los multiplicadores para la configuracion filas x dificultad elegida.</p>"
            "<ul><li>El valor resaltado se puede cobrar ahora.</li><li>El siguiente valor es el premio potencial de la proxima fila.</li></ul>"
        ),
        "payout_rules": (
            "<p>El backend calcula el pago como apuesta inicial por multiplicador actual.</p>"
            "<ul><li>Perdida: pago cero.</li><li>Fila superior: pago automatico del multiplicador maximo.</li><li>Objetivo matematico: RTP 98%.</li></ul>"
        ),
        "fairness_explain": (
            "<p>BOXE es server-authoritative: seed, resultado, full reveal y pago vienen del servidor.</p>"
            "<ul><li>El hash del server seed permite auditoria.</li><li>Replay y rondas terminales usan el mismo payload determinista.</li></ul>"
        ),
        "board_mechanics": (
            "<p>El tablero es una piramide de abajo hacia arriba: con N filas, cells_for_row = rows - row + 1.</p>"
            "<ul><li>Las filas futuras quedan ocultas durante la mano.</li><li>Perdida, cashout y top-row win revelan toda la piramide.</li></ul>"
        ),
        "difficulty_semantics": (
            "<p>La dificultad cambia riesgo y recompensa, no el flujo de la mano.</p>"
            "<ul><li>EASY: menor riesgo.</li><li>MEDIUM: perfil equilibrado.</li><li>HARD: mayor riesgo y multiplicadores mas altos.</li></ul>"
        ),
        "max_win_cap": (
            "<p>BOXE v1 no aplica un max win cap de producto dedicado.</p>"
            "<ul><li>El limite efectivo sigue dependiendo de apuesta, multiplicador y restricciones generales de mesa.</li></ul>"
        ),
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
