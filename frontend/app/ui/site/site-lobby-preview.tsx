export type GameLibraryTitle = {
  title_code: string;
  engine_code: string;
  engine_display_name: string;
  display_name: string;
  catalog_display_name: string;
  description: string | null;
  demo_enabled: boolean;
  real_enabled: boolean;
  featured: boolean;
  position: number;
};

export type GameLibraryResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: GameLibraryTitle[];
};

type SiteLobbyPreviewProps = {
  libraryStatus: "idle" | "loading" | "error";
  libraryMessage: string | null;
  libraryTitles: GameLibraryTitle[];
  hasLibrary: boolean;
};

export function SiteLobbyPreview({
  libraryStatus,
  libraryMessage,
  libraryTitles,
  hasLibrary,
}: SiteLobbyPreviewProps) {
  return (
    <aside className="site-lobby-zone site-lobby-preview-zone" aria-labelledby="site-lobby-preview-title">
      <div className="site-lobby-zone-heading">
        <div>
          <h4 id="site-lobby-preview-title">Lobby preview / order</h4>
          <p>Player library source</p>
        </div>
        <span className="site-lobby-source">GET /games/library</span>
      </div>

      {libraryMessage ? <p className="site-lobby-status error">{libraryMessage}</p> : null}

      {libraryStatus === "loading" && !hasLibrary ? (
        <div className="site-lobby-empty">Loading player lobby preview...</div>
      ) : null}

      {libraryStatus === "error" && !hasLibrary ? (
        <div className="site-lobby-empty error">Player lobby preview could not be loaded.</div>
      ) : null}

      {hasLibrary && libraryTitles.length === 0 ? (
        <div className="site-lobby-empty">No variants are returned by the player library.</div>
      ) : null}

      {hasLibrary && libraryTitles.length > 0 ? (
        <ol className="site-lobby-preview-list">
          {libraryTitles.map((title, index) => (
            <li className="site-lobby-preview-item" key={title.title_code}>
              <span className="site-lobby-preview-rank">{index + 1}</span>
              <div className="site-lobby-preview-copy">
                <div className="site-lobby-preview-title">
                  <strong>{title.display_name}</strong>
                  {title.featured ? <span className="status-inline success">Featured</span> : null}
                </div>
                <span className="mono">{title.title_code}</span>
                <p>{title.description ?? "No lobby description."}</p>
                <div className="site-lobby-preview-meta">
                  <span>{title.engine_display_name}</span>
                  <span>Position {title.position}</span>
                  <span>{formatModes(title)}</span>
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </aside>
  );
}

function formatModes(title: Pick<GameLibraryTitle, "demo_enabled" | "real_enabled">): string {
  if (title.demo_enabled && title.real_enabled) {
    return "Demo + real";
  }
  if (title.demo_enabled) {
    return "Demo";
  }
  if (title.real_enabled) {
    return "Real";
  }
  return "No modes";
}

