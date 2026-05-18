"use client";

export type BoxeBoardPick = {
  row: number;
  position: number;
  outcome: "safe" | "mine";
  multiplier: string;
  payout: string;
};

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

  return (
    <section className="boxe-pyramid-board" aria-label="BOXE pyramid board">
      {visualRows.map((row) => {
        const rowPicks = picks.filter((pick) => pick.row === row);
        const rowHasMine = rowPicks.some((pick) => pick.outcome === "mine");
        const revealOpaqueRow = terminalStatus === "failed_mine" && rowHasMine;
        const isActive = activeRow === row && !disabled;

        return (
          <div
            className={[
              "boxe-pyramid-row",
              isActive ? "active" : "",
              revealOpaqueRow ? "loss-row" : "",
            ].filter(Boolean).join(" ")}
            data-row={row}
            key={row}
          >
            {Array.from({ length: 3 }, (_box, position) => {
              const pick = rowPicks.find((item) => item.position === position);
              const state = pick?.outcome ?? (revealOpaqueRow ? "opaque" : "covered");
              const canPick = isActive && state === "covered";
              return (
                <button
                  aria-label={`BOXE row ${row + 1} position ${position + 1}`}
                  className={`boxe-pyramid-cell ${state}`}
                  data-testid={`boxe-cell-${row}-${position}`}
                  disabled={!canPick}
                  key={position}
                  onClick={() => onPick(row, position)}
                  type="button"
                >
                  <span className="boxe-cell-face" aria-hidden="true">
                    {state === "safe" ? "D" : null}
                    {state === "mine" ? "M" : null}
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
