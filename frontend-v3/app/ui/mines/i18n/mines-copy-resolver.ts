import type { MinesPresentationConfig } from "@/app/lib/types";
import { MINES_DEFAULT_COPY } from "./mines-copy-defaults";
import {
  MINES_ALLOWED_LOCALES,
  MINES_COPY_MANIFEST,
  MINES_DEFAULT_LOCALE,
  type MinesCopyKey,
  type MinesLocaleCode,
} from "./mines-copy-manifest";

export type MinesCopyParams = Record<string, string | number>;

export type MinesCopyResolver = {
  locale: MinesLocaleCode;
  t: (key: MinesCopyKey, params?: MinesCopyParams) => string;
};

const MODE_LABEL_COPY_KEY_MAP: Record<
  "demo" | "real",
  Partial<Record<MinesCopyKey, MinesCopyKey>>
> = {
  demo: {
    "actions.bet": "ui_labels.demo.bet",
    "actions.bet_loading": "ui_labels.demo.bet_loading",
    "actions.collect": "ui_labels.demo.collect",
    "actions.collect_loading": "ui_labels.demo.collect_loading",
    "actions.back_to_site_aria": "ui_labels.demo.home",
    "actions.game_info": "ui_labels.demo.game_info",
  },
  real: {
    "actions.bet": "ui_labels.real.bet",
    "actions.bet_loading": "ui_labels.real.bet_loading",
    "actions.collect": "ui_labels.real.collect",
    "actions.collect_loading": "ui_labels.real.collect_loading",
    "actions.back_to_site_aria": "ui_labels.real.home",
    "actions.game_info": "ui_labels.real.game_info",
  },
};

const LEGACY_LABEL_KEY_MAP: Partial<Record<MinesCopyKey, string>> = {
  "actions.bet": "bet",
  "actions.bet_loading": "bet_loading",
  "actions.collect": "collect",
  "actions.collect_loading": "collect_loading",
  "actions.back_to_site_aria": "home",
  "actions.game_info": "game_info",
};

export function createMinesCopyResolver(
  presentationConfig: MinesPresentationConfig | null | undefined,
  mode: "demo" | "real",
): MinesCopyResolver {
  const runtimeI18n = presentationConfig?.i18n;
  const locale = runtimeI18n
    ? normalizeLocale(runtimeI18n.published_locale ?? runtimeI18n.resolved_locale) ??
      MINES_DEFAULT_LOCALE
    : MINES_DEFAULT_LOCALE;
  const runtimeCopy = runtimeI18n?.copy ?? {};
  const legacyLabels = presentationConfig?.ui_labels?.[mode] ?? {};

  return {
    locale,
    t(key, params = {}) {
      const modeCopyKey = MODE_LABEL_COPY_KEY_MAP[mode][key];
      const legacyKey = LEGACY_LABEL_KEY_MAP[key];
      const template =
        (modeCopyKey ? resolveCopyCandidate(runtimeCopy[modeCopyKey], modeCopyKey) : undefined) ??
        resolveCopyCandidate(runtimeCopy[key], key) ??
        (legacyKey ? legacyLabels[legacyKey] : undefined) ??
        MINES_DEFAULT_COPY[locale]?.[key] ??
        MINES_DEFAULT_COPY[MINES_DEFAULT_LOCALE]?.[key] ??
        key;

      return interpolateMinesCopy(template, params);
    },
  };
}

function resolveCopyCandidate(
  value: string | undefined,
  key: MinesCopyKey,
): string | undefined {
  if (!value || !value.trim() || value === key) {
    return undefined;
  }
  return value;
}

export function validateDefaultMinesCopyCatalog(): string[] {
  const errors: string[] = [];

  for (const locale of MINES_ALLOWED_LOCALES) {
    const copy = MINES_DEFAULT_COPY[locale];
    for (const definition of MINES_COPY_MANIFEST) {
      const value = copy[definition.key];
      if (definition.required && !value.trim()) {
        errors.push(`${locale}.${definition.key} is required`);
      }
      if (definition.maxLength && value.length > definition.maxLength) {
        errors.push(`${locale}.${definition.key} exceeds ${definition.maxLength} characters`);
      }
      for (const placeholder of extractPlaceholders(value)) {
        if (!definition.placeholders?.includes(placeholder)) {
          errors.push(`${locale}.${definition.key} contains unknown placeholder ${placeholder}`);
        }
      }
    }
  }

  return errors;
}

function normalizeLocale(locale: string | undefined): MinesLocaleCode | null {
  return MINES_ALLOWED_LOCALES.includes(locale as MinesLocaleCode)
    ? (locale as MinesLocaleCode)
    : null;
}

function interpolateMinesCopy(template: string, params: MinesCopyParams): string {
  return template.replace(/\{\{([a-zA-Z0-9_]+)\}\}/g, (match, key: string) =>
    params[key] === undefined ? match : String(params[key]),
  );
}

function extractPlaceholders(value: string): string[] {
  return Array.from(value.matchAll(/\{\{([a-zA-Z0-9_]+)\}\}/g), (match) => match[1]);
}
