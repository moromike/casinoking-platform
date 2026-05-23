from __future__ import annotations

from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from app.db.connection import db_connection
from app.modules.platform.admin_audit.service import (
    build_audit_request_fingerprint,
    record_audit_entry,
)
from app.modules.platform.catalog import title_config_service

GAME_CODE = "hi_lo"
DEFAULT_TITLE_CODE = "hilo001"
DEFAULT_LOCALE = "it"
ALLOWED_LOCALES = ("it", "en", "de", "es")
AUDIT_ACTION_TITLE_CONFIG_PUBLISH = "title_config_publish"
AUDIT_RESOURCE_TITLE = "title"

COPY_DEFINITIONS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("game.title", 80, ()),
    ("how_to_play.title", 80, ()),
    ("how_to_play.intro", 180, ()),
    ("how_to_play.card_1_title", 48, ()),
    ("how_to_play.card_1_text", 180, ()),
    ("how_to_play.card_2_title", 48, ()),
    ("how_to_play.card_2_text", 180, ()),
    ("how_to_play.card_3_title", 48, ()),
    ("how_to_play.card_3_text", 180, ()),
    ("how_to_play.continue", 48, ()),
    ("rules.dialog_aria", 80, ("gameTitle",)),
    ("rules.header_title", 80, ("gameTitle",)),
    ("rules.intro", 180, ()),
    ("rules.close_aria", 80, ()),
    ("rules.rules_tab", 32, ()),
    ("rules.replay_tab", 32, ()),
    ("rules.replay_loading", 80, ()),
    ("rules.replay_unavailable", 120, ()),
    ("rules.bet_predict_collect", 180, ()),
    ("rules.bet_predict_collect_heading", 64, ()),
    ("rules.probability_display", 64, ()),
    ("rules.payout_rules", 64, ()),
    ("rules.fairness_explain", 64, ()),
    ("rules.card_deck_mechanics", 64, ()),
    ("rules.skip_semantics", 64, ()),
    ("rules.edge_rank_behavior", 64, ()),
)
COPY_KEYS = tuple(key for key, _max_length, _placeholders in COPY_DEFINITIONS)
RULE_SECTION_KEYS = (
    "bet_predict_collect",
    "probability_display",
    "payout_rules",
    "fairness_explain",
    "card_deck_mechanics",
    "skip_semantics",
    "edge_rank_behavior",
)
DEFAULT_COPY: dict[str, dict[str, str]] = {
    "it": {
        "game.title": "HI-LO",
        "how_to_play.title": "Come si gioca",
        "how_to_play.intro": "Punta, leggi la carta scoperta e scegli il prossimo esito prima di incassare.",
        "how_to_play.card_1_title": "Punta",
        "how_to_play.card_1_text": "Imposta la puntata: il server scopre la carta iniziale e prepara le quote disponibili.",
        "how_to_play.card_2_title": "Predici",
        "how_to_play.card_2_text": "Scegli colore, sopra o sotto. Ogni scelta mostra probabilita reale e moltiplicatore backend.",
        "how_to_play.card_3_title": "Incassa",
        "how_to_play.card_3_text": "Dopo una previsione corretta puoi incassare o continuare la sequenza con rischio crescente.",
        "how_to_play.continue": "Continua",
        "rules.dialog_aria": "Info gioco {{gameTitle}}",
        "rules.header_title": "INFO GIOCO - {{gameTitle}}",
        "rules.intro": "Regole complete HI-LO: carte, probabilita, payout, skip e fairness server-authoritative.",
        "rules.close_aria": "Chiudi info gioco",
        "rules.rules_tab": "REGOLE",
        "rules.replay_tab": "REPLAY",
        "rules.replay_loading": "Caricamento replay...",
        "rules.replay_unavailable": "Replay non ancora disponibile.",
        "rules.bet_predict_collect": "Punta, predici il prossimo esito della carta e incassa prima di sbagliare.",
        "rules.bet_predict_collect_heading": "Punta, predici e incassa",
        "rules.probability_display": "Probabilita e moltiplicatori",
        "rules.payout_rules": "Regole payout",
        "rules.fairness_explain": "Fairness e RTP",
        "rules.card_deck_mechanics": "Carte e valori",
        "rules.skip_semantics": "Skip e continuita",
        "rules.edge_rank_behavior": "A, K e carte limite",
    },
    "en": {
        "game.title": "HI-LO",
        "how_to_play.title": "How to play",
        "how_to_play.intro": "Bet, read the open card and predict the next outcome before you collect.",
        "how_to_play.card_1_title": "Bet",
        "how_to_play.card_1_text": "Set the stake: the server reveals the starting card and prepares the available quotes.",
        "how_to_play.card_2_title": "Predict",
        "how_to_play.card_2_text": "Choose color, lower or higher. Every choice shows true probability and backend multiplier.",
        "how_to_play.card_3_title": "Collect",
        "how_to_play.card_3_text": "After a correct prediction you can collect or keep the sequence going with higher risk.",
        "how_to_play.continue": "Continue",
        "rules.dialog_aria": "Game info {{gameTitle}}",
        "rules.header_title": "GAME INFO - {{gameTitle}}",
        "rules.intro": "Complete HI-LO rules for cards, probability, payout, skip and server-authoritative fairness.",
        "rules.close_aria": "Close game info",
        "rules.rules_tab": "RULES",
        "rules.replay_tab": "REPLAY",
        "rules.replay_loading": "Loading replay...",
        "rules.replay_unavailable": "Replay not available yet.",
        "rules.bet_predict_collect": "Bet, predict the next card outcome and collect before a miss.",
        "rules.bet_predict_collect_heading": "Bet, predict and collect",
        "rules.probability_display": "Probability and multipliers",
        "rules.payout_rules": "Payout rules",
        "rules.fairness_explain": "Fairness and RTP",
        "rules.card_deck_mechanics": "Cards and values",
        "rules.skip_semantics": "Skip and continuity",
        "rules.edge_rank_behavior": "A, K and edge cards",
    },
    "de": {
        "game.title": "HI-LO",
        "how_to_play.title": "So spielst du",
        "how_to_play.intro": "Setze, lies die offene Karte und sage das naechste Ergebnis voraus, bevor du auszahlst.",
        "how_to_play.card_1_title": "Setzen",
        "how_to_play.card_1_text": "Lege den Einsatz fest: der Server deckt die Startkarte auf und bereitet die Quoten vor.",
        "how_to_play.card_2_title": "Vorhersagen",
        "how_to_play.card_2_text": "Waehle Farbe, niedriger oder hoeher. Jede Wahl zeigt echte Wahrscheinlichkeit und Backend-Multiplikator.",
        "how_to_play.card_3_title": "Auszahlen",
        "how_to_play.card_3_text": "Nach einer richtigen Vorhersage kannst du auszahlen oder die Serie mit mehr Risiko fortsetzen.",
        "how_to_play.continue": "Weiter",
        "rules.dialog_aria": "Spielinfo {{gameTitle}}",
        "rules.header_title": "SPIELINFO - {{gameTitle}}",
        "rules.intro": "Vollstaendige HI-LO-Regeln fuer Karten, Wahrscheinlichkeit, Auszahlung, Skip und server-authoritative Fairness.",
        "rules.close_aria": "Spielinfo schliessen",
        "rules.rules_tab": "REGELN",
        "rules.replay_tab": "REPLAY",
        "rules.replay_loading": "Replay wird geladen...",
        "rules.replay_unavailable": "Replay noch nicht verfuegbar.",
        "rules.bet_predict_collect": "Setze, sage das naechste Kartenergebnis voraus und zahle vor einem Fehler aus.",
        "rules.bet_predict_collect_heading": "Setzen, vorhersagen und auszahlen",
        "rules.probability_display": "Wahrscheinlichkeit und Multiplikatoren",
        "rules.payout_rules": "Auszahlungsregeln",
        "rules.fairness_explain": "Fairness und RTP",
        "rules.card_deck_mechanics": "Karten und Werte",
        "rules.skip_semantics": "Skip und Fortsetzung",
        "rules.edge_rank_behavior": "A, K und Randkarten",
    },
    "es": {
        "game.title": "HI-LO",
        "how_to_play.title": "Como se juega",
        "how_to_play.intro": "Apuesta, lee la carta abierta y predice el siguiente resultado antes de cobrar.",
        "how_to_play.card_1_title": "Apostar",
        "how_to_play.card_1_text": "Define la apuesta: el servidor revela la carta inicial y prepara las cuotas disponibles.",
        "how_to_play.card_2_title": "Predecir",
        "how_to_play.card_2_text": "Elige color, menor o mayor. Cada opcion muestra probabilidad real y multiplicador backend.",
        "how_to_play.card_3_title": "Cobrar",
        "how_to_play.card_3_text": "Tras una prediccion correcta puedes cobrar o continuar la secuencia con mas riesgo.",
        "how_to_play.continue": "Continuar",
        "rules.dialog_aria": "Info del juego {{gameTitle}}",
        "rules.header_title": "INFO DEL JUEGO - {{gameTitle}}",
        "rules.intro": "Reglas completas de HI-LO: cartas, probabilidad, pago, skip y fairness server-authoritative.",
        "rules.close_aria": "Cerrar info del juego",
        "rules.rules_tab": "REGLAS",
        "rules.replay_tab": "REPLAY",
        "rules.replay_loading": "Cargando replay...",
        "rules.replay_unavailable": "Replay aun no disponible.",
        "rules.bet_predict_collect": "Apuesta, predice el siguiente resultado de la carta y cobra antes de fallar.",
        "rules.bet_predict_collect_heading": "Apostar, predecir y cobrar",
        "rules.probability_display": "Probabilidad y multiplicadores",
        "rules.payout_rules": "Reglas de pago",
        "rules.fairness_explain": "Fairness y RTP",
        "rules.card_deck_mechanics": "Cartas y valores",
        "rules.skip_semantics": "Skip y continuidad",
        "rules.edge_rank_behavior": "A, K y cartas limite",
    },
}
DEFAULT_RULES_HTML: dict[str, dict[str, str]] = {
    "it": {
        "bet_predict_collect": "<p>HI-LO parte da una puntata e da una carta iniziale generata dal server. Da quel momento scegli una previsione tra colore, sopra o sotto.</p><ul><li>Se la previsione e' corretta, il round resta attivo e il moltiplicatore cumulativo cresce.</li><li>Se la previsione e' sbagliata, il round si chiude in loss e la vincita e' zero.</li><li>Dopo almeno una previsione corretta puoi incassare il payout corrente.</li></ul>",
        "probability_display": "<p>Ogni pulsante mostra la probabilita reale della scelta e il moltiplicatore calcolato dal backend. La probabilita usa un mazzo standard da 52 carte con reinserimento a ogni pescata.</p><p>Il moltiplicatore mostrato e' quello cumulativo che avrai dopo una scelta corretta: piu la previsione e' difficile, piu la quota cresce.</p>",
        "payout_rules": "<p>Il payout e' calcolato server-side come puntata iniziale moltiplicata per il moltiplicatore raggiunto. Il frontend visualizza quote e payout ricevuti dal backend, senza ricalcolare la matematica di gioco.</p><ul><li>Cashout: accredita il payout corrente.</li><li>Loss: chiude il round senza vincita.</li><li>V1 HI-LO non introduce un cap massimo specifico oltre alle policy di piattaforma.</li></ul>",
        "fairness_explain": "<p>Il target RTP e' 98% e la generazione e' server-authoritative. Ogni carta deriva da server seed, client seed, nonce e indice di pescata, con server seed hash esposto durante il round.</p><p>La sequenza e' deterministica e replayable: il player non sceglie la carta, sceglie solo la previsione. Replay e audit possono ricostruire esito, carta pescata e moltiplicatore.</p>",
        "card_deck_mechanics": "<p>Il mazzo logico e' un 52-card deck infinito con replacement: ogni pescata riparte dallo stesso insieme di rank e semi.</p><ul><li>Rank: A, 2, 3, ..., 10, J, Q, K.</li><li>Colori: cuori e quadri sono red; fiori e picche sono black.</li><li>Semi e rank sono mostrati come informazione di gioco, ma la validazione esito resta server-side.</li></ul>",
        "skip_semantics": "<p>Skip permette di cambiare la carta esposta senza modificare puntata o payout corrente. Prima della prima previsione e' libero; durante un round attivo e' limitato.</p><p>Il limite attivo e' 5 skip consecutivi: una previsione corretta azzera il contatore e riapre la sequenza.</p>",
        "edge_rank_behavior": "<p>A e K sono carte limite: per evitare scelte certe, sopra/sotto includono il pareggio sul lato che altrimenti sarebbe impossibile.</p><ul><li>Con A, Down conta A o inferiore; Up conta carte superiori.</li><li>Con K, Up conta K o superiore; Down conta carte inferiori.</li><li>Black e Red restano sempre probabilita 50%.</li></ul>",
    },
    "en": {
        "bet_predict_collect": "<p>HI-LO starts with a stake and a server-generated starting card. From that point you choose a prediction: color, higher or lower.</p><ul><li>A correct prediction keeps the round active and increases the cumulative multiplier.</li><li>A wrong prediction closes the round as a loss with zero payout.</li><li>After at least one correct prediction you can collect the current payout.</li></ul>",
        "probability_display": "<p>Every button shows the true probability of that choice and the multiplier calculated by the backend. Probability uses a standard 52-card deck with replacement on every draw.</p><p>The displayed multiplier is the cumulative multiplier after a correct choice: the harder the prediction, the higher the quote.</p>",
        "payout_rules": "<p>Payout is calculated server-side as initial stake multiplied by the reached multiplier. The frontend displays quotes and payout values received from the backend and never recalculates game math.</p><ul><li>Cashout credits the current payout.</li><li>Loss closes the round with no win.</li><li>HI-LO v1 has no game-specific max cap beyond platform policy.</li></ul>",
        "fairness_explain": "<p>The RTP target is 98% and generation is server-authoritative. Every card derives from server seed, client seed, nonce and draw index, with server seed hash visible during the round.</p><p>The sequence is deterministic and replayable: the player chooses the prediction, not the card. Replay and audit can rebuild outcome, drawn card and multiplier.</p>",
        "card_deck_mechanics": "<p>The logical deck is an infinite 52-card deck with replacement: every draw starts from the same set of ranks and suits.</p><ul><li>Ranks: A, 2, 3, ..., 10, J, Q, K.</li><li>Colors: hearts and diamonds are red; clubs and spades are black.</li><li>Suits and ranks are visible game information, while outcome validation stays server-side.</li></ul>",
        "skip_semantics": "<p>Skip changes the open card without changing stake or current payout. Before the first prediction it is free; during an active round it is limited.</p><p>The active limit is 5 consecutive skips: a correct prediction resets the counter and opens the sequence again.</p>",
        "edge_rank_behavior": "<p>A and K are edge cards: to avoid certain choices, higher/lower include ties on the side that would otherwise be impossible.</p><ul><li>With A, Down counts A or lower; Up counts cards above A.</li><li>With K, Up counts K or higher; Down counts cards below K.</li><li>Black and Red always remain 50% probability.</li></ul>",
    },
    "de": {
        "bet_predict_collect": "<p>HI-LO beginnt mit einem Einsatz und einer vom Server generierten Startkarte. Danach waehlt der Spieler eine Vorhersage: Farbe, hoeher oder niedriger.</p><ul><li>Eine richtige Vorhersage haelt die Runde aktiv und erhoeht den kumulativen Multiplikator.</li><li>Eine falsche Vorhersage beendet die Runde als Verlust mit Auszahlung null.</li><li>Nach mindestens einer richtigen Vorhersage kann der aktuelle Betrag ausgezahlt werden.</li></ul>",
        "probability_display": "<p>Jeder Button zeigt die echte Wahrscheinlichkeit der Wahl und den vom Backend berechneten Multiplikator. Die Wahrscheinlichkeit nutzt ein Standarddeck mit 52 Karten und Replacement bei jeder Ziehung.</p><p>Der angezeigte Multiplikator ist kumulativ nach einer richtigen Wahl: je schwieriger die Vorhersage, desto hoeher die Quote.</p>",
        "payout_rules": "<p>Die Auszahlung wird server-side als Starteinsatz mal erreichtem Multiplikator berechnet. Das Frontend zeigt Backend-Werte fuer Quote und Auszahlung an und berechnet die Spielmathematik nicht neu.</p><ul><li>Cashout schreibt die aktuelle Auszahlung gut.</li><li>Loss beendet die Runde ohne Gewinn.</li><li>HI-LO v1 hat keinen spiel-spezifischen Max-Cap ausser Plattformregeln.</li></ul>",
        "fairness_explain": "<p>Das RTP-Ziel ist 98% und die Generierung ist server-authoritative. Jede Karte entsteht aus Server Seed, Client Seed, Nonce und Ziehungsindex; der Server Seed Hash ist waehrend der Runde sichtbar.</p><p>Die Sequenz ist deterministisch und replayable: der Spieler waehlt die Vorhersage, nicht die Karte. Replay und Audit koennen Ergebnis, gezogene Karte und Multiplikator rekonstruieren.</p>",
        "card_deck_mechanics": "<p>Das logische Deck ist ein unendliches 52-Karten-Deck mit Replacement: jede Ziehung startet mit denselben Ranks und Suits.</p><ul><li>Ranks: A, 2, 3, ..., 10, J, Q, K.</li><li>Farben: Herzen und Karo sind red; Kreuz und Pik sind black.</li><li>Suits und Ranks sind sichtbare Spielinformation, die Validierung bleibt server-side.</li></ul>",
        "skip_semantics": "<p>Skip wechselt die offene Karte, ohne Einsatz oder aktuelle Auszahlung zu veraendern. Vor der ersten Vorhersage ist Skip frei; in einer aktiven Runde ist er begrenzt.</p><p>Das aktive Limit ist 5 aufeinanderfolgende Skips: eine richtige Vorhersage setzt den Zaehler zurueck.</p>",
        "edge_rank_behavior": "<p>A und K sind Randkarten: damit keine sicheren Entscheidungen entstehen, zaehlt hoeher/niedriger den Gleichstand auf der sonst unmoeglichen Seite mit.</p><ul><li>Bei A zaehlt Down A oder niedriger; Up zaehlt Karten ueber A.</li><li>Bei K zaehlt Up K oder hoeher; Down zaehlt Karten unter K.</li><li>Black und Red bleiben immer 50% Wahrscheinlichkeit.</li></ul>",
    },
    "es": {
        "bet_predict_collect": "<p>HI-LO empieza con una apuesta y una carta inicial generada por el servidor. Desde ahi eliges una prediccion: color, mayor o menor.</p><ul><li>Una prediccion correcta mantiene la ronda activa y aumenta el multiplicador acumulado.</li><li>Una prediccion incorrecta cierra la ronda como perdida con pago cero.</li><li>Despues de al menos una prediccion correcta puedes cobrar el pago actual.</li></ul>",
        "probability_display": "<p>Cada boton muestra la probabilidad real de esa opcion y el multiplicador calculado por el backend. La probabilidad usa una baraja estandar de 52 cartas con reemplazo en cada robo.</p><p>El multiplicador mostrado es acumulativo despues de una eleccion correcta: cuanto mas dificil la prediccion, mayor la cuota.</p>",
        "payout_rules": "<p>El pago se calcula server-side como apuesta inicial por el multiplicador alcanzado. El frontend muestra cuotas y pagos recibidos del backend y nunca recalcula la matematica del juego.</p><ul><li>Cashout acredita el pago actual.</li><li>Loss cierra la ronda sin premio.</li><li>HI-LO v1 no tiene un cap maximo especifico aparte de las politicas de plataforma.</li></ul>",
        "fairness_explain": "<p>El RTP objetivo es 98% y la generacion es server-authoritative. Cada carta deriva de server seed, client seed, nonce e indice de robo, con server seed hash visible durante la ronda.</p><p>La secuencia es deterministica y replayable: el jugador elige la prediccion, no la carta. Replay y auditoria pueden reconstruir resultado, carta robada y multiplicador.</p>",
        "card_deck_mechanics": "<p>La baraja logica es una baraja infinita de 52 cartas con reemplazo: cada robo empieza desde el mismo conjunto de rangos y palos.</p><ul><li>Rangos: A, 2, 3, ..., 10, J, Q, K.</li><li>Colores: corazones y diamantes son red; treboles y picas son black.</li><li>Palos y rangos son informacion visible, pero la validacion del resultado queda server-side.</li></ul>",
        "skip_semantics": "<p>Skip cambia la carta abierta sin cambiar apuesta ni pago actual. Antes de la primera prediccion es libre; durante una ronda activa esta limitado.</p><p>El limite activo es 5 skips consecutivos: una prediccion correcta reinicia el contador y reabre la secuencia.</p>",
        "edge_rank_behavior": "<p>A y K son cartas limite: para evitar opciones seguras, mayor/menor incluyen empate en el lado que seria imposible.</p><ul><li>Con A, Down cuenta A o menor; Up cuenta cartas por encima de A.</li><li>Con K, Up cuenta K o mayor; Down cuenta cartas por debajo de K.</li><li>Black y Red siempre mantienen probabilidad 50%.</li></ul>",
    },
}


