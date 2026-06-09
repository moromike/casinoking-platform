"use client";

import {
  MINES_ALLOWED_LOCALES,
  MINES_COPY_MANIFEST,
  MINES_RULE_SECTION_KEYS,
  type MinesCopyKey,
  type MinesLocaleCode,
  type MinesRuleSectionKey,
} from "@/app/ui/mines/i18n/mines-copy-manifest";

export type MinesPublishedLocale = MinesLocaleCode;

export const MINES_PUBLISHED_LOCALES: MinesPublishedLocale[] = [
  ...MINES_ALLOWED_LOCALES,
];

export const MINES_PUBLISHED_LOCALE_LABELS: Record<MinesPublishedLocale, string> = {
  it: "Italian",
  en: "English",
  de: "Deutsch",
  es: "Espanol",
};

export const MINES_IN_GAME_TITLE_KEY: MinesCopyKey = "game.title";

export const MINES_IN_GAME_TITLE_MAX_LENGTH =
  MINES_COPY_MANIFEST.find((definition) => definition.key === MINES_IN_GAME_TITLE_KEY)
    ?.maxLength ?? 80;

const MINES_GENERIC_COPY_FIELDS = MINES_COPY_MANIFEST.filter(
  (definition) => definition.key !== MINES_IN_GAME_TITLE_KEY,
);

const MINES_RULE_SECTION_FIELDS: Array<{
  key: MinesRuleSectionKey;
  label: string;
  helper: string;
}> = [
  {
    key: "ways_to_win",
    label: "Ways to win",
    helper: "Core explanation of safe picks, mines and loss condition.",
  },
  {
    key: "payout_display",
    label: "Payout display",
    helper: "Explain the ladder shown under the MINES title.",
  },
  {
    key: "settings_menu",
    label: "Settings menu",
    helper: "Explain how grid size and mine selections behave.",
  },
  {
    key: "bet_collect",
    label: "Bet & collect",
    helper: "Explain how Bet starts a hand and Collect closes a winning hand.",
  },
  {
    key: "balance_display",
    label: "Balance & display",
    helper: "Explain CHIP display, decimals and visible balance behaviour.",
  },
  {
    key: "general",
    label: "General",
    helper: "Server-authoritative statements and any shared gameplay constraints.",
  },
  {
    key: "history",
    label: "History",
    helper: "Explain where authenticated players can inspect completed hands.",
  },
];

type MinesPublishedLocalePanelProps = {
  activeLocale: MinesPublishedLocale;
  liveLocale: MinesPublishedLocale;
  activeInGameTitle: string;
  publishedInGameTitle: string;
  activeCopy: Record<MinesCopyKey, string>;
  publishedCopy: Record<MinesCopyKey, string>;
  activeRules: Record<MinesRuleSectionKey, { body_html: string }>;
  publishedRules: Record<MinesRuleSectionKey, { body_html: string }>;
  busyAction: string | null;
  onLocaleChange: (locale: MinesPublishedLocale) => void;
  onInGameTitleChange: (value: string) => void;
};

