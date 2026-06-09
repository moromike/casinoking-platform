"use client";

import {
  BOXE_COPY_DEFINITIONS,
  BOXE_RULE_SECTION_DEFINITIONS,
  BOXE_RULE_SECTION_KEYS,
  BOXE_SUPPORTED_LOCALES,
  type BoxeCopyKey,
  type BoxeLocale,
  type BoxeRuleSectionKey,
} from "@/app/ui/boxe/boxe-i18n/boxe-copy-defaults";
import type { BoxeRuntimeConfig } from "@/app/ui/boxe/use-boxe-runtime";
import { TitleEditorOverviewTab } from "@/app/ui/title-editor/tabs";

type BoxeDifficulty = "easy" | "medium" | "hard";

type BoxeAdminPayload = {
  rows_enabled: number[];
  default_rows: number;
  difficulty_enabled: BoxeDifficulty[];
  default_difficulty: BoxeDifficulty;
  default_locale: BoxeLocale;
  copy: Record<BoxeLocale, Record<BoxeCopyKey, string>>;
  rules_html: Record<BoxeLocale, Record<BoxeRuleSectionKey, string>>;
};

type BoxeAdminState = {
  published: BoxeAdminPayload;
  draft: BoxeAdminPayload;
  has_unpublished_changes: boolean;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_updated_by_admin_user_id?: string | null;
  published_at?: string | null;
};

type BoxeConfigOverviewProps = {
  activePayload: BoxeAdminPayload;
  adminState: BoxeAdminState | null;
  busyAction: string | null;
  runtimeConfig: BoxeRuntimeConfig | null;
  onDefaultLocaleChange: (locale: BoxeLocale) => void;
  onInGameTitleChange: (value: string) => void;
};

const BOXE_LOCALE_LABELS: Record<BoxeLocale, string> = {
  it: "Italian",
  en: "English",
  de: "Deutsch",
  es: "Espanol",
};

const BOXE_COPY_TOTAL = BOXE_COPY_DEFINITIONS.length;
const BOXE_RULE_TOTAL = BOXE_RULE_SECTION_KEYS.length;
const BOXE_IN_GAME_TITLE_KEY: BoxeCopyKey = "game.title";
const BOXE_IN_GAME_TITLE_MAX_LENGTH =
  BOXE_COPY_DEFINITIONS.find((definition) => definition.key === BOXE_IN_GAME_TITLE_KEY)
    ?.maxLength ?? 80;

