"use client";

import type { CSSProperties } from "react";

const BOXE_SAFE_SYMBOL_URL = "/game-assets/boxe/diamond_green_v001.png";
const BOXE_MINE_SYMBOL_URL = "/game-assets/boxe/mine_fucsia_002.png";

export type BoxeBoardPick = {
  row: number;
  position: number;
  outcome: "safe" | "mine";
  multiplier: string;
  payout: string;
};

export function getBoxeCellsForRow(row: number, rows: number): number {
  return rows - row + 1;
}

export function BoxePyramidBoard({
  rows,
  picks,
  activeRow,
  disabled,
  terminalStatus,
  onPick,
}: {
  rows: number;
  picks: BoxeBoardPick[];
  activeRow: number | null;
  disabled: boolean;
  terminalStatus: "completed_cashout" | "completed_top_row" | "failed_mine" | null;
  onPick: (row: number, position: number) => void;
}) {
  const visualRows = Array.from({ length: rows }, (_item, index) => rows - index - 1);
  const lastPickedRow = picks.reduce<number | null>(
    (highestRow, pick) => (highestRow === null ? pick.row : Math.max(highestRow, pick.row)),
    null,
  );

  return (
    <section className="boxe-pyramid-board" aria-label="BOXE pyramid board">
      {visualRows.map((row) => {
        const rowPicks = picks.filter((pick) => pick.row === row);
        const cellCount = getBoxeCellsForRow(row, rows);
        const rowHasMine = rowPicks.some((pick) => pick.outcome === "mine");
        const revealOpaqueRow = terminalStatus === "failed_mine" && rowHasMine;
        const isActive = activeRow === row && !disabled;
        const isCompleted = rowPicks.some((pick) => pick.outcome === "safe");
        const isFuture =
          rowPicks.length === 0 &&
          ((activeRow !== null && row > activeRow) ||
            (activeRow === null && lastPickedRow !== null && row > lastPickedRow));

        return (
          <div
            className={[
              "boxe-pyramid-row",
              isActive ? "active" : "",
              isCompleted ? "completed" : "",
              isFuture ? "future" : "",
              revealOpaqueRow ? "loss-row" : "",
            ].filter(Boolean).join(" ")}
            data-row={row}
            key={row}
            style={{ "--boxe-row-cells": cellCount } as CSSProperties}
          >
            {Array.from({ length: cellCount }, (_box, position) => {
              const pick = rowPicks.find((item) => item.position === position);
              const state = pick?.outcome ?? (revealOpaqueRow ? "opaque" : "covered");
              const canPick = isActive && state === "covered";
              return (
                <button
                  aria-label={`BOXE row ${row + 1} position ${position + 1}`}
                  className={`boxe-pyramid-cell ${state}`}
                  data-state={state}
                  data-testid={`boxe-cell-${row}-${position}`}
                  disabled={!canPick}
                  key={position}
                  onClick={() => onPick(row, position)}
                  style={{ "--cell-index": position } as CSSProperties}
                  type="button"
                >
                  <span className="boxe-cell-face" aria-hidden="true">
                    {state === "safe" ? (
                      <img src={BOXE_SAFE_SYMBOL_URL} alt="" draggable={false} />
                    ) : null}
                    {state === "mine" ? (
                      <img src={BOXE_MINE_SYMBOL_URL} alt="" draggable={false} />
                    ) : null}
                  </span>
                </button>
              );
            })}
          </div>
        );
      })}
    </section>
  );
}
