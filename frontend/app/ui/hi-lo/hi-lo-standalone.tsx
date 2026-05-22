"use client";

import { useCallback, useEffect, useState } from "react";
import type { TitleTheme, TitleThemeSkin } from "@/app/lib/types";
import { GameActionError } from "@/app/ui/game-runtime/game-action-error";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import {
  buildGameErrorMessage,
  classifyGameError,
  type GameErrorCopyMap,
} from "@/app/ui/game-runtime/game-error-copy-adapter";
import { GameHowToPlayGate } from "@/app/ui/game-runtime/game-how-to-play-gate";
import {
  GameProviderBootstrap,
  GameProviderBootstrapPreload,
} from "@/app/ui/game-runtime/game-provider-bootstrap";
import {
  filterSafeTableBalanceQuickAmounts,
  GameTableBalanceGate,
  type GameTableBalanceConfirmParams,
  type GameTableBalanceWalletSource,
} from "@/app/ui/game-runtime/game-table-balance-gate";
import { HI_LO_GAME_STORAGE_NAMESPACE } from "@/app/ui/game-runtime/game-storage";
import { useGameLaunchContext } from "@/app/ui/game-runtime/use-game-launch-context";
import { HiLoGameplay } from "./hi-lo-gameplay";
import {
  createHiLoAccessSession,
  createHiLoTableSession,
  loadHiLoRuntimeConfig,
  loadHiLoTableSessionLimits,
  type HiLoAccessSession,
  type HiLoRuntimeConfig,
  type HiLoTableSession,
  type HiLoTableSessionLimits,
} from "./use-hi-lo-runtime";

const HI_LO_RUNTIME_ERROR_COPY_MAP = {
  auth_invalid: "Sessione scaduta, ricarica",
  validation: "Controlla puntata e selezioni.",
  insufficient_balance: "Saldo insufficiente.",
  bonus_wallet_empty: "Saldo bonus vuoto.",
  round_closed: "La mano e' gia' conclusa.",
  network: "Connessione instabile. Riprova.",
  service_unavailable: "Servizio temporaneamente non disponibile.",
  reload_required: "Sessione scaduta, ricarica",
  generic: "Operazione non riuscita. Riprova.",
} satisfies GameErrorCopyMap;

const HI_LO_TABLE_BALANCE_CONFIG = {
  defaultEntryAmount: "100",
  quickAmounts: ["10", "25", "50", "100"],
};

