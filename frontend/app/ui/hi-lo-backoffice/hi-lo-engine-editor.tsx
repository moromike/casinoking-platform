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
  HI_LO_COPY_DEFAULTS,
  HI_LO_COPY_DEFINITIONS,
  HI_LO_DEFAULT_RULE_SECTIONS,
  HI_LO_RULE_SECTION_DEFINITIONS,
  HI_LO_RULE_SECTION_KEYS,
  HI_LO_SUPPORTED_LOCALES,
  type HiLoCopyKey,
  type HiLoLocale,
  type HiLoRuleSectionKey,
} from "@/app/ui/hi-lo/hi-lo-i18n/hi-lo-copy-defaults";
import type { HiLoRuntimeConfig } from "@/app/ui/hi-lo/use-hi-lo-runtime";
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
import { HiLoAssetsEditor, type HiLoAssetKind } from "./hi-lo-assets-editor";
import { HiLoConfigOverview } from "./hi-lo-config-overview";
import {
  HI_LO_ADVANCED_SKIN_DEFAULT,
  HiLoThemeEditor,
  type HiLoSkinAssetKind,
  type HiLoThemeState,
} from "./hi-lo-theme-editor";

type HiLoAdminSubsection =
  | "overview"
  | "copy"
  | "rules"
  | "configuration"
  | "assets"
  | "sounds"
  | "theme"
  | "validation";

type HiLoAdminPayload = {
  default_locale: HiLoLocale;
  copy: Record<HiLoLocale, Record<HiLoCopyKey, string>>;
  rules_html: Record<HiLoLocale, Record<HiLoRuleSectionKey, string>>;
};

type HiLoAdminState = {
  game_code: "hi_lo";
  title_code: string;
  published: HiLoAdminPayload;
  draft: HiLoAdminPayload;
  has_unpublished_changes: boolean;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_updated_by_admin_user_id?: string | null;
  published_at?: string | null;
};

export type HiLoEngineEditorProps = EngineEditorProps<HiLoRuntimeConfig>;

const HI_LO_LOCALES: HiLoLocale[] = [...HI_LO_SUPPORTED_LOCALES];
const HI_LO_IN_GAME_TITLE_KEY: HiLoCopyKey = "game.title";
const HI_LO_GENERIC_COPY_MANIFEST = HI_LO_COPY_DEFINITIONS.filter(
  (definition) => definition.key !== HI_LO_IN_GAME_TITLE_KEY,
);

const HI_LO_SOUND_FIELDS: TitleSoundAssetField[] = [
  {
    kind: "audio_safe_reveal",
    label: "Correct prediction",
    description: "When the player predicts the next card correctly.",
  },
  {
    kind: "audio_mine_hit",
    label: "Wrong prediction",
    description: "When the player misses a prediction.",
  },
  {
    kind: "audio_collect",
    label: "Collect",
    description: "When cashout completes successfully.",
  },
  {
    kind: "audio_win",
    label: "Win",
    description: "When the round closes with a positive payout.",
  },
];

