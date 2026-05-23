"use client";

export const HI_LO_SUPPORTED_LOCALES = ["it", "en", "de", "es"] as const;
export type HiLoLocale = (typeof HI_LO_SUPPORTED_LOCALES)[number];

export type HiLoCopyDefinition = {
  key: string;
  label: string;
  maxLength: number;
};

export const HI_LO_COPY_DEFINITIONS = [
  { key: "game.title", label: "Game title", maxLength: 80 },
  { key: "how_to_play.title", label: "How to play title", maxLength: 80 },
  { key: "how_to_play.intro", label: "How to play intro", maxLength: 180 },
  { key: "how_to_play.card_1_title", label: "How to play card 1 title", maxLength: 48 },
  { key: "how_to_play.card_1_text", label: "How to play card 1 text", maxLength: 180 },
  { key: "how_to_play.card_2_title", label: "How to play card 2 title", maxLength: 48 },
  { key: "how_to_play.card_2_text", label: "How to play card 2 text", maxLength: 180 },
  { key: "how_to_play.card_3_title", label: "How to play card 3 title", maxLength: 48 },
  { key: "how_to_play.card_3_text", label: "How to play card 3 text", maxLength: 180 },
  { key: "how_to_play.continue", label: "How to play continue", maxLength: 48 },
  { key: "rules.dialog_aria", label: "Rules dialog aria", maxLength: 80 },
  { key: "rules.header_title", label: "Rules header title", maxLength: 80 },
  { key: "rules.intro", label: "Rules intro", maxLength: 180 },
  { key: "rules.close_aria", label: "Rules close aria", maxLength: 80 },
  { key: "rules.rules_tab", label: "Rules tab", maxLength: 32 },
  { key: "rules.replay_tab", label: "Replay tab", maxLength: 32 },
  { key: "rules.replay_loading", label: "Replay loading", maxLength: 80 },
  { key: "rules.replay_unavailable", label: "Replay unavailable", maxLength: 120 },
  { key: "rules.bet_predict_collect", label: "Rules summary", maxLength: 180 },
  { key: "rules.bet_predict_collect_heading", label: "Bet predict collect heading", maxLength: 64 },
  { key: "rules.probability_display", label: "Probability heading", maxLength: 64 },
  { key: "rules.payout_rules", label: "Payout rules heading", maxLength: 64 },
  { key: "rules.fairness_explain", label: "Fairness heading", maxLength: 64 },
  { key: "rules.card_deck_mechanics", label: "Card deck heading", maxLength: 64 },
  { key: "rules.skip_semantics", label: "Skip heading", maxLength: 64 },
  { key: "rules.edge_rank_behavior", label: "Edge rank heading", maxLength: 64 },
] as const satisfies readonly HiLoCopyDefinition[];

export type HiLoCopyKey = (typeof HI_LO_COPY_DEFINITIONS)[number]["key"];

export const HI_LO_RULE_SECTION_KEYS = [
  "bet_predict_collect",
  "probability_display",
  "payout_rules",
  "fairness_explain",
  "card_deck_mechanics",
  "skip_semantics",
  "edge_rank_behavior",
] as const;

export type HiLoRuleSectionKey = (typeof HI_LO_RULE_SECTION_KEYS)[number];

export const HI_LO_RULE_SECTION_DEFINITIONS: readonly {
  key: HiLoRuleSectionKey;
  label: string;
}[] = [
  { key: "bet_predict_collect", label: "Bet / Predict / Collect rules" },
  { key: "probability_display", label: "Probability and multiplier display" },
  { key: "payout_rules", label: "Payout rules" },
  { key: "fairness_explain", label: "Fairness / RTP explain" },
  { key: "card_deck_mechanics", label: "Card deck mechanics" },
  { key: "skip_semantics", label: "Skip semantics" },
  { key: "edge_rank_behavior", label: "A/K edge rank behavior" },
];

export type HiLoRuleSectionContent = {
  body_html: string;
};

