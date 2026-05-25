"use client";

import {
  HI_LO_COPY_DEFINITIONS,
  HI_LO_RULE_SECTION_DEFINITIONS,
  HI_LO_RULE_SECTION_KEYS,
  HI_LO_SUPPORTED_LOCALES,
  type HiLoCopyKey,
  type HiLoLocale,
  type HiLoRuleSectionKey,
} from "@/app/ui/hi-lo/hi-lo-i18n/hi-lo-copy-defaults";
import type { HiLoRuntimeConfig } from "@/app/ui/hi-lo/use-hi-lo-runtime";
import { TitleEditorOverviewTab } from "@/app/ui/title-editor/tabs";

type HiLoAdminPayload = {
  default_locale: HiLoLocale;
  gameplay_config: {
    active_skip_limit: number;
  };
  copy: Record<HiLoLocale, Record<HiLoCopyKey, string>>;
  rules_html: Record<HiLoLocale, Record<HiLoRuleSectionKey, string>>;
};

type HiLoAdminState = {
  published: HiLoAdminPayload;
  draft: HiLoAdminPayload;
  has_unpublished_changes: boolean;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_updated_by_admin_user_id?: string | null;
  published_at?: string | null;
};

type HiLoConfigOverviewProps = {
  activePayload: HiLoAdminPayload;
  adminState: HiLoAdminState | null;
  busyAction: string | null;
  runtimeConfig: HiLoRuntimeConfig | null;
  onDefaultLocaleChange: (locale: HiLoLocale) => void;
  onInGameTitleChange: (value: string) => void;
};

const HI_LO_LOCALE_LABELS: Record<HiLoLocale, string> = {
  it: "Italian",
  en: "English",
  de: "Deutsch",
  es: "Espanol",
};

const HI_LO_COPY_TOTAL = HI_LO_COPY_DEFINITIONS.length;
const HI_LO_RULE_TOTAL = HI_LO_RULE_SECTION_KEYS.length;
const HI_LO_IN_GAME_TITLE_KEY: HiLoCopyKey = "game.title";
const HI_LO_IN_GAME_TITLE_MAX_LENGTH =
  HI_LO_COPY_DEFINITIONS.find((definition) => definition.key === HI_LO_IN_GAME_TITLE_KEY)
    ?.maxLength ?? 80;
const HI_LO_DEFAULT_ACTIVE_SKIP_LIMIT = 3;

