"use client";

import { useCallback, useEffect, useRef } from "react";
import { resolveBackendAssetUrl } from "@/app/lib/api";

export type MinesSoundKind =
  | "audio_safe_reveal"
  | "audio_mine_hit"
  | "audio_collect"
  | "audio_win";

type MinesSoundAssets = Partial<Record<MinesSoundKind, string>>;

const SOUND_KINDS: MinesSoundKind[] = [
  "audio_safe_reveal",
  "audio_mine_hit",
  "audio_collect",
  "audio_win",
];

export function useMinesSounds(
  assets: Record<string, string>,
  audioPreferences: { muted: boolean; volume: number },
) {
  const audioRefs = useRef<Partial<Record<MinesSoundKind, HTMLAudioElement>>>({});
  const { muted, volume } = audioPreferences;

  useEffect(() => {
    const nextAudioRefs: Partial<Record<MinesSoundKind, HTMLAudioElement>> = {};
    const soundAssets = extractSoundAssets(assets);

    for (const kind of SOUND_KINDS) {
      const assetUrl = soundAssets[kind];
      if (!assetUrl) {
        continue;
      }
      const audio = new Audio(resolveBackendAssetUrl(assetUrl));
      audio.preload = "auto";
      audio.volume = volume;
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
  }, [assets, volume]);

  const play = useCallback(
    (kind: MinesSoundKind) => {
      if (muted) {
        return;
      }
      const audio = audioRefs.current[kind];
      if (!audio) {
        return;
      }
      audio.volume = volume;
      audio.currentTime = 0;
      void audio.play().catch(() => {
        // Browser audio policy must never block gameplay.
      });
    },
    [muted, volume],
  );

  return {
    hasAnySound: SOUND_KINDS.some((kind) => Boolean(assets[kind])),
    play,
  };
}

function extractSoundAssets(assets: Record<string, string>): MinesSoundAssets {
  return Object.fromEntries(
    SOUND_KINDS.map((kind) => [kind, assets[kind]]).filter(([, value]) => Boolean(value)),
  ) as MinesSoundAssets;
}
