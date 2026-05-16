"use client";

import { useState } from "react";
import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset, TitleThemeSkin } from "@/app/lib/types";

const MINES_THEME_COLOR_FIELDS: Array<{ key: string; label: string }> = [
  { key: "--ck-bg", label: "Background" },
  { key: "--ck-surface", label: "Surface" },
  { key: "--ck-surface-strong", label: "Surface strong" },
  { key: "--ck-fg", label: "Foreground" },
  { key: "--ck-muted", label: "Muted" },
  { key: "--ck-accent", label: "Accent" },
  { key: "--ck-accent-strong", label: "Accent strong" },
  { key: "--ck-good", label: "Good" },
  { key: "--ck-danger", label: "Danger" },
];

const MINES_THEME_TEXT_FIELDS: Array<{ key: string; label: string }> = [
  { key: "--ck-border", label: "Border" },
  { key: "--ck-radius-panel", label: "Radius panel" },
  { key: "--ck-radius-cell", label: "Radius cell" },
  { key: "--ck-shadow-panel", label: "Shadow panel" },
  { key: "--ck-font-family", label: "Font family" },
];

export const MINES_THEME_DEFAULT_TOKENS: Record<string, string> = {
  "--ck-bg": "#09090f",
  "--ck-surface": "#181924",
  "--ck-surface-strong": "#252752",
  "--ck-fg": "#f0f4f7",
  "--ck-muted": "#d8e2eb",
  "--ck-accent": "#56dc49",
  "--ck-accent-strong": "#8ef59b",
  "--ck-good": "#3de7d1",
  "--ck-danger": "#ff764e",
  "--ck-border": "rgba(96, 224, 124, 0.14)",
  "--ck-radius-panel": "20px",
  "--ck-radius-cell": "16px",
  "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.34)",
  "--ck-font-family": "inherit",
};

const MINES_THEME_PRESETS: Array<{
  code: string;
  label: string;
  tokens: Record<string, string>;
}> = [
  {
    code: "classic",
    label: "Classic",
    tokens: MINES_THEME_DEFAULT_TOKENS,
  },
  {
    code: "obsidian",
    label: "Obsidian",
    tokens: {
      "--ck-bg": "#06080d",
      "--ck-surface": "#10151d",
      "--ck-surface-strong": "#1c2530",
      "--ck-fg": "#f4f7fb",
      "--ck-muted": "#9eaec1",
      "--ck-accent": "#f0c95a",
      "--ck-accent-strong": "#ffe48a",
      "--ck-good": "#54d6a2",
      "--ck-danger": "#ff6470",
      "--ck-border": "rgba(240, 201, 90, 0.2)",
      "--ck-radius-panel": "16px",
      "--ck-radius-cell": "14px",
      "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.42)",
      "--ck-font-family": "inherit",
    },
  },
  {
    code: "lagoon",
    label: "Lagoon",
    tokens: {
      "--ck-bg": "#061a1f",
      "--ck-surface": "#0d2930",
      "--ck-surface-strong": "#12434c",
      "--ck-fg": "#eefbff",
      "--ck-muted": "#9fd0d8",
      "--ck-accent": "#4fd3ff",
      "--ck-accent-strong": "#8df0ff",
      "--ck-good": "#6ef0bb",
      "--ck-danger": "#ff8d5c",
      "--ck-border": "rgba(79, 211, 255, 0.22)",
      "--ck-radius-panel": "18px",
      "--ck-radius-cell": "16px",
      "--ck-shadow-panel": "0 18px 34px rgba(0, 35, 43, 0.42)",
      "--ck-font-family": "inherit",
    },
  },
  {
    code: "velvet",
    label: "Velvet",
    tokens: {
      "--ck-bg": "#140910",
      "--ck-surface": "#21111d",
      "--ck-surface-strong": "#361d32",
      "--ck-fg": "#fff4fb",
      "--ck-muted": "#d8b7ca",
      "--ck-accent": "#ff7ab8",
      "--ck-accent-strong": "#ffc1df",
      "--ck-good": "#8fe08e",
      "--ck-danger": "#ffb15c",
      "--ck-border": "rgba(255, 122, 184, 0.22)",
      "--ck-radius-panel": "22px",
      "--ck-radius-cell": "18px",
      "--ck-shadow-panel": "0 18px 34px rgba(54, 8, 37, 0.42)",
      "--ck-font-family": "inherit",
    },
  },
];

