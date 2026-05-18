"use client";

import type { BoxeRuntimeConfig } from "./use-boxe-runtime";
import type { BoxeCopyKey } from "./boxe-i18n/boxe-copy-defaults";

type BoxeCopy = (key: BoxeCopyKey, placeholders?: Record<string, string>) => string;

export function BoxeSettingsPanel({
  runtimeConfig,
  selectedRows,
  selectedDifficulty,
  disabled,
  copy,
  onRowsChange,
  onDifficultyChange,
}: {
  runtimeConfig: BoxeRuntimeConfig;
  selectedRows: number;
  selectedDifficulty: string;
  disabled: boolean;
  copy: BoxeCopy;
  onRowsChange: (rows: number) => void;
  onDifficultyChange: (difficulty: string) => void;
}) {
  return (
    <section className="boxe-settings-panel" aria-label="BOXE settings">
      <div className="boxe-control-block">
        <span>{copy("settings.rows")}</span>
        <div className="boxe-segmented-control" role="group" aria-label={copy("settings.rows")}>
          {runtimeConfig.rows_enabled.map((rows) => (
            <button
              aria-pressed={rows === selectedRows}
              className={rows === selectedRows ? "active" : ""}
              data-testid={`boxe-rows-${rows}`}
              disabled={disabled}
              key={rows}
              onClick={() => onRowsChange(rows)}
              type="button"
            >
              {rows}
            </button>
          ))}
        </div>
      </div>

      <div className="boxe-control-block">
        <span>{copy("settings.difficulty")}</span>
        <div
          className="boxe-segmented-control difficulty"
          role="group"
          aria-label={copy("settings.difficulty")}
        >
          {runtimeConfig.difficulty_enabled.map((difficulty) => (
            <button
              aria-pressed={difficulty === selectedDifficulty}
              className={difficulty === selectedDifficulty ? "active" : ""}
              data-testid={`boxe-difficulty-${difficulty}`}
              disabled={disabled}
              key={difficulty}
              onClick={() => onDifficultyChange(difficulty)}
              type="button"
            >
              {difficulty.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