export function BoxeConfigOverview({
  activePayload,
  adminState,
  busyAction,
  runtimeConfig,
  onDefaultLocaleChange,
  onInGameTitleChange,
}: BoxeConfigOverviewProps) {
  const publishedPayload = adminState?.published ?? null;
  const runtimeLocale = normalizeBoxeLocale(
    runtimeConfig?.presentation_config?.default_locale ?? activePayload.default_locale,
  );
  const defaultLocale = activePayload.default_locale;
  const activeLocaleSummary = readLocaleCoverage(activePayload, defaultLocale);
  const perLocaleCoverage = BOXE_SUPPORTED_LOCALES.map((locale) => ({
    locale,
    draft: readLocaleCoverage(activePayload, locale),
    live: publishedPayload ? readLocaleCoverage(publishedPayload, locale) : null,
  }));
  const draftRuntimeTitle =
    activePayload.copy[activePayload.default_locale]?.[BOXE_IN_GAME_TITLE_KEY] ??
    activePayload.copy.it?.[BOXE_IN_GAME_TITLE_KEY] ??
    "BOXE";
  const liveTitle =
    publishedPayload?.copy[publishedPayload.default_locale]?.[BOXE_IN_GAME_TITLE_KEY] ??
    publishedPayload?.copy.it?.[BOXE_IN_GAME_TITLE_KEY] ??
    "defaults";
  const changedFields = publishedPayload
    ? countChangedFields(activePayload, publishedPayload)
    : 0;

  return (
    <>
      <article className="admin-card">
        <h3>BOXE overview</h3>
        <p className="helper">
          Published locale, rules coverage, fairness notes and rows/difficulty
          diagnostics for this BOXE Title.
        </p>
      </article>
      <article className="admin-card" data-testid="boxe-overview-locale-panel">
        <h3>Published language</h3>
        <p className="helper">
          BOXE keeps one default runtime locale while maintaining full copy and
          rules coverage for every supported locale.
        </p>
        <div className="field">
          <label htmlFor="boxe-published-locale">BOXE runtime language</label>
          <select
            id="boxe-published-locale"
            value={activePayload.default_locale}
            disabled={busyAction !== null}
            onChange={(event) =>
              onDefaultLocaleChange(event.target.value as BoxeLocale)
            }
          >
            {BOXE_SUPPORTED_LOCALES.map((locale) => (
              <option key={locale} value={locale}>
                {BOXE_LOCALE_LABELS[locale]}
              </option>
            ))}
          </select>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Live</span>
          <span>
            {publishedPayload
              ? BOXE_LOCALE_LABELS[publishedPayload.default_locale]
              : "default runtime"}
          </span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Draft</span>
          <span>{BOXE_LOCALE_LABELS[activePayload.default_locale]}</span>
        </div>
        <div className="field mines-in-game-title-field">
          <label htmlFor="boxe-in-game-title">In-game title</label>
          <input
            id="boxe-in-game-title"
            value={draftRuntimeTitle}
            maxLength={BOXE_IN_GAME_TITLE_MAX_LENGTH}
            disabled={busyAction !== null}
            onChange={(event) => onInGameTitleChange(event.target.value)}
          />
          <span className="games-create-helper">
            Max {BOXE_IN_GAME_TITLE_MAX_LENGTH} characters.
          </span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Live title</span>
          <span>{liveTitle}</span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Runtime default</span>
          <span>{BOXE_LOCALE_LABELS[runtimeLocale]}</span>
        </div>
        <div className="admin-summary-strip">
          <span className={activeLocaleSummary.missingCopy ? "meta-pill warning" : "meta-pill"}>
            Copy {activeLocaleSummary.validCopy}/{BOXE_COPY_TOTAL}
          </span>
          <span className={activeLocaleSummary.tooLongCopy ? "meta-pill warning" : "meta-pill"}>
            Too long {activeLocaleSummary.tooLongCopy}
          </span>
          <span className={activeLocaleSummary.missingRules ? "meta-pill warning" : "meta-pill"}>
            Rules {activeLocaleSummary.validRules}/{BOXE_RULE_TOTAL}
          </span>
          <span className={changedFields ? "meta-pill warning" : "meta-pill"}>
            Draft/live diff {changedFields}
          </span>
        </div>
      </article>

      <TitleEditorOverviewTab
        className="admin-grid admin-grid-three"
        sections={[
          {
            id: "boxe-rules-coverage",
            title: "Rules coverage",
            description: "Seven player-facing rules sections are checked per locale.",
            metrics: perLocaleCoverage.map(({ locale, draft, live }) => ({
              label: locale.toUpperCase(),
              value: (
                <>
                  draft {draft.validCopy}/{BOXE_COPY_TOTAL} copy, {draft.validRules}/
                  {BOXE_RULE_TOTAL} rules
                  {live
                    ? ` - live ${live.validCopy}/${BOXE_COPY_TOTAL} copy, ${live.validRules}/${BOXE_RULE_TOTAL} rules`
                    : ""}
                </>
              ),
              valueClassName:
                draft.missingCopy || draft.tooLongCopy || draft.missingRules
                  ? "status-inline warning"
                  : "list-strong",
            })),
            children: (
              <div className="admin-summary-strip">
                {BOXE_RULE_SECTION_DEFINITIONS.map((section) => (
                  <span
                    className={
                      activePayload.rules_html[defaultLocale]?.[section.key]?.trim()
                        ? "meta-pill"
                        : "meta-pill warning"
                    }
                    key={section.key}
                  >
                    {section.label}
                  </span>
                ))}
              </div>
            ),
          },
          {
            id: "boxe-fairness-math",
            title: "Fairness and math",
            description: "Read-only diagnostics from the BOXE math contract.",
            badge: <span className="status-inline success">98% RTP</span>,
            metrics: [
              { label: "RTP target", value: "98%", valueClassName: "list-strong" },
              { label: "Outcome authority", value: "server-authoritative" },
              { label: "Reveal policy", value: "deterministic full pyramid on terminal rounds" },
              { label: "Replay source", value: "terminal full reveal payload" },
              { label: "Anchor low", value: "4 rows EASY first: 1.37x" },
              { label: "Anchor high", value: "8 rows HARD top: 548.80x" },
              { label: "Max win cap", value: "null in BOXE v1" },
            ],
          },
          {
            id: "boxe-config-summary",
            title: "Configuration",
            description: "Rows and difficulty defaults for draft, live and runtime.",
            metrics: [
              {
                label: "Draft rows",
                value: formatRows(activePayload.rows_enabled),
                valueClassName: "list-strong",
              },
              { label: "Draft default row", value: `${activePayload.default_rows}` },
              {
                label: "Live rows",
                value: publishedPayload ? formatRows(publishedPayload.rows_enabled) : "defaults",
              },
              {
                label: "Runtime rows",
                value: runtimeConfig ? formatRows(runtimeConfig.rows_enabled) : "not loaded",
              },
              {
                label: "Draft difficulty",
                value: formatDifficulties(activePayload.difficulty_enabled),
                valueClassName: "list-strong",
              },
              { label: "Draft default difficulty", value: activePayload.default_difficulty },
              {
                label: "Live difficulty",
                value: publishedPayload
                  ? formatDifficulties(publishedPayload.difficulty_enabled)
                  : "defaults",
              },
              {
                label: "Runtime difficulty",
                value: runtimeConfig
                  ? formatDifficulties(runtimeConfig.difficulty_enabled)
                  : "not loaded",
              },
            ],
          },
          {
            id: "boxe-draft-live-state",
            title: "Draft and live state",
            description: "Operational state for the loaded BOXE title config.",
            metrics: [
              {
                label: "Server draft",
                value: adminState?.has_unpublished_changes ? "draft ready" : "aligned",
                valueClassName: adminState?.has_unpublished_changes
                  ? "status-inline info"
                  : "status-inline success",
              },
              {
                label: "Draft updated",
                value: adminState?.draft_updated_at
                  ? formatDateTime(adminState.draft_updated_at)
                  : "default runtime",
              },
              {
                label: "Draft by",
                value: adminState?.draft_updated_by_admin_user_id
                  ? shortValue(adminState.draft_updated_by_admin_user_id)
                  : "default runtime",
              },
              {
                label: "Published at",
                value: adminState?.published_at
                  ? formatDateTime(adminState.published_at)
                  : "default runtime",
              },
              {
                label: "Published by",
                value: adminState?.published_updated_by_admin_user_id
                  ? shortValue(adminState.published_updated_by_admin_user_id)
                  : "default runtime",
              },
            ],
          },
        ]}
      />
    </>
  );
}

