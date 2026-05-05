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
  onUpdateToken,
}: MinesThemeEditorProps) {
  return (
    <div className="stack">
      <article className="admin-card">
        <div className="actions">
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
      </article>

      {hasThemeState ? (
        <article
          className={`admin-card admin-status-banner ${themeEditorStatus.toneClass}`}
          aria-live="polite"
        >
          <span className="admin-status-banner-indicator" aria-hidden="true" />
          <div className="admin-status-banner-copy">
            <span className="meta-pill">Stato tema</span>
            <h3>{themeEditorStatus.label}</h3>
          </div>
        </article>
      ) : null}

      {!activeThemeTokens ? (
        <article className="admin-card">
          <p className="empty-state">Carica il tema per aprire l&apos;editor.</p>
        </article>
      ) : (
        <>
          <article className="admin-card admin-editor-card">
            <h3>Colori</h3>
            <div className="field-grid">
              {MINES_THEME_COLOR_FIELDS.map((field) => (
                <div className="field" key={field.key}>
                  <label htmlFor={`theme-${field.key}`}>{field.label}</label>
                  <input
                    id={`theme-${field.key}`}
                    type="color"
                    value={activeThemeTokens[field.key] ?? "#000000"}
                    onChange={(event) => onUpdateToken(field.key, event.target.value)}
                  />
                </div>
              ))}
            </div>
          </article>
          <article className="admin-card admin-editor-card">
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
          </article>
        </>
      )}
    </div>
  );
}
