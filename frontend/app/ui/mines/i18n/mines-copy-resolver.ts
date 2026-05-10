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

const LEGACY_LABEL_KEY_MAP: Partial<Record<MinesCopyKey, string>> = {
  "actions.bet": "bet",
  "actions.bet_loading": "bet_loading",
  "actions.collect": "collect",
  "actions.collect_loading": "collect_loading",
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
      const legacyKey = LEGACY_LABEL_KEY_MAP[key];
      const template =
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
