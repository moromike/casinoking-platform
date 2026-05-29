import Link from "next/link";

import { getTitleDetailHref } from "./site-lobby-links";

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
          <h4 id="site-lobby-preview-title">Player lobby preview</h4>
          <p>Compact cards ordered as on the site</p>
        </div>
        <span className="site-lobby-source">GET /games/library</span>
      </div>

      {libraryMessage ? <p className="site-lobby-status error">{libraryMessage}</p> : null}

      {libraryStatus === "loading" && !hasLibrary ? (
        <div className="site-lobby-empty">Loading lobby preview...</div>
      ) : null}

      {libraryStatus === "error" && !hasLibrary ? (
        <div className="site-lobby-empty error">Lobby preview is not available.</div>
      ) : null}

      {hasLibrary && libraryTitles.length === 0 ? (
        <div className="site-lobby-empty">The player library returned no visible variants.</div>
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
                  {title.featured ? <span className="status-inline success">Featured</span> : null}
                </div>
                <p>{title.description ?? "No lobby description."}</p>
                <div className="site-lobby-preview-modes" aria-label="Published modes">
                  {title.demo_enabled ? <span>Demo</span> : null}
                  {title.real_enabled ? <span className="is-real">Real</span> : null}
                  {!title.demo_enabled && !title.real_enabled ? <span>No modes</span> : null}
                </div>
                <div className="site-lobby-preview-meta">
                  <span>title_code {title.title_code}</span>
                  <span>engine {title.engine_display_name}</span>
                  <span>order {title.position}</span>
                </div>
                <div className="site-lobby-preview-asset-link">
                  <span>Icon and assets from game detail</span>
                  <Link
                    className="button-secondary"
                    href={getTitleDetailHref(title.engine_code, title.title_code)}
                  >
                    Open assets
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </aside>
  );
}
