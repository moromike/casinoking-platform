"use client";

type MinesBoardAssets = {
  safe_icon_data_url?: string | null;
  mine_icon_data_url?: string | null;
};

type MinesBoardProps = {
  cellCount: number;
  boardSide: number;
  revealedCells: number[];
  minePositions: number[];
  busy: boolean;
  isInteractiveRound: boolean;
  onRevealCell: (cellIndex: number) => void;
  assets?: MinesBoardAssets;
  closed?: boolean;
};

function DiamondIcon() {
  return (
    <svg
      viewBox="0 0 100 100"
      aria-hidden="true"
      className="board-cell-symbol-svg board-cell-symbol-svg-diamond"
      preserveAspectRatio="xMidYMid meet"
    >
      <polygon points="26,18 74,18 86,34 14,34" fill="#f5fbff" />
      <polygon points="14,34 34,58 50,86 26,18" fill="#39c9d3" />
      <polygon points="26,18 50,34 34,58 14,34" fill="#9be8ff" />
      <polygon points="74,18 50,34 66,58 86,34" fill="#59b0ff" />
      <polygon points="86,34 66,58 50,86 74,18" fill="#2f74e4" />
      <polygon points="34,58 50,34 66,58 50,86" fill="#1f56c6" />
      <polygon points="34,58 50,34 26,18 14,34" fill="rgba(255,255,255,0.28)" />
      <polygon points="66,58 50,34 74,18 86,34" fill="rgba(255,255,255,0.14)" />
      <path
        d="M26 18h48l12 16-36 52-36-52Z"
        fill="none"
        stroke="rgba(255,255,255,0.24)"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MineIcon() {
  return (
    <svg
      viewBox="0 0 100 100"
      aria-hidden="true"
      className="board-cell-symbol-svg board-cell-symbol-svg-mine"
      preserveAspectRatio="xMidYMid meet"
    >
      <rect x="10" y="10" width="80" height="80" rx="18" fill="#ff7e57" />
      <rect x="10" y="10" width="80" height="80" rx="18" fill="rgba(255, 184, 160, 0.18)" />
      <text
        x="50"
        y="52"
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="Georgia, Times New Roman, serif"
        fontSize="54"
        fontWeight="700"
        fill="#1e0601"
      >
        M
      </text>
    </svg>
  );
}

function BoardCellSymbol({
  state,
  assets,
}: {
  state: "hidden" | "safe" | "mine";
  assets?: MinesBoardAssets;
}) {
  if (state === "hidden") {
    return null;
  }

  const assetUrl =
    state === "safe" ? assets?.safe_icon_data_url ?? null : assets?.mine_icon_data_url ?? null;
  if (assetUrl) {
    return (
      <img
        className="board-cell-symbol-image"
        src={assetUrl}
        alt=""
        aria-hidden="true"
      />
    );
  }

  return state === "safe" ? <DiamondIcon /> : <MineIcon />;
}

export function MinesBoard({
  cellCount,
  boardSide,
  revealedCells,
  minePositions,
  busy,
  isInteractiveRound,
  onRevealCell,
  assets,
  closed = false,
}: MinesBoardProps) {
  const revealedCellSet = new Set(revealedCells);
  const minePositionSet = new Set(minePositions);

  return (
    <div
      className="mines-board"
      style={{ gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: cellCount }, (_, cellIndex) => {
        const isMine = minePositionSet.has(cellIndex);
        const isRevealed = revealedCellSet.has(cellIndex);
        const state: "hidden" | "safe" | "mine" = isMine ? "mine" : isRevealed ? "safe" : "hidden";

        let className = "board-cell";
        if (state === "safe") {
          className += " revealed-safe";
        } else if (state === "mine") {
          className += " revealed-mine";
        }
        if (closed) {
          className += " closed";
        }

        return (
          <button
            key={`${cellCount}-${cellIndex}`}
            className={className}
            type="button"
            disabled={!isInteractiveRound || isRevealed || busy}
            onClick={() => onRevealCell(cellIndex)}
            aria-label={
              state === "mine"
                ? `Cell ${cellIndex + 1}, mine`
                : state === "safe"
                  ? `Cell ${cellIndex + 1}, safe`
                  : `Cell ${cellIndex + 1}, hidden`
            }
            data-board-state={state}
          >
            <span className="board-cell-index">{String(cellIndex + 1).padStart(2, "0")}</span>
            <span className="board-cell-face">
              <span className="board-cell-face-visual">
                <BoardCellSymbol state={state} assets={assets} />
              </span>
              <span className="board-cell-face-label">
                {state === "mine" ? "MINE" : state === "safe" ? "SAFE" : "PICK"}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
