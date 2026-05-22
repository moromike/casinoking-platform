"use client";

import { useEffect, useMemo, useState } from "react";

import {
  apiDeleteRequest,
  apiFormRequest,
  apiRequest,
  readErrorMessage,
} from "@/app/lib/api";
import type { TitleAsset, TitleThemeSkin } from "@/app/lib/types";
import {
  BOXE_COPY_DEFAULTS,
  BOXE_COPY_DEFINITIONS,
  BOXE_DEFAULT_RULE_SECTIONS,
  BOXE_RULE_SECTION_DEFINITIONS,
  BOXE_RULE_SECTION_KEYS,
  BOXE_SUPPORTED_LOCALES,
  type BoxeCopyKey,
  type BoxeLocale,
  type BoxeRuleSectionKey,
} from "@/app/ui/boxe/boxe-i18n/boxe-copy-defaults";
import {
  BOXE_COPY_MANIFEST,
  validateBoxeCopyAndRulesPayload,
} from "@/app/ui/boxe/boxe-i18n/boxe-copy-manifest";
import type { BoxeRuntimeConfig } from "@/app/ui/boxe/use-boxe-runtime";
import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";
import { TitleEditorCommandBar } from "@/app/ui/title-editor/title-editor-command-bar";
import {
  TitleEditorConfigTab,
  TitleEditorStatusBanner,
  TitleEditorTabFrame,
  TitleEditorValidationDisplay,
  type ValidationIssue,
} from "@/app/ui/title-editor/tabs";
import {
  TITLE_SOUND_ASSET_MIME_TYPES,
  TITLE_SOUND_ASSET_MAX_BYTES,
  TitleSoundAssetsEditor,
  type TitleSoundAssetField,
  type TitleSoundAssetKind,
} from "@/app/ui/title-editor/title-sound-assets-editor";
import {
  BoxeAssetsEditor,
  type BoxeAssetKind,
} from "./boxe-assets-editor";
import {
  BOXE_ADVANCED_SKIN_DEFAULT,
  BoxeThemeEditor,
  type BoxeSkinAssetKind,
  type BoxeThemeState,
} from "./boxe-theme-editor";
import { BoxeConfigOverview } from "./boxe-config-overview";

type BoxeAdminSubsection =
  | "overview"
  | "copy"
  | "rules"
  | "configuration"
  | "assets"
  | "sounds"
  | "theme";
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

export type BoxeEngineEditorProps = EngineEditorProps<BoxeRuntimeConfig>;

const BOXE_LOCALES: BoxeLocale[] = [...BOXE_SUPPORTED_LOCALES];
const BOXE_ROWS = [4, 5, 6, 7, 8];
const BOXE_DIFFICULTIES: BoxeDifficulty[] = ["easy", "medium", "hard"];