class HiLoAdminConfigValidationError(Exception):
    pass


def get_public_admin_config(*, title_code: str = DEFAULT_TITLE_CODE) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    return _build_published_payload(stored_row=stored_row)


def get_admin_config(*, title_code: str = DEFAULT_TITLE_CODE) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    published = _build_published_payload(stored_row=stored_row)
    draft = _build_draft_payload(stored_row=stored_row, published_payload=published)
    return {
        "game_code": GAME_CODE,
        "title_code": title_code,
        "published": published,
        "draft": draft,
        "has_unpublished_changes": draft != published,
        "draft_updated_by_admin_user_id": (
            str(stored_row["draft_updated_by_admin_user_id"])
            if stored_row and stored_row.get("draft_updated_by_admin_user_id")
            else None
        ),
        "draft_updated_at": (
            stored_row["draft_updated_at"].isoformat()
            if stored_row and stored_row.get("draft_updated_at") is not None
            else None
        ),
        "published_updated_by_admin_user_id": (
            str(stored_row["updated_by_admin_user_id"])
            if stored_row and stored_row.get("updated_by_admin_user_id")
            else None
        ),
        "published_at": (
            stored_row["published_at"].isoformat()
            if stored_row and stored_row.get("published_at") is not None
            else None
        ),
    }