function readLocaleCoverage(payload: BoxeAdminPayload, locale: BoxeLocale) {
  let validCopy = 0;
  let missingCopy = 0;
  let tooLongCopy = 0;
  for (const definition of BOXE_COPY_DEFINITIONS) {
    const value = payload.copy[locale]?.[definition.key] ?? "";
    if (!value.trim()) {
      missingCopy += 1;
      continue;
    }
    if (value.length > definition.maxLength) {
      tooLongCopy += 1;
      continue;
    }
    validCopy += 1;
  }

  let validRules = 0;
  let missingRules = 0;
  for (const key of BOXE_RULE_SECTION_KEYS) {
    if (payload.rules_html[locale]?.[key]?.trim()) {
      validRules += 1;
    } else {
      missingRules += 1;
    }
  }

  return {
    validCopy,
    missingCopy,
    tooLongCopy,
    validRules,
    missingRules,
  };
}

function countChangedFields(draft: BoxeAdminPayload, live: BoxeAdminPayload) {
  let count = 0;
  if (draft.default_locale !== live.default_locale) {
    count += 1;
  }
  if (draft.default_rows !== live.default_rows) {
    count += 1;
  }
  if (draft.default_difficulty !== live.default_difficulty) {
    count += 1;
  }
  if (draft.rows_enabled.join("|") !== live.rows_enabled.join("|")) {
    count += 1;
  }
  if (draft.difficulty_enabled.join("|") !== live.difficulty_enabled.join("|")) {
    count += 1;
  }
  for (const locale of BOXE_SUPPORTED_LOCALES) {
    for (const definition of BOXE_COPY_DEFINITIONS) {
      if ((draft.copy[locale]?.[definition.key] ?? "") !== (live.copy[locale]?.[definition.key] ?? "")) {
        count += 1;
      }
    }
    for (const key of BOXE_RULE_SECTION_KEYS) {
      if ((draft.rules_html[locale]?.[key] ?? "") !== (live.rules_html[locale]?.[key] ?? "")) {
        count += 1;
      }
    }
  }
  return count;
}

function normalizeBoxeLocale(value: string): BoxeLocale {
  return BOXE_SUPPORTED_LOCALES.includes(value as BoxeLocale)
    ? (value as BoxeLocale)
    : "it";
}

function formatRows(rows: readonly number[]) {
  return rows.join(", ");
}

function formatDifficulties(difficulties: readonly string[]) {
  return difficulties.map((difficulty) => difficulty.toUpperCase()).join(", ");
}

function shortValue(value: string) {
  return value.length > 10 ? `${value.slice(0, 8)}...` : value;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}
