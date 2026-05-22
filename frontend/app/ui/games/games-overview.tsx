"use client";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameCategoryView } from "./game-category-view";

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

  const engineTitles = catalog.titles.filter((title) => title.engine_code === engineFilterCode);
  const engineMaster = engineTitles.find((title) => title.is_master) ?? null;
  const engineVariants = engineTitles.filter((title) => !title.is_master);
  const engineDisplayName =
    engineMaster?.engine.display_name ??
    engines.find((engine) => engine.engineCode === engineFilterCode)?.displayName ??
    engineFilterCode;

  return (
    <div className="games-management-panel">
      {engineTitles.length === 0 ? (
        <section className="games-empty-state" aria-label="Game category unavailable">
          Game category is unavailable.
        </section>
      ) : null}

      {engineMaster ? (
        <GameCategoryView
          engineCode={engineFilterCode}
          engineDisplayName={engineDisplayName}
          master={engineMaster}
          variants={engineVariants}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onOpenTitle}
          onDuplicateTitle={onDuplicateTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onPreviewTitle={onPreviewTitle}
          onArchiveTitle={onArchiveTitle}
          onRestoreTitle={onRestoreTitle}
        />
      ) : engineTitles.length > 0 ? (
        <section className="games-empty-state" aria-label={`${engineDisplayName} category unavailable`}>
          {engineDisplayName} master is not configured.
        </section>
      ) : null}
    </div>
  );
}
