"use client";

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
    <div className="mines-how-to-play-overlay" role="dialog" aria-modal="true">
      <article className="mines-how-to-play-panel" aria-labelledby="mines-how-to-play-title">
        <div className="mines-how-to-play-heading">
          <h2 id="mines-how-to-play-title">{copy.title}</h2>
          <p>{copy.intro}</p>
        </div>
        <div className="mines-how-to-play-grid">
          {copy.cards.map((card, index) => (
            <section className="mines-how-to-play-card" key={`${index}-${card.title}`}>
              <span className="mines-how-to-play-step">{index + 1}</span>
              <h3>{card.title}</h3>
              <p>{card.text}</p>
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
