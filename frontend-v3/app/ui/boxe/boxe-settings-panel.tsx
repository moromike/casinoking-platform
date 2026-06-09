"use client";

import { GameChipGroup } from "../game-runtime/game-chip-group";
import { GameSettingsPanel } from "../game-runtime/game-settings-panel";
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
    <GameSettingsPanel className="stack mines-control-stack mines-config-sections boxe-settings-panel" ariaLabel="BOXE settings">
      <div className="field mines-config-section boxe-control-block">
        <span>{copy("settings.rows")}</span>
        <GameChipGroup
          ariaLabel={copy("settings.rows")}
          className="choice-chip-row boxe-chip-row boxe-rows-chip-row"
          chipClassName="choice-chip"
          disabled={disabled}
          onChange={onRowsChange}
          options={runtimeConfig.rows_enabled.map((rows) => ({
            label: String(rows),
            value: rows,
            testId: `boxe-rows-${rows}`,
          }))}
          selectedValue={selectedRows}
        />
      </div>

      <div className="field mines-config-section boxe-control-block">
        <span>{copy("settings.difficulty")}</span>
        <GameChipGroup
          ariaLabel={copy("settings.difficulty")}
          className="choice-chip-row boxe-chip-row boxe-difficulty-chip-row"
          chipClassName="choice-chip"
          disabled={disabled}
          onChange={onDifficultyChange}
          options={runtimeConfig.difficulty_enabled.map((difficulty) => ({
            label: difficulty.toUpperCase(),
            value: difficulty,
            testId: `boxe-difficulty-${difficulty}`,
          }))}
          selectedValue={selectedDifficulty}
        />
      </div>
    </GameSettingsPanel>
  );
}
