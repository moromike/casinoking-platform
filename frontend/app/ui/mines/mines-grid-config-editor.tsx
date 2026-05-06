"use client";

import { formatGridChoiceLabel } from "@/app/lib/helpers";
import type {
  MinesPresentationConfig,
  MinesRuntimeConfig,
} from "@/app/lib/types";

type MinesGridConfigEditorProps = {
  config: MinesPresentationConfig;
  runtimeConfig: MinesRuntimeConfig;
  onToggleGrid: (gridSize: number) => void;
  onToggleMineCount: (gridSize: number, mineCount: number) => void;
  onSetDefaultMineCount: (gridSize: number, mineCount: number) => void;
};

export function MinesGridConfigEditor({
  config,
  runtimeConfig,
  onToggleGrid,
  onToggleMineCount,
  onSetDefaultMineCount,
}: MinesGridConfigEditorProps) {
  return (
    <div className="grid-config-panel">
      <div className="grid-config-toolbar">
        <h3>Grid &amp; mines</h3>
        <span className="status-inline info">
          {config.published_grid_sizes.length} griglie in bozza
        </span>
      </div>

      <div className="grid-config-list">
        {runtimeConfig.supported_grid_sizes.map((gridSize) => {
          const gridKey = String(gridSize);
          const isPublished = config.published_grid_sizes.includes(gridSize);
          const supportedMineCounts = runtimeConfig.supported_mine_counts[gridKey] ?? [];
          const publishedMineCounts = config.published_mine_counts[gridKey] ?? [];
          const defaultMineCount = config.default_mine_counts[gridKey];

          return (
            <section className="grid-config-row" key={gridSize}>
              <div className="grid-config-title">
                <strong>{formatGridChoiceLabel(gridSize)}</strong>
                <span className="list-muted">{supportedMineCounts.join(", ")}</span>
              </div>

              <label className="admin-toggle-field grid-config-toggle">
                <input
                  className="admin-toggle-input"
                  type="checkbox"
                  checked={isPublished}
                  readOnly
                  onClick={() => onToggleGrid(gridSize)}
                />
                <span className="admin-toggle-switch" aria-hidden="true">
                  <span className="admin-toggle-knob" />
                </span>
                <span className="admin-toggle-text">Bozza</span>
              </label>

              <div className="grid-config-chips">
                {supportedMineCounts.map((mineCount) => {
                  const isSelected = publishedMineCounts.includes(mineCount);
                  return (
                    <button
                      key={`${gridKey}-${mineCount}`}
                      className={isSelected ? "choice-chip active" : "choice-chip"}
                      type="button"
                      disabled={!isPublished}
                      onClick={() => onToggleMineCount(gridSize, mineCount)}
                    >
                      {mineCount}
                    </button>
                  );
                })}
              </div>

              <div className="grid-config-defaults">
                {isPublished && publishedMineCounts.length > 0 ? (
                  publishedMineCounts.map((mineCount) => (
                    <button
                      key={`default-${gridKey}-${mineCount}`}
                      className={
                        defaultMineCount === mineCount
                          ? "choice-chip active"
                          : "choice-chip"
                      }
                      type="button"
                      onClick={() => onSetDefaultMineCount(gridSize, mineCount)}
                    >
                      Default {mineCount}
                    </button>
                  ))
                ) : (
                  <span className="list-muted">Non pubblicata</span>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
