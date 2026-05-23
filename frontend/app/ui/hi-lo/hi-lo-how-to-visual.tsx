"use client";

type HiLoHowToPlayVisualProps = {
  index: number;
};

const HI_LO_HOW_TO_STATES = [
  { rank: "7", suit: "CLUBS", action: "BET", accent: "black" },
  { rank: "Q", suit: "HEARTS", action: "UP", accent: "red" },
  { rank: "K", suit: "SPADES", action: "COLLECT", accent: "gold" },
] as const;

export function HiLoHowToPlayVisual({ index }: HiLoHowToPlayVisualProps) {
  const state = HI_LO_HOW_TO_STATES[index] ?? HI_LO_HOW_TO_STATES[0];

  return (
    <div
      className={`game-how-to-play-visual hi-lo-how-to-visual is-${state.accent}`}
      aria-hidden="true"
    >
      <div className="hi-lo-how-to-card">
        <span>{state.rank}</span>
        <strong>{state.suit}</strong>
      </div>
      <div className="hi-lo-how-to-action">{state.action}</div>
    </div>
  );
}
