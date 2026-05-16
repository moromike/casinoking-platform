"use client";

/**
 * MinesBackofficeEditor — Admin backoffice editor for Mines game configuration.
 *
 * Extracted from casinoking-console.tsx (P3-WP2).
 * Manages draft/published presentation config, rules HTML, grid/mine publication,
 * demo/real labels, and board assets.
 */

import { useEffect, useRef, useState } from "react";
import {
  formatDateTime,
  formatGridChoiceLabel,
} from "@/app/lib/helpers";
import type {
  FairnessCurrentConfig,
  MinesPresentationConfig,
  MinesRuntimeConfig,
  StatusMessage,
  TitleAsset,
  TitleThemeSkin,
} from "@/app/lib/types";
import {
  apiDeleteRequest,
  apiFormRequest,
  apiRequest,
  readErrorMessage,
} from "@/app/lib/api";
import { TitleEditorCommandBar } from "@/app/ui/title-editor/title-editor-command-bar";
import {
  MinesBoardAssetsEditor,
  type MinesBoardAssetFieldKey,
} from "./mines-board-assets-editor";
import { MinesGridConfigEditor } from "./mines-grid-config-editor";
import { MinesConfigOverview } from "./mines-config-overview";
import {
  MINES_IN_GAME_TITLE_KEY,
  MINES_PUBLISHED_LOCALES,
  MinesCopyEditor,
  MinesPublishedLocalePanel,
  MinesRulesHtmlEditor,
  type MinesPublishedLocale,
} from "./mines-i18n-admin-editor";
import {
  MinesLegacyLabelsEditor,
  type MinesUiLabelKey,
} from "./mines-legacy-labels-editor";
import {
  MINES_ADVANCED_SKIN_DEFAULT,
  MINES_THEME_DEFAULT_TOKENS,
  MinesThemeEditor,
  type MinesSkinAssetKind,
} from "./mines-theme-editor";
import { MinesSoundAssetsEditor } from "./mines-sound-assets-editor";
import type { MinesSoundKind } from "./use-mines-sounds";
import {
  flattenMinesRuleSections,
  MINES_DEFAULT_COPY,
  MINES_DEFAULT_RULE_SECTIONS,
} from "./i18n/mines-copy-defaults";
import {
  MINES_COPY_MANIFEST,
  MINES_RULE_SECTION_KEYS,
  type MinesCopyKey,
  type MinesRuleSectionKey as MinesI18nRuleSectionKey,
} from "./i18n/mines-copy-manifest";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AdminGamesSubsection =
  | "overview"
  | "copy"
  | "rules"
  | "configuration"
  | "labels"
  | "assets"
  | "sounds"
  | "tema";
type MinesRuleSectionKey = MinesI18nRuleSectionKey;

type MinesBackofficeState = {
  game_code: string;
  draft: MinesPresentationConfig;
  published: MinesPresentationConfig;
  has_unpublished_changes: boolean;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_updated_by_admin_user_id?: string | null;
  published_updated_at?: string | null;
  published_at?: string | null;
};

