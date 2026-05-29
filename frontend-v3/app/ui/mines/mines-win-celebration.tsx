"use client";

const CONFETTI_PIECES = 14;

export function MinesWinCelebration() {
  return (
    <div className="mines-win-celebration" aria-hidden="true">
      {Array.from({ length: CONFETTI_PIECES }, (_, index) => (
        <span className="mines-win-celebration-piece" key={index} />
      ))}
    </div>
  );
}
