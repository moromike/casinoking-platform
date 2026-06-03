"use client";

import {
  createHiLoCopyResolver,
  type HiLoCopyResolver,
} from "./hi-lo-i18n/hi-lo-copy-defaults";

type HiLoHowToPlayVisualProps = {
  index: number;
  copy?: HiLoCopyResolver;
};

const HI_LO_HOW_TO_RANKS = [
  { rank: "7", suit: "♣", accent: "black" },
  { rank: "Q", suit: "♥", accent: "red" },
  { rank: "K", suit: "♠", accent: "gold" },
] as const;

const HI_LO_HOW_TO_ACTION_KEYS = [
  "how_to_play.visual_action_bet",
  "how_to_play.visual_action_up",
  "how_to_play.visual_action_collect",
] as const;

const HI_LO_HOW_TO_SUIT_KEYS = [
  "how_to_play.visual_suit_clubs",
  "how_to_play.visual_suit_hearts",
  "how_to_play.visual_suit_spades",
] as const;

export function HiLoHowToPlayVisual({ index, copy }: HiLoHowToPlayVisualProps) {
  const resolvedCopy = copy ?? createHiLoCopyResolver("it");
  const state = HI_LO_HOW_TO_RANKS[index] ?? HI_LO_HOW_TO_RANKS[0];
  const actionKey = HI_LO_HOW_TO_ACTION_KEYS[index] ?? HI_LO_HOW_TO_ACTION_KEYS[0];
  const suitKey = HI_LO_HOW_TO_SUIT_KEYS[index] ?? HI_LO_HOW_TO_SUIT_KEYS[0];

  return (
    <div
      className={`game-how-to-play-visual hi-lo-how-to-visual is-${state.accent}`}
      aria-hidden="true"
    >
      <div className="hi-lo-how-to-card">
        <span>{state.rank}</span>
        <em>{state.suit}</em>
        <strong>{resolvedCopy(suitKey)}</strong>
      </div>
      <div className="hi-lo-how-to-action">{resolvedCopy(actionKey)}</div>
    </div>
  );
}
