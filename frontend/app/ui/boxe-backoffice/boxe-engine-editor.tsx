"use client";

import { useEffect, useMemo, useState } from "react";

import {
  apiDeleteRequest,
  apiFormRequest,
  apiRequest,
  readErrorMessage,
} from "@/app/lib/api";
import type { TitleAsset } from "@/app/lib/types";
import type { BoxeRuntimeConfig } from "@/app/ui/boxe/use-boxe-runtime";
import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";
import { TitleEditorCommandBar } from "@/app/ui/title-editor/title-editor-command-bar";
import {
  TitleEditorConfigTab,
  TitleEditorOverviewTab,
  TitleEditorStatusBanner,
  TitleEditorTabFrame,
  TitleEditorValidationDisplay,
  type ValidationIssue,
} from "@/app/ui/title-editor/tabs";
import {
  BoxeAssetsEditor,
  type BoxeAssetKind,
} from "./boxe-assets-editor";
import {
  BoxeThemeEditor,
  type BoxeThemeState,
} from "./boxe-theme-editor";

type BoxeAdminSubsection =
  | "overview"
  | "copy"
  | "rules"
  | "configuration"
  | "assets"
  | "theme";
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
  const [titleAssets, setTitleAssets] = useState<TitleAsset[]>([]);
  const [themeState, setThemeState] = useState<BoxeThemeState | null>(null);
  const [themeDraftTokens, setThemeDraftTokens] = useState<Record<string, string> | null>(null);
  const [hasThemeLocalUnsavedChanges, setHasThemeLocalUnsavedChanges] = useState(false);

  const validationErrors = useMemo(
    () => (activePayload ? validateBoxePayload(activePayload) : ["Configuration is not loaded"]),
    [activePayload],
  );
  const validationIssues = useMemo<ValidationIssue[]>(
    () =>
      validationErrors.map((message) => ({
        id: message,
        message,
        severity: "error",
      })),
    [validationErrors],
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
    setTitleAssets([]);
    setThemeState(null);
    setThemeDraftTokens(null);
    setHasThemeLocalUnsavedChanges(false);
    void loadBoxeAdminConfig("draft");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleCode]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void (async () => {
      await loadTitleAssets({ announce: false });
      await loadTheme({ announce: false });
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, titleCode]);

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

  async function loadTitleAssets({ announce = true }: { announce?: boolean } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({ kind: "error", text: "A valid admin token is required." });
      }
      return;
    }
    setBusyAction("admin-boxe-assets-load");
    try {
      const assets = await apiRequest<TitleAsset[]>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets`,
        {},
        accessToken,
      );
      setTitleAssets(assets);
      if (announce) {
        setStatus({ kind: "info", text: "BOXE assets loaded." });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE asset loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function uploadTitleAsset(kind: BoxeAssetKind, file: File) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }
    const form = new FormData();
    form.set("asset_kind", kind);
    form.set("file", file);
    setBusyAction(`admin-boxe-asset-upload-${kind}`);
    try {
      const asset = await apiFormRequest<TitleAsset>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets`,
        form,
        accessToken,
      );
      setTitleAssets((current) => [
        ...current.filter((item) => item.asset_kind !== asset.asset_kind),
        asset,
      ].sort((left, right) => left.asset_kind.localeCompare(right.asset_kind)));
      setStatus({ kind: "success", text: `BOXE ${kind} asset uploaded.` });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE asset upload failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteTitleAsset(kind: BoxeAssetKind) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }
    setBusyAction(`admin-boxe-asset-delete-${kind}`);
    try {
      await apiDeleteRequest<TitleAsset>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets/${kind}`,
        accessToken,
      );
      setTitleAssets((current) => current.filter((asset) => asset.asset_kind !== kind));
      setStatus({ kind: "success", text: `BOXE ${kind} asset removed.` });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE asset delete failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function loadTheme({ announce = true }: { announce?: boolean } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({ kind: "error", text: "A valid admin token is required." });
      }
      return;
    }
    setBusyAction("admin-boxe-theme-load");
    try {
      const state = await apiRequest<BoxeThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme`,
        {},
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setHasThemeLocalUnsavedChanges(false);
      if (announce) {
        setStatus({ kind: "info", text: "BOXE theme loaded." });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE theme loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function saveThemeDraft() {
    if (!accessToken || !themeDraftTokens) {
      return;
    }
    setBusyAction("admin-boxe-theme-save");
    try {
      const state = await apiRequest<BoxeThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme`,
        {
          method: "PUT",
          body: JSON.stringify({ tokens: themeDraftTokens }),
        },
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setHasThemeLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "BOXE theme draft saved." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE theme save failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function publishThemeLive() {
    if (!accessToken) {
      return;
    }
    if (hasThemeLocalUnsavedChanges) {
      setStatus({ kind: "error", text: "Save the BOXE theme draft before publishing." });
      return;
    }
    setBusyAction("admin-boxe-theme-publish");
    try {
      const state = await apiRequest<BoxeThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme/publish`,
        { method: "POST" },
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setHasThemeLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "BOXE theme published live." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE theme publish failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function updateThemeToken(key: string, value: string) {
    setThemeDraftTokens((current) => ({
      ...(current ?? themeState?.draft.tokens ?? {}),
      [key]: value,
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  function applyThemePreset(tokens: Record<string, string>) {
    setThemeDraftTokens((current) => ({
      ...(current ?? {}),
      ...tokens,
    }));
    setHasThemeLocalUnsavedChanges(true);
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

      <TitleEditorStatusBanner
        status={{
          label: editorLabel,
          toneClass: editorTone,
          eyebrow: "BOXE editor",
          description: adminState?.published_at
            ? `Live published at ${formatDate(adminState.published_at)}`
            : "No BOXE live publish has been stored yet; defaults are active.",
          testId: "boxe-engine-editor",
        }}
      />

      <TitleEditorTabFrame
        activeTab={activeSubsection}
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "copy", label: "Copy i18n" },
          { id: "rules", label: "Rules HTML" },
          { id: "configuration", label: "Rows & difficulty" },
          { id: "assets", label: "Assets" },
          { id: "theme", label: "Theme" },
        ]}
        onTabChange={setActiveSubsection}
      >

      {!activePayload ? (
        <article className="admin-card">
          <h3>BOXE configuration</h3>
          <p className="empty-state">Load the configuration to open the BOXE editor.</p>
        </article>
      ) : null}

      {activePayload ? <TitleEditorValidationDisplay issues={validationIssues} /> : null}

      {activePayload && activeSubsection === "overview" ? (
        <TitleEditorOverviewTab
          className="admin-grid"
          sections={[
            {
              id: "boxe-overview",
              title: "BOXE overview",
              description: "Draft/live configuration for rows, difficulty, copy and rules.",
              badge: <span className="status-inline info">boxe</span>,
              metrics: [
                { label: "Draft rows", value: activePayload.rows_enabled.join(", ") },
                { label: "Draft default row", value: String(activePayload.default_rows) },
                {
                  label: "Draft difficulty",
                  value: activePayload.difficulty_enabled.join(", "),
                },
                {
                  label: "Draft default difficulty",
                  value: activePayload.default_difficulty,
                },
                {
                  label: "Live rows",
                  value: adminState?.published.rows_enabled.join(", ") ?? "defaults",
                },
                {
                  label: "Runtime rows",
                  value: runtimeConfig?.rows_enabled.join(", ") ?? "not loaded",
                },
              ],
            },
          ]}
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
        <TitleEditorConfigTab
          fields={[
            {
              kind: "choiceSetWithDefault",
              id: "rows",
              title: "Rows enabled",
              choices: BOXE_ROWS,
              selectedValues: activePayload.rows_enabled,
              defaultValue: activePayload.default_rows,
              onToggleChoice: (row) => toggleRows(Number(row)),
              onDefaultChange: (row) =>
                updatePayload((draft) => {
                  draft.default_rows = Number(row);
                }),
            },
            {
              kind: "choiceSetWithDefault",
              id: "difficulty",
              title: "Difficulty enabled",
              choices: BOXE_DIFFICULTIES,
              selectedValues: activePayload.difficulty_enabled,
              defaultValue: activePayload.default_difficulty,
              formatChoice: (difficulty) => String(difficulty).toUpperCase(),
              onToggleChoice: (difficulty) => toggleDifficulty(difficulty as BoxeDifficulty),
              onDefaultChange: (difficulty) =>
                updatePayload((draft) => {
                  draft.default_difficulty = difficulty as BoxeDifficulty;
                }),
            },
          ]}
        />
      ) : null}

      {activeSubsection === "assets" ? (
        <BoxeAssetsEditor
          assets={titleAssets}
          busyAction={busyAction}
          onDeleteAsset={(kind) => void deleteTitleAsset(kind)}
          onUploadAsset={(kind, file) => void uploadTitleAsset(kind, file)}
        />
      ) : null}

      {activeSubsection === "theme" ? (
        <BoxeThemeEditor
          accessToken={accessToken}
          busyAction={busyAction}
          draftTokens={themeDraftTokens}
          hasThemeState={Boolean(themeState)}
          hasLocalUnsavedChanges={hasThemeLocalUnsavedChanges}
          themeState={themeState}
          onApplyPreset={applyThemePreset}
          onLoadTheme={() => void loadTheme()}
          onPublishTheme={() => void publishThemeLive()}
          onSaveTheme={() => void saveThemeDraft()}
          onUpdateToken={updateThemeToken}
        />
      ) : null}
      </TitleEditorTabFrame>
    </>
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