export function MinesPublishedLocalePanel({
  activeLocale,
  liveLocale,
  activeInGameTitle,
  publishedInGameTitle,
  activeCopy,
  publishedCopy,
  activeRules,
  publishedRules,
  busyAction,
  onLocaleChange,
  onInGameTitleChange,
}: MinesPublishedLocalePanelProps) {
  const requiredCopyDefinitions = MINES_COPY_MANIFEST.filter(
    (definition) => definition.required,
  );
  const missingCopyKeys = requiredCopyDefinitions
    .filter((definition) => !activeCopy[definition.key]?.trim())
    .map((definition) => definition.key);
  const tooLongCopyKeys = requiredCopyDefinitions
    .filter((definition) => {
      const value = activeCopy[definition.key] ?? "";
      return typeof definition.maxLength === "number" && value.length > definition.maxLength;
    })
    .map((definition) => definition.key);
  const missingRuleKeys = MINES_RULE_SECTION_KEYS.filter(
    (key) => !activeRules[key]?.body_html?.trim(),
  );
  const changedCopyKeys = MINES_COPY_MANIFEST.filter(
    (definition) =>
      (activeCopy[definition.key] ?? "") !== (publishedCopy[definition.key] ?? ""),
  ).map((definition) => definition.key);
  const changedRuleKeys = MINES_RULE_SECTION_KEYS.filter(
    (key) =>
      (activeRules[key]?.body_html ?? "") !== (publishedRules[key]?.body_html ?? ""),
  );
  const requiredTotal = requiredCopyDefinitions.length + MINES_RULE_SECTION_KEYS.length;
  const invalidKeyCount =
    new Set([...missingCopyKeys, ...tooLongCopyKeys]).size + missingRuleKeys.length;
  const validRequiredCount = Math.max(0, requiredTotal - invalidKeyCount);
  const changedTotal = changedCopyKeys.length + changedRuleKeys.length;

  return (
    <article className="admin-card">
      <h3>Published language</h3>
      <p className="helper">
        The player receives this language only. There is no language switch inside the game.
      </p>
      <div className="field">
        <label htmlFor="mines-published-locale">Mines runtime language</label>
        <select
          id="mines-published-locale"
          value={activeLocale}
          disabled={busyAction !== null}
          onChange={(event) =>
            onLocaleChange(event.target.value as MinesPublishedLocale)
          }
        >
          {MINES_PUBLISHED_LOCALES.map((locale) => (
            <option key={locale} value={locale}>
              {MINES_PUBLISHED_LOCALE_LABELS[locale]}
            </option>
          ))}
        </select>
      </div>
      <div className="admin-metric-row">
        <span className="list-muted">Live</span>
        <span>{MINES_PUBLISHED_LOCALE_LABELS[liveLocale]}</span>
      </div>
      <div className="admin-metric-row">
        <span className="list-muted">Draft</span>
        <span>{MINES_PUBLISHED_LOCALE_LABELS[activeLocale]}</span>
      </div>
      <div className="field mines-in-game-title-field">
        <label htmlFor="mines-in-game-title">In-game title</label>
        <input
          id="mines-in-game-title"
          value={activeInGameTitle}
          maxLength={MINES_IN_GAME_TITLE_MAX_LENGTH}
          disabled={busyAction !== null}
          onChange={(event) => onInGameTitleChange(event.target.value)}
        />
        <span className="games-create-helper">
          Max {MINES_IN_GAME_TITLE_MAX_LENGTH} characters.
        </span>
      </div>
      <div className="admin-metric-row">
        <span className="list-muted">Live title</span>
        <span>{publishedInGameTitle}</span>
      </div>
      <div className="mines-i18n-summary">
        <div className="admin-metric-row">
          <span className="list-muted">Draft coverage</span>
          <span>
            {validRequiredCount}/{requiredTotal} required
          </span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Draft/live diff</span>
          <span>{changedTotal} changed fields</span>
        </div>
        <div className="admin-summary-strip">
          <span className={missingCopyKeys.length ? "meta-pill warning" : "meta-pill"}>
            Missing copy: {missingCopyKeys.length}
          </span>
          <span className={tooLongCopyKeys.length ? "meta-pill warning" : "meta-pill"}>
            Copy too long: {tooLongCopyKeys.length}
          </span>
          <span className={missingRuleKeys.length ? "meta-pill warning" : "meta-pill"}>
            Missing rules: {missingRuleKeys.length}
          </span>
        </div>
        {missingCopyKeys.length || tooLongCopyKeys.length || missingRuleKeys.length ? (
          <p className="helper">
            Fix before publishing:{" "}
            {[...missingCopyKeys, ...tooLongCopyKeys, ...missingRuleKeys].slice(0, 8).join(", ")}
            {[...missingCopyKeys, ...tooLongCopyKeys, ...missingRuleKeys].length > 8
              ? "..."
              : ""}
          </p>
        ) : (
          <p className="helper">Complete i18n coverage for the draft language.</p>
        )}
      </div>
    </article>
  );
}

type MinesCopyEditorProps = {
  locale: MinesPublishedLocale;
  copy: Record<MinesCopyKey, string>;
  onChange: (key: MinesCopyKey, value: string) => void;
};

export function MinesCopyEditor({
  locale,
  copy,
  onChange,
}: MinesCopyEditorProps) {
  return (
    <div className="rules-editor-panel">
      <div className="rules-editor-toolbar">
        <div>
          <h3>Copy player Mines</h3>
          <p className="helper">
            Draft language: {MINES_PUBLISHED_LOCALE_LABELS[locale]}. These
            strings feed the game; the player cannot change them.
          </p>
        </div>
      </div>
      {MINES_GENERIC_COPY_FIELDS.map((definition) => {
        const inputId = `mines-copy-${definition.key.replace(/[^a-z0-9]+/gi, "-")}`;
        const value = copy[definition.key] ?? "";
        const isLongText = (definition.maxLength ?? 0) > 80 || value.length > 80;
        return (
          <article className="rules-editor-row" key={definition.key}>
            <div className="rules-editor-copy">
              <div className="list-row">
                <h3>{definition.key}</h3>
                <span className="meta-pill">
                  {definition.required ? "required" : "optional"}
                </span>
              </div>
              <p className="helper">
                Max {definition.maxLength ?? "n/a"}
                {definition.placeholders?.length
                  ? ` - Placeholder: ${definition.placeholders.join(", ")}`
                  : ""}
              </p>
            </div>
            {isLongText ? (
              <textarea
                id={inputId}
                className="admin-textarea"
                value={value}
                onChange={(event) => onChange(definition.key, event.target.value)}
                spellCheck={false}
              />
            ) : (
              <input
                id={inputId}
                value={value}
                onChange={(event) => onChange(definition.key, event.target.value)}
              />
            )}
          </article>
        );
      })}
    </div>
  );
}

type MinesRulesHtmlEditorProps = {
  rules: Record<MinesRuleSectionKey, { body_html: string }>;
  onChange: (key: MinesRuleSectionKey, value: string) => void;
};

export function MinesRulesHtmlEditor({
  rules,
  onChange,
}: MinesRulesHtmlEditorProps) {
  return (
    <div className="rules-editor-panel">
      <div className="rules-editor-toolbar">
        <h3>Rules HTML editor</h3>
      </div>
      {MINES_RULE_SECTION_FIELDS.map((section) => (
        <article className="rules-editor-row" key={section.key}>
          <div className="rules-editor-copy">
            <div className="list-row">
              <h3>{section.label}</h3>
              <span className="meta-pill">{section.key}</span>
            </div>
            <p className="helper">{section.helper}</p>
          </div>
          <textarea
            className="admin-textarea"
            value={rules[section.key]?.body_html ?? ""}
            onChange={(event) => onChange(section.key, event.target.value)}
            spellCheck={false}
          />
        </article>
      ))}
    </div>
  );
}
