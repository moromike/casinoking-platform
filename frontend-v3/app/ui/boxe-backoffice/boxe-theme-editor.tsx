"use client";

import { useState } from "react";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset, TitleThemeSkin } from "@/app/lib/types";

type BoxeThemeState = {
  title_code: string;
  published: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  draft: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  has_unpublished_changes: boolean;
  published_updated_by_admin_user_id?: string | null;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_at?: string | null;
};

type BoxeThemeEditorProps = {
  accessToken: string | null;
  activeThemeSkin: TitleThemeSkin | null;
  busyAction: string | null;
  draftTokens: Record<string, string> | null;
  hasThemeState: boolean;
  hasLocalUnsavedChanges: boolean;
  titleAssets: TitleAsset[];
  themeState: BoxeThemeState | null;
  onApplyPreset: (tokens: Record<string, string>) => void;
  onDeleteSkinAsset: (kind: BoxeSkinAssetKind) => void;
  onLoadTheme: () => void;
  onPublishTheme: () => void;
  onSaveTheme: () => void;
  onUpdateToken: (key: string, value: string) => void;
  onUpdateSkinField: <Key extends BoxeSkinFieldKey>(
    key: Key,
    value: TitleThemeSkin[Key],
  ) => void;
  onUploadSkinAsset: (kind: BoxeSkinAssetKind, file: File | null) => void;
};

