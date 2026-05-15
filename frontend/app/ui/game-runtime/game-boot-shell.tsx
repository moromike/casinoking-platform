"use client";

import { useEffect, type ReactNode } from "react";
import { TitleThemeProvider } from "@/app/lib/theme/title-theme-provider";
import type { TitleTheme } from "@/app/lib/types";
import type { GameBootStatus } from "./use-game-launch-context";
import { useGameAudioPreferences } from "./use-game-audio-preferences";

export function GameBootShell({
  titleCode,
  statusKind,
  canRenderBootSurface,
  isRuntimeReady,
  showTableGate,
  pageShellClassName,
  productShellClassName,
  onThemeChange,
  onAudioPreferencesChange,
  tableGate,
  providerIntro,
  howToPlay,
  errorDialog,
  runtimeOverlay,
  children,
}: {
  titleCode: string;
  statusKind: GameBootStatus["kind"];
  canRenderBootSurface: boolean;
  isRuntimeReady: boolean;
  showTableGate: boolean;
  pageShellClassName: string;
  productShellClassName: string;
  onThemeChange: (theme: TitleTheme | null) => void;
  onAudioPreferencesChange: (audioPreferences: {
    muted: boolean;
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
    volume: number;
  }) => void;
  tableGate: ReactNode;
  providerIntro: ReactNode;
  howToPlay: ReactNode;
  errorDialog: ReactNode;
  runtimeOverlay: ReactNode;
  children: ReactNode;
}) {
  const audioPreferences = useGameAudioPreferences();

  useEffect(() => {
    onAudioPreferencesChange(audioPreferences);
  }, [
    audioPreferences.muted,
    audioPreferences.setMuted,
    audioPreferences.setVolume,
    audioPreferences.volume,
    onAudioPreferencesChange,
  ]);

  if (!canRenderBootSurface) {
    return null;
  }

  if (showTableGate) {
    return (
      <TitleThemeProvider titleCode={titleCode} onThemeChange={onThemeChange}>
        <main className="page-shell mines-launch-gate-page" data-game-boot-status={statusKind}>
          {tableGate}
        </main>
      </TitleThemeProvider>
    );
  }

  return (
    <TitleThemeProvider titleCode={titleCode} onThemeChange={onThemeChange}>
      <main className={pageShellClassName} data-game-boot-status={statusKind}>
        <section className={productShellClassName}>
          {providerIntro}
          {isRuntimeReady ? howToPlay : null}
          {errorDialog}
          {isRuntimeReady ? children : null}
          {runtimeOverlay}
        </section>
      </main>
    </TitleThemeProvider>
  );
}