def update_admin_config_draft(
    *,
    admin_user_id: str,
    title_code: str,
    payload: dict[str, object],
) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    published = _build_published_payload(stored_row=stored_row)
    draft = _normalize_payload(payload)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)
            title_config_service.upsert_generic_draft(
                cursor=cursor,
                title_code=title_code,
                admin_user_id=admin_user_id,
                published_rules_sections=_store_rules(published),
                published_ui_labels=_store_copy(published),
                draft_rules_sections=_store_rules(draft),
                draft_ui_labels=_store_copy(draft),
            )

    return get_admin_config(title_code=title_code)


def publish_admin_config(*, admin_user_id: str, title_code: str) -> dict[str, object]:
    stored_row = _load_stored_row(title_code=title_code)
    before = _build_published_payload(stored_row=stored_row)
    draft = _build_draft_payload(stored_row=stored_row, published_payload=before)
    after = _normalize_payload(draft)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)
            title_config_service.upsert_generic_published(
                cursor=cursor,
                title_code=title_code,
                admin_user_id=admin_user_id,
                rules_sections=_store_rules(after),
                ui_labels=_store_copy(after),
            )
            audit_payload = _build_publish_audit_payload(
                title_code=title_code,
                before=before,
                after=after,
            )
            record_audit_entry(
                admin_user_id=admin_user_id,
                action_kind=AUDIT_ACTION_TITLE_CONFIG_PUBLISH,
                resource_kind=AUDIT_RESOURCE_TITLE,
                resource_id=title_code,
                payload=audit_payload,
                request_fingerprint=build_audit_request_fingerprint(
                    action_kind=AUDIT_ACTION_TITLE_CONFIG_PUBLISH,
                    resource_kind=AUDIT_RESOURCE_TITLE,
                    resource_id=title_code,
                    payload=audit_payload,
                ),
                cursor=cursor,
            )

    return get_admin_config(title_code=title_code)


