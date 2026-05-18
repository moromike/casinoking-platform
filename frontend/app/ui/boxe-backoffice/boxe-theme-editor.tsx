"use client";

type BoxeThemeState = {
  title_code: string;
  published: { tokens: Record<string, string>; skin?: unknown | null };
  draft: { tokens: Record<string, string>; skin?: unknown | null };
  has_unpublished_changes: boolean;
  published_updated_by_admin_user_id?: string | null;
  draft_updated_by_admin_user_id?: string | null;
  draft_updated_at?: string | null;
  published_at?: string | null;
};

type BoxeThemeEditorProps = {
  accessToken: string | null;
  busyAction: string | null;
  draftTokens: Record<string, string> | null;
  hasThemeState: boolean;
  hasLocalUnsavedChanges: boolean;
  themeState: BoxeThemeState | null;
  onApplyPreset: (tokens: Record<string, string>) => void;
  onLoadTheme: () => void;
  onPublishTheme: () => void;
  onSaveTheme: () => void;
  onUpdateToken: (key: string, value: string) => void;
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

export type { BoxeThemeState };

export function BoxeThemeEditor({
  accessToken,
  busyAction,
  draftTokens,
  hasThemeState,
  hasLocalUnsavedChanges,
  themeState,
  onApplyPreset,
  onLoadTheme,
  onPublishTheme,
  onSaveTheme,
  onUpdateToken,
}: BoxeThemeEditorProps) {
  const tokens = draftTokens ?? BOXE_THEME_DEFAULT_TOKENS;
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

  return (
    <article className="admin-card" data-testid="boxe-theme-editor">
      <div className="admin-card-heading">
        <div>
          <h3>Theme</h3>
          <p>BOXE uses the shared Title theme token allowlist. Advanced skin is out of scope v1.</p>
        </div>
        <span className="status-inline info">{statusLabel}</span>
      </div>
      <div className="editor-command-bar">
        <button
          className="button-secondary"
          type="button"
          disabled={!accessToken || busyAction !== null}
          onClick={onLoadTheme}
        >
          {busyAction === "admin-boxe-theme-load" ? "Loading theme..." : "Load theme"}
        </button>
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
      </div>

      {!hasThemeState ? (
        <p className="empty-state">Load the theme to edit BOXE title tokens.</p>
      ) : (
        <div className="stack">
          <section className="theme-editor-section">
            <h4>Presets</h4>
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
                    {["--ck-bg", "--ck-surface", "--ck-accent", "--ck-good"].map((tokenKey) => (
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
            <h4>Colors</h4>
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
            <h4>Radius, shadows, and font</h4>
            <div className="field-grid">
              {BOXE_THEME_TEXT_FIELDS.map((field) => (
                <label className="field" htmlFor={`boxe-theme-${field.key}`} key={field.key}>
                  <span>{field.label}</span>
                  <input
                    id={`boxe-theme-${field.key}`}
                    type="text"
                    value={tokens[field.key] ?? ""}
                    onChange={(event) => onUpdateToken(field.key, event.target.value)}
                  />
                </label>
              ))}
            </div>
          </section>
        </div>
      )}
    </article>
  );
}