type AdminThemeState = {
  title_code: string;
  published: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  draft: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  has_unpublished_changes: boolean;
  published_updated_by_admin_user_id?: string | null;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_at?: string | null;
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MINES_BACKOFFICE_DEFAULT_TITLE_CODE = "mines_classic";
const SKIN_ASSET_ALLOWED_MIME_TYPES = ["image/png", "image/webp"];
const SKIN_ASSET_MAX_BYTES: Record<MinesSkinAssetKind, number> = {
  title_logo: 150 * 1024,
  game_area_background: 400 * 1024,
  cell_face_down_background: 256 * 1024,
};
const MINES_BACKOFFICE_BUSY_STATUS = {
  "admin-mines-backoffice-load-draft": {
    label: "Caricamento bozza salvata",
    toneClass: "info",
  },
  "admin-mines-backoffice-load-published": {
    label: "Caricamento live pubblicato",
    toneClass: "info",
  },
  "admin-mines-backoffice-save": {
    label: "Salvataggio bozza",
    toneClass: "info",
  },
  "admin-mines-backoffice-publish": {
    label: "Pubblicazione live",
    toneClass: "info",
  },
} as const;

// ---------------------------------------------------------------------------
// Helpers (module-level)
// ---------------------------------------------------------------------------

function sampleMineCountsForAdmin(values: number[]): number[] {
  if (values.length <= 5) {
    return [...values];
  }

  const lastIndex = values.length - 1;
  const sampledIndices = new Set<number>();
  for (let index = 0; index < 5; index += 1) {
    sampledIndices.add(Math.round((index * lastIndex) / 4));
  }

  return [...sampledIndices].sort((a, b) => a - b).map((index) => values[index]);
}

const MINES_BOARD_ASSET_KIND_BY_FIELD = {
  safe_icon_data_url: "symbol_safe",
  mine_icon_data_url: "symbol_mine",
} as const;

function buildAdminMinesBackofficePayload(config: MinesPresentationConfig) {
  const i18nRuleSections = readAdminMinesI18nRuleSections(config);
  return {
    rules_sections: flattenMinesRuleSections(i18nRuleSections),
    published_grid_sizes: config.published_grid_sizes,
    published_mine_counts: config.published_mine_counts,
    default_mine_counts: config.default_mine_counts,
    ui_labels: config.ui_labels,
    board_assets: config.board_assets,
    published_locale_code: readMinesPublishedLocale(config),
    i18n_copy: readAdminMinesI18nCopy(config),
    i18n_rules_sections: i18nRuleSections,
  };
}

function readMinesPublishedLocale(config: MinesPresentationConfig): MinesPublishedLocale {
  return normalizeMinesPublishedLocale(
    config.i18n?.resolved_locale ??
      config.i18n?.default_locale ??
      config.i18n?.fallback_locale ??
      "it",
  );
}

function normalizeMinesPublishedLocale(value: string): MinesPublishedLocale {
  return MINES_PUBLISHED_LOCALES.includes(value as MinesPublishedLocale)
    ? (value as MinesPublishedLocale)
    : "it";
}

function readAdminMinesI18nCopy(
  config: MinesPresentationConfig,
): Record<MinesCopyKey, string> {
  const locale = readMinesPublishedLocale(config);
  const runtimeCopy = config.i18n?.copy ?? {};
  return Object.fromEntries(
    MINES_COPY_MANIFEST.map((definition) => [
      definition.key,
      runtimeCopy[definition.key] ?? MINES_DEFAULT_COPY[locale][definition.key],
    ]),
  ) as Record<MinesCopyKey, string>;
}

function readAdminMinesI18nRuleSections(
  config: MinesPresentationConfig,
): Record<MinesRuleSectionKey, { body_html: string }> {
  const locale = readMinesPublishedLocale(config);
  const runtimeRules = config.i18n?.rules_sections ?? {};
  return Object.fromEntries(
    MINES_RULE_SECTION_KEYS.map((key) => {
      const runtimeSection = runtimeRules[key];
      const runtimeBody =
        runtimeSection && typeof runtimeSection.body_html === "string"
          ? runtimeSection.body_html
          : null;
      return [
        key,
        {
          body_html:
            runtimeBody ??
            config.rules_sections[key] ??
            MINES_DEFAULT_RULE_SECTIONS[locale][key].body_html,
        },
      ];
    }),
  ) as Record<MinesRuleSectionKey, { body_html: string }>;
}

function readMinesBackofficeBusyStatus(busyAction: string | null) {
  if (!busyAction || !(busyAction in MINES_BACKOFFICE_BUSY_STATUS)) {
    return null;
  }

  return MINES_BACKOFFICE_BUSY_STATUS[
    busyAction as keyof typeof MINES_BACKOFFICE_BUSY_STATUS
  ];
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

type MinesBackofficeEditorProps = {
  titleCode?: string;
  accessToken: string | null;
  runtimeConfig: MinesRuntimeConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: React.Dispatch<React.SetStateAction<MinesRuntimeConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

export function MinesBackofficeEditor({
  titleCode = MINES_BACKOFFICE_DEFAULT_TITLE_CODE,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
  adminFairnessCurrent,
}: MinesBackofficeEditorProps) {
  const encodedTitleCode = encodeURIComponent(titleCode);
  const titleConfigPath = `/admin/games/titles/${encodedTitleCode}/config`;
  const titleConfigPublishPath = `/admin/games/titles/${encodedTitleCode}/config/publish`;
  const titleAssetsPath = `/admin/titles/${encodedTitleCode}/assets`;
  const titleThemePath = `/admin/titles/${encodedTitleCode}/theme`;
  const titleThemePublishPath = `/admin/titles/${encodedTitleCode}/theme/publish`;

  const [adminGamesSubsection, setAdminGamesSubsection] =
    useState<AdminGamesSubsection>("overview");
  const [adminMinesBackofficeState, setAdminMinesBackofficeState] =
    useState<MinesBackofficeState | null>(null);
  const [adminMinesBackofficeActiveConfig, setAdminMinesBackofficeActiveConfig] =
    useState<MinesPresentationConfig | null>(null);
  const [hasLocalUnsavedChanges, setHasLocalUnsavedChanges] = useState(false);
  const adminMinesBackofficeActiveConfigRef = useRef<MinesPresentationConfig | null>(null);

  const [adminThemeState, setAdminThemeState] = useState<AdminThemeState | null>(null);
  const [localThemeDraftTokens, setLocalThemeDraftTokens] = useState<Record<string, string> | null>(null);
  const [localThemeDraftSkin, setLocalThemeDraftSkin] = useState<TitleThemeSkin | null>(null);
  const [hasThemeLocalUnsaved, setHasThemeLocalUnsaved] = useState(false);
  const [adminTitleAssets, setAdminTitleAssets] = useState<TitleAsset[]>([]);

  useEffect(() => {
    adminMinesBackofficeActiveConfigRef.current = null;
    setAdminGamesSubsection("overview");
    setAdminMinesBackofficeState(null);
    setAdminMinesBackofficeActiveConfig(null);
    setHasLocalUnsavedChanges(false);
    setAdminThemeState(null);
    setLocalThemeDraftTokens(null);
    setLocalThemeDraftSkin(null);
    setHasThemeLocalUnsaved(false);
    setAdminTitleAssets([]);
  }, [titleCode]);

  const activeAdminMinesBackofficeConfig =
    adminMinesBackofficeActiveConfig ??
    adminMinesBackofficeState?.draft ??
    runtimeConfig?.presentation_config ??
    null;
  const publishedAdminMinesBackofficeConfig =
    adminMinesBackofficeState?.published ?? runtimeConfig?.presentation_config ?? null;
  const activePublishedLocale = activeAdminMinesBackofficeConfig
    ? readMinesPublishedLocale(activeAdminMinesBackofficeConfig)
    : "it";
  const livePublishedLocale = publishedAdminMinesBackofficeConfig
    ? readMinesPublishedLocale(publishedAdminMinesBackofficeConfig)
    : "it";
  const activeI18nCopy = activeAdminMinesBackofficeConfig
    ? readAdminMinesI18nCopy(activeAdminMinesBackofficeConfig)
    : null;
  const publishedI18nCopy = publishedAdminMinesBackofficeConfig
    ? readAdminMinesI18nCopy(publishedAdminMinesBackofficeConfig)
    : null;
  const activeInGameTitle = activeI18nCopy?.[MINES_IN_GAME_TITLE_KEY] ?? "";
  const publishedInGameTitle = publishedI18nCopy?.[MINES_IN_GAME_TITLE_KEY] ?? "";
  const activeI18nRuleSections = activeAdminMinesBackofficeConfig
    ? readAdminMinesI18nRuleSections(activeAdminMinesBackofficeConfig)
    : null;
  const publishedI18nRuleSections = publishedAdminMinesBackofficeConfig
    ? readAdminMinesI18nRuleSections(publishedAdminMinesBackofficeConfig)
    : null;
  const busyEditorStatus = readMinesBackofficeBusyStatus(busyAction);
  const editorStatus =
    busyEditorStatus ??
    (hasLocalUnsavedChanges
      ? {
          label: "Modifiche non salvate",
          toneClass: "warning",
        }
      : adminMinesBackofficeState?.has_unpublished_changes
        ? {
            label: "Bozza pronta",
            toneClass: "info",
          }
        : {
            label: "Pubblicato",
            toneClass: "success",
          });
  const canSaveDraft =
    Boolean(accessToken) &&
    busyAction === null &&
    Boolean(activeAdminMinesBackofficeConfig) &&
    hasLocalUnsavedChanges;
  const canPublishLive =
    Boolean(accessToken) &&
    busyAction === null &&
    !hasLocalUnsavedChanges &&
    Boolean(adminMinesBackofficeState?.has_unpublished_changes);

  const activeThemeTokens =
    localThemeDraftTokens ?? adminThemeState?.draft?.tokens ?? MINES_THEME_DEFAULT_TOKENS;
  const activeThemeSkin =
    localThemeDraftSkin ?? adminThemeState?.draft?.skin ?? MINES_ADVANCED_SKIN_DEFAULT;
  const canSaveThemeDraft =
    Boolean(accessToken) && busyAction === null && hasThemeLocalUnsaved;
  const canPublishThemeLive =
    Boolean(accessToken) &&
    busyAction === null &&
    !hasThemeLocalUnsaved &&
    Boolean(adminThemeState?.has_unpublished_changes);
  const themeEditorStatus = hasThemeLocalUnsaved
    ? { label: "Modifiche non salvate", toneClass: "warning" }
    : adminThemeState?.has_unpublished_changes
      ? { label: "Bozza pronta", toneClass: "info" }
      : { label: "Pubblicato", toneClass: "success" };

  useEffect(() => {
    adminMinesBackofficeActiveConfigRef.current = adminMinesBackofficeActiveConfig;
  }, [adminMinesBackofficeActiveConfig]);

  // Auto-load backoffice config when component mounts
  useEffect(() => {
    if (!accessToken) {
      return;
    }
    if (adminMinesBackofficeState) {
      return;
    }
    void loadAdminMinesBackofficeConfig({
      announce: false,
      setSection: false,
    });
  }, [accessToken, adminMinesBackofficeState]);

  // Auto-load theme when component mounts
  useEffect(() => {
    if (!accessToken) {
      return;
    }
    if (adminThemeState) {
      return;
    }
    void loadAdminTheme({ announce: false });
  }, [accessToken, adminThemeState]);

  // ---------------------------------------------------------------------------
  // Draft helpers
  // ---------------------------------------------------------------------------

  function cloneMinesBackofficeConfig(
    config: MinesPresentationConfig,
  ): MinesPresentationConfig {
    return {
      ...config,
      rules_sections: { ...config.rules_sections },
      published_grid_sizes: [...config.published_grid_sizes],
      published_mine_counts: Object.fromEntries(
        Object.entries(config.published_mine_counts).map(([gridKey, values]) => [
          gridKey,
          [...values],
        ]),
      ),
      default_mine_counts: { ...config.default_mine_counts },
      ui_labels: Object.fromEntries(
        Object.entries(config.ui_labels).map(([mode, labels]) => [mode, { ...labels }]),
      ),
      i18n: config.i18n
        ? {
            ...config.i18n,
            available_locales: [...(config.i18n.available_locales ?? [])],
            copy: { ...(config.i18n.copy ?? {}) },
            rules_sections: Object.fromEntries(
              Object.entries(config.i18n.rules_sections ?? {}).map(([key, section]) => [
                key,
                { ...section },
              ]),
            ),
          }
        : undefined,
      board_assets: {
        safe_icon_data_url: config.board_assets?.safe_icon_data_url ?? null,
        mine_icon_data_url: config.board_assets?.mine_icon_data_url ?? null,
      },
    };
  }

  function setAdminMinesBackofficeEditorConfig(
    config: MinesPresentationConfig | null,
    hasUnsavedChanges: boolean,
  ) {
    adminMinesBackofficeActiveConfigRef.current = config;
    setAdminMinesBackofficeActiveConfig(config);
    setHasLocalUnsavedChanges(hasUnsavedChanges);
  }

  function updateAdminMinesBackofficeDraft(
    updater: (draft: MinesPresentationConfig) => MinesPresentationConfig | null,
  ) {
    const baseConfig =
      adminMinesBackofficeActiveConfigRef.current ??
      adminMinesBackofficeState?.draft ??
      runtimeConfig?.presentation_config ??
      null;
    if (!baseConfig) {
      return;
    }

    const nextDraft = updater(cloneMinesBackofficeConfig(baseConfig));
    if (!nextDraft) {
      return;
    }

    setAdminMinesBackofficeEditorConfig(cloneMinesBackofficeConfig(nextDraft), true);
  }

  function setAdminMinesBackofficeActiveFromSource(
    data: MinesBackofficeState,
    source: "draft" | "published",
  ) {
    setAdminMinesBackofficeEditorConfig(cloneMinesBackofficeConfig(data[source]), false);
  }

  // ---------------------------------------------------------------------------
  // API actions
  // ---------------------------------------------------------------------------

  async function loadAdminMinesBackofficeConfig({
    announce = true,
    setSection = true,
    activeSource = "draft",
  }: {
    announce?: boolean;
    setSection?: boolean;
    activeSource?: "draft" | "published";
  } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({
          kind: "error",
          text: "Serve un bearer token admin per aprire il backoffice Mines.",
        });
      }
      return;
    }

    const loadAction =
      activeSource === "published"
        ? "admin-mines-backoffice-load-published"
        : "admin-mines-backoffice-load-draft";

    setBusyAction(loadAction);
    try {
      const data = await apiRequest<MinesBackofficeState>(
        titleConfigPath,
        {},
        accessToken,
      );
      setAdminMinesBackofficeState(data);
      setAdminMinesBackofficeActiveFromSource(data, activeSource);
      setRuntimeConfig((current) =>
        current ? { ...current, presentation_config: data.published } : current,
      );
      if (announce) {
        setStatus({
          kind: "info",
          text:
            activeSource === "published"
              ? "Payload attivo sostituito con la configurazione live di produzione."
              : "Payload attivo riallineato con la bozza salvata nel backend admin.",
        });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento backoffice Mines non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleSaveAdminMinesBackofficeConfig() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di salvare il backoffice Mines.",
      });
      return;
    }
    if (!activeAdminMinesBackofficeConfig) {
      setStatus({
        kind: "error",
        text: "La configurazione Mines non e' ancora disponibile.",
      });
      return;
    }

    setBusyAction("admin-mines-backoffice-save");
    try {
      const data = await apiRequest<MinesBackofficeState>(
        titleConfigPath,
        {
          method: "PUT",
          body: JSON.stringify(
            buildAdminMinesBackofficePayload(activeAdminMinesBackofficeConfig),
          ),
        },
        accessToken,
      );
      setAdminMinesBackofficeState(data);
      setAdminMinesBackofficeActiveFromSource(data, "draft");
      setStatus({
        kind: "success",
        text: `Draft Mines salvato${data.draft_updated_at ? ` alle ${formatDateTime(data.draft_updated_at)}` : ""}. Il live resta invariato finche' non pubblichi.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Salvataggio backoffice Mines non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublishAdminMinesBackofficeConfig() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di pubblicare il backoffice Mines.",
      });
      return;
    }

    if (hasLocalUnsavedChanges) {
      setStatus({
        kind: "error",
        text: "Salva prima la bozza locale. La pubblicazione live usa solo la bozza gia' salvata nel backend.",
      });
      return;
    }

    if (!adminMinesBackofficeState?.has_unpublished_changes) {
      setStatus({
        kind: "error",
        text: "Non ci sono differenze tra bozza salvata e live da pubblicare.",
      });
      return;
    }

    setBusyAction("admin-mines-backoffice-publish");
    try {
      const data = await apiRequest<MinesBackofficeState>(
        titleConfigPublishPath,
        {
          method: "POST",
        },
        accessToken,
      );
      setAdminMinesBackofficeState(data);
      setAdminMinesBackofficeActiveFromSource(data, "draft");
      setRuntimeConfig((current) =>
        current ? { ...current, presentation_config: data.published } : current,
      );
      setStatus({
        kind: "success",
        text: `Bozza Mines pubblicata live${data.published_at ? ` alle ${formatDateTime(data.published_at)}` : ""}.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Pubblicazione backoffice Mines non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  // ---------------------------------------------------------------------------
  // Theme API actions
  // ---------------------------------------------------------------------------

  async function loadAdminTheme({ announce = true }: { announce?: boolean } = {}) {
    if (!accessToken) {
      if (announce) {
        setStatus({ kind: "error", text: "Serve un bearer token admin per caricare il tema." });
      }
      return;
    }
    setBusyAction("admin-theme-load");
    try {
      const data = await apiRequest<AdminThemeState>(titleThemePath, {}, accessToken);
      setAdminThemeState(data);
      setLocalThemeDraftTokens({ ...data.draft.tokens });
      setLocalThemeDraftSkin(data.draft.skin ? { ...data.draft.skin } : null);
      setHasThemeLocalUnsaved(false);
      if (announce) {
        setStatus({ kind: "info", text: "Tema caricato." });
      }
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Caricamento tema non riuscito.") });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleSaveAdminTheme() {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Serve un bearer token admin prima di salvare il tema." });
      return;
    }
    if (!activeThemeTokens) {
      setStatus({ kind: "error", text: "I token tema non sono ancora disponibili." });
      return;
    }
    setBusyAction("admin-theme-save");
    try {
      const data = await apiRequest<AdminThemeState>(
        titleThemePath,
        { method: "PUT", body: JSON.stringify({ tokens: buildThemeDraftPayload() }) },
        accessToken,
      );
      setAdminThemeState(data);
      setLocalThemeDraftTokens({ ...data.draft.tokens });
      setLocalThemeDraftSkin(data.draft.skin ? { ...data.draft.skin } : null);
      setHasThemeLocalUnsaved(false);
      setStatus({
        kind: "success",
        text: `Bozza tema salvata${data.draft_updated_at ? ` alle ${formatDateTime(data.draft_updated_at)}` : ""}. Il live resta invariato finche' non pubblichi.`,
      });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Salvataggio tema non riuscito.") });
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublishAdminTheme() {
    if (!accessToken) {
      setStatus({ kind: "error", text: "Serve un bearer token admin prima di pubblicare il tema." });
      return;
    }
    if (hasThemeLocalUnsaved) {
      setStatus({
        kind: "error",
        text: "Salva prima la bozza locale. La pubblicazione live usa solo la bozza gia' salvata nel backend.",
      });
      return;
    }
    if (!adminThemeState?.has_unpublished_changes) {
      setStatus({ kind: "error", text: "Non ci sono differenze tra bozza tema salvata e live da pubblicare." });
      return;
    }
    setBusyAction("admin-theme-publish");
    try {
      const data = await apiRequest<AdminThemeState>(
        titleThemePublishPath,
        { method: "POST" },
        accessToken,
      );
      setAdminThemeState(data);
      setLocalThemeDraftTokens({ ...data.draft.tokens });
      setLocalThemeDraftSkin(data.draft.skin ? { ...data.draft.skin } : null);
      setHasThemeLocalUnsaved(false);
      setStatus({
        kind: "success",
        text: `Tema pubblicato live${data.published_at ? ` alle ${formatDateTime(data.published_at)}` : ""}.`,
      });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Pubblicazione tema non riuscita.") });
    } finally {
      setBusyAction(null);
    }
  }

  function updateThemeToken(key: string, value: string) {
    setLocalThemeDraftTokens((current) => {
      return { ...(current ?? activeThemeTokens), [key]: value };
    });
    setHasThemeLocalUnsaved(true);
  }

  function applyThemeTokens(tokens: Record<string, string>) {
    setLocalThemeDraftTokens((current) => ({
      ...(current ?? {}),
      ...tokens,
    }));
    setHasThemeLocalUnsaved(true);
  }

  function updateThemeSkinField<Key extends keyof TitleThemeSkin>(
    key: Key,
    value: TitleThemeSkin[Key],
  ) {
    setLocalThemeDraftSkin((current) => ({
      ...(current ?? MINES_ADVANCED_SKIN_DEFAULT),
      [key]: value,
    }));
    setHasThemeLocalUnsaved(true);
  }

  function markThemeAssetChangeAsUnsaved() {
    setLocalThemeDraftSkin((currentSkin) => ({
      ...(currentSkin ?? activeThemeSkin ?? MINES_ADVANCED_SKIN_DEFAULT),
    }));
    setHasThemeLocalUnsaved(true);
  }

  function buildThemeDraftPayload(): Record<string, unknown> {
    const payload: Record<string, unknown> = { ...activeThemeTokens };
    if (activeThemeSkin) {
      payload.skin = activeThemeSkin;
    }
    return payload;
  }

  // ---------------------------------------------------------------------------
  // Grid / mine toggles
  // ---------------------------------------------------------------------------

  function toggleAdminPublishedGrid(gridSize: number) {
    if (!runtimeConfig) {
      return;
    }

    let validationMessage: string | null = null;
    updateAdminMinesBackofficeDraft((draft) => {
      const gridKey = String(gridSize);
      const isPublished = draft.published_grid_sizes.includes(gridSize);
      if (isPublished) {
        if (draft.published_grid_sizes.length === 1) {
          validationMessage = "Almeno una griglia deve restare pubblicata.";
          return null;
        }
        const nextPublishedGridSizes = draft.published_grid_sizes
          .filter((value) => value !== gridSize)
          .sort((a, b) => a - b);
        const nextPublishedMineCounts = { ...draft.published_mine_counts };
        delete nextPublishedMineCounts[gridKey];
        const nextDefaultMineCounts = { ...draft.default_mine_counts };
        delete nextDefaultMineCounts[gridKey];
        return {
          ...draft,
          published_grid_sizes: nextPublishedGridSizes,
          published_mine_counts: nextPublishedMineCounts,
          default_mine_counts: nextDefaultMineCounts,
        };
      }

      const supportedMineCounts = sampleMineCountsForAdmin(
        runtimeConfig.supported_mine_counts[gridKey] ?? [],
      );
      if (supportedMineCounts.length === 0) {
        validationMessage = `La griglia ${formatGridChoiceLabel(gridSize)} non ha mine count ufficiali disponibili.`;
        return null;
      }
      return {
        ...draft,
        published_grid_sizes: [...draft.published_grid_sizes, gridSize].sort((a, b) => a - b),
        published_mine_counts: {
          ...draft.published_mine_counts,
          [gridKey]: supportedMineCounts,
        },
        default_mine_counts: {
          ...draft.default_mine_counts,
          [gridKey]: supportedMineCounts[Math.floor(supportedMineCounts.length / 2)],
        },
      };
    });

    if (validationMessage) {
      setStatus({ kind: "error", text: validationMessage });
    }
  }

  function toggleAdminPublishedMineCount(gridSize: number, mineCount: number) {
    let validationMessage: string | null = null;
    updateAdminMinesBackofficeDraft((draft) => {
      const gridKey = String(gridSize);
      const currentMineCounts = draft.published_mine_counts[gridKey] ?? [];
      const isSelected = currentMineCounts.includes(mineCount);

      if (isSelected) {
        if (currentMineCounts.length === 1) {
          validationMessage = `La griglia ${formatGridChoiceLabel(gridSize)} deve mantenere almeno una scelta mine.`;
          return null;
        }
        const nextMineCounts = currentMineCounts
          .filter((value) => value !== mineCount)
          .sort((a, b) => a - b);
        const nextDefaultMineCount = nextMineCounts.includes(draft.default_mine_counts[gridKey])
          ? draft.default_mine_counts[gridKey]
          : nextMineCounts[Math.floor(nextMineCounts.length / 2)];
        return {
          ...draft,
          published_mine_counts: {
            ...draft.published_mine_counts,
            [gridKey]: nextMineCounts,
          },
          default_mine_counts: {
            ...draft.default_mine_counts,
            [gridKey]: nextDefaultMineCount,
          },
        };
      }

      if (currentMineCounts.length >= 5) {
        validationMessage = `La griglia ${formatGridChoiceLabel(gridSize)} puo' pubblicare al massimo 5 scelte mine.`;
        return null;
      }

      const nextMineCounts = [...currentMineCounts, mineCount].sort((a, b) => a - b);
      return {
        ...draft,
        published_mine_counts: {
          ...draft.published_mine_counts,
          [gridKey]: nextMineCounts,
        },
        default_mine_counts: {
          ...draft.default_mine_counts,
          [gridKey]: draft.default_mine_counts[gridKey] ?? mineCount,
        },
      };
    });

    if (validationMessage) {
      setStatus({ kind: "error", text: validationMessage });
    }
  }

  // ---------------------------------------------------------------------------
  // Field updaters
  // ---------------------------------------------------------------------------

  function setAdminDefaultMineCount(gridSize: number, mineCount: number) {
    updateAdminMinesBackofficeDraft((draft) => {
      const gridKey = String(gridSize);
      if (!(draft.published_mine_counts[gridKey] ?? []).includes(mineCount)) {
        return null;
      }
      if (draft.default_mine_counts[gridKey] === mineCount) {
        return null;
      }
      return {
        ...draft,
        default_mine_counts: {
          ...draft.default_mine_counts,
          [gridKey]: mineCount,
        },
      };
    });
  }

  function updateAdminRuleSection(sectionKey: MinesRuleSectionKey, value: string) {
    updateAdminMinesBackofficeDraft((draft) => {
      const currentRules = readAdminMinesI18nRuleSections(draft);
      if ((currentRules[sectionKey]?.body_html ?? "") === value) {
        return null;
      }
      const locale = readMinesPublishedLocale(draft);
      return {
        ...draft,
        rules_sections: {
          ...draft.rules_sections,
          [sectionKey]: value,
        },
        i18n: {
          ...(draft.i18n ?? {}),
          resolved_locale: locale,
          default_locale: locale,
          fallback_locale: locale,
          available_locales: [locale],
          copy: readAdminMinesI18nCopy(draft),
          rules_sections: {
            ...currentRules,
            [sectionKey]: { body_html: value },
          },
        },
      };
    });
  }

  function updateAdminModeLabel(
    mode: "demo" | "real",
    labelKey: MinesUiLabelKey,
    value: string,
  ) {
    updateAdminMinesBackofficeDraft((draft) => {
      if ((draft.ui_labels[mode]?.[labelKey] ?? "") === value) {
        return null;
      }
      return {
        ...draft,
        ui_labels: {
          ...draft.ui_labels,
          [mode]: {
            ...draft.ui_labels[mode],
            [labelKey]: value,
          },
        },
      };
    });
  }

  function updateAdminPublishedLocale(locale: MinesPublishedLocale) {
    updateAdminMinesBackofficeDraft((draft) => {
      const currentLocale = readMinesPublishedLocale(draft);
      if (currentLocale === locale) {
        return null;
      }
      const defaultRuleSections = MINES_DEFAULT_RULE_SECTIONS[locale];
      return {
        ...draft,
        rules_sections: flattenMinesRuleSections(defaultRuleSections),
        i18n: {
          ...(draft.i18n ?? {}),
          resolved_locale: locale,
          default_locale: locale,
          fallback_locale: locale,
          available_locales: [locale],
          copy: { ...MINES_DEFAULT_COPY[locale] },
          rules_sections: { ...defaultRuleSections },
        },
      };
    });
  }

  function updateAdminI18nCopyValue(key: MinesCopyKey, value: string) {
    updateAdminMinesBackofficeDraft((draft) => {
      const currentCopy = readAdminMinesI18nCopy(draft);
      if ((currentCopy[key] ?? "") === value) {
        return null;
      }
      const locale = readMinesPublishedLocale(draft);
      return {
        ...draft,
        i18n: {
          ...(draft.i18n ?? {}),
          resolved_locale: locale,
          default_locale: locale,
          fallback_locale: locale,
          available_locales: [locale],
          copy: {
            ...currentCopy,
            [key]: value,
          },
        },
      };
    });
  }

  async function updateAdminBoardAsset(
    key: MinesBoardAssetFieldKey,
    file: File | null,
  ) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di aggiornare gli asset Mines.",
      });
      return;
    }

    if (!file) {
      setBusyAction("admin-board-asset-delete");
      try {
        await apiDeleteRequest<TitleAsset>(
          `${titleAssetsPath}/${MINES_BOARD_ASSET_KIND_BY_FIELD[key]}`,
          accessToken,
        );
        setAdminTitleAssets((currentAssets) =>
          currentAssets.filter(
            (currentAsset) =>
              currentAsset.asset_kind !== MINES_BOARD_ASSET_KIND_BY_FIELD[key],
          ),
        );
      } catch (error) {
        const errorMessage = readErrorMessage(error, "");
        if (!errorMessage.includes("Active asset not found")) {
          setStatus({
            kind: "error",
            text: readErrorMessage(error, "Ripristino asset Mines non riuscito."),
          });
          return;
        }
      } finally {
        setBusyAction(null);
      }
      updateAdminMinesBackofficeDraft((draft) => {
        if ((draft.board_assets?.[key] ?? null) === null) {
          return null;
        }
        return {
          ...draft,
          board_assets: {
            ...(draft.board_assets ?? {
              safe_icon_data_url: null,
              mine_icon_data_url: null,
            }),
            [key]: null,
          },
        };
      });
      setStatus({
        kind: "success",
        text: "Icona Mines ripristinata. Salva la bozza per applicarla al config.",
      });
      return;
    }

    if (!["image/svg+xml", "image/png"].includes(file.type)) {
      setStatus({
        kind: "error",
        text: "Gli asset Mines supportano solo SVG o PNG.",
      });
      return;
    }

    if (file.size > 150 * 1024) {
      setStatus({
        kind: "error",
        text: "L'asset supera 150 KB. Riduci peso o dimensioni prima dell'upload.",
      });
      return;
    }

    setBusyAction("admin-board-asset-upload");
    try {
      const formData = new FormData();
      formData.set("asset_kind", MINES_BOARD_ASSET_KIND_BY_FIELD[key]);
      formData.set("file", file);
      const asset = await apiFormRequest<TitleAsset>(
        titleAssetsPath,
        formData,
        accessToken,
      );
      setAdminTitleAssets((currentAssets) => [
        ...currentAssets.filter(
          (currentAsset) =>
            currentAsset.asset_kind !== MINES_BOARD_ASSET_KIND_BY_FIELD[key],
        ),
        asset,
      ]);
      updateAdminMinesBackofficeDraft((draft) => {
        if ((draft.board_assets?.[key] ?? null) === asset.public_url) {
          return null;
        }
        return {
          ...draft,
          board_assets: {
            ...(draft.board_assets ?? {
              safe_icon_data_url: null,
              mine_icon_data_url: null,
            }),
            [key]: asset.public_url,
          },
        };
      });
      setStatus({
        kind: "success",
        text: "Icona Mines aggiornata. Salva la bozza per applicarla al config.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Upload asset Mines non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function loadAdminTitleAssets() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di leggere gli asset del Title.",
      });
      return;
    }

    try {
      const assets = await apiRequest<TitleAsset[]>(titleAssetsPath, {}, accessToken);
      setAdminTitleAssets(assets);
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Lettura asset Title non riuscita."),
      });
    }
  }

  async function updateAdminSkinAsset(kind: MinesSkinAssetKind, file: File | null) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di aggiornare gli asset skin.",
      });
      return;
    }
    if (!file) {
      return;
    }
    if (!SKIN_ASSET_ALLOWED_MIME_TYPES.includes(file.type)) {
      setStatus({
        kind: "error",
        text: "File non caricato: la Skin avanzata supporta solo PNG o WebP.",
      });
      return;
    }
    if (file.size > SKIN_ASSET_MAX_BYTES[kind]) {
      setStatus({
        kind: "error",
        text: `File non caricato: pesa ${formatBytes(file.size)}. Il limite e' ${formatBytes(SKIN_ASSET_MAX_BYTES[kind])}.`,
      });
      return;
    }

    setBusyAction("admin-skin-asset-upload");
    try {
      const formData = new FormData();
      formData.set("asset_kind", kind);
      formData.set("file", file);
      const asset = await apiFormRequest<TitleAsset>(
        titleAssetsPath,
        formData,
        accessToken,
      );
      setAdminTitleAssets((currentAssets) => [
        ...currentAssets.filter((currentAsset) => currentAsset.asset_kind !== kind),
        asset,
      ]);
      markThemeAssetChangeAsUnsaved();
      setStatus({
        kind: "success",
        text: "Asset skin aggiornato.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Upload asset skin non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteAdminSkinAsset(kind: MinesSkinAssetKind) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di rimuovere gli asset skin.",
      });
      return;
    }

    setBusyAction("admin-skin-asset-delete");
    try {
      await apiDeleteRequest<TitleAsset>(`${titleAssetsPath}/${kind}`, accessToken);
      setAdminTitleAssets((currentAssets) =>
        currentAssets.filter((currentAsset) => currentAsset.asset_kind !== kind),
      );
      markThemeAssetChangeAsUnsaved();
      setStatus({
        kind: "success",
        text: "Asset skin rimosso.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Rimozione asset skin non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function updateAdminSoundAsset(kind: MinesSoundKind, file: File | null) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di aggiornare i suoni Mines.",
      });
      return;
    }
    if (!file) {
      return;
    }
    if (!["audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"].includes(file.type)) {
      setStatus({
        kind: "error",
        text: "I suoni Mines supportano solo MP3, OGG, WAV o WebM audio.",
      });
      return;
    }
    if (file.size > 1024 * 1024) {
      setStatus({
        kind: "error",
        text: "Il suono supera 1 MB. Usa MP3/OGG o un WAV molto corto.",
      });
      return;
    }

    setBusyAction("admin-sound-upload");
    try {
      const formData = new FormData();
      formData.set("asset_kind", kind);
      formData.set("file", file);
      const asset = await apiFormRequest<TitleAsset>(
        titleAssetsPath,
        formData,
        accessToken,
      );
      setAdminTitleAssets((currentAssets) => [
        ...currentAssets.filter((currentAsset) => currentAsset.asset_kind !== kind),
        asset,
      ]);
      setStatus({
        kind: "success",
        text: "Suono Mines aggiornato.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Upload suono Mines non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function deleteAdminSoundAsset(kind: MinesSoundKind) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di rimuovere i suoni Mines.",
      });
      return;
    }

    setBusyAction("admin-sound-delete");
    try {
      await apiDeleteRequest<TitleAsset>(`${titleAssetsPath}/${kind}`, accessToken);
      setAdminTitleAssets((currentAssets) =>
        currentAssets.filter((currentAsset) => currentAsset.asset_kind !== kind),
      );
      setStatus({
        kind: "success",
        text: "Suono Mines rimosso.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Rimozione suono Mines non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  // ---------------------------------------------------------------------------
  // JSX
  // ---------------------------------------------------------------------------

  return (
    <>
      <TitleEditorCommandBar
        accessToken={accessToken}
        busyAction={busyAction}
        canSaveDraft={canSaveDraft}
        canPublishLive={canPublishLive}
        onLoadDraft={() =>
          void loadAdminMinesBackofficeConfig({
            activeSource: "draft",
          })
        }
        onLoadPublished={() =>
          void loadAdminMinesBackofficeConfig({
            activeSource: "published",
          })
        }
        onSaveDraft={() => void handleSaveAdminMinesBackofficeConfig()}
        onPublishLive={() => void handlePublishAdminMinesBackofficeConfig()}
      />
      <article
        className={`admin-card admin-status-banner ${editorStatus.toneClass}`}
        aria-live="polite"
        aria-busy={busyEditorStatus !== null || undefined}
      >
        <span className="admin-status-banner-indicator" aria-hidden="true" />
        <div className="admin-status-banner-copy">
          <span className="meta-pill">Stato editor</span>
          <h3>Stato Editor: {editorStatus.label}</h3>
        </div>
      </article>

      <div className="admin-subnav editor-subnav">
        <button
          className={adminGamesSubsection === "overview" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("overview")}
        >
          Overview
        </button>
        <button
          className={adminGamesSubsection === "copy" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("copy")}
        >
          Copy i18n
        </button>
        <button
          className={adminGamesSubsection === "rules" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("rules")}
        >
          Rules HTML
        </button>
        <button
          className={adminGamesSubsection === "configuration" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("configuration")}
        >
          Grid &amp; mines
        </button>
        <button
          className={adminGamesSubsection === "labels" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("labels")}
        >
          Demo / Real labels
        </button>
        <button
          className={adminGamesSubsection === "assets" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("assets")}
        >
          Board assets
        </button>
        <button
          className={adminGamesSubsection === "sounds" ? "button" : "button-secondary"}
          type="button"
          onClick={() => {
            setAdminGamesSubsection("sounds");
            void loadAdminTitleAssets();
          }}
        >
          Sounds
        </button>
        <button
          className={adminGamesSubsection === "tema" ? "button" : "button-secondary"}
          type="button"
          onClick={() => {
            setAdminGamesSubsection("tema");
            void loadAdminTitleAssets();
          }}
        >
          Tema
        </button>
      </div>

      {!activeAdminMinesBackofficeConfig ? (
        <article className="admin-card">
          <h3>Games</h3>
          <p className="empty-state">
            Carica la configurazione per aprire l&apos;editor backoffice di Mines.
          </p>
        </article>
      ) : null}

      {adminGamesSubsection === "overview" &&
      runtimeConfig &&
      activeAdminMinesBackofficeConfig &&
      activeI18nCopy &&
      publishedI18nCopy &&
      activeI18nRuleSections &&
      publishedI18nRuleSections ? (
        <>
          <MinesPublishedLocalePanel
            activeLocale={activePublishedLocale}
            liveLocale={livePublishedLocale}
            activeInGameTitle={activeInGameTitle}
            publishedInGameTitle={publishedInGameTitle}
            activeCopy={activeI18nCopy}
            publishedCopy={publishedI18nCopy}
            activeRules={activeI18nRuleSections}
            publishedRules={publishedI18nRuleSections}
            busyAction={busyAction}
            onLocaleChange={(locale) =>
              updateAdminPublishedLocale(normalizeMinesPublishedLocale(locale))
            }
            onInGameTitleChange={(value) =>
              updateAdminI18nCopyValue(MINES_IN_GAME_TITLE_KEY, value)
            }
          />
          <MinesConfigOverview
            runtimeConfig={runtimeConfig}
            activeConfig={activeAdminMinesBackofficeConfig}
            publishedConfig={publishedAdminMinesBackofficeConfig}
            backofficeState={adminMinesBackofficeState}
            adminFairnessCurrent={adminFairnessCurrent}
          />
        </>
      ) : null}

      {adminGamesSubsection === "copy" && activeAdminMinesBackofficeConfig && activeI18nCopy ? (
        <MinesCopyEditor
          locale={activePublishedLocale}
          copy={activeI18nCopy}
          onChange={updateAdminI18nCopyValue}
        />
      ) : null}

      {adminGamesSubsection === "rules" && activeAdminMinesBackofficeConfig && activeI18nRuleSections ? (
        <MinesRulesHtmlEditor
          rules={activeI18nRuleSections}
          onChange={updateAdminRuleSection}
        />
      ) : null}

      {adminGamesSubsection === "configuration" && runtimeConfig && activeAdminMinesBackofficeConfig ? (
        <MinesGridConfigEditor
          config={activeAdminMinesBackofficeConfig}
          runtimeConfig={runtimeConfig}
          onToggleGrid={toggleAdminPublishedGrid}
          onToggleMineCount={toggleAdminPublishedMineCount}
          onSetDefaultMineCount={setAdminDefaultMineCount}
        />
      ) : null}

      {adminGamesSubsection === "labels" && activeAdminMinesBackofficeConfig ? (
        <MinesLegacyLabelsEditor
          config={activeAdminMinesBackofficeConfig}
          onChange={updateAdminModeLabel}
        />
      ) : null}

      {adminGamesSubsection === "tema" ? (
        <MinesThemeEditor
          accessToken={accessToken}
          activeThemeTokens={activeThemeTokens}
          activeThemeSkin={activeThemeSkin}
          titleAssets={adminTitleAssets}
          busyAction={busyAction}
          canSaveThemeDraft={canSaveThemeDraft}
          canPublishThemeLive={canPublishThemeLive}
          hasThemeState={Boolean(adminThemeState)}
          themeEditorStatus={themeEditorStatus}
          onLoadTheme={() => void loadAdminTheme()}
          onSaveTheme={() => void handleSaveAdminTheme()}
          onPublishTheme={() => void handlePublishAdminTheme()}
          onApplyTokens={applyThemeTokens}
          onUpdateToken={updateThemeToken}
          onUpdateSkinField={updateThemeSkinField}
          onUploadSkinAsset={(kind, file) => void updateAdminSkinAsset(kind, file)}
          onDeleteSkinAsset={(kind) => void deleteAdminSkinAsset(kind)}
        />
      ) : null}

      {adminGamesSubsection === "assets" && activeAdminMinesBackofficeConfig ? (
        <MinesBoardAssetsEditor
          config={activeAdminMinesBackofficeConfig}
          busyAction={busyAction}
          onUpdateAsset={(key, file) => void updateAdminBoardAsset(key, file)}
        />
      ) : null}

      {adminGamesSubsection === "sounds" ? (
        <MinesSoundAssetsEditor
          assets={adminTitleAssets}
          busyAction={busyAction}
          onDeleteAsset={(kind) => void deleteAdminSoundAsset(kind)}
          onUploadAsset={(kind, file) => void updateAdminSoundAsset(kind, file)}
        />
      ) : null}
    </>
  );
}
