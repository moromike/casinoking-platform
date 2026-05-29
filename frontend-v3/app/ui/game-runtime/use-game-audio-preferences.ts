"use client";

import { useCallback, useEffect, useState } from "react";

const EFFECTS_MUTED_STORAGE_KEY = "ck.audio.effectsMuted";
const EFFECTS_VOLUME_STORAGE_KEY = "ck.audio.effectsVolume";
const DEFAULT_EFFECTS_VOLUME = 0.45;

export function useGameAudioPreferences() {
  const [muted, setMutedState] = useState(false);
  const [volume, setVolumeState] = useState(DEFAULT_EFFECTS_VOLUME);

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

  const setMuted = useCallback((nextMuted: boolean) => {
    setMutedState(nextMuted);
    window.localStorage.setItem(EFFECTS_MUTED_STORAGE_KEY, String(nextMuted));
  }, []);

  const setVolume = useCallback((nextVolume: number) => {
    const normalizedVolume = clampVolume(nextVolume);
    setVolumeState(normalizedVolume);
    window.localStorage.setItem(EFFECTS_VOLUME_STORAGE_KEY, String(normalizedVolume));
  }, []);

  return {
    muted,
    setMuted,
    setVolume,
    volume,
  };
}

function clampVolume(value: number) {
  return Math.max(0, Math.min(value, 1));
}
