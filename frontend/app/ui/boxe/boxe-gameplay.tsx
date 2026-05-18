"use client";

import { GameShortViewportGate } from "@/app/ui/game-runtime/game-short-viewport-gate";
import type { CSSProperties } from "react";
import type { BoxeRuntimeConfig } from "./use-boxe-runtime";

export function BoxeGameplay({
  runtimeConfig,
}: {
  runtimeConfig: BoxeRuntimeConfig;
}) {
  const defaultMultipliers =
    runtimeConfig.multiplier_paths[String(runtimeConfig.default_rows)]?.[
      runtimeConfig.default_difficulty
    ] ?? [];

  return (
    <section className="boxe-gameplay" aria-labelledby="boxe-gameplay-title">
      <GameShortViewportGate
        title="Ruota il dispositivo"
        description="BOXE richiede piu altezza per giocare in landscape."
      />
      <div className="boxe-gameplay-header">
        <div>
          <span className="eyebrow">{runtimeConfig.title_code}</span>
          <h1 id="boxe-gameplay-title">BOXE gameplay - 3B in arrivo</h1>
        </div>
        <strong>{runtimeConfig.rtp_label} RTP</strong>
      </div>
      <div className="boxe-placeholder-board" aria-label="BOXE placeholder board">
        {Array.from({ length: runtimeConfig.default_rows }, (_, index) => {
          const rowNumber = runtimeConfig.default_rows - index;
          return (
            <div
              className="boxe-placeholder-row"
              key={rowNumber}
              style={{ "--row": rowNumber } as CSSProperties}
            >
              {Array.from({ length: 3 }, (_box, boxIndex) => (
                <span key={boxIndex} />
              ))}
            </div>
          );
        })}
      </div>
      <div className="boxe-runtime-summary">
        <span>Rows {runtimeConfig.rows_enabled.join(", ")}</span>
        <span>Difficulty {runtimeConfig.difficulty_enabled.join(", ")}</span>
        <span>Default {runtimeConfig.default_rows} / {runtimeConfig.default_difficulty}</span>
      </div>
      {defaultMultipliers.length > 0 ? (
        <div className="boxe-multiplier-strip" aria-label="Default multiplier path">
          {defaultMultipliers.map((multiplier, index) => (
            <span key={`${multiplier}-${index}`}>{multiplier}x</span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
