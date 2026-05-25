"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { TitleTheme, TitleThemeSkin } from "@/app/lib/types";
import { GameActionError } from "@/app/ui/game-runtime/game-action-error";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import {
  buildGameErrorMessage,
  classifyGameError,
  isBearerTokenAuthError,
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
import {
  clearStoredAuthState,
  HI_LO_GAME_STORAGE_NAMESPACE,
} from "@/app/ui/game-runtime/game-storage";
import { useGameEmbedBridge } from "@/app/ui/game-runtime/use-game-embed-bridge";
import { useGameLaunchContext } from "@/app/ui/game-runtime/use-game-launch-context";
import { HiLoGameplay } from "./hi-lo-gameplay";
import { HiLoHowToPlayVisual } from "./hi-lo-how-to-visual";
import {
  createHiLoCopyResolver,
  type HiLoCopyResolver,
} from "./hi-lo-i18n/hi-lo-copy-defaults";
import {
  closeHiLoAccessSession,
  createHiLoAccessSession,
  createHiLoTableSession,
  loadHiLoActiveRound,
  loadHiLoRuntimeConfig,
  loadHiLoTableSessionLimits,
  provisionHiLoDemoPlayer,
  type HiLoAccessSession,
  type HiLoRoundResponse,
  type HiLoRuntimeConfig,
  type HiLoTableSession,
  type HiLoTableSessionLimits,
} from "./use-hi-lo-runtime";

const HI_LO_TABLE_BALANCE_CONFIG = {
  defaultEntryAmount: "100",
  quickAmounts: ["10", "25", "50", "100"],
};
const HI_LO_FALLBACK_RUNTIME_ERROR_COPY_MAP = createHiLoRuntimeErrorCopyMap(
  createHiLoCopyResolver("it"),
);

export function HiLoStandalone() {
  const [runtimeConfig, setRuntimeConfig] = useState<HiLoRuntimeConfig | null>(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [titleThemeAssets, setTitleThemeAssets] = useState<Record<string, string>>({});
  const [titleThemeSkin, setTitleThemeSkin] = useState<TitleThemeSkin | null>(null);
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [isTableBalanceComplete, setIsTableBalanceComplete] = useState(false);
  const [isCheckingActiveRound, setIsCheckingActiveRound] = useState(false);
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<GameTableBalanceWalletSource>("cash");
  const [accessSession, setAccessSession] = useState<HiLoAccessSession | null>(null);
  const [tableSession, setTableSession] = useState<HiLoTableSession | null>(null);
  const [resumedRound, setResumedRound] = useState<HiLoRoundResponse | null>(null);
  const [tableSessionLimits, setTableSessionLimits] =
    useState<HiLoTableSessionLimits | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState("");
  const [runtimeAccessToken, setRuntimeAccessToken] = useState<string | null>(null);
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
  const runtimeLocale = runtimeConfig?.presentation_config?.default_locale ?? "it";
  const hiLoCopy = useMemo(
    () => createHiLoCopyResolver(
      runtimeLocale,
      runtimeConfig?.presentation_config?.copy?.[runtimeLocale],
    ),
    [runtimeConfig?.presentation_config?.copy, runtimeLocale],
  );
  const runtimeErrorCopyMap = useMemo(
    () => createHiLoRuntimeErrorCopyMap(hiLoCopy),
    [hiLoCopy],
  );

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
    setIsCheckingActiveRound(false);
    setAccessSession(null);
    setTableSession(null);
    setTableSessionLimits(null);
    setResumedRound(null);
    setRuntimeAccessToken(null);
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
        setRuntimeError(buildGameErrorMessage(error, HI_LO_FALLBACK_RUNTIME_ERROR_COPY_MAP));
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
  const { isHostFullscreen, requestClose: requestEmbedClose } = useGameEmbedBridge({
    gameCode: "hi_lo",
    enabled: isEmbeddedView,
  });
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
    isLaunchContextReady && !isDemoMode && !isTableBalanceComplete && !resumedRound && !isCheckingActiveRound;
  const showProviderIntroGate =
    (isLaunchContextReady || bootStatus.kind === "fatal") &&
    !showTableBalanceGate &&
    !isProviderIntroComplete;
  const showHowToPlayGate =
    isRuntimeReady &&
    !showTableBalanceGate &&
    !isCheckingActiveRound &&
    isProviderIntroComplete &&
    !isHowToPlayComplete;
  const lockedTableWalletSource =
    "request" in bootStatus && bootStatus.request && !bootStatus.request.forceDemoMode
      ? bootStatus.request.walletSource
      : null;
  const tableGateToken =
    runtimeAccessToken ??
    ("storageSnapshot" in bootStatus ? (bootStatus.storageSnapshot?.accessToken ?? "") : "");
  const tableGateTitleCode =
    "request" in bootStatus && bootStatus.request ? bootStatus.request.titleCode : titleCode;
  const tableEntryMaxAmount = tableSessionLimits?.max_table_amount ?? "0";
  const tableAvailableBalance = tableSessionLimits?.wallet_balance_available ?? "0";
  const tableDefaultAmount =
    tableSessionLimits?.default_table_amount ?? HI_LO_TABLE_BALANCE_CONFIG.defaultEntryAmount;
  useEffect(() => {
    if (!isLaunchContextReady || !runtimeConfig || !tableGateToken || resumedRound || isTableBalanceComplete) {
      return;
    }
    let isMounted = true;

    async function loadActiveRoundWithDemoRecovery() {
      setIsCheckingActiveRound(true);
      try {
        const activeRound = await loadHiLoActiveRound({
          titleCode: tableGateTitleCode,
          token: tableGateToken,
          walletSource: isDemoMode ? "demo" : selectedTableWalletType,
        });
        if (!isMounted || !activeRound) {
          return;
        }
        setResumedRound(activeRound);
        if (activeRound.table_session) {
          setTableSession(activeRound.table_session);
          setSelectedTableWalletType(activeRound.table_session.wallet_type);
        }
        setIsTableBalanceComplete(true);
        setIsProviderIntroComplete(true);
        setIsHowToPlayComplete(true);
        setRuntimeError("");
      } catch (error: unknown) {
        if (!isMounted) {
          return;
        }
        if (
          isDemoMode &&
          isBearerTokenAuthError(error) &&
          runtimeAccessToken !== tableGateToken
        ) {
          try {
            clearStoredAuthState(window.localStorage, HI_LO_GAME_STORAGE_NAMESPACE);
            const demoAuth = await provisionHiLoDemoPlayer();
            if (!isMounted) {
              return;
            }
            window.localStorage.setItem("casinoking.access_token", demoAuth.access_token);
            window.localStorage.setItem("casinoking.email", demoAuth.email);
            setRuntimeAccessToken(demoAuth.access_token);
            setRuntimeError("");
            return;
          } catch (recoveryError: unknown) {
            if (!isMounted) {
              return;
            }
            setRuntimeError(buildGameErrorMessage(recoveryError, runtimeErrorCopyMap));
            return;
          }
        }
        setRuntimeError(buildGameErrorMessage(error, runtimeErrorCopyMap));
      } finally {
        if (isMounted) {
          setIsCheckingActiveRound(false);
        }
      }
    }

    void loadActiveRoundWithDemoRecovery();
    return () => {
      isMounted = false;
    };
  }, [
    isLaunchContextReady,
    isTableBalanceComplete,
    resumedRound,
    runtimeConfig,
    tableGateTitleCode,
    tableGateToken,
    runtimeAccessToken,
    isDemoMode,
    runtimeErrorCopyMap,
    selectedTableWalletType,
  ]);

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
          setRuntimeError(buildGameErrorMessage(error, runtimeErrorCopyMap));
        }
      });
    return () => {
      isMounted = false;
    };
  }, [runtimeErrorCopyMap, selectedTableWalletType, showTableBalanceGate, tableGateToken]);

  const handleExit = useCallback(async () => {
    if (isHostFullscreen) {
      setAccessSession(null);
      setTableSession(null);
      setResumedRound(null);
      return;
    }
    const currentAccessSessionId = accessSession?.id ?? tableSession?.access_session_id;
    const closeToken = runtimeAccessToken ?? tableGateToken;
    if (!isDemoMode && currentAccessSessionId && closeToken) {
      try {
        await closeHiLoAccessSession({
          accessSessionId: currentAccessSessionId,
          token: closeToken,
        });
      } catch {
        // Do not trap the player on exit. The server timeout path will still auto-settle.
      }
      setAccessSession(null);
      setTableSession(null);
      setResumedRound(null);
    }
    if (requestEmbedClose()) {
      return;
    }
    window.location.assign("/");
  }, [
    accessSession?.id,
    isDemoMode,
    isHostFullscreen,
    requestEmbedClose,
    runtimeAccessToken,
    tableGateToken,
    tableSession?.access_session_id,
  ]);

  const handleConfirmTableBalance = useCallback(
    async ({ tableEntryAmount: nextEntryAmount, walletSource }: GameTableBalanceConfirmParams) => {
      if (!tableGateToken) {
        setRuntimeError(hiLoCopy("runtime.error.auth_invalid"));
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
        setRuntimeError(buildGameErrorMessage(error, runtimeErrorCopyMap));
      }
    },
    [hiLoCopy, runtimeErrorCopyMap, tableGateTitleCode, tableGateToken],
  );

  const providerIntro = showProviderIntroGate ? (
    <GameProviderBootstrap
      ready={isRuntimeReady || runtimeError.length > 0}
      onComplete={() => setIsProviderIntroComplete(true)}
    />
  ) : null;

  const howToPlay = showHowToPlayGate ? (
    <GameHowToPlayGate
      title={hiLoCopy("how_to_play.title")}
      titleId="hi-lo-how-to-play-title"
      intro={hiLoCopy("how_to_play.intro")}
      continueLabel={hiLoCopy("how_to_play.continue")}
      cards={[
        {
          title: hiLoCopy("how_to_play.card_1_title"),
          text: hiLoCopy("how_to_play.card_1_text"),
          visual: <HiLoHowToPlayVisual index={0} />,
        },
        {
          title: hiLoCopy("how_to_play.card_2_title"),
          text: hiLoCopy("how_to_play.card_2_text"),
          visual: <HiLoHowToPlayVisual index={1} />,
        },
        {
          title: hiLoCopy("how_to_play.card_3_title"),
          text: hiLoCopy("how_to_play.card_3_text"),
          visual: <HiLoHowToPlayVisual index={2} />,
        },
      ]}
      onContinue={() => setIsHowToPlayComplete(true)}
    />
  ) : null;

  const tableGate = showTableBalanceGate ? (
    <GameTableBalanceGate
      amount={tableEntryAmount}
      amountLabel={hiLoCopy("runtime.table.amount_label")}
      amountPlaceholder={formatWholeChipInput(tableDefaultAmount)}
      availableBalanceAmount={formatWholeChipInput(tableAvailableBalance)}
      availableBalanceLabel={hiLoCopy("runtime.table.available_balance")}
      availableBalanceValue={`${formatWholeChipInput(tableAvailableBalance)} ${hiLoCopy("runtime.balance.chip_suffix")}`}
      busyLabel={hiLoCopy("runtime.table.busy")}
      closeAriaLabel={hiLoCopy("runtime.action.close_aria")}
      confirmLabel={hiLoCopy("runtime.table.confirm")}
      eyebrow="HI-LO"
      isReady={tableSessionLimits !== null}
      lockedWalletSource={lockedTableWalletSource}
      maximumAmount={formatWholeChipInput(tableEntryMaxAmount)}
      maximumAmountLabel={`${formatWholeChipInput(tableEntryMaxAmount)} ${hiLoCopy("runtime.balance.chip_suffix")}`}
      maximumLabel={hiLoCopy("runtime.table.maximum")}
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
      title={hiLoCopy("runtime.table.title")}
      walletGroupAriaLabel={hiLoCopy("runtime.table.wallet_source")}
      walletOptions={[
        {
          balanceLabel: `100 ${hiLoCopy("runtime.balance.chip_suffix")}`,
          label: hiLoCopy("runtime.balance.real"),
          value: "cash",
        },
        {
          balanceLabel: `100 ${hiLoCopy("runtime.balance.chip_suffix")}`,
          label: hiLoCopy("runtime.balance.bonus"),
          value: "bonus",
        },
      ]}
    />
  ) : null;

  const errorDialog = runtimeError ? (
    <GameActionError
      actionLabel={hiLoCopy("runtime.action.retry")}
      dismissLabel={hiLoCopy("runtime.action.back_to_site")}
      message={runtimeError}
      onAction={() => window.location.reload()}
      onDismiss={handleExit}
      testId="hi-lo-runtime-error-dialog"
      title={hiLoCopy("runtime.error.title")}
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
            runtimeAccessToken ??
            (bootStatus.kind === "runtime_ready"
              ? bootStatus.storageSnapshot.accessToken
              : "")
          }
          runtimeConfig={runtimeConfig}
          titleThemeAssets={titleThemeAssets}
          titleThemeSkin={titleThemeSkin}
          accessSessionId={accessSession?.id ?? null}
          initialRound={resumedRound}
          tableSession={tableSession}
          onExit={handleExit}
          onTableSessionChange={setTableSession}
        />
      ) : (
        <div className="hi-lo-loading" role="status">
          {hiLoCopy("runtime.loading")}
        </div>
      )}
    </GameBootShell>
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

function createHiLoRuntimeErrorCopyMap(copy: HiLoCopyResolver): GameErrorCopyMap {
  return {
    auth_invalid: copy("runtime.error.auth_invalid"),
    validation: copy("runtime.error.validation"),
    insufficient_balance: copy("runtime.error.insufficient_balance"),
    bonus_wallet_empty: copy("runtime.error.bonus_wallet_empty"),
    round_closed: copy("runtime.error.round_closed"),
    network: copy("runtime.error.network"),
    service_unavailable: copy("runtime.error.service_unavailable"),
    reload_required: copy("runtime.error.reload_required"),
    generic: copy("runtime.error.generic"),
  };
}
