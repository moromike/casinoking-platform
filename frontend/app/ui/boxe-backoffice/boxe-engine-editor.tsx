"use client";

import { useEffect, useMemo, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import type { BoxeRuntimeConfig } from "@/app/ui/boxe/use-boxe-runtime";
import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";
import { TitleEditorCommandBar } from "@/app/ui/title-editor/title-editor-command-bar";

type BoxeAdminSubsection = "overview" | "copy" | "rules" | "configuration";
type BoxeLocale = "it" | "en" | "de" | "es";
type BoxeDifficulty = "easy" | "medium" | "hard";

type BoxeAdminPayload = {
  rows_enabled: number[];
  default_rows: number;
  difficulty_enabled: BoxeDifficulty[];
  default_difficulty: BoxeDifficulty;
  default_locale: BoxeLocale;
  copy: Record<BoxeLocale, Record<BoxeCopyKey, string>>;
  rules_html: Record<BoxeLocale, Record<"bet_collect", string>>;
};

type BoxeAdminState = {
  game_code: "boxe";
  title_code: string;
  published: BoxeAdminPayload;
  draft: BoxeAdminPayload;
  has_unpublished_changes: boolean;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_updated_by_admin_user_id?: string | null;
  published_at?: string | null;
};

type BoxeCopyKey =
  | "game.title"
  | "actions.bet"
  | "actions.collect"
  | "round.won_notice"
  | "round.lost_notice"
  | "rules.bet_collect"
  | "errors.insufficient_balance"
  | "errors.round_closed"
  | "errors.network_retry";

type BoxeCopyDefinition = {
  key: BoxeCopyKey;
  label: string;
  maxLength: number;
};

export type BoxeEngineEditorProps = EngineEditorProps<BoxeRuntimeConfig>;

const BOXE_LOCALES: BoxeLocale[] = ["it", "en", "de", "es"];
const BOXE_ROWS = [4, 5, 6, 7, 8];
const BOXE_DIFFICULTIES: BoxeDifficulty[] = ["easy", "medium", "hard"];

const BOXE_COPY_DEFINITIONS: BoxeCopyDefinition[] = [
  { key: "game.title", label: "Game title", maxLength: 80 },
  { key: "actions.bet", label: "Bet action", maxLength: 32 },
  { key: "actions.collect", label: "Collect action", maxLength: 32 },
  { key: "round.won_notice", label: "Win notice", maxLength: 160 },
  { key: "round.lost_notice", label: "Loss notice", maxLength: 120 },
  { key: "rules.bet_collect", label: "Rules summary", maxLength: 160 },
  { key: "errors.insufficient_balance", label: "Insufficient balance", maxLength: 140 },
  { key: "errors.round_closed", label: "Round closed", maxLength: 120 },
  { key: "errors.network_retry", label: "Network retry", maxLength: 180 },
];

export function BoxeEngineEditor({
  titleCode,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
}: BoxeEngineEditorProps) {
  const [adminState, setAdminState] = useState<BoxeAdminState | null>(null);
  const [activePayload, setActivePayload] = useState<BoxeAdminPayload | null>(null);
  const [activeSubsection, setActiveSubsection] =
    useState<BoxeAdminSubsection>("overview");
  const [activeLocale, setActiveLocale] = useState<BoxeLocale>("it");
  const [hasLocalUnsavedChanges, setHasLocalUnsavedChanges] = useState(false);

  const validationErrors = useMemo(
    () => (activePayload ? validateBoxePayload(activePayload) : ["Configuration is not loaded"]),
    [activePayload],
  );
  const canSaveDraft =
    Boolean(accessToken && activePayload && hasLocalUnsavedChanges && validationErrors.length === 0) &&
    busyAction === null;
  const canPublishLive =
    Boolean(accessToken && adminState && !hasLocalUnsavedChanges && validationErrors.length === 0) &&
    busyAction === null;
  const hasServerDraft = Boolean(adminState?.has_unpublished_changes);
  const editorTone = validationErrors.length > 0 ? "warning" : hasLocalUnsavedChanges ? "info" : hasServerDraft ? "info" : "success";
  const editorLabel =
    validationErrors.length > 0
      ? "Validation required"
      : hasLocalUnsavedChanges
        ? "Unsaved changes"
        : hasServerDraft
          ? "Draft ready"
          : "Live";

  useEffect(() => {
    setAdminState(null);
    setActivePayload(null);
    setHasLocalUnsavedChanges(false);
    setActiveSubsection("overview");
    void loadBoxeAdminConfig("draft");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleCode]);

  async function loadBoxeAdminConfig(source: "draft" | "published") {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }

    setBusyAction(
      source === "published"
        ? "admin-boxe-backoffice-load-published"
        : "admin-boxe-backoffice-load-draft",
    );
    try {
      const state = await apiRequest<BoxeAdminState>(
        `/admin/games/boxe/config?title_code=${encodeURIComponent(titleCode)}`,
        {},
        accessToken,
      );
      setAdminState(state);
      setActivePayload(clonePayload(source === "published" ? state.published : state.draft));
      setHasLocalUnsavedChanges(false);
      setStatus({
        kind: "info",
        text:
          source === "published"
            ? "BOXE live configuration loaded."
            : "BOXE draft configuration loaded.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE configuration loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function saveDraft() {
    if (!accessToken || !activePayload) {
      return;
    }
    const errors = validateBoxePayload(activePayload);
    if (errors.length > 0) {
      setStatus({ kind: "error", text: errors[0] });
      return;
    }

    setBusyAction("admin-boxe-backoffice-save");
    try {
      const state = await apiRequest<BoxeAdminState>(
        `/admin/games/boxe/config/draft?title_code=${encodeURIComponent(titleCode)}`,
        {
          method: "PUT",
          body: JSON.stringify(activePayload),
        },
        accessToken,
      );
      setAdminState(state);
      setActivePayload(clonePayload(state.draft));
      setHasLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "BOXE draft saved." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE draft save failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function publishLive() {
    if (!accessToken) {
      return;
    }

    setBusyAction("admin-boxe-backoffice-publish");
    try {
      const state = await apiRequest<BoxeAdminState>(
        `/admin/games/boxe/config/publish?title_code=${encodeURIComponent(titleCode)}`,
        { method: "POST" },
        accessToken,
      );
      setAdminState(state);
      setActivePayload(clonePayload(state.draft));
      setRuntimeConfig((current) =>
        current
          ? {
              ...current,
              rows_enabled: state.published.rows_enabled,
              default_rows: state.published.default_rows,
              difficulty_enabled: state.published.difficulty_enabled,
              default_difficulty: state.published.default_difficulty,
              presentation_config: {
                default_locale: state.published.default_locale,
                copy: state.published.copy,
                rules_html: state.published.rules_html,
              },
            }
          : current,
      );
      setHasLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "BOXE live configuration published." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE publish failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function updatePayload(mutator: (draft: BoxeAdminPayload) => void) {
    setActivePayload((current) => {
      if (!current) {
        return current;
      }
      const next = clonePayload(current);
      mutator(next);
      return next;
    });
    setHasLocalUnsavedChanges(true);
  }

  function toggleRows(row: number) {
    updatePayload((draft) => {
      const enabled = new Set(draft.rows_enabled);
      if (enabled.has(row)) {
        enabled.delete(row);
      } else {
        enabled.add(row);
      }
      draft.rows_enabled = BOXE_ROWS.filter((candidate) => enabled.has(candidate));
      if (!draft.rows_enabled.includes(draft.default_rows)) {
        draft.default_rows = draft.rows_enabled[0] ?? row;
      }
    });
  }

  function toggleDifficulty(difficulty: BoxeDifficulty) {
    updatePayload((draft) => {
      const enabled = new Set(draft.difficulty_enabled);
      if (enabled.has(difficulty)) {
        enabled.delete(difficulty);
      } else {
        enabled.add(difficulty);
      }
      draft.difficulty_enabled = BOXE_DIFFICULTIES.filter((candidate) => enabled.has(candidate));
      if (!draft.difficulty_enabled.includes(draft.default_difficulty)) {
        draft.default_difficulty = draft.difficulty_enabled[0] ?? difficulty;
      }
    });
  }

  return (
    <>
      <TitleEditorCommandBar
        engineCode="boxe"
        accessToken={accessToken}
        busyAction={busyAction}
        canSaveDraft={canSaveDraft}
        canPublishLive={canPublishLive}
        onLoadDraft={() => void loadBoxeAdminConfig("draft")}
        onLoadPublished={() => void loadBoxeAdminConfig("published")}
        onSaveDraft={() => void saveDraft()}
        onPublishLive={() => void publishLive()}
      />

      <article
        className={`admin-card admin-status-banner ${editorTone}`}
        aria-live="polite"
        data-testid="boxe-engine-editor"
      >
        <span className="admin-status-banner-indicator" aria-hidden="true" />
        <div className="admin-status-banner-copy">
          <span className="meta-pill">BOXE editor</span>
          <h3>Editor Status: {editorLabel}</h3>
          <p className="helper">
            {adminState?.published_at
              ? `Live published at ${formatDate(adminState.published_at)}`
              : "No BOXE live publish has been stored yet; defaults are active."}
          </p>
        </div>
      </article>

      <div className="admin-subnav editor-subnav">
        {[
          ["overview", "Overview"],
          ["copy", "Copy i18n"],
          ["rules", "Rules HTML"],
          ["configuration", "Rows & difficulty"],
        ].map(([key, label]) => (
          <button
            className={activeSubsection === key ? "button" : "button-secondary"}
            key={key}
            type="button"
            onClick={() => setActiveSubsection(key as BoxeAdminSubsection)}
          >
            {label}
          </button>
        ))}
      </div>

      {!activePayload ? (
        <article className="admin-card">
          <h3>BOXE configuration</h3>
          <p className="empty-state">Load the configuration to open the BOXE editor.</p>
        </article>
      ) : null}

      {activePayload && validationErrors.length > 0 ? (
        <article className="admin-card">
          <h3>Validation errors</h3>
          <ul className="stack compact">
            {validationErrors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </article>
      ) : null}

      {activePayload && activeSubsection === "overview" ? (
        <BoxeOverview
          draft={activePayload}
          published={adminState?.published ?? null}
          runtimeConfig={runtimeConfig}
        />
      ) : null}

      {activePayload && activeSubsection === "copy" ? (
        <BoxeCopyEditor
          activeLocale={activeLocale}
          payload={activePayload}
          onLocaleChange={setActiveLocale}
          onChange={(key, value) =>
            updatePayload((draft) => {
              draft.copy[activeLocale][key] = value;
            })
          }
        />
      ) : null}

      {activePayload && activeSubsection === "rules" ? (
        <BoxeRulesEditor
          activeLocale={activeLocale}
          payload={activePayload}
          onLocaleChange={setActiveLocale}
          onChange={(value) =>
            updatePayload((draft) => {
              draft.rules_html[activeLocale].bet_collect = value;
            })
          }
        />
      ) : null}

      {activePayload && activeSubsection === "configuration" ? (
        <BoxeGameConfigEditor
          payload={activePayload}
          onToggleRows={toggleRows}
          onDefaultRowsChange={(row) =>
            updatePayload((draft) => {
              draft.default_rows = row;
            })
          }
          onToggleDifficulty={toggleDifficulty}
          onDefaultDifficultyChange={(difficulty) =>
            updatePayload((draft) => {
              draft.default_difficulty = difficulty;
            })
          }
        />
      ) : null}
    </>
  );
}

function BoxeOverview({
  draft,
  published,
  runtimeConfig,
}: {
  draft: BoxeAdminPayload;
  published: BoxeAdminPayload | null;
  runtimeConfig: BoxeRuntimeConfig | null;
}) {
  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>BOXE overview</h3>
          <p>Draft/live configuration for rows, difficulty, copy and rules.</p>
        </div>
        <span className="status-inline info">boxe</span>
      </div>
      <div className="admin-metric-grid">
        <Metric label="Draft rows" value={draft.rows_enabled.join(", ")} />
        <Metric label="Draft default row" value={String(draft.default_rows)} />
        <Metric label="Draft difficulty" value={draft.difficulty_enabled.join(", ")} />
        <Metric label="Draft default difficulty" value={draft.default_difficulty} />
        <Metric label="Live rows" value={published?.rows_enabled.join(", ") ?? "defaults"} />
        <Metric label="Runtime rows" value={runtimeConfig?.rows_enabled.join(", ") ?? "not loaded"} />
      </div>
    </article>
  );
}

function BoxeCopyEditor({
  activeLocale,
  payload,
  onLocaleChange,
  onChange,
}: {
  activeLocale: BoxeLocale;
  payload: BoxeAdminPayload;
  onLocaleChange: (locale: BoxeLocale) => void;
  onChange: (key: BoxeCopyKey, value: string) => void;
}) {
  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Copy i18n</h3>
          <p>Player-facing BOXE copy for all supported locales.</p>
        </div>
        <LocaleButtons activeLocale={activeLocale} onLocaleChange={onLocaleChange} />
      </div>
      <div className="stack">
        {BOXE_COPY_DEFINITIONS.map((definition) => (
          <label className="field" key={definition.key}>
            <span>
              {definition.label}
              <small className="helper"> `{definition.key}` max {definition.maxLength}</small>
            </span>
            <input
              value={payload.copy[activeLocale][definition.key]}
              maxLength={definition.maxLength}
              onChange={(event) => onChange(definition.key, event.target.value)}
            />
          </label>
        ))}
      </div>
    </article>
  );
}

function BoxeRulesEditor({
  activeLocale,
  payload,
  onLocaleChange,
  onChange,
}: {
  activeLocale: BoxeLocale;
  payload: BoxeAdminPayload;
  onLocaleChange: (locale: BoxeLocale) => void;
  onChange: (value: string) => void;
}) {
  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Rules HTML</h3>
          <p>Rules body shown for BOXE game info. Sanitized on save.</p>
        </div>
        <LocaleButtons activeLocale={activeLocale} onLocaleChange={onLocaleChange} />
      </div>
      <label className="field">
        <span>Bet / Pick / Collect rules</span>
        <textarea
          rows={8}
          value={payload.rules_html[activeLocale].bet_collect}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
    </article>
  );
}

function BoxeGameConfigEditor({
  payload,
  onToggleRows,
  onDefaultRowsChange,
  onToggleDifficulty,
  onDefaultDifficultyChange,
}: {
  payload: BoxeAdminPayload;
  onToggleRows: (row: number) => void;
  onDefaultRowsChange: (row: number) => void;
  onToggleDifficulty: (difficulty: BoxeDifficulty) => void;
  onDefaultDifficultyChange: (difficulty: BoxeDifficulty) => void;
}) {
  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Rows & difficulty</h3>
          <p>These options are exposed to new BOXE rounds after publish.</p>
        </div>
      </div>
      <div className="stack">
        <section className="stack compact">
          <h4>Rows enabled</h4>
          <div className="inline-actions">
            {BOXE_ROWS.map((row) => (
              <label className="meta-pill" key={row}>
                <input
                  type="checkbox"
                  checked={payload.rows_enabled.includes(row)}
                  onChange={() => onToggleRows(row)}
                />
                {row}
              </label>
            ))}
          </div>
          <label className="field">
            <span>Default rows</span>
            <select
              value={payload.default_rows}
              onChange={(event) => onDefaultRowsChange(Number(event.target.value))}
            >
              {payload.rows_enabled.map((row) => (
                <option key={row} value={row}>
                  {row}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className="stack compact">
          <h4>Difficulty enabled</h4>
          <div className="inline-actions">
            {BOXE_DIFFICULTIES.map((difficulty) => (
              <label className="meta-pill" key={difficulty}>
                <input
                  type="checkbox"
                  checked={payload.difficulty_enabled.includes(difficulty)}
                  onChange={() => onToggleDifficulty(difficulty)}
                />
                {difficulty.toUpperCase()}
              </label>
            ))}
          </div>
          <label className="field">
            <span>Default difficulty</span>
            <select
              value={payload.default_difficulty}
              onChange={(event) => onDefaultDifficultyChange(event.target.value as BoxeDifficulty)}
            >
              {payload.difficulty_enabled.map((difficulty) => (
                <option key={difficulty} value={difficulty}>
                  {difficulty.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
        </section>
      </div>
    </article>
  );
}

function LocaleButtons({
  activeLocale,
  onLocaleChange,
}: {
  activeLocale: BoxeLocale;
  onLocaleChange: (locale: BoxeLocale) => void;
}) {
  return (
    <div className="inline-actions">
      {BOXE_LOCALES.map((locale) => (
        <button
          className={activeLocale === locale ? "button" : "button-secondary"}
          key={locale}
          type="button"
          onClick={() => onLocaleChange(locale)}
        >
          {locale.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="admin-metric-row">
      <span className="list-muted">{label}</span>
      <span className="list-strong">{value}</span>
    </div>
  );
}

function clonePayload(payload: BoxeAdminPayload): BoxeAdminPayload {
  return JSON.parse(JSON.stringify(payload)) as BoxeAdminPayload;
}

function validateBoxePayload(payload: BoxeAdminPayload): string[] {
  const errors: string[] = [];
  if (payload.rows_enabled.length === 0) {
    errors.push("Rows must include at least one value.");
  }
  if (!payload.rows_enabled.includes(payload.default_rows)) {
    errors.push("Default rows must be enabled.");
  }
  if (payload.difficulty_enabled.length === 0) {
    errors.push("Difficulty must include at least one value.");
  }
  if (!payload.difficulty_enabled.includes(payload.default_difficulty)) {
    errors.push("Default difficulty must be enabled.");
  }
  for (const locale of BOXE_LOCALES) {
    for (const definition of BOXE_COPY_DEFINITIONS) {
      const value = payload.copy[locale]?.[definition.key] ?? "";
      if (!value.trim()) {
        errors.push(`${locale}.${definition.key} is required.`);
      }
      if (value.length > definition.maxLength) {
        errors.push(`${locale}.${definition.key} exceeds ${definition.maxLength} characters.`);
      }
    }
    if (!payload.rules_html[locale]?.bet_collect?.trim()) {
      errors.push(`${locale}.rules.bet_collect is required.`);
    }
  }
  return errors;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}
