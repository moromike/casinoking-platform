"use client";

import { GameChipGroup } from "@/app/ui/game-runtime/game-chip-group";
import { GameSettingsPanel } from "@/app/ui/game-runtime/game-settings-panel";
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
    <GameSettingsPanel className="boxe-settings-panel" ariaLabel="BOXE settings">
      <div className="boxe-control-block">
        <span>{copy("settings.rows")}</span>
        <GameChipGroup
          ariaLabel={copy("settings.rows")}
          className="boxe-chip-row boxe-rows-chip-row"
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

      <div className="boxe-control-block">
        <span>{copy("settings.difficulty")}</span>
        <GameChipGroup
          ariaLabel={copy("settings.difficulty")}
          className="boxe-chip-row boxe-difficulty-chip-row"
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
