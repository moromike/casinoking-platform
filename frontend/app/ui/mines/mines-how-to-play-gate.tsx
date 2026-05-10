"use client";

import { DiamondIcon, MineIcon } from "./mines-board";

type MinesHowToPlayGateProps = {
  copy: {
    title: string;
    intro: string;
    continueLabel: string;
    cards: Array<{
      title: string;
      text: string;
    }>;
  };
  onContinue: () => void;
};

export function MinesHowToPlayGate({ copy, onContinue }: MinesHowToPlayGateProps) {
  return (
    <div
      className="mines-how-to-play-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onContinue}
    >
      <article className="mines-how-to-play-panel" aria-labelledby="mines-how-to-play-title">
        <div className="mines-how-to-play-heading">
          <h2 id="mines-how-to-play-title">{copy.title}</h2>
          <p>{copy.intro}</p>
        </div>
        <div className="mines-how-to-play-grid">
          {copy.cards.map((card, index) => (
            <section className="mines-how-to-play-card" key={`${index}-${card.title}`}>
              <MinesHowToPlayVisual index={index} />
              <div className="mines-how-to-play-copy">
                <span className="mines-how-to-play-step">{index + 1}</span>
                <h3>{card.title}</h3>
                <p>{card.text}</p>
              </div>
            </section>
          ))}
        </div>
        <button className="button mines-how-to-play-continue" type="button" onClick={onContinue}>
          {copy.continueLabel}
        </button>
      </article>
    </div>
  );
}

function MinesHowToPlayVisual({ index }: { index: number }) {
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
      <span className={`mines-how-to-play-visual-cell is-${state}`} key={cellIndex}>
        {state === "safe" ? <DiamondIcon /> : null}
        {state === "mine" ? <MineIcon /> : null}
      </span>
    );
  });

  return (
    <div className={`mines-how-to-play-visual is-card-${cardNumber}`} aria-hidden="true">
      <div className="mines-how-to-play-visual-board">{cells}</div>
      <div className="mines-how-to-play-visual-controls">
        <span className="mines-how-to-play-visual-control" />
        <span className="mines-how-to-play-visual-control is-active" />
        <span className="mines-how-to-play-visual-control" />
      </div>
    </div>
  );
}
