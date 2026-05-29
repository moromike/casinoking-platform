"use client";

import { useCallback, useEffect, useRef } from "react";
import { resolveBackendAssetUrl } from "@/app/lib/api";

type TitleSoundAssetKind =
  | "audio_safe_reveal"
  | "audio_mine_hit"
  | "audio_collect"
  | "audio_win";

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

const BOXE_AUDIO_EVENT_TO_ASSET: Partial<Record<BoxeAudioEvent, TitleSoundAssetKind>> = {
  safe_reveal: "audio_safe_reveal",
  mine_reveal: "audio_mine_hit",
  cashout_won: "audio_collect",
  top_row_won: "audio_win",
};

export function useBoxeAudio(
  audioPreferences: BoxeAudioPreferences,
  assets: Record<string, string>,
) {
  const audioRefs = useRef<Partial<Record<TitleSoundAssetKind, HTMLAudioElement>>>({});

  useEffect(() => {
    const nextAudioRefs: Partial<Record<TitleSoundAssetKind, HTMLAudioElement>> = {};

    for (const kind of Object.values(BOXE_AUDIO_EVENT_TO_ASSET)) {
      if (!kind) {
        continue;
      }
      const assetUrl = assets[kind];
      if (!assetUrl) {
        continue;
      }
      const audio = new Audio(resolveBackendAssetUrl(assetUrl));
      audio.preload = "auto";
      audio.volume = audioPreferences.volume;
      nextAudioRefs[kind] = audio;
    }

    audioRefs.current = nextAudioRefs;

    return () => {
      for (const audio of Object.values(nextAudioRefs)) {
        audio.pause();
        audio.removeAttribute("src");
        audio.load();
      }
    };
  }, [assets, audioPreferences.volume]);

  const play = useCallback(
    (event: BoxeAudioEvent) => {
      if (typeof window === "undefined") {
        return;
      }
      const assetKind = BOXE_AUDIO_EVENT_TO_ASSET[event];
      const audio = assetKind ? audioRefs.current[assetKind] : undefined;

      window.dispatchEvent(
        new CustomEvent("boxe:audio-event", {
          detail: {
            event,
            muted: audioPreferences.muted,
            volume: audioPreferences.volume,
            hasSoundAsset: Boolean(audio),
          },
        }),
      );

      if (audioPreferences.muted || !audio) {
        return;
      }
      audio.volume = audioPreferences.volume;
      audio.currentTime = 0;
      void audio.play().catch(() => {
        // Browser audio policy must never block gameplay.
      });
    },
    [audioPreferences.muted, audioPreferences.volume],
  );

  return {
    hasAnySound: Object.values(BOXE_AUDIO_EVENT_TO_ASSET).some((kind) =>
      kind ? Boolean(assets[kind]) : false,
    ),
    play,
  };
}
