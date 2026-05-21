"use client";

export const BOXE_SUPPORTED_LOCALES = ["it", "en", "de", "es"] as const;
export type BoxeLocale = (typeof BOXE_SUPPORTED_LOCALES)[number];

export type BoxeCopyKey =
  | "actions.bet"
  | "actions.bet_loading"
  | "actions.collect"
  | "actions.collect_loading"
  | "actions.collect_with_amount"
  | "actions.back_to_site_aria"
  | "actions.fullscreen"
  | "actions.game_info"
  | "actions.retry"
  | "actions.reset"
  | "balance.insufficient"
  | "balance.label"
  | "balance.demo"
  | "failure.generic"
  | "failure.network"
  | "failure.round_closed"
  | "round.lost"
  | "round.top_row_win"
  | "round.won_amount"
  | "settings.bet_amount"
  | "settings.difficulty"
  | "settings.rows"
  | "rules.bet_collect"
  | "rules.bet_collect_heading"
  | "rules.balance_display"
  | "rules.close_aria"
  | "rules.dialog_aria"
  | "rules.general"
  | "rules.header_title"
  | "rules.history"
  | "rules.intro"
  | "rules.payout_display"
  | "rules.replay_loading"
  | "rules.replay_tab"
  | "rules.replay_unavailable"
  | "rules.rules_tab"
  | "rules.settings_menu"
  | "rules.ways_to_win"
  | "states.choose_safe"
  | "states.pick_next";

export const BOXE_RULE_SECTION_KEYS = [
  "ways_to_win",
  "payout_display",
  "settings_menu",
  "bet_collect",
  "balance_display",
  "general",
  "history",
] as const;

export type BoxeRuleSectionKey = (typeof BOXE_RULE_SECTION_KEYS)[number];

export type BoxeRuleSectionContent = {
  body_html: string;
};