def _load_stored_row(*, title_code: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return title_config_service.load_generic_row(cursor=cursor, title_code=title_code)


def _build_published_payload(*, stored_row: dict[str, object] | None) -> dict[str, object]:
    if stored_row is None:
        return _empty_payload()
    return _hydrate_payload(
        rules_store=_as_dict(stored_row.get("rules_sections_json")),
        copy_store=_as_dict(stored_row.get("ui_labels_json")),
    )


def _build_draft_payload(
    *,
    stored_row: dict[str, object] | None,
    published_payload: dict[str, object],
) -> dict[str, object]:
    if stored_row is None:
        return deepcopy(published_payload)
    draft_rules = _as_dict(stored_row.get("draft_rules_sections_json"))
    draft_copy = _as_dict(stored_row.get("draft_ui_labels_json"))
    if not draft_rules and not draft_copy:
        return deepcopy(published_payload)
    return _hydrate_payload(rules_store=draft_rules, copy_store=draft_copy)


def _empty_payload() -> dict[str, object]:
    return {
        "default_locale": DEFAULT_LOCALE,
        "copy": deepcopy(DEFAULT_COPY),
        "rules_html": deepcopy(DEFAULT_RULES_HTML),
    }


def _hydrate_payload(
    *,
    rules_store: dict[str, object],
    copy_store: dict[str, object],
) -> dict[str, object]:
    default_locale = _normalize_default_locale(copy_store.get("default_locale"))
    raw_copy = _as_dict(copy_store.get("copy"))
    raw_rules = _as_dict(rules_store.get("rules_html"))
    copy: dict[str, dict[str, str]] = {}
    rules_html: dict[str, dict[str, str]] = {}

    for locale in ALLOWED_LOCALES:
        locale_copy = _as_dict(raw_copy.get(locale))
        copy[locale] = _hydrate_locale_values(
            stored=locale_copy,
            defaults=DEFAULT_COPY[locale],
            keys=COPY_KEYS,
        )

        locale_rules = _as_dict(raw_rules.get(locale))
        rules_html[locale] = _hydrate_locale_values(
            stored=locale_rules,
            defaults=DEFAULT_RULES_HTML[locale],
            keys=RULE_SECTION_KEYS,
        )

    return {
        "default_locale": default_locale,
        "copy": copy,
        "rules_html": rules_html,
    }


def _hydrate_locale_values(
    *,
    stored: dict[str, object],
    defaults: dict[str, str],
    keys: tuple[str, ...],
) -> dict[str, str]:
    hydrated: dict[str, str] = {}
    for key in keys:
        value = stored.get(key)
        hydrated[key] = value if isinstance(value, str) and value.strip() else defaults[key]
    return hydrated


def _normalize_payload(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise HiLoAdminConfigValidationError("payload must be an object")
    return {
        "default_locale": _normalize_default_locale(payload.get("default_locale")),
        "copy": _normalize_copy(payload.get("copy")),
        "rules_html": _normalize_rules_html(payload.get("rules_html")),
    }


def _normalize_default_locale(raw_default: object) -> str:
    default_locale = str(raw_default or DEFAULT_LOCALE).strip().lower()
    if default_locale not in ALLOWED_LOCALES:
        raise HiLoAdminConfigValidationError("default_locale must be a supported HI-LO locale")
    return default_locale


def _normalize_copy(raw_copy: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_copy, dict):
        raise HiLoAdminConfigValidationError("copy must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_payload = raw_copy.get(locale)
        if not isinstance(locale_payload, dict):
            raise HiLoAdminConfigValidationError(f"copy.{locale} must be an object")
        normalized[locale] = {}
        for key, max_length, required_placeholders in COPY_DEFINITIONS:
            raw_value = locale_payload.get(key)
            if not isinstance(raw_value, str):
                raise HiLoAdminConfigValidationError(f"copy.{locale}.{key} must be a string")
            value = raw_value.strip()
            if not value:
                raise HiLoAdminConfigValidationError(f"copy.{locale}.{key} is required")
            if len(value) > max_length:
                raise HiLoAdminConfigValidationError(
                    f"copy.{locale}.{key} exceeds {max_length} characters"
                )
            placeholders = _extract_placeholders(value)
            for placeholder in placeholders:
                if placeholder not in required_placeholders:
                    raise HiLoAdminConfigValidationError(
                        f"copy.{locale}.{key} contains unknown placeholder {placeholder}"
                    )
            for placeholder in required_placeholders:
                if placeholder not in placeholders:
                    raise HiLoAdminConfigValidationError(
                        f"copy.{locale}.{key} is missing placeholder {placeholder}"
                    )
            normalized[locale][key] = value
    return normalized


def _normalize_rules_html(raw_rules: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_rules, dict):
        raise HiLoAdminConfigValidationError("rules_html must be an object")
    normalized: dict[str, dict[str, str]] = {}
    for locale in ALLOWED_LOCALES:
        locale_rules = raw_rules.get(locale)
        if not isinstance(locale_rules, dict):
            raise HiLoAdminConfigValidationError(f"rules_html.{locale} must be an object")
        normalized[locale] = {}
        for key in RULE_SECTION_KEYS:
            raw_value = locale_rules.get(key)
            if not isinstance(raw_value, str):
                raise HiLoAdminConfigValidationError(f"rules_html.{locale}.{key} must be a string")
            value = _sanitize_html(raw_value)
            if not value:
                raise HiLoAdminConfigValidationError(f"rules_html.{locale}.{key} is required")
            normalized[locale][key] = value
    return normalized


def _store_copy(payload: dict[str, object]) -> dict[str, object]:
    return {
        "default_locale": payload["default_locale"],
        "copy": payload["copy"],
    }


def _store_rules(payload: dict[str, object]) -> dict[str, object]:
    return {"rules_html": payload["rules_html"]}


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _sanitize_html(value: str) -> str:
    sanitizer = _SafeHtmlSanitizer()
    sanitizer.feed(value.strip())
    sanitizer.close()
    return sanitizer.get_html().strip()


class _SafeHtmlSanitizer(HTMLParser):
    allowed_tags = {
        "p",
        "br",
        "strong",
        "em",
        "ul",
        "ol",
        "li",
        "code",
        "a",
    }
    self_closing_tags = {"br"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed_tags:
            return
        if tag == "a":
            href = None
            for key, value in attrs:
                if key == "href" and value and _is_safe_href(value):
                    href = value
                    break
            if href:
                self.parts.append(
                    f'<a href="{escape(href, quote=True)}" rel="noopener noreferrer">'
                )
                self.open_tags.append(tag)
            return
        self.parts.append(f"<{tag}>")
        if tag not in self.self_closing_tags:
            self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.allowed_tags or tag in self.self_closing_tags:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.parts.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))

    def get_html(self) -> str:
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")
        return "".join(self.parts)


def _is_safe_href(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto"} and not value.lower().startswith("javascript:")


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


def _ensure_admin_user_exists(*, cursor, admin_user_id: str) -> None:
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'admin'
        """,
        (admin_user_id,),
    )
    if cursor.fetchone() is None:
        raise HiLoAdminConfigValidationError("Admin user not found")


def _build_publish_audit_payload(
    *,
    title_code: str,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        "engine_code": GAME_CODE,
        "title_code": title_code,
        "before": _compact_audit_snapshot(before),
        "after": _compact_audit_snapshot(after),
    }


def _compact_audit_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    copy = _as_dict(snapshot.get("copy"))
    rules_html = _as_dict(snapshot.get("rules_html"))
    return {
        "default_locale": snapshot.get("default_locale"),
        "copy_locales": sorted(copy.keys()),
        "rules_locales": sorted(rules_html.keys()),
    }
