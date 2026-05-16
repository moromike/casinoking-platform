"use client";

import type { ReactNode } from "react";
import type { GameBootStatus } from "./use-game-launch-context";

export function GameBootDecisionFlow({
  statusKind,
  canRenderBootSurface,
  isRuntimeReady,
  showTableBalanceGate,
  showProviderIntroGate,
  showHowToPlayGate,
  tableGatePageShellClassName,
  pageShellClassName,
  productShellClassName,
  tableGate,
  providerIntro,
  howToPlay,
  errorDialog,
  runtimeOverlay,
  children,
}: {
  statusKind: GameBootStatus["kind"];
  canRenderBootSurface: boolean;
  isRuntimeReady: boolean;
  showTableBalanceGate: boolean;
  showProviderIntroGate: boolean;
  showHowToPlayGate: boolean;
  tableGatePageShellClassName: string;
  pageShellClassName: string;
  productShellClassName: string;
  tableGate: ReactNode;
  providerIntro: ReactNode;
  howToPlay: ReactNode;
  errorDialog: ReactNode;
  runtimeOverlay: ReactNode;
  children: ReactNode;
}) {
  if (!canRenderBootSurface) {
    return null;
  }

  if (showTableBalanceGate) {
    return (
      <GameTableBalanceGate
        pageShellClassName={tableGatePageShellClassName}
        statusKind={statusKind}
      >
        {tableGate}
      </GameTableBalanceGate>
    );
  }

  return (
    <main className={pageShellClassName} data-game-boot-status={statusKind}>
      <section className={productShellClassName}>
        <GameProviderIntroGate active={showProviderIntroGate}>
          {providerIntro}
        </GameProviderIntroGate>
        <GameHowToPlayGate active={showHowToPlayGate}>
          {howToPlay}
        </GameHowToPlayGate>
        {errorDialog}
        {isRuntimeReady ? children : null}
        {runtimeOverlay}
      </section>
    </main>
  );
}

export function GameTableBalanceGate({
  pageShellClassName,
  statusKind,
  children,
}: {
  pageShellClassName: string;
  statusKind: GameBootStatus["kind"];
  children: ReactNode;
}) {
  return (
    <main className={pageShellClassName} data-game-boot-status={statusKind}>
      {children}
    </main>
  );
}

export function GameProviderIntroGate({
  active,
  children,
}: {
  active: boolean;
  children: ReactNode;
}) {
  return active ? <>{children}</> : null;
}

export function GameHowToPlayGate({
  active,
  children,
}: {
  active: boolean;
  children: ReactNode;
}) {
  return active ? <>{children}</> : null;
}
