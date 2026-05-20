"use client";

export const BOXE_SUPPORTED_LOCALES = ["it", "en", "de", "es"] as const;
export type BoxeLocale = (typeof BOXE_SUPPORTED_LOCALES)[number];

export type BoxeCopyKey =
  | "actions.bet"
  | "actions.collect"
  | "actions.collect_with_amount"
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
  | "states.choose_safe"
  | "states.pick_next";

const BOXE_COPY_DEFAULTS: Record<BoxeLocale, Record<BoxeCopyKey, string>> = {
  it: {
    "actions.bet": "Punta",
    "actions.collect": "Incassa",
    "actions.collect_with_amount": "Incassa {{amount}} CHIP",
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
    "states.choose_safe": "Scegli una box sicura",
    "states.pick_next": "Sali alla prossima riga",
  },
  en: {
    "actions.bet": "Bet",
    "actions.collect": "Collect",
    "actions.collect_with_amount": "Collect {{amount}} CHIP",
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
    "states.choose_safe": "Choose a safe box",
    "states.pick_next": "Move to the next row",
  },
  de: {
    "actions.bet": "SETZEN",
    "actions.collect": "AUSZAHLEN",
    "actions.collect_with_amount": "{{amount}} CHIP AUSZAHLEN",
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
    "states.choose_safe": "Waehle eine sichere Box",
    "states.pick_next": "Weiter zur naechsten Reihe",
  },
  es: {
    "actions.bet": "APOSTAR",
    "actions.collect": "COBRAR",
    "actions.collect_with_amount": "COBRAR {{amount}} CHIP",
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
    "states.choose_safe": "Elige una caja segura",
    "states.pick_next": "Sube a la siguiente fila",
  },
};

export function resolveBoxeLocale(language: string | undefined): BoxeLocale {
  const normalized = (language ?? "it").slice(0, 2).toLowerCase();
  return BOXE_SUPPORTED_LOCALES.includes(normalized as BoxeLocale)
    ? (normalized as BoxeLocale)
    : "it";
}

export function createBoxeCopyResolver(locale: BoxeLocale) {
  const copyCatalog = BOXE_COPY_DEFAULTS[locale] ?? BOXE_COPY_DEFAULTS.it;
  return (key: BoxeCopyKey, placeholders: Record<string, string> = {}) => {
    let value = copyCatalog[key] ?? BOXE_COPY_DEFAULTS.it[key] ?? key;
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