export const MINES_ADVANCED_SKIN_DEFAULT: TitleThemeSkin = {
  title_render_mode: "text",
  button_density: "default",
  button_radius: "rounded",
  button_style: "raised",
  button_emphasis: "primary",
  game_area_background_fit: "cover",
  game_area_background_position: "center",
  game_area_overlay: "medium",
};

export type MinesSkinAssetKind =
  | "title_logo"
  | "game_area_background"
  | "cell_face_down_background";

type MinesSkinFieldKey = keyof TitleThemeSkin;

const MINES_SKIN_ASSET_SPECS: Array<{
  kind: MinesSkinAssetKind;
  label: string;
  guidance: string;
  maxBytes: number;
  previewClassName: string;
}> = [
  {
    kind: "title_logo",
    label: "Title logo",
    guidance: "PNG/WebP, consigliato 720 x 180 px, max 150 KB.",
    maxBytes: 150 * 1024,
    previewClassName: "skin-asset-preview-logo",
  },
  {
    kind: "game_area_background",
    label: "Game area background",
    guidance: "PNG/WebP, consigliato 1280 x 720 px, max 400 KB.",
    maxBytes: 400 * 1024,
    previewClassName: "skin-asset-preview-background",
  },
  {
    kind: "cell_face_down_background",
    label: "Closed cell texture",
    guidance: "PNG/WebP, consigliato 256 x 256 px, max 256 KB.",
    maxBytes: 256 * 1024,
    previewClassName: "skin-asset-preview-cell",
  },
];

const MINES_SKIN_IMAGE_MIME_TYPES = ["image/png", "image/webp"];

type ThemeEditorStatus = {
  label: string;
  toneClass: string;
};

type MinesThemeEditorProps = {
  accessToken: string | null;
  activeThemeTokens: Record<string, string>;
  activeThemeSkin: TitleThemeSkin | null;
  titleAssets: TitleAsset[];
  busyAction: string | null;
  canSaveThemeDraft: boolean;
  canPublishThemeLive: boolean;
  hasThemeState: boolean;
  themeEditorStatus: ThemeEditorStatus;
  onLoadTheme: () => void;
  onSaveTheme: () => void;
  onPublishTheme: () => void;
  onApplyTokens: (tokens: Record<string, string>) => void;
  onUpdateToken: (key: string, value: string) => void;
  onUpdateSkinField: <Key extends MinesSkinFieldKey>(
    key: Key,
    value: TitleThemeSkin[Key],
  ) => void;
  onUploadSkinAsset: (kind: MinesSkinAssetKind, file: File | null) => void;
  onDeleteSkinAsset: (kind: MinesSkinAssetKind) => void;
};

