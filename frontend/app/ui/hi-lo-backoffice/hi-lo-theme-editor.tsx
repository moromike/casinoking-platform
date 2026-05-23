"use client";

import { useState } from "react";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset, TitleThemeSkin } from "@/app/lib/types";

export type HiLoThemeState = {
  title_code: string;
  published: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  draft: { tokens: Record<string, string>; skin?: TitleThemeSkin | null };
  has_unpublished_changes: boolean;
  published_updated_by_admin_user_id?: string | null;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_at?: string | null;
};

type HiLoThemeEditorProps = {
  accessToken: string | null;
  activeThemeSkin: TitleThemeSkin | null;
  busyAction: string | null;
  draftTokens: Record<string, string> | null;
  hasThemeState: boolean;
  hasLocalUnsavedChanges: boolean;
  titleAssets: TitleAsset[];
  themeState: HiLoThemeState | null;
  onApplyPreset: (tokens: Record<string, string>) => void;
  onDeleteSkinAsset: (kind: HiLoSkinAssetKind) => void;
  onLoadTheme: () => void;
  onPublishTheme: () => void;
  onSaveTheme: () => void;
  onUpdateToken: (key: string, value: string) => void;
  onUpdateSkinField: <Key extends keyof TitleThemeSkin>(
    key: Key,
    value: TitleThemeSkin[Key],
  ) => void;
  onUploadSkinAsset: (kind: HiLoSkinAssetKind, file: File | null) => void;
};

