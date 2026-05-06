"use client";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameStatusBadges } from "./game-status-badges";

type GameMasterCardProps = {
  master: CatalogTitle;
  variantsCount: number;
};

export function GameMasterCard({ master, variantsCount }: GameMasterCardProps) {
  return (
    <section className="games-master-block" aria-labelledby="games-master-title">
      <div className="games-master-main">
        <div className="games-master-heading">
          <span className="games-section-label">Master</span>
          <h5 id="games-master-title">{master.display_name}</h5>
          <p className="mono">{master.title_code}</p>
        </div>
        <GameStatusBadges title={master} includeType />
      </div>

      <dl className="games-master-meta">
        <div>
          <dt>Engine</dt>
          <dd>{master.engine.display_name}</dd>
        </div>
        <div>
          <dt>Variants</dt>
          <dd>{variantsCount}</dd>
        </div>
      </dl>

      <div className="games-master-actions">
        <a
          className="button-secondary"
          href={`/mines?title_code=${encodeURIComponent(master.title_code)}&mode=demo&preview=1`}
          target="_blank"
          rel="noreferrer"
        >
          Preview
        </a>
      </div>
    </section>
  );
}
