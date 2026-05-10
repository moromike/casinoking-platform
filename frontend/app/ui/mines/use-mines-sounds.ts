"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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

const EFFECTS_MUTED_STORAGE_KEY = "ck.audio.effectsMuted";
const EFFECTS_VOLUME_STORAGE_KEY = "ck.audio.effectsVolume";
const DEFAULT_EFFECTS_VOLUME = 0.45;

export function useMinesSounds(assets: Record<string, string>) {
  const [muted, setMutedState] = useState(false);
  const [volume, setVolumeState] = useState(DEFAULT_EFFECTS_VOLUME);
  const audioRefs = useRef<Partial<Record<MinesSoundKind, HTMLAudioElement>>>({});

  useEffect(() => {
    const storedMuted = window.localStorage.getItem(EFFECTS_MUTED_STORAGE_KEY);
    const storedVolume = window.localStorage.getItem(EFFECTS_VOLUME_STORAGE_KEY);
    setMutedState(storedMuted === "true");
    if (storedVolume !== null) {
      const parsedVolume = Number.parseFloat(storedVolume);
      if (Number.isFinite(parsedVolume)) {
        setVolumeState(clampVolume(parsedVolume));
      }
    }
  }, []);

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

  const setMuted = useCallback((nextMuted: boolean) => {
    setMutedState(nextMuted);
    window.localStorage.setItem(EFFECTS_MUTED_STORAGE_KEY, String(nextMuted));
  }, []);

  const setVolume = useCallback((nextVolume: number) => {
    const normalizedVolume = clampVolume(nextVolume);
    setVolumeState(normalizedVolume);
    window.localStorage.setItem(EFFECTS_VOLUME_STORAGE_KEY, String(normalizedVolume));
  }, []);

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
    muted,
    play,
    setMuted,
    setVolume,
    volume,
  };
}

function extractSoundAssets(assets: Record<string, string>): MinesSoundAssets {
  return Object.fromEntries(
    SOUND_KINDS.map((kind) => [kind, assets[kind]]).filter(([, value]) => Boolean(value)),
  ) as MinesSoundAssets;
}

function clampVolume(value: number) {
  return Math.max(0, Math.min(value, 1));
}
