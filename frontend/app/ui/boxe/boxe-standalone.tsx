"use client";

import { useCallback, useEffect, useState } from "react";
import type { TitleTheme } from "@/app/lib/types";
import { ApiRequestError, readErrorMessage } from "@/app/lib/api";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import { GameHowToPlayGate } from "@/app/ui/game-runtime/game-how-to-play-gate";
import {
  GameProviderBootstrap,
  GameProviderBootstrapPreload,
} from "@/app/ui/game-runtime/game-provider-bootstrap";
import {
  GameTableBalanceGate,
  type GameTableBalanceConfirmParams,
  type GameTableBalanceWalletSource,
} from "@/app/ui/game-runtime/game-table-balance-gate";
import { BOXE_GAME_STORAGE_NAMESPACE } from "@/app/ui/game-runtime/game-storage";
import { useGameLaunchContext } from "@/app/ui/game-runtime/use-game-launch-context";
import { BoxeGameplay } from "./boxe-gameplay";
import { BOXE_TABLE_BALANCE_CONFIG } from "./boxe-table-balance-config";
import {
  createBoxeAccessSession,
  createBoxeTableSession,
  loadBoxeRuntimeConfig,
  loadBoxeTableSessionLimits,
  type BoxeAccessSession,
  type BoxeRuntimeConfig,
  type BoxeTableSession,
  type BoxeTableSessionLimits,
} from "./use-boxe-runtime";