export function HiLoConfigOverview({
  activePayload,
  adminState,
  busyAction,
  runtimeConfig,
  onDefaultLocaleChange,
  onInGameTitleChange,
}: HiLoConfigOverviewProps) {
  const publishedPayload = adminState?.published ?? null;
  const runtimeLocale = normalizeHiLoLocale(
    runtimeConfig?.presentation_config?.default_locale ?? activePayload.default_locale,
  );
  const activeLocaleSummary = readLocaleCoverage(activePayload, activePayload.default_locale);
  const perLocaleCoverage = HI_LO_SUPPORTED_LOCALES.map((locale) => ({
    locale,
    draft: readLocaleCoverage(activePayload, locale),
    live: publishedPayload ? readLocaleCoverage(publishedPayload, locale) : null,
  }));
  const draftRuntimeTitle =
    activePayload.copy[activePayload.default_locale]?.[HI_LO_IN_GAME_TITLE_KEY] ??
    activePayload.copy.it?.[HI_LO_IN_GAME_TITLE_KEY] ??
    "HI-LO";
  const liveTitle =
    publishedPayload?.copy[publishedPayload.default_locale]?.[HI_LO_IN_GAME_TITLE_KEY] ??
    publishedPayload?.copy.it?.[HI_LO_IN_GAME_TITLE_KEY] ??
    "defaults";
  const changedFields = publishedPayload
    ? countChangedFields(activePayload, publishedPayload)
    : 0;

  return (
    <>
      <article className="admin-card">
        <h3>HI-LO overview</h3>
        <p className="helper">
          Published locale, rules coverage, fairness notes and gameplay contract
          diagnostics for this HI-LO Title.
        </p>
      </article>
      <article className="admin-card" data-testid="hi-lo-overview-locale-panel">
        <h3>Published language</h3>
        <p className="helper">
          HI-LO keeps one default runtime locale while maintaining full copy and
          rules coverage for every supported locale.
        </p>
        <div className="field">
          <label htmlFor="hi-lo-published-locale">HI-LO runtime language</label>
          <select
            id="hi-lo-published-locale"
            value={activePayload.default_locale}
            disabled={busyAction !== null}
            onChange={(event) => onDefaultLocaleChange(event.target.value as HiLoLocale)}
          >
            {HI_LO_SUPPORTED_LOCALES.map((locale) => (
              <option key={locale} value={locale}>
                {HI_LO_LOCALE_LABELS[locale]}
              </option>
            ))}
          </select>
        </div>
        <div className="field mines-in-game-title-field">
          <label htmlFor="hi-lo-in-game-title">In-game title</label>
          <input
            id="hi-lo-in-game-title"
            value={draftRuntimeTitle}
            maxLength={HI_LO_IN_GAME_TITLE_MAX_LENGTH}
            disabled={busyAction !== null}
            onChange={(event) => onInGameTitleChange(event.target.value)}
          />
          <span className="games-create-helper">
            Max {HI_LO_IN_GAME_TITLE_MAX_LENGTH} characters.
          </span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Live title</span>
          <span>{liveTitle}</span>
        </div>
        <div className="admin-metric-row">
          <span className="list-muted">Runtime default</span>
          <span>{HI_LO_LOCALE_LABELS[runtimeLocale]}</span>
        </div>
        <div className="admin-summary-strip">
          <span className={activeLocaleSummary.missingCopy ? "meta-pill warning" : "meta-pill"}>
            Copy {activeLocaleSummary.validCopy}/{HI_LO_COPY_TOTAL}
          </span>
          <span className={activeLocaleSummary.tooLongCopy ? "meta-pill warning" : "meta-pill"}>
            Too long {activeLocaleSummary.tooLongCopy}
          </span>
          <span className={activeLocaleSummary.missingRules ? "meta-pill warning" : "meta-pill"}>
            Rules {activeLocaleSummary.validRules}/{HI_LO_RULE_TOTAL}
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
            id: "hi-lo-rules-coverage",
            title: "Rules coverage",
            description: "Seven player-facing rules sections are checked per locale.",
            metrics: perLocaleCoverage.map(({ locale, draft, live }) => ({
              label: locale.toUpperCase(),
              value: (
                <>
                  draft {draft.validCopy}/{HI_LO_COPY_TOTAL} copy, {draft.validRules}/
                  {HI_LO_RULE_TOTAL} rules
                  {live
                    ? ` - live ${live.validCopy}/${HI_LO_COPY_TOTAL} copy, ${live.validRules}/${HI_LO_RULE_TOTAL} rules`
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
                {HI_LO_RULE_SECTION_DEFINITIONS.map((section) => (
                  <span
                    className={
                      activePayload.rules_html[activePayload.default_locale]?.[section.key]?.trim()
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
            id: "hi-lo-fairness-math",
            title: "Fairness and math",
            description: "Read-only diagnostics from the HI-LO math contract.",
            badge: <span className="status-inline success">98% RTP</span>,
            metrics: [
              { label: "RTP target", value: "98%", valueClassName: "list-strong" },
              { label: "Outcome authority", value: "server-authoritative" },
              { label: "Deck model", value: "52-card deck with replacement" },
              { label: "Fairness", value: "server seed hash + client seed + nonce" },
              { label: "Replay source", value: "deterministic action timeline" },
              {
                label: "Active skip limit",
                value: runtimeConfig?.active_skip_limit ?? HI_LO_DEFAULT_ACTIVE_SKIP_LIMIT,
              },
              { label: "Game-specific max cap", value: "none in HI-LO v1" },
            ],
          },
          {
            id: "hi-lo-config-summary",
            title: "Configuration",
            description: "Gameplay contract exposed to runtime.",
            metrics: [
              {
                label: "Actions",
                value: runtimeConfig?.actions.join(", ") ?? "black, red, down, up",
                valueClassName: "list-strong",
              },
              {
                label: "Skip limit",
                value: runtimeConfig?.active_skip_limit ?? HI_LO_DEFAULT_ACTIVE_SKIP_LIMIT,
              },
              {
                label: "Draft skip limit",
                value: activePayload.gameplay_config.active_skip_limit,
              },
              { label: "Difficulty matrix", value: "not applicable: card probabilities derive from rank/color" },
              { label: "Draft locale", value: HI_LO_LOCALE_LABELS[activePayload.default_locale] },
              {
                label: "Live locale",
                value: publishedPayload
                  ? HI_LO_LOCALE_LABELS[publishedPayload.default_locale]
                  : "defaults",
              },
            ],
          },
          {
            id: "hi-lo-draft-live-state",
            title: "Draft and live state",
            description: "Operational state for the loaded HI-LO title config.",
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

function readLocaleCoverage(payload: HiLoAdminPayload, locale: HiLoLocale) {
  let validCopy = 0;
  let missingCopy = 0;
  let tooLongCopy = 0;
  for (const definition of HI_LO_COPY_DEFINITIONS) {
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
  for (const key of HI_LO_RULE_SECTION_KEYS) {
    if ((payload.rules_html[locale]?.[key] ?? "").trim()) {
      validRules += 1;
    } else {
      missingRules += 1;
    }
  }

  return { validCopy, missingCopy, tooLongCopy, validRules, missingRules };
}

function countChangedFields(left: HiLoAdminPayload, right: HiLoAdminPayload) {
  let changed = left.default_locale === right.default_locale ? 0 : 1;
  for (const locale of HI_LO_SUPPORTED_LOCALES) {
    for (const definition of HI_LO_COPY_DEFINITIONS) {
      if ((left.copy[locale]?.[definition.key] ?? "") !== (right.copy[locale]?.[definition.key] ?? "")) {
        changed += 1;
      }
    }
    for (const key of HI_LO_RULE_SECTION_KEYS) {
      if ((left.rules_html[locale]?.[key] ?? "") !== (right.rules_html[locale]?.[key] ?? "")) {
        changed += 1;
      }
    }
  }
  return changed;
}

function normalizeHiLoLocale(locale: string | undefined): HiLoLocale {
  const normalized = (locale ?? "it").slice(0, 2).toLowerCase();
  return HI_LO_SUPPORTED_LOCALES.includes(normalized as HiLoLocale)
    ? (normalized as HiLoLocale)
    : "it";
}

function formatDateTime(value: string) {
  try {
    return new Intl.DateTimeFormat("it-IT", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function shortValue(value: string) {
  return value.length <= 12 ? value : `${value.slice(0, 8)}...`;
}
