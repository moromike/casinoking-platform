"use client";

import { DiamondIcon, MineIcon } from "./mines-board";

export function MinesHowToPlayVisual({ index }: { index: number }) {
  const cardNumber = Math.min(Math.max(index + 1, 1), 3);
  const safeCells =
    cardNumber === 1 ? [] : cardNumber === 2 ? [6, 7, 11, 12, 17] : [6, 12, 17];
  const mineCells = cardNumber === 3 ? [4, 20] : [];
  const selectedCells = cardNumber === 1 ? [12] : [];
  const cells = Array.from({ length: 25 }, (_, cellIndex) => {
    const isSafe = safeCells.includes(cellIndex);
    const isMine = mineCells.includes(cellIndex);
    const isSelected = selectedCells.includes(cellIndex);
    const state = isMine ? "mine" : isSafe ? "safe" : isSelected ? "selected" : "hidden";

    return (
      <span className={`game-how-to-play-visual-cell is-${state}`} key={cellIndex}>
        {state === "safe" ? <DiamondIcon /> : null}
        {state === "mine" ? <MineIcon /> : null}
      </span>
    );
  });

  return (
    <div className={`game-how-to-play-visual is-card-${cardNumber}`} aria-hidden="true">
      <div className="game-how-to-play-visual-board">{cells}</div>
      <div className="game-how-to-play-visual-controls">
        <span className="game-how-to-play-visual-control" />
        <span className="game-how-to-play-visual-control is-active" />
        <span className="game-how-to-play-visual-control" />
      </div>
    </div>
  );
}
