"use client";

import { useCallback, useEffect, useState } from "react";
import type { TitleTheme } from "@/app/lib/types";
import { ApiRequestError, readErrorMessage } from "@/app/lib/api";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import { GameHowToPlayGate } from "@/app/ui/game-runtime/game-how-to-play-gate";
import { GameProviderBootstrap } from "@/app/ui/game-runtime/game-provider-bootstrap";
import { BOXE_GAME_STORAGE_NAMESPACE } from "@/app/ui/game-runtime/game-storage";
import { useGameLaunchContext } from "@/app/ui/game-runtime/use-game-launch-context";
import { BoxeGameplay } from "./boxe-gameplay";
import { BOXE_TABLE_BALANCE_CONFIG } from "./boxe-table-balance-config";
import { loadBoxeRuntimeConfig, type BoxeRuntimeConfig } from "./use-boxe-runtime";

export function BoxeStandalone() {
  const [runtimeConfig, setRuntimeConfig] = useState<BoxeRuntimeConfig | null>(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [isTableBalanceComplete, setIsTableBalanceComplete] = useState(false);
  const [audioPreferences, setAudioPreferences] = useState({
    muted: false,
    setMuted: (_value: boolean) => {},
    setVolume: (_value: number) => {},
    volume: 0.45,
  });

  const {
    status: bootStatus,
    markRuntimeReady,
    markFatal,
  } = useGameLaunchContext({
    storageNamespace: BOXE_GAME_STORAGE_NAMESPACE,
    missingTitleRedirectTo: "/",
  });

  const handleTitleThemeChange = useCallback((_theme: TitleTheme | null) => {
    setIsTitleThemeResolved(true);
  }, []);

  const isLaunchContextReady =
    bootStatus.kind === "launch_ready" || bootStatus.kind === "runtime_ready";
  const isRuntimeReady = bootStatus.kind === "runtime_ready";
  const canRenderBootSurface =
    isLaunchContextReady || (bootStatus.kind === "fatal" && "request" in bootStatus);
  const titleCode = "request" in bootStatus && bootStatus.request
    ? bootStatus.request.titleCode
    : "boxe001";

  useEffect(() => {
    if (bootStatus.kind !== "launch_ready") {
      return;
    }

    setRuntimeConfig(null);
    setRuntimeError("");
    setIsTitleThemeResolved(false);
    setIsProviderIntroComplete(false);
    setIsHowToPlayComplete(false);
    setIsTableBalanceComplete(false);

    let isMounted = true;
    loadBoxeRuntimeConfig(bootStatus.request.titleCode)
      .then((config) => {
        if (isMounted) {
          setRuntimeConfig(config);
        }
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setRuntimeError(readErrorMessage(error, "BOXE config non disponibile."));
        if (error instanceof ApiRequestError && error.status >= 500) {
          markFatal("runtime");
        }
      });

    return () => {
      isMounted = false;
    };
  }, [bootStatus, markFatal]);

  useEffect(() => {
    if (bootStatus.kind === "launch_ready" && runtimeConfig && isTitleThemeResolved) {
      markRuntimeReady();
    }
  }, [bootStatus.kind, isTitleThemeResolved, markRuntimeReady, runtimeConfig]);

  const showProviderIntroGate = isLaunchContextReady && !isProviderIntroComplete;
  const showHowToPlayGate =
    isRuntimeReady && isProviderIntroComplete && !isHowToPlayComplete;
  const showTableBalanceGate =
    isRuntimeReady &&
    isProviderIntroComplete &&
    isHowToPlayComplete &&
    !isTableBalanceComplete;

  const providerIntro = showProviderIntroGate ? (
    <GameProviderBootstrap
      ready={isRuntimeReady || runtimeError.length > 0}
      onComplete={() => setIsProviderIntroComplete(true)}
    />
  ) : null;

  const howToPlay = showHowToPlayGate ? (
    <GameHowToPlayGate
      title="Come si gioca"
      titleId="boxe-how-to-play-title"
      intro="Punta, scegli una box e incassa quando sei in vantaggio."
      continueLabel="Continua"
      cards={[
        {
          title: "Bet",
          text: "Imposta puntata, righe e difficolta.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={0} />
            </div>
          ),
        },
        {
          title: "Pick",
          text: "Scegli una box nella riga attiva.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={1} />
            </div>
          ),
        },
        {
          title: "Collect",
          text: "Incassa dopo una scelta sicura oppure completa la riga finale per chiudere la mano.",
          visual: (
            <div className="game-how-to-play-mobile-hidden">
              <BoxeHowToPlayVisual index={2} />
            </div>
          ),
        },
      ]}
      onContinue={() => setIsHowToPlayComplete(true)}
    />
  ) : null;

  const tableGate = showTableBalanceGate ? (
    <section className="boxe-gate boxe-table-balance" data-testid="boxe-table-balance-gate">
      <div className="boxe-gate-heading">
        <span className="eyebrow">BOXE</span>
        <h1>Table balance</h1>
      </div>
      <div className="boxe-table-balance-options">
        {BOXE_TABLE_BALANCE_CONFIG.quickAmounts.map((amount) => (
          <span key={amount}>{amount} CHIP</span>
        ))}
      </div>
      <p>Demo boot usa il balance runtime provvisorio. Il cashier reale arriva in Fase 5.</p>
      <button
        className="button boxe-primary-action"
        type="button"
        onClick={() => setIsTableBalanceComplete(true)}
      >
        Continua
      </button>
    </section>
  ) : null;

  const errorDialog = runtimeError ? (
    <div className="boxe-error" role="alert">
      {runtimeError}
    </div>
  ) : null;

  return (
    <GameBootShell
      titleCode={titleCode}
      statusKind={bootStatus.kind}
      canRenderBootSurface={canRenderBootSurface}
      isRuntimeReady={isRuntimeReady}
      showTableBalanceGate={showTableBalanceGate}
      showProviderIntroGate={showProviderIntroGate}
      showHowToPlayGate={showHowToPlayGate}
      tableGatePageShellClassName="page-shell boxe-page-shell"
      pageShellClassName="page-shell boxe-page-shell"
      productShellClassName="boxe-product-shell"
      onThemeChange={handleTitleThemeChange}
      onAudioPreferencesChange={setAudioPreferences}
      tableGate={tableGate}
      providerIntro={providerIntro}
      howToPlay={howToPlay}
      errorDialog={errorDialog}
      runtimeOverlay={null}
    >
      {runtimeConfig ? (
        <BoxeGameplay
          audioPreferences={audioPreferences}
          bootRequest={bootStatus.kind === "runtime_ready" ? bootStatus.request : {
            titleCode,
            forceDemoMode: true,
            previewToken: "",
            isEmbeddedView: false,
            walletSource: null,
          }}
          initialAccessToken={
            bootStatus.kind === "runtime_ready"
              ? bootStatus.storageSnapshot.accessToken
              : ""
          }
          runtimeConfig={runtimeConfig}
        />
      ) : (
        <div className="boxe-loading" role="status">
          Caricamento BOXE...
        </div>
      )}
      <span className="boxe-audio-state" data-muted={audioPreferences.muted} hidden />
    </GameBootShell>
  );
}

