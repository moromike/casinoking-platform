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
  const cells = Array.from({ length: 9 }, (_, cellIndex) => {
    const isDiamond = cardNumber === 2 && [1, 4, 7].includes(cellIndex);
    const isMine = cardNumber === 3 && [2, 6].includes(cellIndex);
    const className = [
      "mines-how-to-play-visual-cell",
      isDiamond ? "is-diamond" : "",
      isMine ? "is-mine" : "",
    ]
      .filter(Boolean)
      .join(" ");

    return <span className={className} key={cellIndex} />;
  });

  return (
    <div className={`mines-how-to-play-visual is-card-${cardNumber}`} aria-hidden="true">
      <div className="mines-how-to-play-visual-grid">{cells}</div>
      <div className="mines-how-to-play-visual-side">
        <span className="mines-how-to-play-visual-chip is-wide" />
        <span className="mines-how-to-play-visual-chip" />
        <span className="mines-how-to-play-visual-chip is-accent" />
      </div>
    </div>
  );
}