const BOXE_THEME_COLOR_FIELDS: Array<{ key: string; label: string }> = [
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

const BOXE_THEME_TEXT_FIELDS: Array<{ key: string; label: string }> = [
  { key: "--ck-border", label: "Border" },
  { key: "--ck-radius-panel", label: "Radius panel" },
  { key: "--ck-radius-cell", label: "Radius cell" },
  { key: "--ck-shadow-panel", label: "Shadow panel" },
  { key: "--ck-font-family", label: "Font family" },
];

const BOXE_THEME_DEFAULT_TOKENS: Record<string, string> = {
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

const BOXE_THEME_PRESETS: Array<{
  code: string;
  label: string;
  tokens: Record<string, string>;
}> = [
  {
    code: "classic",
    label: "Classic",
    tokens: BOXE_THEME_DEFAULT_TOKENS,
  },
  {
    code: "emerald",
    label: "Emerald",
    tokens: {
      "--ck-bg": "#07110f",
      "--ck-surface": "#10201d",
      "--ck-surface-strong": "#173630",
      "--ck-fg": "#f1fbf8",
      "--ck-muted": "#a8c9c0",
      "--ck-accent": "#58d68d",
      "--ck-accent-strong": "#b7f5d0",
      "--ck-good": "#55e0c4",
      "--ck-danger": "#ff5b8d",
      "--ck-border": "rgba(88, 214, 141, 0.22)",
      "--ck-radius-panel": "18px",
      "--ck-radius-cell": "16px",
      "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.36)",
      "--ck-font-family": "inherit",
    },
  },
];

export const BOXE_ADVANCED_SKIN_DEFAULT: TitleThemeSkin = {
  title_render_mode: "text",
  button_density: "default",
  button_radius: "rounded",
  button_style: "raised",
  button_emphasis: "primary",
  game_area_background_fit: "cover",
  game_area_background_position: "center",
  game_area_overlay: "medium",
  closed_cell_background_dominance: "balanced",
};

export type BoxeSkinAssetKind =
  | "title_logo"
  | "game_area_background"
  | "cell_face_down_background";

type BoxeSkinFieldKey = keyof TitleThemeSkin;

const BOXE_SKIN_ASSET_SPECS: Array<{
  kind: BoxeSkinAssetKind;
  label: string;
  guidance: string;
  maxBytes: number;
  previewClassName: string;
}> = [
  {
    kind: "title_logo",
    label: "Title logo",
    guidance: "PNG/WebP, recommended 720 x 180 px, max 150 KB. Rendered contained, no crop or stretch.",
    maxBytes: 150 * 1024,
    previewClassName: "skin-asset-preview-logo",
  },
  {
    kind: "game_area_background",
    label: "Game area background",
    guidance: "PNG/WebP, recommended 1280 x 720 px, max 400 KB. Cover crops, Contain letterboxes; never stretched.",
    maxBytes: 400 * 1024,
    previewClassName: "skin-asset-preview-background",
  },
  {
    kind: "cell_face_down_background",
    label: "Closed box texture",
    guidance: "PNG/WebP, recommended 256 x 256 px, max 256 KB. Rendered cover in each BOXE cell; edges may crop.",
    maxBytes: 256 * 1024,
    previewClassName: "skin-asset-preview-cell",
  },
];

const BOXE_SKIN_IMAGE_MIME_TYPES = ["image/png", "image/webp"];

export type { BoxeThemeState };

export function BoxeThemeEditor({
  accessToken,
  activeThemeSkin,
  busyAction,
  draftTokens,
  hasThemeState,
  hasLocalUnsavedChanges,
  titleAssets,
  themeState,
  onApplyPreset,
  onDeleteSkinAsset,
  onLoadTheme,
  onPublishTheme,
  onSaveTheme,
  onUpdateToken,
  onUpdateSkinField,
  onUploadSkinAsset,
}: BoxeThemeEditorProps) {
  const [skinAssetError, setSkinAssetError] = useState<string | null>(null);
  const tokens = draftTokens ?? BOXE_THEME_DEFAULT_TOKENS;
  const skin = activeThemeSkin ?? BOXE_ADVANCED_SKIN_DEFAULT;
  const canSave = Boolean(accessToken) && busyAction === null && hasLocalUnsavedChanges;
  const canPublish =
    Boolean(accessToken) &&
    busyAction === null &&
    !hasLocalUnsavedChanges &&
    Boolean(themeState?.has_unpublished_changes);
  const statusLabel = !hasThemeState
    ? "Theme not loaded"
    : hasLocalUnsavedChanges
      ? "Unsaved changes"
      : themeState?.has_unpublished_changes
        ? "Draft ready"
        : "Published";
  const isThemeLoaded = hasThemeState && Boolean(draftTokens);

  function handleSkinUpload(kind: BoxeSkinAssetKind, file: File | null) {
    setSkinAssetError(null);
    if (!file) {
      return;
    }
    const spec = BOXE_SKIN_ASSET_SPECS.find((item) => item.kind === kind);
    if (!spec) {
      return;
    }
    if (!BOXE_SKIN_IMAGE_MIME_TYPES.includes(file.type)) {
      setSkinAssetError("File not uploaded: use PNG or WebP.");
      return;
    }
    if (file.size > spec.maxBytes) {
      setSkinAssetError(
        `File not uploaded: it weighs ${formatBytes(file.size)}. ${spec.label} accepts up to ${formatBytes(spec.maxBytes)}.`,
      );
      return;
    }
    onUploadSkinAsset(kind, file);
  }

  return (
    <div className="theme-editor-panel" data-testid="boxe-theme-editor">
      <div className="theme-editor-toolbar">
        <div className="theme-editor-status">
          <span className="status-inline info">{statusLabel}</span>
        </div>
        <div className="theme-editor-actions">
          <button
            className="button-secondary"
            type="button"
            disabled={!accessToken || busyAction !== null}
            onClick={onLoadTheme}
          >
            {busyAction === "admin-boxe-theme-load"
              ? "Loading theme..."
              : isThemeLoaded
                ? "Reload theme"
                : "Load theme"}
          </button>
          {isThemeLoaded ? (
            <>
              <button
                className="button"
                type="button"
                disabled={!canSave}
                onClick={onSaveTheme}
              >
                {busyAction === "admin-boxe-theme-save" ? "Saving draft..." : "Save draft"}
              </button>
              <button
                className="button"
                type="button"
                disabled={!canPublish}
                onClick={onPublishTheme}
              >
                {busyAction === "admin-boxe-theme-publish" ? "Publishing live..." : "Publish live"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      {!isThemeLoaded ? (
        <article className="theme-editor-empty-state" aria-live="polite">
          <p>Load the theme to open the editor.</p>
        </article>
      ) : (
        <>
          <section className="theme-editor-section">
            <h3>Preset skin</h3>
            <div className="theme-preset-grid">
              {BOXE_THEME_PRESETS.map((preset) => (
                <button
                  className="theme-preset-button"
                  key={preset.code}
                  type="button"
                  onClick={() => onApplyPreset(preset.tokens)}
                >
                  <strong>{preset.label}</strong>
                  <span className="theme-preset-swatches">
                    {["--ck-bg", "--ck-surface", "--ck-accent", "--ck-good", "--ck-danger"].map((tokenKey) => (
                      <span
                        aria-hidden="true"
                        className="legend-swatch"
                        key={`${preset.code}-${tokenKey}`}
                        style={{ background: preset.tokens[tokenKey] }}
                      />
                    ))}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="theme-editor-section">
            <h3>Colors</h3>
            <div className="theme-token-grid">
              {BOXE_THEME_COLOR_FIELDS.map((field) => (
                <label className="theme-token-field" htmlFor={`boxe-theme-${field.key}`} key={field.key}>
                  <span>{field.label}</span>
                  <input
                    id={`boxe-theme-${field.key}`}
                    type="color"
                    value={tokens[field.key] ?? "#000000"}
                    onChange={(event) => onUpdateToken(field.key, event.target.value)}
                  />
                </label>
              ))}
            </div>
          </section>

          <section className="theme-editor-section">
            <h3>Radius, shadows, and font</h3>
            <div className="field-grid">
              {BOXE_THEME_TEXT_FIELDS.map((field) => (
                <div className="field" key={field.key}>
                  <label htmlFor={`boxe-theme-${field.key}`}>{field.label}</label>
                  <input
                    id={`boxe-theme-${field.key}`}
                    type="text"
                    value={tokens[field.key] ?? ""}
                    onChange={(event) => onUpdateToken(field.key, event.target.value)}
                  />
                </div>
              ))}
            </div>
          </section>

          <section className="theme-editor-section">
            <h3>Advanced skin</h3>
            <div className="field-grid two-up">
              <div className="field">
                <label htmlFor="boxe-skin-title-render-mode">Title</label>
                <select
                  id="boxe-skin-title-render-mode"
                  value={skin.title_render_mode}
                  onChange={(event) =>
                    onUpdateSkinField(
                      "title_render_mode",
                      event.target.value as TitleThemeSkin["title_render_mode"],
                    )
                  }
                >
                  <option value="text">Text</option>
                  <option value="image">Image</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="boxe-skin-game-area-fit">Board background</label>
                <select
                  id="boxe-skin-game-area-fit"
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
                <label htmlFor="boxe-skin-game-area-position">Background position</label>
                <select
                  id="boxe-skin-game-area-position"
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
                <label htmlFor="boxe-skin-game-area-overlay">Overlay</label>
                <select
                  id="boxe-skin-game-area-overlay"
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
                <label htmlFor="boxe-skin-closed-cell-dominance">Closed boxes</label>
                <select
                  id="boxe-skin-closed-cell-dominance"
                  value={
                    skin.closed_cell_background_dominance ??
                    BOXE_ADVANCED_SKIN_DEFAULT.closed_cell_background_dominance
                  }
                  onChange={(event) =>
                    onUpdateSkinField(
                      "closed_cell_background_dominance",
                      event.target.value as TitleThemeSkin["closed_cell_background_dominance"],
                    )
                  }
                >
                  <option value="subtle">Game background dominant</option>
                  <option value="balanced">Balanced</option>
                  <option value="strong">Cell dominant</option>
                  <option value="solid">Solid cell</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="boxe-skin-button-density">Button density</label>
                <select
                  id="boxe-skin-button-density"
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
                <label htmlFor="boxe-skin-button-radius">Button radius</label>
                <select
                  id="boxe-skin-button-radius"
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
                <label htmlFor="boxe-skin-button-style">Button style</label>
                <select
                  id="boxe-skin-button-style"
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
                <label htmlFor="boxe-skin-button-emphasis">Button emphasis</label>
                <select
                  id="boxe-skin-button-emphasis"
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
              {BOXE_SKIN_ASSET_SPECS.map((spec) => {
                const asset = titleAssets.find((item) => item.asset_kind === spec.kind) ?? null;
                const resolvedUrl = asset ? resolveBackendAssetUrl(asset.public_url) : null;
                return (
                  <article className="board-asset-row skin-asset-row" key={spec.kind}>
                    <div className={`board-asset-preview skin-asset-preview ${spec.previewClassName}`}>
                      {resolvedUrl ? <img src={resolvedUrl} alt="" /> : <span>No asset</span>}
                    </div>
                    <div className="board-asset-copy skin-asset-copy">
                      <h3>{spec.label}</h3>
                      <p>{spec.guidance}</p>
                      <span className="meta-pill">
                        {asset ? `${asset.mime} - ${formatBytes(asset.byte_size)}` : "No asset"}
                      </span>
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
                        Remove
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}