const BOXE_COPY_DEFAULTS: Record<BoxeLocale, Record<BoxeCopyKey, string>> = {
  it: {
    "actions.bet": "Punta",
    "actions.bet_loading": "Punto...",
    "actions.collect": "Incassa",
    "actions.collect_loading": "Incasso...",
    "actions.collect_with_amount": "Incassa {{amount}} CHIP",
    "actions.back_to_site_aria": "Torna al sito",
    "actions.fullscreen": "Fullscreen",
    "actions.game_info": "Info gioco",
    "actions.retry": "Riprova",
    "actions.reset": "Nuova mano",
    "balance.insufficient": "Saldo insufficiente",
    "balance.label": "Saldo",
    "balance.demo": "Saldo demo",
    "failure.generic": "Azione non completata.",
    "failure.network": "Connessione instabile. Riprova la stessa azione.",
    "failure.round_closed": "La mano e' gia' conclusa.",
    "round.lost": "Game over. Hai scelto una mina.",
    "round.top_row_win": "Top row completata. Vincita automatica {{amount}} CHIP.",
    "round.won_amount": "Hai incassato {{amount}} CHIP.",
    "settings.bet_amount": "Puntata",
    "settings.difficulty": "Difficolta",
    "settings.rows": "Righe",
    "rules.bet_collect": "Punta, scegli una casella per riga e incassa dopo una scelta sicura.",
    "rules.bet_collect_heading": "Punta e incassa",
    "rules.balance_display": "Saldo e reveal finale",
    "rules.close_aria": "Chiudi info gioco",
    "rules.dialog_aria": "Info gioco {{gameTitle}}",
    "rules.general": "Fairness e RTP",
    "rules.header_title": "INFO GIOCO - {{gameTitle}}",
    "rules.history": "Storico e replay",
    "rules.intro": "Regole leggibili dal tavolo e focalizzate sul gioco reale.",
    "rules.payout_display": "Moltiplicatori e payout",
    "rules.replay_loading": "Caricamento replay...",
    "rules.replay_tab": "REPLAY",
    "rules.replay_unavailable": "Replay non ancora disponibile.",
    "rules.rules_tab": "REGOLE",
    "rules.settings_menu": "Righe e difficolta",
    "rules.ways_to_win": "Come vincere",
    "states.choose_safe": "Scegli una box sicura",
    "states.pick_next": "Sali alla prossima riga",
  },
  en: {
    "actions.bet": "Bet",
    "actions.bet_loading": "Betting...",
    "actions.collect": "Collect",
    "actions.collect_loading": "Collecting...",
    "actions.collect_with_amount": "Collect {{amount}} CHIP",
    "actions.back_to_site_aria": "Back to site",
    "actions.fullscreen": "Fullscreen",
    "actions.game_info": "Game info",
    "actions.retry": "Retry",
    "actions.reset": "New round",
    "balance.insufficient": "Insufficient balance",
    "balance.label": "Balance",
    "balance.demo": "Demo balance",
    "failure.generic": "Action was not completed.",
    "failure.network": "Connection is unstable. Retry the same action.",
    "failure.round_closed": "The round is already closed.",
    "round.lost": "Game over. You picked a mine.",
    "round.top_row_win": "Top row cleared. Auto win {{amount}} CHIP.",
    "round.won_amount": "You collected {{amount}} CHIP.",
    "settings.bet_amount": "Bet amount",
    "settings.difficulty": "Difficulty",
    "settings.rows": "Rows",
    "rules.bet_collect": "Bet, pick one box per row, and collect after a safe pick.",
    "rules.bet_collect_heading": "Bet and collect",
    "rules.balance_display": "Balance and final reveal",
    "rules.close_aria": "Close game info",
    "rules.dialog_aria": "Game info {{gameTitle}}",
    "rules.general": "Fairness and RTP",
    "rules.header_title": "GAME INFO - {{gameTitle}}",
    "rules.history": "History and replay",
    "rules.intro": "Table-readable rules focused on real gameplay.",
    "rules.payout_display": "Multipliers and payout",
    "rules.replay_loading": "Loading replay...",
    "rules.replay_tab": "REPLAY",
    "rules.replay_unavailable": "Replay not available yet.",
    "rules.rules_tab": "RULES",
    "rules.settings_menu": "Rows and difficulty",
    "rules.ways_to_win": "Ways to win",
    "states.choose_safe": "Choose a safe box",
    "states.pick_next": "Move to the next row",
  },
  de: {
    "actions.bet": "SETZEN",
    "actions.bet_loading": "Setze...",
    "actions.collect": "AUSZAHLEN",
    "actions.collect_loading": "Zahle aus...",
    "actions.collect_with_amount": "{{amount}} CHIP AUSZAHLEN",
    "actions.back_to_site_aria": "Zurueck zur Seite",
    "actions.fullscreen": "Fullscreen",
    "actions.game_info": "Spielinfo",
    "actions.retry": "Erneut versuchen",
    "actions.reset": "Neue Runde",
    "balance.insufficient": "Guthaben reicht nicht aus",
    "balance.label": "Guthaben",
    "balance.demo": "Demo-Guthaben",
    "failure.generic": "Aktion nicht abgeschlossen.",
    "failure.network": "Verbindung instabil. Wiederhole dieselbe Aktion.",
    "failure.round_closed": "Die Runde ist bereits beendet.",
    "round.lost": "Game over. Du hast eine Mine gewaehlt.",
    "round.top_row_win": "Oberste Reihe geschafft. Automatischer Gewinn {{amount}} CHIP.",
    "round.won_amount": "Du hast {{amount}} CHIP ausgezahlt.",
    "settings.bet_amount": "Einsatz",
    "settings.difficulty": "Schwierigkeit",
    "settings.rows": "Reihen",
    "rules.bet_collect": "Setze, waehle ein Feld pro Reihe und zahle nach einem sicheren Treffer aus.",
    "rules.bet_collect_heading": "Setzen und auszahlen",
    "rules.balance_display": "Guthaben und finale Aufdeckung",
    "rules.close_aria": "Spielinfo schliessen",
    "rules.dialog_aria": "Spielinfo {{gameTitle}}",
    "rules.general": "Fairness und RTP",
    "rules.header_title": "SPIELINFO - {{gameTitle}}",
    "rules.history": "Historie und Replay",
    "rules.intro": "Regeln direkt am Tisch, fokussiert auf das reale Spiel.",
    "rules.payout_display": "Multiplikatoren und Auszahlung",
    "rules.replay_loading": "Replay wird geladen...",
    "rules.replay_tab": "REPLAY",
    "rules.replay_unavailable": "Replay noch nicht verfuegbar.",
    "rules.rules_tab": "REGELN",
    "rules.settings_menu": "Reihen und Schwierigkeit",
    "rules.ways_to_win": "So gewinnst du",
    "states.choose_safe": "Waehle eine sichere Box",
    "states.pick_next": "Weiter zur naechsten Reihe",
  },
  es: {
    "actions.bet": "APOSTAR",
    "actions.bet_loading": "Apostando...",
    "actions.collect": "COBRAR",
    "actions.collect_loading": "Cobrando...",
    "actions.collect_with_amount": "COBRAR {{amount}} CHIP",
    "actions.back_to_site_aria": "Volver al sitio",
    "actions.fullscreen": "Fullscreen",
    "actions.game_info": "Info juego",
    "actions.retry": "Reintentar",
    "actions.reset": "Nueva ronda",
    "balance.insufficient": "Saldo insuficiente",
    "balance.label": "Saldo",
    "balance.demo": "Saldo demo",
    "failure.generic": "La accion no se completo.",
    "failure.network": "Conexion inestable. Reintenta la misma accion.",
    "failure.round_closed": "La ronda ya esta cerrada.",
    "round.lost": "Game over. Elegiste una mina.",
    "round.top_row_win": "Fila superior completada. Premio automatico {{amount}} CHIP.",
    "round.won_amount": "Cobraste {{amount}} CHIP.",
    "settings.bet_amount": "Apuesta",
    "settings.difficulty": "Dificultad",
    "settings.rows": "Filas",
    "rules.bet_collect": "Apuesta, elige una caja por fila y cobra tras una eleccion segura.",
    "rules.bet_collect_heading": "Apostar y cobrar",
    "rules.balance_display": "Saldo y revelado final",
    "rules.close_aria": "Cerrar info del juego",
    "rules.dialog_aria": "Info del juego {{gameTitle}}",
    "rules.general": "Fairness y RTP",
    "rules.header_title": "INFO DEL JUEGO - {{gameTitle}}",
    "rules.history": "Historial y replay",
    "rules.intro": "Reglas legibles desde la mesa y centradas en el juego real.",
    "rules.payout_display": "Multiplicadores y pago",
    "rules.replay_loading": "Cargando replay...",
    "rules.replay_tab": "REPLAY",
    "rules.replay_unavailable": "Replay aun no disponible.",
    "rules.rules_tab": "REGLAS",
    "rules.settings_menu": "Filas y dificultad",
    "rules.ways_to_win": "Como ganar",
    "states.choose_safe": "Elige una caja segura",
    "states.pick_next": "Sube a la siguiente fila",
  },
};