const BOXE_SOUND_FIELDS: TitleSoundAssetField[] = [
  {
    kind: "audio_safe_reveal",
    label: "Safe reveal",
    description: "When the player finds a safe box.",
  },
  {
    kind: "audio_mine_hit",
    label: "Mine hit",
    description: "When the player finds a mine.",
  },
  {
    kind: "audio_collect",
    label: "Collect",
    description: "When cashout completes successfully.",
  },
  {
    kind: "audio_win",
    label: "Win",
    description: "When the round closes with an automatic win.",
  },
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
  const [themeDraftSkin, setThemeDraftSkin] = useState<TitleThemeSkin | null>(null);
  const [hasThemeLocalUnsavedChanges, setHasThemeLocalUnsavedChanges] = useState(false);

  const validationIssues = useMemo<ValidationIssue[]>(
    () => (activePayload ? validateBoxePayload(activePayload) : [
      {
        id: "configuration.not_loaded",
        message: "Configuration is not loaded.",
        severity: "error",
      },
    ]),
    [activePayload],
  );
  const validationErrors = useMemo(
    () => validationIssues.map((issue) => issue.path ? `${issue.path}: ${issue.message}` : issue.message),
    [validationIssues],
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
    setThemeDraftSkin(null);
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
      const hydratedState = hydrateBoxeAdminState(state);
      setAdminState(hydratedState);
      setActivePayload(clonePayload(source === "published" ? hydratedState.published : hydratedState.draft));
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
    const issues = validateBoxePayload(activePayload);
    if (issues.length > 0) {
      const firstIssue = issues[0];
      setStatus({
        kind: "error",
        text: firstIssue.path
          ? `${firstIssue.path}: ${firstIssue.message}`
          : firstIssue.message,
      });
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
      const hydratedState = hydrateBoxeAdminState(state);
      setAdminState(hydratedState);
      setActivePayload(clonePayload(hydratedState.draft));
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
      const hydratedState = hydrateBoxeAdminState(state);
      setAdminState(hydratedState);
      setActivePayload(clonePayload(hydratedState.draft));
      setRuntimeConfig((current) =>
        current
          ? {
              ...current,
              rows_enabled: hydratedState.published.rows_enabled,
              default_rows: hydratedState.published.default_rows,
              difficulty_enabled: hydratedState.published.difficulty_enabled,
              default_difficulty: hydratedState.published.default_difficulty,
              presentation_config: {
                default_locale: hydratedState.published.default_locale,
                copy: hydratedState.published.copy,
                rules_html: hydratedState.published.rules_html,
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

  async function uploadTitleAsset(kind: string, file: File) {
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

  async function uploadSoundAsset(kind: TitleSoundAssetKind, file: File | null) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }
    if (!file) {
      return;
    }
    if (
      !TITLE_SOUND_ASSET_MIME_TYPES.includes(
        file.type as (typeof TITLE_SOUND_ASSET_MIME_TYPES)[number],
      )
    ) {
      setStatus({
        kind: "error",
        text: "BOXE sounds support MP3, OGG, WAV or WebM audio only.",
      });
      return;
    }
    if (file.size > TITLE_SOUND_ASSET_MAX_BYTES) {
      setStatus({
        kind: "error",
        text: "The sound exceeds 1 MB. Use MP3/OGG or a very short WAV.",
      });
      return;
    }

    const form = new FormData();
    form.set("asset_kind", kind);
    form.set("file", file);
    setBusyAction(`admin-boxe-sound-upload-${kind}`);
    try {
      const asset = await apiFormRequest<TitleAsset>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets`,
        form,
        accessToken,
      );
      setTitleAssets((current) =>
        [
          ...current.filter((item) => item.asset_kind !== asset.asset_kind),
          asset,
        ].sort((left, right) => left.asset_kind.localeCompare(right.asset_kind)),
      );
      setStatus({ kind: "success", text: "BOXE sound updated." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE sound upload failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteTitleAsset(kind: string) {
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

  async function deleteSoundAsset(kind: TitleSoundAssetKind) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }
    setBusyAction(`admin-boxe-sound-delete-${kind}`);
    try {
      await apiDeleteRequest<TitleAsset>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets/${kind}`,
        accessToken,
      );
      setTitleAssets((current) => current.filter((asset) => asset.asset_kind !== kind));
      setStatus({ kind: "success", text: "BOXE sound removed." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "BOXE sound removal failed."),
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
      setThemeDraftSkin(state.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT);
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
          body: JSON.stringify({ tokens: buildThemeDraftPayload() }),
        },
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setThemeDraftSkin(state.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT);
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
      setThemeDraftSkin(state.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT);
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

  function updateThemeSkinField<Key extends keyof TitleThemeSkin>(
    key: Key,
    value: TitleThemeSkin[Key],
  ) {
    setThemeDraftSkin((current) => ({
      ...(current ?? themeState?.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT),
      [key]: value,
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  function buildThemeDraftPayload(): Record<string, unknown> {
    return {
      ...(themeDraftTokens ?? {}),
      skin: themeDraftSkin ?? BOXE_ADVANCED_SKIN_DEFAULT,
    };
  }

  function applyThemePreset(tokens: Record<string, string>) {
    setThemeDraftTokens((current) => ({
      ...(current ?? {}),
      ...tokens,
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  function markThemeAssetChangeAsUnsaved() {
    setThemeDraftSkin((current) => ({
      ...(current ?? themeState?.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT),
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  async function uploadSkinAsset(kind: BoxeSkinAssetKind, file: File | null) {
    if (!file) {
      return;
    }
    await uploadTitleAsset(kind, file);
    markThemeAssetChangeAsUnsaved();
  }

  async function deleteSkinAsset(kind: BoxeSkinAssetKind) {
    await deleteTitleAsset(kind);
    markThemeAssetChangeAsUnsaved();
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
          { id: "sounds", label: "Sounds" },
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
        <BoxeConfigOverview
          activeLocale={activeLocale}
          activePayload={activePayload}
          adminState={adminState}
          busyAction={busyAction}
          runtimeConfig={runtimeConfig}
          onDefaultLocaleChange={(locale) => {
            setActiveLocale(locale);
            updatePayload((draft) => {
              draft.default_locale = locale;
            });
          }}
          onInGameTitleChange={(value) =>
            updatePayload((draft) => {
              draft.copy[draft.default_locale]["game.title"] = value;
            })
          }
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
          onChange={(key, value) =>
            updatePayload((draft) => {
              draft.rules_html[activeLocale][key] = value;
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

      {activeSubsection === "sounds" ? (
        <TitleSoundAssetsEditor
          assets={titleAssets}
          busyAction={busyAction}
          fields={BOXE_SOUND_FIELDS}
          onDeleteAsset={(kind) => void deleteSoundAsset(kind)}
          onUploadAsset={(kind, file) => void uploadSoundAsset(kind, file)}
        />
      ) : null}

      {activeSubsection === "theme" ? (
        <BoxeThemeEditor
          accessToken={accessToken}
          activeThemeSkin={themeDraftSkin ?? themeState?.draft.skin ?? BOXE_ADVANCED_SKIN_DEFAULT}
          busyAction={busyAction}
          draftTokens={themeDraftTokens}
          hasThemeState={Boolean(themeState)}
          hasLocalUnsavedChanges={hasThemeLocalUnsavedChanges}
          titleAssets={titleAssets}
          themeState={themeState}
          onApplyPreset={applyThemePreset}
          onDeleteSkinAsset={(kind) => void deleteSkinAsset(kind)}
          onLoadTheme={() => void loadTheme()}
          onPublishTheme={() => void publishThemeLive()}
          onSaveTheme={() => void saveThemeDraft()}
          onUpdateSkinField={updateThemeSkinField}
          onUpdateToken={updateThemeToken}
          onUploadSkinAsset={(kind, file) => void uploadSkinAsset(kind, file)}
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
    <div className="rules-editor-panel">
      <div className="rules-editor-toolbar">
        <div>
          <h3>Copy i18n</h3>
          <p className="helper">
            Draft language: {activeLocale.toUpperCase()}. These strings feed the
            game; the player cannot change them.
          </p>
        </div>
        <LocaleButtons activeLocale={activeLocale} onLocaleChange={onLocaleChange} />
      </div>
      {BOXE_COPY_MANIFEST.map((definition) => {
        const value = payload.copy[activeLocale][definition.key] ?? "";
        const inputId = `boxe-copy-${definition.key.replace(/[^a-z0-9]+/gi, "-")}`;
        const isLongText = definition.maxLength > 80 || value.length > 80;

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
                {definition.label} - max {definition.maxLength} - {definition.format}
                {definition.placeholders?.length
                  ? ` - Placeholder: ${definition.placeholders.join(", ")}`
                  : ""}
                {definition.helper ? ` - ${definition.helper}` : ""}
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

function BoxeRulesEditor({
  activeLocale,
  payload,
  onLocaleChange,
  onChange,
}: {
  activeLocale: BoxeLocale;
  payload: BoxeAdminPayload;
  onLocaleChange: (locale: BoxeLocale) => void;
  onChange: (key: BoxeRuleSectionKey, value: string) => void;
}) {
  return (
    <div className="rules-editor-panel">
      <div className="rules-editor-toolbar">
        <div>
          <h3>Rules HTML editor</h3>
          <p className="helper">
            Draft language: {activeLocale.toUpperCase()}. Sanitized on save.
          </p>
        </div>
        <LocaleButtons activeLocale={activeLocale} onLocaleChange={onLocaleChange} />
      </div>
      {BOXE_RULE_SECTION_DEFINITIONS.map((section) => (
        <article className="rules-editor-row" key={section.key}>
          <div className="rules-editor-copy">
            <div className="list-row">
              <h3>{section.label}</h3>
              <span className="meta-pill">{section.key}</span>
            </div>
            <p className="helper">Rules body shown for BOXE game info.</p>
          </div>
          <textarea
            className="admin-textarea"
            value={payload.rules_html[activeLocale][section.key]}
            onChange={(event) => onChange(section.key, event.target.value)}
            spellCheck={false}
          />
        </article>
      ))}
    </div>
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

function hydrateBoxeAdminState(state: BoxeAdminState): BoxeAdminState {
  return {
    ...state,
    published: hydrateBoxePayload(state.published),
    draft: hydrateBoxePayload(state.draft),
  };
}

function hydrateBoxePayload(payload: BoxeAdminPayload): BoxeAdminPayload {
  const rawCopy = payload.copy as Partial<Record<BoxeLocale, Partial<Record<BoxeCopyKey, string>>>>;
  const rawRules = payload.rules_html as Partial<
    Record<BoxeLocale, Partial<Record<BoxeRuleSectionKey, string>>>
  >;
  const copy = {} as Record<BoxeLocale, Record<BoxeCopyKey, string>>;
  const rulesHtml = {} as Record<BoxeLocale, Record<BoxeRuleSectionKey, string>>;

  for (const locale of BOXE_LOCALES) {
    copy[locale] = {} as Record<BoxeCopyKey, string>;
    for (const definition of BOXE_COPY_DEFINITIONS) {
      const fallbackValue = BOXE_COPY_DEFAULTS[locale][definition.key];
      copy[locale][definition.key] = rawCopy[locale]?.[definition.key] ?? fallbackValue;
    }

    rulesHtml[locale] = {} as Record<BoxeRuleSectionKey, string>;
    for (const key of BOXE_RULE_SECTION_KEYS) {
      const fallbackSection =
        BOXE_DEFAULT_RULE_SECTIONS[locale]?.[key] ?? BOXE_DEFAULT_RULE_SECTIONS.it[key];
      rulesHtml[locale][key] = rawRules[locale]?.[key] ?? fallbackSection.body_html;
    }
  }

  return {
    ...payload,
    copy,
    rules_html: rulesHtml,
  };
}

function validateBoxePayload(payload: BoxeAdminPayload): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  if (payload.rows_enabled.length === 0) {
    issues.push({
      id: "rows_enabled.required",
      path: "rows_enabled",
      message: "Rows must include at least one value.",
      severity: "error",
    });
  }
  if (!payload.rows_enabled.includes(payload.default_rows)) {
    issues.push({
      id: "default_rows.enabled",
      path: "default_rows",
      message: "Default rows must be enabled.",
      severity: "error",
    });
  }
  if (payload.difficulty_enabled.length === 0) {
    issues.push({
      id: "difficulty_enabled.required",
      path: "difficulty_enabled",
      message: "Difficulty must include at least one value.",
      severity: "error",
    });
  }
  if (!payload.difficulty_enabled.includes(payload.default_difficulty)) {
    issues.push({
      id: "default_difficulty.enabled",
      path: "default_difficulty",
      message: "Default difficulty must be enabled.",
      severity: "error",
    });
  }
  return [...issues, ...validateBoxeCopyAndRulesPayload(payload, BOXE_LOCALES)];
}