export const HI_LO_COPY_DEFAULTS: Record<HiLoLocale, Record<HiLoCopyKey, string>> = {
  it: {
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
  en: {
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
  de: {
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
  es: {
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
};

export const HI_LO_DEFAULT_RULE_SECTIONS: Record<
  HiLoLocale,
  Record<HiLoRuleSectionKey, HiLoRuleSectionContent>
> = {
  it: {
    bet_predict_collect: {
      body_html:
        "<p>HI-LO parte da una puntata e da una carta iniziale generata dal server. Da quel momento scegli una previsione tra colore, sopra o sotto.</p><ul><li>Se la previsione e' corretta, il round resta attivo e il moltiplicatore cumulativo cresce.</li><li>Se la previsione e' sbagliata, il round si chiude in loss e la vincita e' zero.</li><li>Dopo almeno una previsione corretta puoi incassare il payout corrente.</li></ul>",
    },
    probability_display: {
      body_html:
        "<p>Ogni pulsante mostra la probabilita reale della scelta e il moltiplicatore calcolato dal backend. La probabilita usa un mazzo standard da 52 carte con reinserimento a ogni pescata.</p><p>Il moltiplicatore mostrato e' quello cumulativo che avrai dopo una scelta corretta: piu la previsione e' difficile, piu la quota cresce.</p>",
    },
    payout_rules: {
      body_html:
        "<p>Il payout e' calcolato server-side come puntata iniziale moltiplicata per il moltiplicatore raggiunto. Il frontend visualizza quote e payout ricevuti dal backend, senza ricalcolare la matematica di gioco.</p><ul><li>Cashout: accredita il payout corrente.</li><li>Loss: chiude il round senza vincita.</li><li>V1 HI-LO non introduce un cap massimo specifico oltre alle policy di piattaforma.</li></ul>",
    },
    fairness_explain: {
      body_html:
        "<p>Il target RTP e' 98% e la generazione e' server-authoritative. Ogni carta deriva da server seed, client seed, nonce e indice di pescata, con server seed hash esposto durante il round.</p><p>La sequenza e' deterministica e replayable: il player non sceglie la carta, sceglie solo la previsione. Replay e audit possono ricostruire esito, carta pescata e moltiplicatore.</p>",
    },
    card_deck_mechanics: {
      body_html:
        "<p>Il mazzo logico e' un 52-card deck infinito con replacement: ogni pescata riparte dallo stesso insieme di rank e semi.</p><ul><li>Rank: A, 2, 3, ..., 10, J, Q, K.</li><li>Colori: cuori e quadri sono red; fiori e picche sono black.</li><li>Semi e rank sono mostrati come informazione di gioco, ma la validazione esito resta server-side.</li></ul>",
    },
    skip_semantics: {
      body_html:
        "<p>Skip permette di cambiare la carta esposta senza modificare puntata o payout corrente. Prima della prima previsione e' libero; durante un round attivo e' limitato.</p><p>Il limite attivo e' 5 skip consecutivi: una previsione corretta azzera il contatore e riapre la sequenza.</p>",
    },
    edge_rank_behavior: {
      body_html:
        "<p>A e K sono carte limite: per evitare scelte certe, sopra/sotto includono il pareggio sul lato che altrimenti sarebbe impossibile.</p><ul><li>Con A, Down conta A o inferiore; Up conta carte superiori.</li><li>Con K, Up conta K o superiore; Down conta carte inferiori.</li><li>Black e Red restano sempre probabilita 50%.</li></ul>",
    },
  },
  en: {
    bet_predict_collect: {
      body_html:
        "<p>HI-LO starts with a stake and a server-generated starting card. From that point you choose a prediction: color, higher or lower.</p><ul><li>A correct prediction keeps the round active and increases the cumulative multiplier.</li><li>A wrong prediction closes the round as a loss with zero payout.</li><li>After at least one correct prediction you can collect the current payout.</li></ul>",
    },
    probability_display: {
      body_html:
        "<p>Every button shows the true probability of that choice and the multiplier calculated by the backend. Probability uses a standard 52-card deck with replacement on every draw.</p><p>The displayed multiplier is the cumulative multiplier after a correct choice: the harder the prediction, the higher the quote.</p>",
    },
    payout_rules: {
      body_html:
        "<p>Payout is calculated server-side as initial stake multiplied by the reached multiplier. The frontend displays quotes and payout values received from the backend and never recalculates game math.</p><ul><li>Cashout credits the current payout.</li><li>Loss closes the round with no win.</li><li>HI-LO v1 has no game-specific max cap beyond platform policy.</li></ul>",
    },
    fairness_explain: {
      body_html:
        "<p>The RTP target is 98% and generation is server-authoritative. Every card derives from server seed, client seed, nonce and draw index, with server seed hash visible during the round.</p><p>The sequence is deterministic and replayable: the player chooses the prediction, not the card. Replay and audit can rebuild outcome, drawn card and multiplier.</p>",
    },
    card_deck_mechanics: {
      body_html:
        "<p>The logical deck is an infinite 52-card deck with replacement: every draw starts from the same set of ranks and suits.</p><ul><li>Ranks: A, 2, 3, ..., 10, J, Q, K.</li><li>Colors: hearts and diamonds are red; clubs and spades are black.</li><li>Suits and ranks are visible game information, while outcome validation stays server-side.</li></ul>",
    },
    skip_semantics: {
      body_html:
        "<p>Skip changes the open card without changing stake or current payout. Before the first prediction it is free; during an active round it is limited.</p><p>The active limit is 5 consecutive skips: a correct prediction resets the counter and opens the sequence again.</p>",
    },
    edge_rank_behavior: {
      body_html:
        "<p>A and K are edge cards: to avoid certain choices, higher/lower include ties on the side that would otherwise be impossible.</p><ul><li>With A, Down counts A or lower; Up counts cards above A.</li><li>With K, Up counts K or higher; Down counts cards below K.</li><li>Black and Red always remain 50% probability.</li></ul>",
    },
  },
  de: {
    bet_predict_collect: {
      body_html:
        "<p>HI-LO beginnt mit einem Einsatz und einer vom Server generierten Startkarte. Danach waehlt der Spieler eine Vorhersage: Farbe, hoeher oder niedriger.</p><ul><li>Eine richtige Vorhersage haelt die Runde aktiv und erhoeht den kumulativen Multiplikator.</li><li>Eine falsche Vorhersage beendet die Runde als Verlust mit Auszahlung null.</li><li>Nach mindestens einer richtigen Vorhersage kann der aktuelle Betrag ausgezahlt werden.</li></ul>",
    },
    probability_display: {
      body_html:
        "<p>Jeder Button zeigt die echte Wahrscheinlichkeit der Wahl und den vom Backend berechneten Multiplikator. Die Wahrscheinlichkeit nutzt ein Standarddeck mit 52 Karten und Replacement bei jeder Ziehung.</p><p>Der angezeigte Multiplikator ist kumulativ nach einer richtigen Wahl: je schwieriger die Vorhersage, desto hoeher die Quote.</p>",
    },
    payout_rules: {
      body_html:
        "<p>Die Auszahlung wird server-side als Starteinsatz mal erreichtem Multiplikator berechnet. Das Frontend zeigt Backend-Werte fuer Quote und Auszahlung an und berechnet die Spielmathematik nicht neu.</p><ul><li>Cashout schreibt die aktuelle Auszahlung gut.</li><li>Loss beendet die Runde ohne Gewinn.</li><li>HI-LO v1 hat keinen spiel-spezifischen Max-Cap ausser Plattformregeln.</li></ul>",
    },
    fairness_explain: {
      body_html:
        "<p>Das RTP-Ziel ist 98% und die Generierung ist server-authoritative. Jede Karte entsteht aus Server Seed, Client Seed, Nonce und Ziehungsindex; der Server Seed Hash ist waehrend der Runde sichtbar.</p><p>Die Sequenz ist deterministisch und replayable: der Spieler waehlt die Vorhersage, nicht die Karte. Replay und Audit koennen Ergebnis, gezogene Karte und Multiplikator rekonstruieren.</p>",
    },
    card_deck_mechanics: {
      body_html:
        "<p>Das logische Deck ist ein unendliches 52-Karten-Deck mit Replacement: jede Ziehung startet mit denselben Ranks und Suits.</p><ul><li>Ranks: A, 2, 3, ..., 10, J, Q, K.</li><li>Farben: Herzen und Karo sind red; Kreuz und Pik sind black.</li><li>Suits und Ranks sind sichtbare Spielinformation, die Validierung bleibt server-side.</li></ul>",
    },
    skip_semantics: {
      body_html:
        "<p>Skip wechselt die offene Karte, ohne Einsatz oder aktuelle Auszahlung zu veraendern. Vor der ersten Vorhersage ist Skip frei; in einer aktiven Runde ist er begrenzt.</p><p>Das aktive Limit ist 5 aufeinanderfolgende Skips: eine richtige Vorhersage setzt den Zaehler zurueck.</p>",
    },
    edge_rank_behavior: {
      body_html:
        "<p>A und K sind Randkarten: damit keine sicheren Entscheidungen entstehen, zaehlt hoeher/niedriger den Gleichstand auf der sonst unmoeglichen Seite mit.</p><ul><li>Bei A zaehlt Down A oder niedriger; Up zaehlt Karten ueber A.</li><li>Bei K zaehlt Up K oder hoeher; Down zaehlt Karten unter K.</li><li>Black und Red bleiben immer 50% Wahrscheinlichkeit.</li></ul>",
    },
  },
  es: {
    bet_predict_collect: {
      body_html:
        "<p>HI-LO empieza con una apuesta y una carta inicial generada por el servidor. Desde ahi eliges una prediccion: color, mayor o menor.</p><ul><li>Una prediccion correcta mantiene la ronda activa y aumenta el multiplicador acumulado.</li><li>Una prediccion incorrecta cierra la ronda como perdida con pago cero.</li><li>Despues de al menos una prediccion correcta puedes cobrar el pago actual.</li></ul>",
    },
    probability_display: {
      body_html:
        "<p>Cada boton muestra la probabilidad real de esa opcion y el multiplicador calculado por el backend. La probabilidad usa una baraja estandar de 52 cartas con reemplazo en cada robo.</p><p>El multiplicador mostrado es acumulativo despues de una eleccion correcta: cuanto mas dificil la prediccion, mayor la cuota.</p>",
    },
    payout_rules: {
      body_html:
        "<p>El pago se calcula server-side como apuesta inicial por el multiplicador alcanzado. El frontend muestra cuotas y pagos recibidos del backend y nunca recalcula la matematica del juego.</p><ul><li>Cashout acredita el pago actual.</li><li>Loss cierra la ronda sin premio.</li><li>HI-LO v1 no tiene un cap maximo especifico aparte de las politicas de plataforma.</li></ul>",
    },
    fairness_explain: {
      body_html:
        "<p>El RTP objetivo es 98% y la generacion es server-authoritative. Cada carta deriva de server seed, client seed, nonce e indice de robo, con server seed hash visible durante la ronda.</p><p>La secuencia es deterministica y replayable: el jugador elige la prediccion, no la carta. Replay y auditoria pueden reconstruir resultado, carta robada y multiplicador.</p>",
    },
    card_deck_mechanics: {
      body_html:
        "<p>La baraja logica es una baraja infinita de 52 cartas con reemplazo: cada robo empieza desde el mismo conjunto de rangos y palos.</p><ul><li>Rangos: A, 2, 3, ..., 10, J, Q, K.</li><li>Colores: corazones y diamantes son red; treboles y picas son black.</li><li>Palos y rangos son informacion visible, pero la validacion del resultado queda server-side.</li></ul>",
    },
    skip_semantics: {
      body_html:
        "<p>Skip cambia la carta abierta sin cambiar apuesta ni pago actual. Antes de la primera prediccion es libre; durante una ronda activa esta limitado.</p><p>El limite activo es 5 skips consecutivos: una prediccion correcta reinicia el contador y reabre la secuencia.</p>",
    },
    edge_rank_behavior: {
      body_html:
        "<p>A y K son cartas limite: para evitar opciones seguras, mayor/menor incluyen empate en el lado que seria imposible.</p><ul><li>Con A, Down cuenta A o menor; Up cuenta cartas por encima de A.</li><li>Con K, Up cuenta K o mayor; Down cuenta cartas por debajo de K.</li><li>Black y Red siempre mantienen probabilidad 50%.</li></ul>",
    },
  },
};

export type HiLoCopyResolver = (
  key: HiLoCopyKey,
  replacements?: Record<string, string>,
) => string;

export function createHiLoCopyResolver(
  locale: string | undefined,
  overrides?: Partial<Record<HiLoCopyKey, string>>,
): HiLoCopyResolver {
  const resolvedLocale = resolveHiLoLocale(locale);
  const defaults = HI_LO_COPY_DEFAULTS[resolvedLocale] ?? HI_LO_COPY_DEFAULTS.it;
  const fallbackDefaults = HI_LO_COPY_DEFAULTS.it;

  return (key, replacements = {}) => {
    const overrideValue = overrides?.[key];
    const rawValue = overrideValue?.trim()
      ? overrideValue
      : defaults[key] ?? fallbackDefaults[key] ?? key;
    return interpolateHiLoCopy(rawValue, replacements);
  };
}

export function resolveHiLoLocale(locale: string | undefined): HiLoLocale {
  const normalized = (locale ?? "it").slice(0, 2).toLowerCase();
  return HI_LO_SUPPORTED_LOCALES.includes(normalized as HiLoLocale)
    ? (normalized as HiLoLocale)
    : "it";
}

export function interpolateHiLoCopy(value: string, replacements: Record<string, string>) {
  return Object.entries(replacements).reduce(
    (text, [key, replacement]) => text.split(`{{${key}}}`).join(replacement),
    value,
  );
}