export const BOXE_DEFAULT_RULE_SECTIONS: Record<
  BoxeLocale,
  Record<BoxeRuleSectionKey, BoxeRuleSectionContent>
> = {
  it: {
    ways_to_win: {
      body_html:
        "<p>BOXE si gioca su una piramide dal basso verso l'alto. Dopo la puntata scegli una sola box nella riga attiva: se e' sicura sali alla riga successiva, se contiene una mina la mano termina in perdita.</p>",
    },
    payout_display: {
      body_html:
        "<p>La scala dei moltiplicatori mostra il percorso della configurazione righe x difficolta. Dopo ogni scelta sicura il moltiplicatore corrente e' il valore incassabile; completare la riga piu' alta incassa automaticamente il valore massimo.</p>",
    },
    settings_menu: {
      body_html:
        "<p>Le righe disponibili vanno da 4 a 8. EASY usa meno rischio e moltiplicatori piu' bassi, MEDIUM e' intermedia, HARD aumenta rischio e potenziale. Durante una mano attiva righe e difficolta restano bloccate.</p>",
    },
    bet_collect: {
      body_html:
        "<p>Punta avvia una nuova mano. Incassa e' disponibile dopo una scelta sicura con moltiplicatore maggiore di 1. Il payout e' puntata iniziale per moltiplicatore corrente ed e' calcolato solo dal backend.</p>",
    },
    balance_display: {
      body_html:
        "<p>Saldo, puntata e vincita sono mostrati in CHIP. Su perdita, cashout o top-row win la risposta terminale include la rivelazione completa della piramide.</p>",
    },
    general: {
      body_html:
        "<p>BOXE e' server-authoritative: seed, esito, full reveal, payout e stato finale arrivano dal server. Il frontend mostra la piramide e non decide mai risultato o matematica. Il target RTP e' 98% sulle configurazioni supportate.</p>",
    },
    history: {
      body_html:
        "<p>Le mani concluse possono essere riviste nello storico/replay con server seed hash, client seed e verifica outcome. Il replay consuma la stessa full pyramid reveal server-authoritative del round terminale.</p>",
    },
  },
  en: {
    ways_to_win: {
      body_html:
        "<p>BOXE is played on a bottom-to-top pyramid. After betting, pick exactly one box in the active row: a safe box moves you upward, while a mine ends the hand in loss.</p>",
    },
    payout_display: {
      body_html:
        "<p>The multiplier ladder shows the path for the selected rows x difficulty setup. After each safe pick, the current multiplier is the collectible value; clearing the top row automatically collects the maximum value.</p>",
    },
    settings_menu: {
      body_html:
        "<p>Available row counts are 4 to 8. EASY uses lower risk and lower multipliers, MEDIUM is balanced, and HARD raises both risk and potential. Rows and difficulty are locked during an active hand.</p>",
    },
    bet_collect: {
      body_html:
        "<p>Bet starts a new hand. Collect is available after a safe pick with multiplier greater than 1. Payout equals initial bet times current multiplier and is calculated only by the backend.</p>",
    },
    balance_display: {
      body_html:
        "<p>Balance, bet and win are shown in CHIP. On loss, cashout or top-row win, the terminal response includes the full pyramid reveal.</p>",
    },
    general: {
      body_html:
        "<p>BOXE is server-authoritative: seed, outcome, full reveal, payout and final status come from the server. The frontend displays the pyramid and never decides outcome or math. The target RTP is 98% across supported configurations.</p>",
    },
    history: {
      body_html:
        "<p>Completed hands can be reviewed in history/replay with server seed hash, client seed and outcome verification. Replay consumes the same server-authoritative full pyramid reveal as the terminal round.</p>",
    },
  },
  de: {
    ways_to_win: {
      body_html:
        "<p>BOXE wird auf einer Pyramide von unten nach oben gespielt. Nach dem Einsatz waehlt man genau eine Box in der aktiven Reihe: eine sichere Box fuehrt nach oben, eine Mine beendet die Runde als Verlust.</p>",
    },
    payout_display: {
      body_html:
        "<p>Die Multiplikator-Leiste zeigt den Pfad fuer die gewaehlten Reihen x Schwierigkeit. Nach jeder sicheren Wahl ist der aktuelle Multiplikator der auszahlbare Wert; die oberste Reihe zahlt automatisch den Maximalwert aus.</p>",
    },
    settings_menu: {
      body_html:
        "<p>Verfuegbar sind 4 bis 8 Reihen. EASY nutzt weniger Risiko und niedrigere Multiplikatoren, MEDIUM ist ausgeglichen, HARD erhoeht Risiko und Potenzial. Reihen und Schwierigkeit sind waehrend einer aktiven Runde gesperrt.</p>",
    },
    bet_collect: {
      body_html:
        "<p>Setzen startet eine neue Runde. Auszahlen ist nach einer sicheren Wahl mit Multiplikator groesser als 1 verfuegbar. Die Auszahlung ist Einsatz mal aktueller Multiplikator und wird nur vom Backend berechnet.</p>",
    },
    balance_display: {
      body_html:
        "<p>Guthaben, Einsatz und Gewinn werden in CHIP angezeigt. Bei Verlust, Cashout oder Gewinn in der obersten Reihe enthaelt die finale Antwort die komplette Pyramiden-Aufdeckung.</p>",
    },
    general: {
      body_html:
        "<p>BOXE ist server-authoritative: Seed, Ergebnis, Full Reveal, Auszahlung und finaler Status kommen vom Server. Das Frontend zeigt die Pyramide und entscheidet nie Ergebnis oder Mathematik. Der Ziel-RTP ist 98% fuer alle unterstuetzten Konfigurationen.</p>",
    },
    history: {
      body_html:
        "<p>Abgeschlossene Runden koennen in Historie/Replay mit Server-Seed-Hash, Client Seed und Outcome-Verifikation geprueft werden. Replay nutzt dieselbe server-authoritative Full Pyramid Reveal wie die terminale Runde.</p>",
    },
  },
  es: {
    ways_to_win: {
      body_html:
        "<p>BOXE se juega en una piramide de abajo hacia arriba. Tras apostar, eliges exactamente una caja en la fila activa: una caja segura te hace subir, una mina termina la mano en perdida.</p>",
    },
    payout_display: {
      body_html:
        "<p>La escala de multiplicadores muestra el recorrido para la configuracion filas x dificultad. Tras cada eleccion segura, el multiplicador actual es el valor cobrable; completar la fila superior cobra automaticamente el valor maximo.</p>",
    },
    settings_menu: {
      body_html:
        "<p>Las filas disponibles van de 4 a 8. EASY usa menos riesgo y multiplicadores mas bajos, MEDIUM es intermedia, HARD aumenta riesgo y potencial. Filas y dificultad quedan bloqueadas durante una mano activa.</p>",
    },
    bet_collect: {
      body_html:
        "<p>Apostar inicia una nueva mano. Cobrar esta disponible tras una eleccion segura con multiplicador mayor que 1. El pago es apuesta inicial por multiplicador actual y lo calcula solo el backend.</p>",
    },
    balance_display: {
      body_html:
        "<p>Saldo, apuesta y ganancia se muestran en CHIP. En perdida, cashout o premio de fila superior, la respuesta terminal incluye la revelacion completa de la piramide.</p>",
    },
    general: {
      body_html:
        "<p>BOXE es server-authoritative: seed, resultado, full reveal, pago y estado final vienen del servidor. El frontend muestra la piramide y nunca decide resultado ni matematica. El RTP objetivo es 98% en las configuraciones admitidas.</p>",
    },
    history: {
      body_html:
        "<p>Las manos completadas se pueden revisar en historial/replay con server seed hash, client seed y verificacion de resultado. El replay consume la misma full pyramid reveal server-authoritative de la ronda terminal.</p>",
    },
  },
};

