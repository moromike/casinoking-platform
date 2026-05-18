"use client";

import { useCallback } from "react";

export type BoxeAudioEvent =
  | "bet_placed"
  | "safe_reveal"
  | "mine_reveal"
  | "cashout_won"
  | "top_row_won";

export type BoxeAudioPreferences = {
  muted: boolean;
  volume: number;
};

export function useBoxeAudio(audioPreferences: BoxeAudioPreferences) {
  const play = useCallback(
    (event: BoxeAudioEvent) => {
      if (typeof window === "undefined") {
        return;
      }

      window.dispatchEvent(
        new CustomEvent("boxe:audio-event", {
          detail: {
            event,
            muted: audioPreferences.muted,
            volume: audioPreferences.volume,
            hasSoundAsset: false,
          },
        }),
      );

      // BOXE v1 has no uploaded sound assets yet. The event is intentionally
      // silent and testable; future 4B asset work can attach real audio here.
    },
    [audioPreferences.muted, audioPreferences.volume],
  );

  return { play };
}