function BoxeHowToPlayVisual({ index }: { index: number }) {
  const cardNumber = Math.min(Math.max(index + 1, 1), 3);
  const safeCells =
    cardNumber === 1 ? [12] : cardNumber === 2 ? [11, 12, 13, 17] : [7, 12, 17];
  const mineCells = cardNumber === 3 ? [4, 20] : [];
  const selectedCells = cardNumber === 1 ? [12] : cardNumber === 2 ? [17] : [];
  const cells = Array.from({ length: 25 }, (_, cellIndex) => {
    const isSafe = safeCells.includes(cellIndex);
    const isMine = mineCells.includes(cellIndex);
    const isSelected = selectedCells.includes(cellIndex);
    const state = isMine ? "mine" : isSafe ? "safe" : isSelected ? "selected" : "hidden";

    return <span className={`game-how-to-play-visual-cell is-${state}`} key={cellIndex} />;
  });

  return (
    <div className={`game-how-to-play-visual is-card-${cardNumber}`} aria-hidden="true">
      <div className="game-how-to-play-visual-board">{cells}</div>
      <div className="game-how-to-play-visual-controls">
        <span className="game-how-to-play-visual-control" />
        <span className="game-how-to-play-visual-control is-active" />
        <span className="game-how-to-play-visual-control" />
      </div>
    </div>
  );
}
