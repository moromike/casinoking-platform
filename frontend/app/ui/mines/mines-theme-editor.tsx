"use client";

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

const MINES_THEME_DEFAULT_TOKENS: Record<string, string> = {
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

type ThemeEditorStatus = {
  label: string;
  toneClass: string;
};

type MinesThemeEditorProps = {
  accessToken: string | null;
  activeThemeTokens: Record<string, string> | null;
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
};

export function MinesThemeEditor({
  accessToken,
  activeThemeTokens,
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
}: MinesThemeEditorProps) {
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

      {!activeThemeTokens ? (
        <div className="theme-editor-empty-state">
          <p>Carica il tema per aprire l&apos;editor.</p>
        </div>
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}
