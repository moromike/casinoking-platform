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
          <h4 id="site-lobby-preview-title">Anteprima lobby player</h4>
          <p>Card compatte ordinate come sul sito</p>
        </div>
        <span className="site-lobby-source">GET /games/library</span>
      </div>

      {libraryMessage ? <p className="site-lobby-status error">{libraryMessage}</p> : null}

      {libraryStatus === "loading" && !hasLibrary ? (
        <div className="site-lobby-empty">Caricamento anteprima lobby...</div>
      ) : null}

      {libraryStatus === "error" && !hasLibrary ? (
        <div className="site-lobby-empty error">L'anteprima lobby non e' disponibile.</div>
      ) : null}

      {hasLibrary && libraryTitles.length === 0 ? (
        <div className="site-lobby-empty">La libreria player non restituisce varianti visibili.</div>
      ) : null}

      {hasLibrary && libraryTitles.length > 0 ? (
        <ol className="site-lobby-preview-list">
          {libraryTitles.map((title, index) => (
            <li className="site-lobby-preview-item site-lobby-preview-card" key={title.title_code}>
              <div className="site-lobby-preview-art" aria-hidden="true">
                <span className="site-lobby-preview-rank">{index + 1}</span>
                <div className="site-lobby-preview-art-copy">
                  <span>{title.engine_display_name}</span>
                  <strong>{title.display_name}</strong>
                </div>
                <div className="site-lobby-preview-board">
                  {Array.from({ length: 9 }, (_, boardIndex) => (
                    <span className={boardIndex === 4 ? "is-gem" : ""} key={boardIndex} />
                  ))}
                </div>
              </div>

              <div className="site-lobby-preview-copy">
                <div className="site-lobby-preview-title">
                  <strong>{title.display_name}</strong>
                  {title.featured ? <span className="status-inline success">In evidenza</span> : null}
                </div>
                <p>{title.description ?? "Nessuna descrizione lobby."}</p>
                <div className="site-lobby-preview-modes" aria-label="Modalita' pubblicate">
                  {title.demo_enabled ? <span>Demo</span> : null}
                  {title.real_enabled ? <span className="is-real">Real</span> : null}
                  {!title.demo_enabled && !title.real_enabled ? <span>Nessuna modalita'</span> : null}
                </div>
                <div className="site-lobby-preview-meta">
                  <span>title_code {title.title_code}</span>
                  <span>engine {title.engine_display_name}</span>
                  <span>ordine {title.position}</span>
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </aside>
  );
}
