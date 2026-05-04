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
} from "@/app/lib/types";
import { apiRequest, readErrorMessage } from "@/app/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AdminGamesSubsection = "overview" | "rules" | "configuration" | "labels" | "assets";
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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Phase 3: backoffice config now lives under a Title (engine `mines`,
// title `mines_classic`). The legacy /admin/games/mines/backoffice-config*
// endpoints still work as aliases on the backend, but the frontend talks
// to the new Title-aware paths to avoid lingering on deprecated routes.
const MINES_BACKOFFICE_TITLE_CODE = "mines_classic";
const MINES_BACKOFFICE_CONFIG_PATH = `/admin/games/titles/${MINES_BACKOFFICE_TITLE_CODE}/config`;
const MINES_BACKOFFICE_PUBLISH_PATH = `/admin/games/titles/${MINES_BACKOFFICE_TITLE_CODE}/config/publish`;

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

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Impossibile leggere il file selezionato."));
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("File non valido."));
        return;
      }
      resolve(reader.result);
    };
    reader.readAsDataURL(file);
  });
}

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
  accessToken: string | null;
  runtimeConfig: MinesRuntimeConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: React.Dispatch<React.SetStateAction<MinesRuntimeConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

export function MinesBackofficeEditor({
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
  adminFairnessCurrent,
}: MinesBackofficeEditorProps) {
  const [adminGamesSubsection, setAdminGamesSubsection] =
    useState<AdminGamesSubsection>("overview");
  const [adminMinesBackofficeState, setAdminMinesBackofficeState] =
    useState<MinesBackofficeState | null>(null);
  const [adminMinesBackofficeActiveConfig, setAdminMinesBackofficeActiveConfig] =
    useState<MinesPresentationConfig | null>(null);
  const [hasLocalUnsavedChanges, setHasLocalUnsavedChanges] = useState(false);
  const adminMinesBackofficeActiveConfigRef = useRef<MinesPresentationConfig | null>(null);

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
        MINES_BACKOFFICE_CONFIG_PATH,
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
        MINES_BACKOFFICE_CONFIG_PATH,
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
        MINES_BACKOFFICE_PUBLISH_PATH,
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
    if (!file) {
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
      const dataUrl = await readFileAsDataUrl(file);
      updateAdminMinesBackofficeDraft((draft) => {
        if ((draft.board_assets?.[key] ?? null) === dataUrl) {
          return null;
        }
        return {
          ...draft,
          board_assets: {
            ...(draft.board_assets ?? {
              safe_icon_data_url: null,
              mine_icon_data_url: null,
            }),
            [key]: dataUrl,
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
      <div className="actions">
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

      <div className="admin-subnav">
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
        <div className="stack">
          <article className="admin-card">
            <h3>Rules HTML editor</h3>
          </article>
          {MINES_RULE_SECTION_FIELDS.map((section) => (
            <article className="admin-card admin-editor-card" key={section.key}>
              <div className="list-row">
                <h3>{section.label}</h3>
                <span className="meta-pill">{section.key}</span>
              </div>
              <p className="helper">{section.helper}</p>
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
        <div className="stack">
          <article className="admin-card">
            <h3>Grid &amp; mines publication</h3>
          </article>
          <div className="admin-grid admin-grid-three">
            {runtimeConfig.supported_grid_sizes.map((gridSize) => {
              const gridKey = String(gridSize);
              const isPublished = activeAdminMinesBackofficeConfig.published_grid_sizes.includes(gridSize);
              const publishedMineCounts =
                activeAdminMinesBackofficeConfig.published_mine_counts[gridKey] ?? [];
              const defaultMineCount =
                activeAdminMinesBackofficeConfig.default_mine_counts[gridKey];
              return (
                <article className="admin-card" key={gridSize}>
                  <div className="list-row">
                    <h3>{formatGridChoiceLabel(gridSize)}</h3>
                    <label className="admin-toggle-field">
                      <input
                        className="admin-toggle-input"
                        type="checkbox"
                        checked={isPublished}
                        readOnly
                        onClick={() => toggleAdminPublishedGrid(gridSize)}
                      />
                      <span className="admin-toggle-switch" aria-hidden="true">
                        <span className="admin-toggle-knob" />
                      </span>
                      <span className="admin-toggle-text">Includi nella bozza</span>
                    </label>
                  </div>
                  <p className="helper">
                    Runtime ufficiale: {(runtimeConfig.supported_mine_counts[gridKey] ?? []).join(", ")}
                  </p>
                  <div className="choice-chip-row admin-chip-grid">
                    {(runtimeConfig.supported_mine_counts[gridKey] ?? []).map((mineCount) => {
                      const isSelected = publishedMineCounts.includes(mineCount);
                      return (
                        <button
                          key={`${gridKey}-${mineCount}`}
                          className={isSelected ? "choice-chip active" : "choice-chip"}
                          type="button"
                          disabled={!isPublished}
                          onClick={() => toggleAdminPublishedMineCount(gridSize, mineCount)}
                        >
                          {mineCount}
                        </button>
                      );
                    })}
                  </div>
                  {isPublished ? (
                    <>
                      <p className="helper">
                        Default mine count per {formatGridChoiceLabel(gridSize)}.
                      </p>
                      <div className="choice-chip-row admin-chip-grid">
                        {publishedMineCounts.map((mineCount) => (
                          <button
                            key={`default-${gridKey}-${mineCount}`}
                            className={defaultMineCount === mineCount ? "choice-chip active" : "choice-chip"}
                            type="button"
                            onClick={() => setAdminDefaultMineCount(gridSize, mineCount)}
                          >
                            Default {mineCount}
                          </button>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p className="empty-state">Questa griglia non e&apos; pubblicata nel gioco live.</p>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      ) : null}

      {adminGamesSubsection === "labels" && activeAdminMinesBackofficeConfig ? (
        <div className="admin-grid">
          {(["demo", "real"] as const).map((mode) => (
            <article className="admin-card admin-editor-card" key={mode}>
              <div className="list-row">
                <h3>{mode === "demo" ? "Demo mode labels" : "Real mode labels"}</h3>
                <span className="meta-pill">{mode}</span>
              </div>
              <div className="field-grid">
                {MINES_LABEL_FIELDS.map((field) => (
                  <div className="field" key={`${mode}-${field.key}`}>
                    <label htmlFor={`${mode}-${field.key}`}>{field.label}</label>
                    <input
                      id={`${mode}-${field.key}`}
                      value={activeAdminMinesBackofficeConfig.ui_labels[mode]?.[field.key] ?? ""}
                      onChange={(event) => updateAdminModeLabel(mode, field.key, event.target.value)}
                    />
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {adminGamesSubsection === "assets" && activeAdminMinesBackofficeConfig ? (
        <div className="stack">
          <article className="admin-card">
            <h3>Board assets</h3>
            <p className="helper">
              Carica un asset quadrato SVG o PNG per diamante e mina. Consigliato:
              SVG o PNG trasparente, minimo 256x256, safe area interna 12-15%,
              peso sotto 150 KB.
            </p>
          </article>
          <div className="admin-grid">
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
              <article className="admin-card admin-editor-card" key={assetField.key}>
                <div className="list-row">
                  <h3>{assetField.label}</h3>
                  <span className="meta-pill">
                    {activeAdminMinesBackofficeConfig.board_assets?.[assetField.key]
                      ? "Draft ready"
                      : "Default runtime"}
                  </span>
                </div>
                <div className="admin-board-asset-preview">
                  {activeAdminMinesBackofficeConfig.board_assets?.[assetField.key] ? (
                    <img
                      src={activeAdminMinesBackofficeConfig.board_assets[assetField.key] ?? ""}
                      alt=""
                      aria-hidden="true"
                      className="admin-board-asset-preview-image"
                    />
                  ) : (
                    <span className="empty-state">
                      Nessun asset custom in bozza. Il gioco usa l&apos;icona di default.
                    </span>
                  )}
                </div>
                <div className="actions">
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