export function BoxeStandalone() {
  const [runtimeConfig, setRuntimeConfig] = useState<BoxeRuntimeConfig | null>(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [isTableBalanceComplete, setIsTableBalanceComplete] = useState(false);
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<GameTableBalanceWalletSource>("cash");
  const [accessSession, setAccessSession] = useState<BoxeAccessSession | null>(null);
  const [tableSession, setTableSession] = useState<BoxeTableSession | null>(null);
  const [tableSessionLimits, setTableSessionLimits] =
    useState<BoxeTableSessionLimits | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState(
    BOXE_TABLE_BALANCE_CONFIG.defaultEntryAmount,
  );
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
    setAccessSession(null);
    setTableSession(null);
    setTableSessionLimits(null);
    setSelectedTableWalletType(bootStatus.request.walletSource ?? "cash");
    setTableEntryAmount(BOXE_TABLE_BALANCE_CONFIG.defaultEntryAmount);

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

  const isDemoMode =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.forceDemoMode : true;
  const showTableBalanceGate =
    isLaunchContextReady && !isDemoMode && !isTableBalanceComplete;
  const showProviderIntroGate =
    (isLaunchContextReady || bootStatus.kind === "fatal") &&
    !showTableBalanceGate &&
    !isProviderIntroComplete;
  const showHowToPlayGate =
    isRuntimeReady &&
    !showTableBalanceGate &&
    isProviderIntroComplete &&
    !isHowToPlayComplete;
  const lockedTableWalletSource =
    "request" in bootStatus && bootStatus.request && !bootStatus.request.forceDemoMode
      ? bootStatus.request.walletSource
      : null;
  const tableGateToken =
    "storageSnapshot" in bootStatus ? (bootStatus.storageSnapshot?.accessToken ?? "") : "";
  const tableGateTitleCode =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.titleCode : titleCode;
  const tableEntryMaxAmount = tableSessionLimits?.max_table_amount ?? "0";
  const tableAvailableBalance = tableSessionLimits?.wallet_balance_available ?? "0";
  const tableDefaultAmount =
    tableSessionLimits?.default_table_amount ?? BOXE_TABLE_BALANCE_CONFIG.defaultEntryAmount;

  useEffect(() => {
    if (!showTableBalanceGate || !tableGateToken) {
      return;
    }
    let isMounted = true;
    setTableSessionLimits(null);
    loadBoxeTableSessionLimits(tableGateToken, selectedTableWalletType)
      .then((limits) => {
        if (!isMounted) {
          return;
        }
        setTableSessionLimits(limits);
        setTableEntryAmount(formatWholeChipInput(limits.default_table_amount));
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setRuntimeError(readErrorMessage(error, "Saldo tavolo non disponibile."));
        }
      });
    return () => {
      isMounted = false;
    };
  }, [selectedTableWalletType, showTableBalanceGate, tableGateToken]);

  const handleExit = useCallback(() => {
    window.location.assign("/");
  }, []);

  const handleConfirmTableBalance = useCallback(
    async ({ tableEntryAmount: nextEntryAmount, walletSource }: GameTableBalanceConfirmParams) => {
      if (!tableGateToken) {
        setRuntimeError("Accedi per giocare con saldo reale.");
        return;
      }
      try {
        const normalizedAmount = formatWholeChipInput(nextEntryAmount);
        const nextAccessSession = await createBoxeAccessSession({
          titleCode: tableGateTitleCode,
          token: tableGateToken,
        });
        const nextTableSession = await createBoxeTableSession({
          titleCode: tableGateTitleCode,
          walletType: walletSource,
          tableBudgetAmount: normalizedAmount,
          accessSessionId: nextAccessSession.id,
          token: tableGateToken,
        });
        setAccessSession(nextAccessSession);
        setTableSession(nextTableSession);
        setSelectedTableWalletType(nextTableSession.wallet_type);
        setTableEntryAmount(normalizedAmount);
        setRuntimeError("");
        setIsTableBalanceComplete(true);
      } catch (error) {
        setRuntimeError(readErrorMessage(error, "Ingresso tavolo non disponibile."));
      }
    },
    [tableGateTitleCode, tableGateToken],
  );

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
    <GameTableBalanceGate
      amount={tableEntryAmount}
      amountLabel="Importo ingresso tavolo"
      amountPlaceholder={formatWholeChipInput(tableDefaultAmount)}
      availableBalanceLabel="Saldo disponibile"
      availableBalanceValue={`${formatWholeChipInput(tableAvailableBalance)} CHIP`}
      busyLabel="Ingresso..."
      closeAriaLabel="Torna al sito"
      confirmLabel="Entra nel gioco"
      eyebrow="BOXE"
      isReady={tableSessionLimits !== null}
      lockedWalletSource={lockedTableWalletSource}
      maximumAmount={formatWholeChipInput(tableEntryMaxAmount)}
      maximumAmountLabel={`${formatWholeChipInput(tableEntryMaxAmount)} CHIP`}
      maximumLabel="Massimo"
      onAmountChange={(amount) => setTableEntryAmount(amount.replace(/\D/g, ""))}
      onClose={handleExit}
      onConfirm={handleConfirmTableBalance}
      onWalletSourceChange={setSelectedTableWalletType}
      preload={<GameProviderBootstrapPreload />}
      quickAmounts={BOXE_TABLE_BALANCE_CONFIG.quickAmounts.map((amount) => ({
        value: amount,
      }))}
      selectedWalletSource={selectedTableWalletType}
      testId="boxe-table-balance-gate"
      title="Scegli il saldo del tavolo"
      walletGroupAriaLabel="Fonte saldo"
      walletOptions={[
        {
          balanceLabel: "100 CHIP",
          label: "Saldo reale",
          value: "cash",
        },
        {
          balanceLabel: "100 CHIP",
          label: "Bonus",
          value: "bonus",
        },
      ]}
    />
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
      tableGatePageShellClassName="page-shell game-table-balance-page"
      pageShellClassName="page-shell boxe-page-shell"
      productShellClassName="game-product-shell game-visual-product-shell boxe-product-shell"
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
          accessSessionId={accessSession?.id ?? null}
          tableSession={tableSession}
          onExit={handleExit}
          onOpenGameInfo={() => setIsHowToPlayComplete(false)}
          onTableSessionChange={setTableSession}
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

function formatWholeChipInput(value: string | number | null | undefined) {
  const numeric = Number.parseFloat(String(value ?? "0"));
  if (!Number.isFinite(numeric)) {
    return "0";
  }
  return String(Math.floor(numeric));
}
