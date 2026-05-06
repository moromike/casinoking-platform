"use client";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameCategoryView } from "./game-category-view";
import { GameStatusBadges } from "./game-status-badges";

type SiteCatalog = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type GamesOverviewProps = {
  catalog: SiteCatalog;
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string },
  ) => Promise<void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
};

export function GamesOverview({
  catalog,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onPreviewTitle,
}: GamesOverviewProps) {
  const minesTitles = catalog.titles.filter((title) => title.engine_code === "mines");
  const minesMaster = minesTitles.find((title) => title.is_master) ?? null;
  const minesVariants = minesTitles.filter((title) => !title.is_master);
  const otherTitles = catalog.titles.filter((title) => title.engine_code !== "mines");

  return (
    <div className="games-management-panel">
      {minesMaster ? (
        <GameCategoryView
          master={minesMaster}
          variants={minesVariants}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onOpenTitle}
          onDuplicateTitle={onDuplicateTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onPreviewTitle={onPreviewTitle}
        />
      ) : (
        <section className="games-empty-state" aria-label="Mines category unavailable">
          Mines master is not configured.
        </section>
      )}

      {otherTitles.length > 0 ? (
        <section className="games-other-engines" aria-labelledby="games-other-engines-title">
          <div className="games-other-engines-heading">
            <h4 id="games-other-engines-title">Other engines</h4>
          </div>
          <div className="games-other-engine-list">
            {otherTitles.map((title) => (
              <article className="games-other-engine-row" key={title.title_code}>
                <div>
                  <h5>{title.display_name}</h5>
                  <p className="mono">{title.title_code}</p>
                </div>
                <div className="games-other-engine-meta">
                  <span className="list-muted">{title.engine.display_name}</span>
                  <GameStatusBadges title={title} includeType />
                </div>
                {onOpenTitle ? (
                  <button
                    className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                    type="button"
                    onClick={() => onOpenTitle(title)}
                  >
                    {selectedTitleCode === title.title_code ? "Detail open" : "Open detail"}
                  </button>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
