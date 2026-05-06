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
  shortId,
} from "@/app/lib/helpers";
import type {
  FairnessCurrentConfig,
  MinesPresentationConfig,
  MinesRuntimeConfig,
  StatusMessage,
  TitleAsset,
} from "@/app/lib/types";
import {
  apiDeleteRequest,
  apiFormRequest,
  apiRequest,
  readErrorMessage,
  resolveBackendAssetUrl,
} from "@/app/lib/api";
import { MinesGridConfigEditor } from "./mines-grid-config-editor";
import { MinesThemeEditor } from "./mines-theme-editor";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AdminGamesSubsection = "overview" | "rules" | "configuration" | "labels" | "assets" | "tema";
type MinesRuleSectionKey = keyof NonNullable<MinesPresentationConfig["rules_sections"]>;
type MinesUILabelKey = (typeof MINES_LABEL_FIELDS)[number]["key"];

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
  published: { tokens: Record<string, string> };
  draft: { tokens: Record<string, string> };
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

const MINES_RULE_SECTION_FIELDS: Array<{
  key: keyof NonNullable<MinesPresentationConfig["rules_sections"]>;
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

const MINES_LABEL_FIELDS: Array<{
  key: "bet" | "bet_loading" | "collect" | "collect_loading" | "home" | "fullscreen" | "game_info";
  label: string;
}> = [
  { key: "bet", label: "Bet" },
  { key: "bet_loading", label: "Bet loading" },
  { key: "collect", label: "Collect" },
  { key: "collect_loading", label: "Collect loading" },
  { key: "home", label: "Home" },
  { key: "fullscreen", label: "Fullscreen" },
  { key: "game_info", label: "Game info" },
];

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
  return {
    rules_sections: config.rules_sections,
    published_grid_sizes: config.published_grid_sizes,
    published_mine_counts: config.published_mine_counts,
    default_mine_counts: config.default_mine_counts,
    ui_labels: config.ui_labels,
    board_assets: config.board_assets,
  };
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
  const [hasThemeLocalUnsaved, setHasThemeLocalUnsaved] = useState(false);

  useEffect(() => {
    adminMinesBackofficeActiveConfigRef.current = null;
    setAdminGamesSubsection("overview");
    setAdminMinesBackofficeState(null);
    setAdminMinesBackofficeActiveConfig(null);
    setHasLocalUnsavedChanges(false);
    setAdminThemeState(null);
    setLocalThemeDraftTokens(null);
    setHasThemeLocalUnsaved(false);
  }, [titleCode]);

  const activeAdminMinesBackofficeConfig =
    adminMinesBackofficeActiveConfig ??
    adminMinesBackofficeState?.draft ??
    runtimeConfig?.presentation_config ??
    null;
  const publishedAdminMinesBackofficeConfig =
    adminMinesBackofficeState?.published ?? runtimeConfig?.presentation_config ?? null;
  const editorStatus = hasLocalUnsavedChanges
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
        };
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

  const activeThemeTokens = localThemeDraftTokens ?? adminThemeState?.draft?.tokens ?? null;
  const canSaveThemeDraft =
    Boolean(accessToken) && busyAction === null && hasThemeLocalUnsaved && activeThemeTokens !== null;
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
        { method: "PUT", body: JSON.stringify({ tokens: activeThemeTokens }) },
        accessToken,
      );
      setAdminThemeState(data);
      setLocalThemeDraftTokens({ ...data.draft.tokens });
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
      if (!current) {
        return current;
      }
      return { ...current, [key]: value };
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
      if ((draft.rules_sections[sectionKey] ?? "") === value) {
        return null;
      }
      return {
        ...draft,
        rules_sections: {
          ...draft.rules_sections,
          [sectionKey]: value,
        },
      };
    });
  }

  function updateAdminModeLabel(
    mode: "demo" | "real",
    labelKey: MinesUILabelKey,
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

  async function updateAdminBoardAsset(
    key: "safe_icon_data_url" | "mine_icon_data_url",
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
      try {
        await apiDeleteRequest<TitleAsset>(
          `${titleAssetsPath}/${MINES_BOARD_ASSET_KIND_BY_FIELD[key]}`,
          accessToken,
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

    try {
      const formData = new FormData();
      formData.set("asset_kind", MINES_BOARD_ASSET_KIND_BY_FIELD[key]);
      formData.set("file", file);
      const asset = await apiFormRequest<TitleAsset>(
        titleAssetsPath,
        formData,
        accessToken,
      );
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
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Lettura asset Mines non riuscita."),
      });
    }
  }

  // ---------------------------------------------------------------------------
  // JSX
  // ---------------------------------------------------------------------------

  return (
    <>
      <div className="editor-command-bar">
        <button
          className="button-secondary"
          type="button"
          disabled={!accessToken || busyAction !== null}
          onClick={() =>
            void loadAdminMinesBackofficeConfig({
              activeSource: "draft",
            })
          }
        >
          {busyAction === "admin-mines-backoffice-load-draft"
            ? "Carico bozza salvata..."
            : "Carica bozza salvata"}
        </button>
        <button
          className="button-secondary"
          type="button"
          disabled={!accessToken || busyAction !== null}
          onClick={() =>
            void loadAdminMinesBackofficeConfig({
              activeSource: "published",
            })
          }
        >
          {busyAction === "admin-mines-backoffice-load-published"
            ? "Carico live pubblicato..."
            : "Carica live pubblicato"}
        </button>
        <button
          className="button"
          type="button"
          disabled={!canSaveDraft}
          onClick={() => void handleSaveAdminMinesBackofficeConfig()}
        >
          {busyAction === "admin-mines-backoffice-save" ? "Salvo bozza..." : "Salva bozza"}
        </button>
        <button
          className="button"
          type="button"
          disabled={!canPublishLive}
          onClick={() => void handlePublishAdminMinesBackofficeConfig()}
        >
          {busyAction === "admin-mines-backoffice-publish" ? "Pubblico live..." : "Pubblica live"}
        </button>
      </div>
      <article
        className={`admin-card admin-status-banner ${editorStatus.toneClass}`}
        aria-live="polite"
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
          className={adminGamesSubsection === "tema" ? "button" : "button-secondary"}
          type="button"
          onClick={() => setAdminGamesSubsection("tema")}
        >
          Tema
        </button>
      </div>

      {!activeAdminMinesBackofficeConfig ? (
        <article className="admin-card">
          <h3>Mines backoffice</h3>
          <p className="empty-state">
            Carica la configurazione per aprire l&apos;editor backoffice di Mines.
          </p>
        </article>
      ) : null}

      {adminGamesSubsection === "overview" && runtimeConfig && activeAdminMinesBackofficeConfig ? (
        <div className="admin-grid admin-grid-three">
          <article className="admin-card">
            <h3>Runtime ufficiale</h3>
            <div className="admin-metric-row"><span className="list-muted">Launch key</span><span className="mono">mines</span></div>
            <div className="admin-metric-row"><span className="list-muted">Route player</span><span className="mono">/mines</span></div>
            <div className="admin-metric-row"><span className="list-muted">Grid supportate</span><span className="list-strong">{runtimeConfig.supported_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Payout runtime</span><span className="mono">{runtimeConfig.payout_runtime_file}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Fairness version</span><span className="list-strong">{runtimeConfig.fairness_version}</span></div>
          </article>

          <article className="admin-card">
            <h3>Configurazione pubblicata</h3>
            <div className="admin-metric-row"><span className="list-muted">Grid live</span><span className="list-strong">{publishedAdminMinesBackofficeConfig?.published_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
            {publishedAdminMinesBackofficeConfig?.published_grid_sizes.map((gridSize) => (
              <div className="admin-metric-row" key={gridSize}>
                <span className="list-muted">{formatGridChoiceLabel(gridSize)}</span>
                <span>{(publishedAdminMinesBackofficeConfig?.published_mine_counts[String(gridSize)] ?? []).join(", ")} &middot; default {(publishedAdminMinesBackofficeConfig?.default_mine_counts[String(gridSize)] ?? "n/a")}</span>
              </div>
            ))}
            <div className="admin-metric-row"><span className="list-muted">Published by</span><span>{adminMinesBackofficeState?.published_updated_by_admin_user_id ? shortId(adminMinesBackofficeState.published_updated_by_admin_user_id) : "default runtime"}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Published at</span><span>{adminMinesBackofficeState?.published_at ? formatDateTime(adminMinesBackofficeState.published_at) : "default runtime"}</span></div>
          </article>

          <article className="admin-card">
            <h3>Bozza corrente</h3>
            <div className="admin-metric-row"><span className="list-muted">Grid bozza</span><span className="list-strong">{activeAdminMinesBackofficeConfig.published_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
            {activeAdminMinesBackofficeConfig.published_grid_sizes.map((gridSize) => (
              <div className="admin-metric-row" key={`draft-${gridSize}`}>
                <span className="list-muted">{formatGridChoiceLabel(gridSize)}</span>
                <span>{(activeAdminMinesBackofficeConfig.published_mine_counts[String(gridSize)] ?? []).join(", ")} &middot; default {(activeAdminMinesBackofficeConfig.default_mine_counts[String(gridSize)] ?? "n/a")}</span>
              </div>
            ))}
            <div className="admin-metric-row"><span className="list-muted">Draft by</span><span>{adminMinesBackofficeState?.draft_updated_by_admin_user_id ? shortId(adminMinesBackofficeState.draft_updated_by_admin_user_id) : "default runtime"}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Draft at</span><span>{adminMinesBackofficeState?.draft_updated_at ? formatDateTime(adminMinesBackofficeState.draft_updated_at) : "default runtime"}</span></div>
          </article>

          <article className="admin-card">
            <h3>Fairness live Mines</h3>
            {adminFairnessCurrent ? (
              <>
                <div className="admin-metric-row"><span className="list-muted">Versione</span><span className="list-strong">{adminFairnessCurrent.fairness_version}</span></div>
                <div className="admin-metric-row"><span className="list-muted">Fase</span><span className="list-strong">{adminFairnessCurrent.fairness_phase}</span></div>
                <div className="admin-metric-row"><span className="list-muted">User verifiable</span><span className={`status-inline ${adminFairnessCurrent.user_verifiable ? "success" : "warning"}`}>{adminFairnessCurrent.user_verifiable ? "yes" : "no"}</span></div>
                <div className="admin-metric-row"><span className="list-muted">Seed attivato</span><span>{adminFairnessCurrent.seed_activated_at ? formatDateTime(adminFairnessCurrent.seed_activated_at) : "n/a"}</span></div>
              </>
            ) : (
              <p className="empty-state">Carica lo stato fairness.</p>
            )}
          </article>
        </div>
      ) : null}

      {adminGamesSubsection === "rules" && activeAdminMinesBackofficeConfig ? (
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
                value={activeAdminMinesBackofficeConfig.rules_sections[section.key] ?? ""}
                onChange={(event) => updateAdminRuleSection(section.key, event.target.value)}
                spellCheck={false}
              />
            </article>
          ))}
        </div>
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
        <div className="labels-editor-panel">
          <div className="labels-editor-toolbar">
            <h3>Demo / Real labels</h3>
          </div>
          <div className="labels-editor-table">
            <div className="labels-editor-head">
              <span />
              <span>Demo mode labels</span>
              <span>Real mode labels</span>
            </div>
            {MINES_LABEL_FIELDS.map((field) => (
              <div className="labels-editor-row" key={field.key}>
                <label htmlFor={`demo-${field.key}`}>{field.label}</label>
                <input
                  id={`demo-${field.key}`}
                  value={activeAdminMinesBackofficeConfig.ui_labels.demo?.[field.key] ?? ""}
                  onChange={(event) => updateAdminModeLabel("demo", field.key, event.target.value)}
                />
                <input
                  id={`real-${field.key}`}
                  value={activeAdminMinesBackofficeConfig.ui_labels.real?.[field.key] ?? ""}
                  onChange={(event) => updateAdminModeLabel("real", field.key, event.target.value)}
                />
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {adminGamesSubsection === "tema" ? (
        <MinesThemeEditor
          accessToken={accessToken}
          activeThemeTokens={activeThemeTokens}
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
        />
      ) : null}

      {adminGamesSubsection === "assets" && activeAdminMinesBackofficeConfig ? (
        <div className="board-assets-panel">
          <div className="board-assets-toolbar">
            <div>
              <h3>Board assets</h3>
              <p className="helper">SVG o PNG quadrato per diamante e mina.</p>
            </div>
            <span className="status-inline info">max 150 KB</span>
          </div>
          <div className="board-assets-grid">
            {(
              [
                {
                  key: "safe_icon_data_url" as const,
                  label: "Diamond asset",
                },
                {
                  key: "mine_icon_data_url" as const,
                  label: "Mine asset",
                },
              ] as const
            ).map((assetField) => (
              <article className="board-asset-row" key={assetField.key}>
                <div className="board-asset-preview">
                  {activeAdminMinesBackofficeConfig.board_assets?.[assetField.key] ? (
                    <img
                      src={resolveBackendAssetUrl(
                        activeAdminMinesBackofficeConfig.board_assets[assetField.key] ?? "",
                      )}
                      alt=""
                      aria-hidden="true"
                    />
                  ) : (
                    <span>Default</span>
                  )}
                </div>
                <div className="board-asset-copy">
                  <h3>{assetField.label}</h3>
                  <span className="meta-pill">
                    {activeAdminMinesBackofficeConfig.board_assets?.[assetField.key]
                      ? "Draft ready"
                      : "Default runtime"}
                  </span>
                </div>
                <div className="board-asset-actions">
                  <label className="button-secondary admin-file-label">
                    Carica file
                    <input
                      type="file"
                      accept="image/svg+xml,image/png"
                      className="admin-file-input"
                      onChange={(event) => {
                        const file = event.target.files?.[0] ?? null;
                        void updateAdminBoardAsset(assetField.key, file);
                        event.currentTarget.value = "";
                      }}
                    />
                  </label>
                  <button
                    className="button-ghost"
                    type="button"
                    onClick={() => void updateAdminBoardAsset(assetField.key, null)}
                  >
                    Ripristina default
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}
