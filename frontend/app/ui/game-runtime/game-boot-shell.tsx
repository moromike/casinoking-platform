"use client";

import { useEffect, type ReactNode } from "react";
import { TitleThemeProvider } from "@/app/lib/theme/title-theme-provider";
import type { TitleTheme } from "@/app/lib/types";
import type { GameBootStatus } from "./use-game-launch-context";
import { GameBootDecisionFlow } from "./game-boot-decision-flow";
import { useGameAudioPreferences } from "./use-game-audio-preferences";

export function GameBootShell({
  titleCode,
  statusKind,
  canRenderBootSurface,
  isRuntimeReady,
  showTableBalanceGate,
  showProviderIntroGate,
  showHowToPlayGate,
  tableGatePageShellClassName,
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
  showTableBalanceGate: boolean;
  showProviderIntroGate: boolean;
  showHowToPlayGate: boolean;
  tableGatePageShellClassName: string;
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

  return (
    <TitleThemeProvider titleCode={titleCode} onThemeChange={onThemeChange}>
      <GameBootDecisionFlow
        statusKind={statusKind}
        canRenderBootSurface={canRenderBootSurface}
        isRuntimeReady={isRuntimeReady}
        showTableBalanceGate={showTableBalanceGate}
        showProviderIntroGate={showProviderIntroGate}
        showHowToPlayGate={showHowToPlayGate}
        tableGatePageShellClassName={tableGatePageShellClassName}
        pageShellClassName={pageShellClassName}
        productShellClassName={productShellClassName}
        tableGate={tableGate}
        providerIntro={providerIntro}
        howToPlay={howToPlay}
        errorDialog={errorDialog}
        runtimeOverlay={runtimeOverlay}
      >
        {children}
      </GameBootDecisionFlow>
    </TitleThemeProvider>
  );
}