export type BoxeRuntimeCopyCatalog = Partial<Record<string, Record<string, string>>>;
export type BoxeCopyResolver = (
  key: BoxeCopyKey,
  placeholders?: Record<string, string>,
) => string;

export function resolveBoxeLocale(language: string | undefined): BoxeLocale {
  const normalized = (language ?? "it").slice(0, 2).toLowerCase();
  return BOXE_SUPPORTED_LOCALES.includes(normalized as BoxeLocale)
    ? (normalized as BoxeLocale)
    : "it";
}

export function createBoxeCopyResolver(
  locale: BoxeLocale,
  runtimeCopy?: BoxeRuntimeCopyCatalog,
): BoxeCopyResolver {
  const copyCatalog = BOXE_COPY_DEFAULTS[locale] ?? BOXE_COPY_DEFAULTS.it;
  const runtimeCatalog = runtimeCopy?.[locale] ?? runtimeCopy?.it;
  return (key: BoxeCopyKey, placeholders: Record<string, string> = {}) => {
    let value = runtimeCatalog?.[key] ?? copyCatalog[key] ?? BOXE_COPY_DEFAULTS.it[key] ?? key;
    for (const [placeholder, replacement] of Object.entries(placeholders)) {
      value = value.split(`{{${placeholder}}}`).join(replacement);
    }
    return value;
  };
}

export function validateBoxeCopyDefaults(): string[] {
  const keys = Object.keys(BOXE_COPY_DEFAULTS.it) as BoxeCopyKey[];
  const errors: string[] = [];
  for (const locale of BOXE_SUPPORTED_LOCALES) {
    for (const key of keys) {
      if (!BOXE_COPY_DEFAULTS[locale][key]) {
        errors.push(`${locale}.${key}`);
      }
    }
  }
  return errors;
}
