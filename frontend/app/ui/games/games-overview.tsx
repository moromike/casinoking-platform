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
  engineFilterCode?: string;
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string; is_test?: boolean },
  ) => Promise<boolean | void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
  onArchiveTitle?: (title: CatalogTitle) => Promise<void>;
  onRestoreTitle?: (title: CatalogTitle) => Promise<void>;
  onOpenEngine?: (engineCode: string) => void;
};

export function GamesOverview({
  catalog,
  engineFilterCode,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onPreviewTitle,
  onArchiveTitle,
  onRestoreTitle,
  onOpenEngine,
}: GamesOverviewProps) {
  const minesTitles = catalog.titles.filter((title) => title.engine_code === "mines");
  const minesMaster = minesTitles.find((title) => title.is_master) ?? null;
  const minesVariants = minesTitles.filter((title) => !title.is_master);
  const otherTitles = engineFilterCode
    ? catalog.titles.filter((title) => title.engine_code === engineFilterCode && title.engine_code !== "mines")
    : catalog.titles.filter((title) => title.engine_code !== "mines");
  const showMines = !engineFilterCode || engineFilterCode === "mines";
  const hasEngineMatches = showMines ? minesTitles.length > 0 : otherTitles.length > 0;
  const engines = Array.from(
    catalog.titles.reduce((byEngine, title) => {
      const current = byEngine.get(title.engine_code) ?? {
        engineCode: title.engine_code,
        displayName: title.engine.display_name,
        status: title.engine.status,
        master: null as CatalogTitle | null,
        variants: 0,
        siteActive: false,
      };
      if (title.is_master) {
        current.master = title;
      } else {
        current.variants += 1;
      }
      current.siteActive = current.siteActive || title.site_title_status === "active";
      byEngine.set(title.engine_code, current);
      return byEngine;
    }, new Map<string, {
      engineCode: string;
      displayName: string;
      status: string;
      master: CatalogTitle | null;
      variants: number;
      siteActive: boolean;
    }>()),
  ).map(([, engine]) => engine);

  if (!engineFilterCode) {
    return (
      <div className="games-management-panel">
        <section className="games-engine-hub" aria-labelledby="games-engine-hub-title">
          <div className="games-engine-hub-heading">
            <span className="games-section-label">Game engines</span>
            <h4 id="games-engine-hub-title">Games</h4>
          </div>
          <div className="games-engine-list">
            {engines.map((engine) => (
              <article className="games-engine-row" key={engine.engineCode}>
                <div className="games-engine-main">
                  <h5>{engine.displayName}</h5>
                  <p className="mono">{engine.engineCode}</p>
                </div>
                <dl className="games-engine-meta" aria-label={`${engine.displayName} summary`}>
                  <div>
                    <dt>Master</dt>
                    <dd>{engine.master?.display_name ?? "n/a"}</dd>
                  </div>
                  <div>
                    <dt>Variants</dt>
                    <dd>{engine.variants}</dd>
                  </div>
                  <div>
                    <dt>Site</dt>
                    <dd>{engine.siteActive ? "active" : "inactive"}</dd>
                  </div>
                </dl>
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => onOpenEngine?.(engine.engineCode)}
                  disabled={!onOpenEngine}
                >
                  Open {engine.displayName}
                </button>
              </article>
            ))}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="games-management-panel">
      {engineFilterCode && !hasEngineMatches ? (
        <section className="games-empty-state" aria-label="Game category unavailable">
          Game category is unavailable.
        </section>
      ) : null}

      {showMines && minesMaster ? (
        <GameCategoryView
          master={minesMaster}
          variants={minesVariants}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onOpenTitle}
          onDuplicateTitle={onDuplicateTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onPreviewTitle={onPreviewTitle}
          onArchiveTitle={onArchiveTitle}
          onRestoreTitle={onRestoreTitle}
        />
      ) : showMines ? (
        <section className="games-empty-state" aria-label="Mines category unavailable">
          Mines master is not configured.
        </section>
      ) : null}

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