export const HI_LO_ADVANCED_SKIN_DEFAULT: TitleThemeSkin = {
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

const HI_LO_THEME_DEFAULT_TOKENS: Record<string, string> = {
  "--ck-bg": "#07111d",
  "--ck-surface": "#111827",
  "--ck-surface-strong": "#2a171c",
  "--ck-fg": "#fff7ed",
  "--ck-muted": "#f8c7a6",
  "--ck-accent": "#dc2626",
  "--ck-accent-strong": "#f59e0b",
  "--ck-good": "#22c55e",
  "--ck-danger": "#ef4444",
  "--ck-border": "rgba(245, 158, 11, 0.24)",
  "--ck-radius-panel": "22px",
  "--ck-radius-cell": "18px",
  "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.36)",
  "--ck-font-family": "inherit",
};

const HI_LO_THEME_PRESETS = [
  {
    code: "classic",
    label: "Classic HI-LO",
    tokens: HI_LO_THEME_DEFAULT_TOKENS,
  },
  {
    code: "casino-red",
    label: "Casino red",
    tokens: {
      ...HI_LO_THEME_DEFAULT_TOKENS,
      "--ck-bg": "#100f18",
      "--ck-surface": "#1f1720",
      "--ck-surface-strong": "#3a1821",
      "--ck-accent": "#ef4444",
      "--ck-accent-strong": "#facc15",
    },
  },
];

const HI_LO_THEME_COLOR_FIELDS = [
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

const HI_LO_THEME_TEXT_FIELDS = [
  { key: "--ck-border", label: "Border" },
  { key: "--ck-radius-panel", label: "Radius panel" },
  { key: "--ck-radius-cell", label: "Radius card" },
  { key: "--ck-shadow-panel", label: "Shadow panel" },
  { key: "--ck-font-family", label: "Font family" },
];

export type HiLoSkinAssetKind =
  | "title_logo"
  | "game_area_background"
  | "cell_face_down_background";

const HI_LO_SKIN_ASSET_SPECS: Array<{
  kind: HiLoSkinAssetKind;
  label: string;
  guidance: string;
  maxBytes: number;
  previewClassName: string;
}> = [
  {
    kind: "title_logo",
    label: "Title logo",
    guidance: "PNG/WebP, 720 x 180 px, max 150 KB. Rendered contained.",
    maxBytes: 150 * 1024,
    previewClassName: "skin-asset-preview-logo",
  },
  {
    kind: "game_area_background",
    label: "Game area background",
    guidance: "PNG/WebP, 1280 x 720 px, max 400 KB. Cover or contain.",
    maxBytes: 400 * 1024,
    previewClassName: "skin-asset-preview-background",
  },
  {
    kind: "cell_face_down_background",
    label: "Card back texture",
    guidance: "PNG/WebP/SVG, 256 x 384 px, max 256 KB. Rendered cover.",
    maxBytes: 256 * 1024,
    previewClassName: "skin-asset-preview-cell",
  },
];

const HI_LO_SKIN_IMAGE_MIME_TYPES = ["image/png", "image/webp", "image/svg+xml"];

export function HiLoThemeEditor({
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
}: HiLoThemeEditorProps) {
  const [skinAssetError, setSkinAssetError] = useState<string | null>(null);
  const tokens = draftTokens ?? HI_LO_THEME_DEFAULT_TOKENS;
  const skin = activeThemeSkin ?? HI_LO_ADVANCED_SKIN_DEFAULT;
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

  function handleSkinUpload(kind: HiLoSkinAssetKind, file: File | null) {
    setSkinAssetError(null);
    if (!file) {
      return;
    }
    const spec = HI_LO_SKIN_ASSET_SPECS.find((item) => item.kind === kind);
    if (!spec) {
      return;
    }
    if (!HI_LO_SKIN_IMAGE_MIME_TYPES.includes(file.type)) {
      setSkinAssetError("File not uploaded: use PNG, WebP or SVG.");
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
    <div className="theme-editor-panel" data-testid="hi-lo-theme-editor">
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
            {busyAction === "admin-hi-lo-theme-load"
              ? "Loading theme..."
              : isThemeLoaded
                ? "Reload theme"
                : "Load theme"}
          </button>
          {isThemeLoaded ? (
            <>
              <button className="button" type="button" disabled={!canSave} onClick={onSaveTheme}>
                {busyAction === "admin-hi-lo-theme-save" ? "Saving draft..." : "Save draft"}
              </button>
              <button
                className="button"
                type="button"
                disabled={!canPublish}
                onClick={onPublishTheme}
              >
                {busyAction === "admin-hi-lo-theme-publish" ? "Publishing live..." : "Publish live"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      <div className="theme-editor-presets">
        {HI_LO_THEME_PRESETS.map((preset) => (
          <button
            className="button-secondary"
            key={preset.code}
            type="button"
            disabled={!isThemeLoaded || busyAction !== null}
            onClick={() => onApplyPreset(preset.tokens)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {isThemeLoaded ? (
        <>
          <section className="theme-editor-grid">
            <article className="admin-card">
              <h3>Theme tokens</h3>
              <div className="theme-token-grid">
                {HI_LO_THEME_COLOR_FIELDS.map((field) => (
                  <label className="field" key={field.key}>
                    <span>{field.label}</span>
                    <input
                      type="color"
                      value={normalizeColor(tokens[field.key])}
                      onChange={(event) => onUpdateToken(field.key, event.target.value)}
                    />
                  </label>
                ))}
                {HI_LO_THEME_TEXT_FIELDS.map((field) => (
                  <label className="field" key={field.key}>
                    <span>{field.label}</span>
                    <input
                      value={tokens[field.key] ?? ""}
                      onChange={(event) => onUpdateToken(field.key, event.target.value)}
                    />
                  </label>
                ))}
              </div>
            </article>

            <article className="admin-card">
              <h3>Advanced skin</h3>
              <p className="helper">
                Same conceptual skin controls as Mines: title presentation,
                gameplay background, card-back dominance and button treatment.
              </p>
              <div className="theme-token-grid">
                <SkinSelect
                  label="Title presentation"
                  value={skin.title_render_mode}
                  options={["text", "image"]}
                  onChange={(value) => onUpdateSkinField("title_render_mode", value)}
                />
                <SkinSelect
                  label="Table image fit"
                  value={skin.game_area_background_fit}
                  options={["cover", "contain"]}
                  onChange={(value) => onUpdateSkinField("game_area_background_fit", value)}
                />
                <SkinSelect
                  label="Table position"
                  value={skin.game_area_background_position}
                  options={["center", "top", "bottom", "left", "right"]}
                  onChange={(value) => onUpdateSkinField("game_area_background_position", value)}
                />
                <SkinSelect
                  label="Table overlay"
                  value={skin.game_area_overlay}
                  options={["none", "light", "medium", "strong"]}
                  onChange={(value) => onUpdateSkinField("game_area_overlay", value)}
                />
                <SkinSelect
                  label="Card-back dominance"
                  value={skin.closed_cell_background_dominance}
                  options={["subtle", "balanced", "strong", "solid"]}
                  onChange={(value) => onUpdateSkinField("closed_cell_background_dominance", value)}
                />
                <SkinSelect
                  label="Button density"
                  value={skin.button_density}
                  options={["compact", "default", "large"]}
                  onChange={(value) => onUpdateSkinField("button_density", value)}
                />
                <SkinSelect
                  label="Button radius"
                  value={skin.button_radius}
                  options={["square", "soft", "rounded"]}
                  onChange={(value) => onUpdateSkinField("button_radius", value)}
                />
                <SkinSelect
                  label="Button style"
                  value={skin.button_style}
                  options={["flat", "outlined", "raised"]}
                  onChange={(value) => onUpdateSkinField("button_style", value)}
                />
                <SkinSelect
                  label="Button emphasis"
                  value={skin.button_emphasis}
                  options={["primary", "secondary", "danger", "neutral"]}
                  onChange={(value) => onUpdateSkinField("button_emphasis", value)}
                />
              </div>
            </article>
          </section>

          <section className="theme-editor-skin-assets">
            <article className="admin-card">
              <div className="admin-card-heading">
                <div>
                  <h3>Skin assets</h3>
                  <p>Logo, card table background and card-back texture.</p>
                </div>
                {skinAssetError ? <span className="status-inline error">{skinAssetError}</span> : null}
              </div>
              <div className="board-assets-grid">
                {HI_LO_SKIN_ASSET_SPECS.map((spec) => {
                  const asset = titleAssets.find((item) => item.asset_kind === spec.kind);
                  return (
                    <article className="board-asset-row" key={spec.kind}>
                      <div className={`board-asset-preview ${spec.previewClassName}`}>
                        {asset ? (
                          <img src={resolveBackendAssetUrl(asset.public_url)} alt="" aria-hidden="true" />
                        ) : (
                          <span>Default</span>
                        )}
                      </div>
                      <div className="board-asset-copy">
                        <h3>{spec.label}</h3>
                        <p>{spec.guidance}</p>
                      </div>
                      <div className="board-asset-actions">
                        <label className="button-secondary admin-file-label">
                          Upload file
                          <input
                            type="file"
                            accept="image/png,image/webp,image/svg+xml"
                            className="admin-file-input"
                            disabled={busyAction !== null}
                            onChange={(event) => {
                              handleSkinUpload(spec.kind, event.target.files?.[0] ?? null);
                              event.currentTarget.value = "";
                            }}
                          />
                        </label>
                        <button
                          className="button-ghost"
                          type="button"
                          disabled={!asset || busyAction !== null}
                          onClick={() => onDeleteSkinAsset(spec.kind)}
                        >
                          Restore default
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </article>
          </section>
        </>
      ) : null}
    </div>
  );
}

function SkinSelect<TValue extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: TValue;
  options: readonly TValue[];
  onChange: (value: TValue) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value as TValue)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function normalizeColor(value: string | undefined) {
  return /^#[0-9a-fA-F]{6}$/.test(value ?? "") ? value ?? "#000000" : "#000000";
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}
