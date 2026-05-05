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
    <div className="stack">
      <article className="admin-card">
        <h3>Grid &amp; mines publication</h3>
      </article>
      <div className="admin-grid admin-grid-three">
        {runtimeConfig.supported_grid_sizes.map((gridSize) => {
          const gridKey = String(gridSize);
          const isPublished = config.published_grid_sizes.includes(gridSize);
          const publishedMineCounts = config.published_mine_counts[gridKey] ?? [];
          const defaultMineCount = config.default_mine_counts[gridKey];

          return (
            <article className="admin-card" key={gridSize}>
              <div className="list-row">
                <h3>{formatGridChoiceLabel(gridSize)}</h3>
                <label className="admin-toggle-field">
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
                  <span className="admin-toggle-text">Includi nella bozza</span>
                </label>
              </div>
              <p className="helper">
                Runtime ufficiale:{" "}
                {(runtimeConfig.supported_mine_counts[gridKey] ?? []).join(", ")}
              </p>
              <div className="choice-chip-row admin-chip-grid">
                {(runtimeConfig.supported_mine_counts[gridKey] ?? []).map(
                  (mineCount) => {
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
                  },
                )}
              </div>
              {isPublished ? (
                <>
                  <p className="helper">
                    Default mine count per {formatGridChoiceLabel(gridSize)}.
                  </p>
                  <div className="choice-chip-row admin-chip-grid">
                    {publishedMineCounts.map((mineCount) => (
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
                    ))}
                  </div>
                </>
              ) : (
                <p className="empty-state">
                  Questa griglia non e&apos; pubblicata nel gioco live.
                </p>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