export function HiLoStandalone() {
  const [runtimeConfig, setRuntimeConfig] = useState<HiLoRuntimeConfig | null>(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [titleThemeAssets, setTitleThemeAssets] = useState<Record<string, string>>({});
  const [titleThemeSkin, setTitleThemeSkin] = useState<TitleThemeSkin | null>(null);
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [isTableBalanceComplete, setIsTableBalanceComplete] = useState(false);
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<GameTableBalanceWalletSource>("cash");
  const [accessSession, setAccessSession] = useState<HiLoAccessSession | null>(null);
  const [tableSession, setTableSession] = useState<HiLoTableSession | null>(null);
  const [tableSessionLimits, setTableSessionLimits] =
    useState<HiLoTableSessionLimits | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState("");
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
    storageNamespace: HI_LO_GAME_STORAGE_NAMESPACE,
    missingTitleRedirectTo: "/",
  });

  const handleTitleThemeChange = useCallback((theme: TitleTheme | null) => {
    setTitleThemeAssets(theme?.assets ?? {});
    setTitleThemeSkin(theme?.skin ?? null);
    setIsTitleThemeResolved(true);
  }, []);

  const isLaunchContextReady =
    bootStatus.kind === "launch_ready" || bootStatus.kind === "runtime_ready";
  const isRuntimeReady = bootStatus.kind === "runtime_ready";
  const canRenderBootSurface =
    isLaunchContextReady || (bootStatus.kind === "fatal" && "request" in bootStatus);
  const titleCode = "request" in bootStatus && bootStatus.request
    ? bootStatus.request.titleCode
    : "hilo001";

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
    setTableEntryAmount("");

    let isMounted = true;
    loadHiLoRuntimeConfig(bootStatus.request.titleCode)
      .then((config) => {
        if (isMounted) {
          setRuntimeConfig(config);
        }
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setRuntimeError(buildGameErrorMessage(error, HI_LO_RUNTIME_ERROR_COPY_MAP));
        if (classifyGameError(error) === "service_unavailable") {
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
  const isEmbeddedView =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.isEmbeddedView : false;
  const pageShellClassName = [
    "page-shell",
    "hi-lo-page-shell",
    isEmbeddedView ? "hi-lo-page-shell-embedded" : null,
  ].filter(Boolean).join(" ");
  const productShellClassName = [
    "panel",
    "game-product-shell",
    "game-visual-product-shell",
    "hi-lo-product-shell",
    isEmbeddedView ? "hi-lo-product-shell-embedded" : null,
    titleThemeSkin ? "hi-lo-product-shell-skinned" : null,
  ].filter(Boolean).join(" ");
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
    tableSessionLimits?.default_table_amount ?? HI_LO_TABLE_BALANCE_CONFIG.defaultEntryAmount;

  useEffect(() => {
    if (!showTableBalanceGate || !tableGateToken) {
      return;
    }
    let isMounted = true;
    setTableSessionLimits(null);
    loadHiLoTableSessionLimits(tableGateToken, selectedTableWalletType)
      .then((limits) => {
        if (!isMounted) {
          return;
        }
        setTableSessionLimits(limits);
        setTableEntryAmount(formatSafeDefaultTableEntry(limits.default_table_amount));
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setRuntimeError(buildGameErrorMessage(error, HI_LO_RUNTIME_ERROR_COPY_MAP));
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
        setRuntimeError(HI_LO_RUNTIME_ERROR_COPY_MAP.auth_invalid);
        return;
      }
      try {
        const normalizedAmount = formatWholeChipInput(nextEntryAmount);
        const nextAccessSession = await createHiLoAccessSession({
          titleCode: tableGateTitleCode,
          token: tableGateToken,
        });
        const nextTableSession = await createHiLoTableSession({
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
        setRuntimeError(buildGameErrorMessage(error, HI_LO_RUNTIME_ERROR_COPY_MAP));
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
      titleId="hi-lo-how-to-play-title"
      intro="Punta, scegli il prossimo esito della carta e incassa prima di sbagliare."
      continueLabel="Continua"
      cards={[
        {
          title: "Bet",
          text: "Imposta la puntata e guarda la carta iniziale.",
          visual: <HiLoHowToPlayVisual index={0} />,
        },
        {
          title: "Predict",
          text: "Scegli colore, sopra o sotto usando i moltiplicatori proposti.",
          visual: <HiLoHowToPlayVisual index={1} />,
        },
        {
          title: "Collect",
          text: "Incassa dopo una previsione corretta o continua la serie.",
          visual: <HiLoHowToPlayVisual index={2} />,
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
      availableBalanceAmount={formatWholeChipInput(tableAvailableBalance)}
      availableBalanceLabel="Saldo disponibile"
      availableBalanceValue={`${formatWholeChipInput(tableAvailableBalance)} CHIP`}
      busyLabel="Ingresso..."
      closeAriaLabel="Torna al sito"
      confirmLabel="Entra nel gioco"
      eyebrow="HI-LO"
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
      quickAmounts={filterSafeTableBalanceQuickAmounts(
        HI_LO_TABLE_BALANCE_CONFIG.quickAmounts.map((amount) => ({ value: amount })),
        tableEntryMaxAmount,
        tableAvailableBalance,
      )}
      selectedWalletSource={selectedTableWalletType}
      testId="hi-lo-table-balance-gate"
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
    <GameActionError
      actionLabel="Riprova"
      message={runtimeError}
      onAction={() => window.location.reload()}
      testId="hi-lo-runtime-error-dialog"
      title="Azione richiesta"
    />
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
      pageShellClassName={pageShellClassName}
      productShellClassName={productShellClassName}
      onThemeChange={handleTitleThemeChange}
      onAudioPreferencesChange={setAudioPreferences}
      tableGate={tableGate}
      providerIntro={providerIntro}
      howToPlay={howToPlay}
      errorDialog={errorDialog}
      runtimeOverlay={null}
    >
      {runtimeConfig ? (
        <HiLoGameplay
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
          titleThemeAssets={titleThemeAssets}
          titleThemeSkin={titleThemeSkin}
          accessSessionId={accessSession?.id ?? null}
          tableSession={tableSession}
          onExit={handleExit}
          onTableSessionChange={setTableSession}
        />
      ) : (
        <div className="hi-lo-loading" role="status">
          Caricamento HI-LO...
        </div>
      )}
    </GameBootShell>
  );
}

function HiLoHowToPlayVisual({ index }: { index: number }) {
  const cards = [
    { rank: "7", suit: "clubs", label: "BLACK", accent: "black" },
    { rank: "Q", suit: "hearts", label: "UP", accent: "red" },
    { rank: "K", suit: "spades", label: "COLLECT", accent: "gold" },
  ][index] ?? { rank: "7", suit: "clubs", label: "BLACK", accent: "black" };

  return (
    <div className={`game-how-to-play-visual hi-lo-how-to-visual is-${cards.accent}`} aria-hidden="true">
      <div className="hi-lo-how-to-card">
        <span>{cards.rank}</span>
        <strong>{cards.suit.toUpperCase()}</strong>
      </div>
      <div className="hi-lo-how-to-action">{cards.label}</div>
    </div>
  );
}

function formatWholeChipInput(value: string) {
  const numeric = Number.parseFloat(value || "0");
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return "0";
  }
  return String(Math.floor(numeric));
}

function formatSafeDefaultTableEntry(value: string) {
  const formatted = formatWholeChipInput(value);
  return formatted === "0" ? "" : formatted;
}