export function MinesThemeEditor({
  accessToken,
  activeThemeTokens,
  activeThemeSkin,
  titleAssets,
  busyAction,
  canSaveThemeDraft,
  canPublishThemeLive,
  hasThemeState,
  themeEditorStatus,
  onLoadTheme,
  onSaveTheme,
  onPublishTheme,
  onApplyTokens,
  onUpdateToken,
  onUpdateSkinField,
  onUploadSkinAsset,
  onDeleteSkinAsset,
}: MinesThemeEditorProps) {
  const [skinAssetError, setSkinAssetError] = useState<string | null>(null);
  const skin = activeThemeSkin ?? MINES_ADVANCED_SKIN_DEFAULT;

  function handleSkinUpload(kind: MinesSkinAssetKind, file: File | null) {
    setSkinAssetError(null);
    if (!file) {
      return;
    }
    const spec = MINES_SKIN_ASSET_SPECS.find((item) => item.kind === kind);
    if (!spec) {
      return;
    }
    if (!MINES_SKIN_IMAGE_MIME_TYPES.includes(file.type)) {
      setSkinAssetError("File non caricato: usa PNG o WebP.");
      return;
    }
    if (file.size > spec.maxBytes) {
      setSkinAssetError(
        `File non caricato: pesa ${formatBytes(file.size)}. ${spec.label} accetta massimo ${formatBytes(spec.maxBytes)}.`,
      );
      return;
    }
    onUploadSkinAsset(kind, file);
  }

  return (
    <div className="theme-editor-panel">
      <div className="theme-editor-toolbar">
        <div className="theme-editor-status">
          <span className={`status-inline ${themeEditorStatus.toneClass}`}>
            {hasThemeState ? themeEditorStatus.label : "Tema non caricato"}
          </span>
        </div>
        <div className="theme-editor-actions">
          <button
            className="button-secondary"
            type="button"
            disabled={!accessToken || busyAction !== null}
            onClick={onLoadTheme}
          >
            {busyAction === "admin-theme-load" ? "Carico tema..." : "Ricarica tema"}
          </button>
          <button
            className="button"
            type="button"
            disabled={!canSaveThemeDraft}
            onClick={onSaveTheme}
          >
            {busyAction === "admin-theme-save" ? "Salvo bozza..." : "Salva bozza"}
          </button>
          <button
            className="button"
            type="button"
            disabled={!canPublishThemeLive}
            onClick={onPublishTheme}
          >
            {busyAction === "admin-theme-publish" ? "Pubblico live..." : "Pubblica live"}
          </button>
        </div>
      </div>

      <section className="theme-editor-section">
        <h3>Preset skin</h3>
        <div className="theme-preset-grid">
          {MINES_THEME_PRESETS.map((preset) => (
            <button
              className="theme-preset-button"
              key={preset.code}
              type="button"
              onClick={() => onApplyTokens(preset.tokens)}
            >
              <strong>{preset.label}</strong>
              <span className="theme-preset-swatches">
                {[
                  "--ck-bg",
                  "--ck-surface",
                  "--ck-accent",
                  "--ck-good",
                  "--ck-danger",
                ].map((tokenKey) => (
                  <span
                    aria-hidden="true"
                    className="legend-swatch"
                    key={`${preset.code}-${tokenKey}`}
                    style={{
                      background: preset.tokens[tokenKey],
                      borderColor: preset.tokens["--ck-border"],
                    }}
                  />
                ))}
              </span>
            </button>
          ))}
        </div>
      </section>
      <section className="theme-editor-section">
        <h3>Colori</h3>
        <div className="theme-token-grid">
          {MINES_THEME_COLOR_FIELDS.map((field) => (
            <label className="theme-token-field" htmlFor={`theme-${field.key}`} key={field.key}>
              <span>{field.label}</span>
              <input
                id={`theme-${field.key}`}
                type="color"
                value={activeThemeTokens[field.key] ?? "#000000"}
                onChange={(event) => onUpdateToken(field.key, event.target.value)}
              />
            </label>
          ))}
        </div>
      </section>
      <section className="theme-editor-section">
        <h3>Radius, ombre e font</h3>
        <div className="field-grid">
          {MINES_THEME_TEXT_FIELDS.map((field) => (
            <div className="field" key={field.key}>
              <label htmlFor={`theme-${field.key}`}>{field.label}</label>
              <input
                id={`theme-${field.key}`}
                type="text"
                value={activeThemeTokens[field.key] ?? ""}
                onChange={(event) => onUpdateToken(field.key, event.target.value)}
              />
            </div>
          ))}
        </div>
      </section>
      <section className="theme-editor-section">
        <h3>Skin avanzata</h3>
        <div className="field-grid two-up">
              <div className="field">
                <label htmlFor="skin-title-render-mode">Titolo</label>
                <select
                  id="skin-title-render-mode"
                  value={skin.title_render_mode}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "title_render_mode",
                      event.target.value as TitleThemeSkin["title_render_mode"],
                    )
                  }
                >
                  <option value="text">Testo</option>
                  <option value="image">Immagine</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-game-area-fit">Sfondo board</label>
                <select
                  id="skin-game-area-fit"
                  value={skin.game_area_background_fit}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "game_area_background_fit",
                      event.target.value as TitleThemeSkin["game_area_background_fit"],
                    )
                  }
                >
                  <option value="cover">Cover</option>
                  <option value="contain">Contain</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-game-area-position">Posizione sfondo</label>
                <select
                  id="skin-game-area-position"
                  value={skin.game_area_background_position}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "game_area_background_position",
                      event.target.value as TitleThemeSkin["game_area_background_position"],
                    )
                  }
                >
                  <option value="center">Center</option>
                  <option value="top">Top</option>
                  <option value="bottom">Bottom</option>
                  <option value="left">Left</option>
                  <option value="right">Right</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-game-area-overlay">Overlay</label>
                <select
                  id="skin-game-area-overlay"
                  value={skin.game_area_overlay}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "game_area_overlay",
                      event.target.value as TitleThemeSkin["game_area_overlay"],
                    )
                  }
                >
                  <option value="none">None</option>
                  <option value="light">Light</option>
                  <option value="medium">Medium</option>
                  <option value="strong">Strong</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-button-density">Button density</label>
                <select
                  id="skin-button-density"
                  value={skin.button_density}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "button_density",
                      event.target.value as TitleThemeSkin["button_density"],
                    )
                  }
                >
                  <option value="compact">Compact</option>
                  <option value="default">Default</option>
                  <option value="large">Large</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-button-radius">Button radius</label>
                <select
                  id="skin-button-radius"
                  value={skin.button_radius}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "button_radius",
                      event.target.value as TitleThemeSkin["button_radius"],
                    )
                  }
                >
                  <option value="square">Square</option>
                  <option value="soft">Soft</option>
                  <option value="rounded">Rounded</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-button-style">Button style</label>
                <select
                  id="skin-button-style"
                  value={skin.button_style}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "button_style",
                      event.target.value as TitleThemeSkin["button_style"],
                    )
                  }
                >
                  <option value="flat">Flat</option>
                  <option value="outlined">Outlined</option>
                  <option value="raised">Raised</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="skin-button-emphasis">Button emphasis</label>
                <select
                  id="skin-button-emphasis"
                  value={skin.button_emphasis}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "button_emphasis",
                      event.target.value as TitleThemeSkin["button_emphasis"],
                    )
                  }
                >
                  <option value="primary">Primary</option>
                  <option value="secondary">Secondary</option>
                  <option value="danger">Danger</option>
                  <option value="neutral">Neutral</option>
                </select>
              </div>
        </div>
        <div className="skin-preview-strip" aria-hidden="true">
          <button className="button skin-preview-button" type="button">
            Bet
          </button>
          <button className="button-secondary skin-preview-button" type="button">
            Collect
          </button>
        </div>
      </section>
      <section className="theme-editor-section">
        <h3>Skin assets</h3>
        {skinAssetError ? <p className="status-message error">{skinAssetError}</p> : null}
        <div className="board-assets-grid">
              {MINES_SKIN_ASSET_SPECS.map((spec) => {
                const asset =
                  titleAssets.find((item) => item.asset_kind === spec.kind) ?? null;
                const resolvedUrl = asset ? resolveBackendAssetUrl(asset.public_url) : null;
                return (
                  <article className="board-asset-row skin-asset-row" key={spec.kind}>
                    <div className={`board-asset-preview skin-asset-preview ${spec.previewClassName}`}>
                      {resolvedUrl ? <img src={resolvedUrl} alt="" /> : <span>Nessun asset</span>}
                    </div>
                    <div className="board-asset-copy skin-asset-copy">
                      <h3>{spec.label}</h3>
                      <p>
                        {asset
                          ? `${asset.mime} - ${formatBytes(asset.byte_size)}`
                          : spec.guidance}
                      </p>
                    </div>
                    <div className="board-asset-actions">
                      <label className="button-secondary admin-file-label">
                        Upload
                        <input
                          type="file"
                          accept="image/png,image/webp"
                          className="admin-file-input"
                          disabled={busyAction !== null}
                          onChange={(event) => {
                            const file = event.target.files?.[0] ?? null;
                            handleSkinUpload(spec.kind, file);
                            event.currentTarget.value = "";
                          }}
                        />
                      </label>
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={!asset || busyAction !== null}
                        onClick={() => onDeleteSkinAsset(spec.kind)}
                      >
                        Rimuovi
                      </button>
                    </div>
                  </article>
                );
              })}
        </div>
      </section>
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}