export function HiLoEngineEditor({
  titleCode,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
}: HiLoEngineEditorProps) {
  const [adminState, setAdminState] = useState<HiLoAdminState | null>(null);
  const [activePayload, setActivePayload] = useState<HiLoAdminPayload | null>(null);
  const [activeSubsection, setActiveSubsection] =
    useState<HiLoAdminSubsection>("overview");
  const [activeLocale, setActiveLocale] = useState<HiLoLocale>("it");
  const [hasLocalUnsavedChanges, setHasLocalUnsavedChanges] = useState(false);
  const [titleAssets, setTitleAssets] = useState<TitleAsset[]>([]);
  const [themeState, setThemeState] = useState<HiLoThemeState | null>(null);
  const [themeDraftTokens, setThemeDraftTokens] = useState<Record<string, string> | null>(null);
  const [themeDraftSkin, setThemeDraftSkin] = useState<TitleThemeSkin | null>(null);
  const [hasThemeLocalUnsavedChanges, setHasThemeLocalUnsavedChanges] = useState(false);

  const validationIssues = useMemo<ValidationIssue[]>(
    () => (activePayload ? validateHiLoPayload(activePayload) : [
      {
        id: "configuration.not_loaded",
        message: "Configuration is not loaded.",
        severity: "error",
      },
    ]),
    [activePayload],
  );
  const validationErrors = useMemo(
    () => validationIssues
      .filter((issue) => issue.severity !== "warning")
      .map((issue) => issue.path ? `${issue.path}: ${issue.message}` : issue.message),
    [validationIssues],
  );
  const hasServerDraft = Boolean(adminState?.has_unpublished_changes);
  const canSaveDraft =
    Boolean(accessToken && activePayload && hasLocalUnsavedChanges && validationErrors.length === 0) &&
    busyAction === null;
  const canPublishLive =
    Boolean(accessToken && adminState && hasServerDraft && !hasLocalUnsavedChanges && validationErrors.length === 0) &&
    busyAction === null;
  const editorTone = validationErrors.length > 0
    ? "warning"
    : hasLocalUnsavedChanges
      ? "info"
      : hasServerDraft
        ? "info"
        : "success";
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
    void loadHiLoAdminConfig("draft");
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

  async function loadHiLoAdminConfig(source: "draft" | "published") {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }

    setBusyAction(
      source === "published"
        ? "admin-hi-lo-backoffice-load-published"
        : "admin-hi-lo-backoffice-load-draft",
    );
    try {
      const state = await apiRequest<HiLoAdminState>(
        `/admin/games/hi-lo/config?title_code=${encodeURIComponent(titleCode)}`,
        {},
        accessToken,
      );
      const hydratedState = hydrateHiLoAdminState(state);
      const selectedPayload = source === "published" ? hydratedState.published : hydratedState.draft;
      setAdminState(hydratedState);
      setActiveLocale(selectedPayload.default_locale);
      setActivePayload(clonePayload(selectedPayload));
      setHasLocalUnsavedChanges(false);
      setStatus({
        kind: "info",
        text:
          source === "published"
            ? "HI-LO live configuration loaded."
            : "HI-LO draft configuration loaded.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO configuration loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function saveDraft() {
    if (!accessToken || !activePayload) {
      return;
    }
    const issues = validateHiLoPayload(activePayload).filter((issue) => issue.severity !== "warning");
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

    setBusyAction("admin-hi-lo-backoffice-save");
    try {
      const state = await apiRequest<HiLoAdminState>(
        `/admin/games/hi-lo/config/draft?title_code=${encodeURIComponent(titleCode)}`,
        {
          method: "PUT",
          body: JSON.stringify(activePayload),
        },
        accessToken,
      );
      const hydratedState = hydrateHiLoAdminState(state);
      setAdminState(hydratedState);
      setActiveLocale(hydratedState.draft.default_locale);
      setActivePayload(clonePayload(hydratedState.draft));
      setHasLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "HI-LO draft saved. Live remains unchanged until you publish." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO draft save failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function publishLive() {
    if (!accessToken) {
      return;
    }

    setBusyAction("admin-hi-lo-backoffice-publish");
    try {
      const state = await apiRequest<HiLoAdminState>(
        `/admin/games/hi-lo/config/publish?title_code=${encodeURIComponent(titleCode)}`,
        { method: "POST" },
        accessToken,
      );
      const hydratedState = hydrateHiLoAdminState(state);
      setAdminState(hydratedState);
      setActiveLocale(hydratedState.draft.default_locale);
      setActivePayload(clonePayload(hydratedState.draft));
      setRuntimeConfig((current) =>
        current
          ? {
              ...current,
              presentation_config: {
                default_locale: hydratedState.published.default_locale,
                copy: hydratedState.published.copy,
                rules_html: hydratedState.published.rules_html,
              },
            }
          : current,
      );
      setHasLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "HI-LO draft published live." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO publish failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function updatePayload(mutator: (draft: HiLoAdminPayload) => void) {
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

  async function loadTitleAssets({ announce = true }: { announce?: boolean } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({ kind: "error", text: "A valid admin token is required." });
      }
      return;
    }
    setBusyAction("admin-hi-lo-assets-load");
    try {
      const assets = await apiRequest<TitleAsset[]>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets`,
        {},
        accessToken,
      );
      setTitleAssets(assets);
      if (announce) {
        setStatus({ kind: "info", text: "HI-LO assets loaded." });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO asset loading failed."),
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
    setBusyAction(`admin-hi-lo-asset-upload-${kind}`);
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
      setStatus({ kind: "success", text: `HI-LO ${kind} asset uploaded.` });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO asset upload failed."),
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
        text: "HI-LO sounds support MP3, OGG, WAV or WebM audio only.",
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
    await uploadTitleAsset(kind, file);
  }

  async function deleteTitleAsset(kind: string) {
    if (!accessToken) {
      setStatus({ kind: "error", text: "A valid admin token is required." });
      return;
    }
    setBusyAction(`admin-hi-lo-asset-delete-${kind}`);
    try {
      await apiDeleteRequest<TitleAsset>(
        `/admin/titles/${encodeURIComponent(titleCode)}/assets/${kind}`,
        accessToken,
      );
      setTitleAssets((current) => current.filter((asset) => asset.asset_kind !== kind));
      setStatus({ kind: "success", text: `HI-LO ${kind} asset removed.` });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO asset delete failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteSoundAsset(kind: TitleSoundAssetKind) {
    await deleteTitleAsset(kind);
  }

  async function loadTheme({ announce = true }: { announce?: boolean } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({ kind: "error", text: "A valid admin token is required." });
      }
      return;
    }
    setBusyAction("admin-hi-lo-theme-load");
    try {
      const state = await apiRequest<HiLoThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme`,
        {},
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setThemeDraftSkin(state.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT);
      setHasThemeLocalUnsavedChanges(false);
      if (announce) {
        setStatus({ kind: "info", text: "HI-LO theme loaded." });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO theme loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function saveThemeDraft() {
    if (!accessToken || !themeDraftTokens) {
      return;
    }
    setBusyAction("admin-hi-lo-theme-save");
    try {
      const state = await apiRequest<HiLoThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme`,
        {
          method: "PUT",
          body: JSON.stringify({ tokens: buildThemeDraftPayload() }),
        },
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setThemeDraftSkin(state.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT);
      setHasThemeLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "HI-LO theme draft saved." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO theme save failed."),
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
      setStatus({ kind: "error", text: "Save the HI-LO theme draft before publishing." });
      return;
    }
    setBusyAction("admin-hi-lo-theme-publish");
    try {
      const state = await apiRequest<HiLoThemeState>(
        `/admin/titles/${encodeURIComponent(titleCode)}/theme/publish`,
        { method: "POST" },
        accessToken,
      );
      setThemeState(state);
      setThemeDraftTokens({ ...state.draft.tokens });
      setThemeDraftSkin(state.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT);
      setHasThemeLocalUnsavedChanges(false);
      setStatus({ kind: "success", text: "HI-LO theme published live." });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "HI-LO theme publish failed."),
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
      ...(current ?? themeState?.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT),
      [key]: value,
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  function buildThemeDraftPayload(): Record<string, unknown> {
    return {
      ...(themeDraftTokens ?? {}),
      skin: themeDraftSkin ?? HI_LO_ADVANCED_SKIN_DEFAULT,
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
      ...(current ?? themeState?.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT),
    }));
    setHasThemeLocalUnsavedChanges(true);
  }

  async function uploadSkinAsset(kind: HiLoSkinAssetKind, file: File | null) {
    if (!file) {
      return;
    }
    await uploadTitleAsset(kind, file);
    markThemeAssetChangeAsUnsaved();
  }

  async function deleteSkinAsset(kind: HiLoSkinAssetKind) {
    await deleteTitleAsset(kind);
    markThemeAssetChangeAsUnsaved();
  }

  return (
    <>
      <TitleEditorCommandBar
        engineCode="hi_lo"
        accessToken={accessToken}
        busyAction={busyAction}
        canSaveDraft={canSaveDraft}
        canPublishLive={canPublishLive}
        onLoadDraft={() => void loadHiLoAdminConfig("draft")}
        onLoadPublished={() => void loadHiLoAdminConfig("published")}
        onSaveDraft={() => void saveDraft()}
        onPublishLive={() => void publishLive()}
      />

      <TitleEditorStatusBanner
        status={{
          label: editorLabel,
          toneClass: editorTone,
          testId: "hi-lo-engine-editor",
        }}
      />

      <TitleEditorTabFrame
        activeTab={activeSubsection}
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "copy", label: "Copy i18n" },
          { id: "rules", label: "Rules HTML" },
          { id: "configuration", label: "Gameplay config" },
          { id: "assets", label: "Assets" },
          { id: "sounds", label: "Sounds" },
          { id: "theme", label: "Theme" },
          { id: "validation", label: "Validation" },
        ]}
        onTabChange={setActiveSubsection}
      >
        {!activePayload ? (
          <article className="admin-card">
            <h3>HI-LO configuration</h3>
            <p className="empty-state">Load the configuration to open the HI-LO editor.</p>
          </article>
        ) : null}

        {activePayload && activeSubsection !== "validation" ? (
          <TitleEditorValidationDisplay issues={validationIssues} />
        ) : null}

        {activePayload && activeSubsection === "overview" ? (
          <HiLoConfigOverview
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
          <HiLoCopyEditor
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
          <HiLoRulesEditor
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
                kind: "custom",
                id: "hi-lo-gameplay-contract",
                render: () => (
                  <article className="admin-card" data-testid="hi-lo-config-contract">
                    <div className="admin-card-heading">
                      <div>
                        <h3>Gameplay contract</h3>
                        <p>
                          HI-LO v1 keeps gameplay math code-owned: admin can
                          manage player-facing copy, rules, assets, sounds and
                          theme without changing probabilities.
                        </p>
                      </div>
                      <span className="status-inline success">98% RTP</span>
                    </div>
                    <div className="admin-summary-strip">
                      <span className="meta-pill">Actions: black/red/down/up</span>
                      <span className="meta-pill">Skip limit: {runtimeConfig?.active_skip_limit ?? 5}</span>
                      <span className="meta-pill">Deck: 52 cards with replacement</span>
                      <span className="meta-pill">Max cap: platform policy only</span>
                    </div>
                  </article>
                ),
              },
            ]}
          />
        ) : null}

        {activeSubsection === "assets" ? (
          <HiLoAssetsEditor
            assets={titleAssets}
            busyAction={busyAction}
            onDeleteAsset={(kind: HiLoAssetKind) => void deleteTitleAsset(kind)}
            onUploadAsset={(kind: HiLoAssetKind, file) => void uploadTitleAsset(kind, file)}
          />
        ) : null}

        {activeSubsection === "sounds" ? (
          <TitleSoundAssetsEditor
            assets={titleAssets}
            busyAction={busyAction}
            fields={HI_LO_SOUND_FIELDS}
            onDeleteAsset={(kind) => void deleteSoundAsset(kind)}
            onUploadAsset={(kind, file) => void uploadSoundAsset(kind, file)}
          />
        ) : null}

        {activeSubsection === "theme" ? (
          <HiLoThemeEditor
            accessToken={accessToken}
            activeThemeSkin={themeDraftSkin ?? themeState?.draft.skin ?? HI_LO_ADVANCED_SKIN_DEFAULT}
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

        {activePayload && activeSubsection === "validation" ? (
          <TitleEditorValidationDisplay
            issues={validationIssues}
            title="HI-LO validation"
          />
        ) : null}
      </TitleEditorTabFrame>
    </>
  );
}

function HiLoCopyEditor({
  activeLocale,
  payload,
  onLocaleChange,
  onChange,
}: {
  activeLocale: HiLoLocale;
  payload: HiLoAdminPayload;
  onLocaleChange: (locale: HiLoLocale) => void;
  onChange: (key: HiLoCopyKey, value: string) => void;
}) {
  return (
    <div className="rules-editor-panel">
      <div className="rules-editor-toolbar">
        <div>
          <h3>Copy i18n</h3>
          <p className="helper">
            Draft language: {activeLocale.toUpperCase()}. These strings feed
            how-to-play, info modal and game title.
          </p>
        </div>
        <LocaleButtons activeLocale={activeLocale} onLocaleChange={onLocaleChange} />
      </div>
      {HI_LO_GENERIC_COPY_MANIFEST.map((definition) => {
        const value = payload.copy[activeLocale][definition.key] ?? "";
        const inputId = `hi-lo-copy-${definition.key.replace(/[^a-z0-9]+/gi, "-")}`;
        const isLongText = definition.maxLength > 80 || value.length > 80;

        return (
          <article className="rules-editor-row" key={definition.key}>
            <div className="rules-editor-copy">
              <div className="list-row">
                <h3>{definition.key}</h3>
                <span className="meta-pill">required</span>
              </div>
              <p className="helper">
                {definition.label} - max {definition.maxLength}
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

function HiLoRulesEditor({
  activeLocale,
  payload,
  onLocaleChange,
  onChange,
}: {
  activeLocale: HiLoLocale;
  payload: HiLoAdminPayload;
  onLocaleChange: (locale: HiLoLocale) => void;
  onChange: (key: HiLoRuleSectionKey, value: string) => void;
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
      {HI_LO_RULE_SECTION_DEFINITIONS.map((section) => (
        <article className="rules-editor-row" key={section.key}>
          <div className="rules-editor-copy">
            <div className="list-row">
              <h3>{section.label}</h3>
              <span className="meta-pill">{section.key}</span>
            </div>
            <p className="helper">Rules body shown for HI-LO game info.</p>
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
  activeLocale: HiLoLocale;
  onLocaleChange: (locale: HiLoLocale) => void;
}) {
  return (
    <div className="inline-actions">
      {HI_LO_LOCALES.map((locale) => (
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

function clonePayload(payload: HiLoAdminPayload): HiLoAdminPayload {
  return JSON.parse(JSON.stringify(payload)) as HiLoAdminPayload;
}

function hydrateHiLoAdminState(state: HiLoAdminState): HiLoAdminState {
  return {
    ...state,
    published: hydrateHiLoPayload(state.published),
    draft: hydrateHiLoPayload(state.draft),
  };
}

function hydrateHiLoPayload(payload: HiLoAdminPayload): HiLoAdminPayload {
  const rawCopy = payload.copy as Partial<Record<HiLoLocale, Partial<Record<HiLoCopyKey, string>>>>;
  const rawRules = payload.rules_html as Partial<
    Record<HiLoLocale, Partial<Record<HiLoRuleSectionKey, string>>>
  >;
  const copy = {} as Record<HiLoLocale, Record<HiLoCopyKey, string>>;
  const rulesHtml = {} as Record<HiLoLocale, Record<HiLoRuleSectionKey, string>>;

  for (const locale of HI_LO_LOCALES) {
    copy[locale] = {} as Record<HiLoCopyKey, string>;
    for (const definition of HI_LO_COPY_DEFINITIONS) {
      const fallbackValue = HI_LO_COPY_DEFAULTS[locale][definition.key];
      copy[locale][definition.key] = rawCopy[locale]?.[definition.key] ?? fallbackValue;
    }

    rulesHtml[locale] = {} as Record<HiLoRuleSectionKey, string>;
    for (const key of HI_LO_RULE_SECTION_KEYS) {
      const fallbackSection =
        HI_LO_DEFAULT_RULE_SECTIONS[locale]?.[key] ?? HI_LO_DEFAULT_RULE_SECTIONS.it[key];
      rulesHtml[locale][key] = rawRules[locale]?.[key] ?? fallbackSection.body_html;
    }
  }

  return {
    ...payload,
    default_locale: HI_LO_LOCALES.includes(payload.default_locale)
      ? payload.default_locale
      : "it",
    copy,
    rules_html: rulesHtml,
  };
}

function validateHiLoPayload(payload: HiLoAdminPayload): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (!HI_LO_LOCALES.includes(payload.default_locale)) {
    issues.push({
      id: "default_locale.supported",
      path: "default_locale",
      message: "Default locale must be supported.",
      severity: "error",
    });
  }

  for (const locale of HI_LO_LOCALES) {
    for (const definition of HI_LO_COPY_DEFINITIONS) {
      const value = payload.copy[locale]?.[definition.key] ?? "";
      if (!value.trim()) {
        issues.push({
          id: `copy.${locale}.${definition.key}.required`,
          path: `copy.${locale}.${definition.key}`,
          message: "Copy is required.",
          severity: "error",
        });
        continue;
      }
      if (value.length > definition.maxLength) {
        issues.push({
          id: `copy.${locale}.${definition.key}.length`,
          path: `copy.${locale}.${definition.key}`,
          message: `Copy exceeds ${definition.maxLength} characters.`,
          severity: "error",
        });
      }
      if (
        (definition.key === "rules.dialog_aria" ||
          definition.key === "rules.header_title") &&
        !value.includes("{{gameTitle}}")
      ) {
        issues.push({
          id: `copy.${locale}.${definition.key}.placeholder`,
          path: `copy.${locale}.${definition.key}`,
          message: "Copy must include {{gameTitle}}.",
          severity: "error",
        });
      }
    }

    for (const sectionKey of HI_LO_RULE_SECTION_KEYS) {
      const value = payload.rules_html[locale]?.[sectionKey] ?? "";
      if (!value.trim()) {
        issues.push({
          id: `rules_html.${locale}.${sectionKey}.required`,
          path: `rules_html.${locale}.${sectionKey}`,
          message: "Rules HTML is required.",
          severity: "error",
        });
        continue;
      }
      if (!/<p>|<ul>|<ol>/.test(value)) {
        issues.push({
          id: `rules_html.${locale}.${sectionKey}.richness`,
          path: `rules_html.${locale}.${sectionKey}`,
          message: "Rules should include structured HTML.",
          severity: "warning",
        });
      }
    }
  }

  return issues;
}
