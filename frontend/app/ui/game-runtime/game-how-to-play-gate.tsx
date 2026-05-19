"use client";

import type { ReactNode } from "react";

export type GameHowToPlayCard = {
  title: string;
  text: string;
  visual?: ReactNode;
};

type GameHowToPlayGateProps = {
  cards: GameHowToPlayCard[];
  continueLabel: string;
  intro?: string;
  onContinue: () => void;
  title: string;
  titleId?: string;
};

export function GameHowToPlayGate({
  cards,
  continueLabel,
  intro,
  onContinue,
  title,
  titleId = "game-how-to-play-title",
}: GameHowToPlayGateProps) {
  return (
    <div
      className="game-how-to-play-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onContinue}
    >
      <article className="game-how-to-play-panel" aria-labelledby={titleId}>
        <div className="game-how-to-play-heading">
          <h2 id={titleId}>{title}</h2>
          {intro ? <p>{intro}</p> : null}
        </div>
        <div className="game-how-to-play-grid">
          {cards.map((card, index) => (
            <section className="game-how-to-play-card" key={`${index}-${card.title}`}>
              {card.visual}
              <div className="game-how-to-play-copy">
                <span className="game-how-to-play-step">{index + 1}</span>
                <h3>{card.title}</h3>
                <p>{card.text}</p>
              </div>
            </section>
          ))}
        </div>
        <button className="button game-how-to-play-continue" type="button" onClick={onContinue}>
          {continueLabel}
        </button>
      </article>
    </div>
  );
}
