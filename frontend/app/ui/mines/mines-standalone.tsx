"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  formatGridChoiceLabel,
  formatWholeChipDisplay,
  getDefaultVisibleMineCount,
  getMineOptions,
  getVisibleGridSizes,
  getVisibleMineOptions,
  isExpiredIsoDate,
  normalizeWholeChipInput,
} from "@/app/lib/helpers";
import { MinesGameplay } from "./mines-gameplay";
import type { MinesRoundReplay } from "./mines-replay-viewer";
import { MinesHowToPlayVisual } from "./mines-how-to-play-visual";
import {
  createMinesCopyResolver,
  type MinesCopyResolver,
} from "./i18n/mines-copy-resolver";
import type {
  LatestAccessSessionHistory,
  MinesCashoutResult,
  MinesRevealResult,
} from "./types";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import { GameHowToPlayGate } from "@/app/ui/game-runtime/game-how-to-play-gate";
import {
  GameProviderBootstrap,
  GameProviderBootstrapPreload,
} from "@/app/ui/game-runtime/game-provider-bootstrap";
import {
  filterSafeTableBalanceQuickAmounts,
  GameTableBalanceGate,
  type GameTableBalanceConfirmParams,
} from "@/app/ui/game-runtime/game-table-balance-gate";
import { useGameLaunchContext } from "@/app/ui/game-runtime/use-game-launch-context";
import {
  MINES_GAME_STORAGE_NAMESPACE,
  clearStoredAuthState,
  clearStoredDemoChipBalance,
  clearStoredDemoLaunchToken,
  clearStoredRealLaunchToken,
  clearStoredSessionId,
  readGameStorageSnapshot,
  writeStoredDemoAnonToken,
  writeStoredDemoChipBalance,
  writeStoredDemoLaunchToken,
  writeStoredRealLaunchToken,
  writeStoredSessionId,
} from "@/app/ui/game-runtime/game-storage";
import type {
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  SessionSnapshot,
  StatusMessage,
  TitleTheme,
  TitleThemeSkin,
  Wallet,
} from "@/app/lib/types";
import { ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";

const MINES_EMBED_CLOSE_MESSAGE = "casinoking:mines-close";
const MINES_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:mines-fullscreen-state";
const MINES_STANDALONE_MEDIA_QUERY = "(max-width: 960px), (pointer: coarse)";
const ACCESS_SESSION_GAME_CODE = "mines";
const MINES_TITLE_CODE = "mines_classic";
const ACCESS_SESSION_PING_INTERVAL_MS = 30_000;
const ACCESS_SESSION_WARNING_MS = 170_000;
const ACCESS_SESSION_EXPIRY_MS = 180_000;
const ACCESS_SESSION_COUNTDOWN_SECONDS = 10;

type DemoTokenResponse = {
  anonymous_token: string;
};

type DemoLaunchResponse = {
  game_launch_token: string;
  expires_at: string;
  anonymous_id: string;
  balance_chips?: string;
};

type DemoStartResponse = {
  game_session_id: string;
  mode: "demo";
  wallet_balance_after: string;
};

type LaunchTokenResponse = {
  game_code: string;
  title_code: string;
  game_launch_token: string;
  platform_session_id: string;
  play_session_id: string;
  game_play_session_id: string;
  expires_at: string;
};

type LaunchTokenValidationResponse = {
  game_code: string;
  title_code: string;
  player_id: string;
  platform_session_id: string;
  play_session_id: string;
  game_play_session_id: string;
  expires_at: string;
};

type StartSessionResponse = {
  game_session_id: string;
  table_session_id?: string | null;
  table_session?: TableSessionResponse;
};

type AccessSessionResponse = {
  id: string;
  user_id: string;
  game_code: string;
  title_code: string;
  site_code: string;
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  status: "active" | "closed" | "timed_out";
};

type TableSessionLimitsResponse = {
  wallet_balance_available: string;
  table_session_max_chips: string;
  default_table_amount: string;
  max_table_amount: string;
};

type TableSessionResponse = {
  id: string;
  access_session_id: string | null;
  game_code: string;
  title_code: string;
  site_code: string;
  wallet_type: "cash" | "bonus";
  table_budget_amount: string;
  table_balance_amount: string;
  loss_limit_amount: string;
  loss_reserved_amount: string;
  loss_consumed_amount: string;
  loss_remaining_amount: string;
  status: "active" | "closed" | "timed_out";
};

type TableWalletType = "cash" | "bonus";

type RecentSessionSummary = {
  game_session_id: string;
  status: "active" | "won" | "lost" | "cancelled";
  title_code: string;
  site_code: string;
  access_session_id: string | null;
  table_session_id?: string | null;
  access_session: {
    id: string;
    title_code: string;
    site_code: string;
    status: "active" | "closed" | "timed_out";
  } | null;
};

type ResumeSessionTarget = {
  gameSessionId: string;
  titleCode: string;
};

type FatalRuntimeOverlay = {
  title: string;
  text: string;
};

type RefreshAuthenticatedStateOptions = {
  preferredGameSessionId?: string | null;
  showResumeOverlay?: boolean;
  tableWalletType?: TableWalletType;
};

type GameErrorContext =
  | "load-runtime"
  | "create-access-session"
  | "refresh-access-session"
  | "refresh-auth-state"
  | "resume-session"
  | "start-demo"
  | "create-table-session"
  | "start-session"
  | "reveal"
  | "cashout";

export function MinesStandalone() {
  const [accessToken, setAccessToken] = useState("");
  const [accessSessionId, setAccessSessionId] = useState("");
  const [gameLaunchToken, setGameLaunchToken] = useState("");
  const [gameLaunchTokenExpiresAt, setGameLaunchTokenExpiresAt] = useState("");
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [runtimeConfig, setRuntimeConfig] = useState<MinesRuntimeConfig | null>(null);
  const [currentSession, setCurrentSession] = useState<SessionSnapshot | null>(null);
  const [tableSession, setTableSession] = useState<TableSessionResponse | null>(null);
  const [tableSessionLimits, setTableSessionLimits] = useState<TableSessionLimitsResponse | null>(
    null,
  );
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<TableWalletType>("cash");
  const [lockedTableWalletType, setLockedTableWalletType] = useState<TableWalletType | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState("");
  const [selectedGridSize, setSelectedGridSize] = useState(25);
  const [selectedMineCount, setSelectedMineCount] = useState(3);
  const [betAmount, setBetAmount] = useState("5");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [inactivityCountdownSeconds, setInactivityCountdownSeconds] = useState<number | null>(
    null,
  );
  const [isAccessSessionExpired, setIsAccessSessionExpired] = useState(false);
  const [isEmbeddedView, setIsEmbeddedView] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isHostFullscreen, setIsHostFullscreen] = useState(false);
  const [isSessionResumeLoading, setIsSessionResumeLoading] = useState(false);
  const [fatalRuntimeOverlay, setFatalRuntimeOverlay] = useState<FatalRuntimeOverlay | null>(null);
  const [launchTitleCode, setLaunchTitleCode] = useState(MINES_TITLE_CODE);
  const [forceDemoMode, setForceDemoMode] = useState(false);
  const [adminPreviewToken, setAdminPreviewToken] = useState("");
  const [demoAnonToken, setDemoAnonToken] = useState("");
  const [demoGameLaunchToken, setDemoGameLaunchToken] = useState("");
  const [demoGameLaunchTokenExpiresAt, setDemoGameLaunchTokenExpiresAt] = useState("");
  const [demoChipBalance, setDemoChipBalance] = useState("100");
  const [isRuntimeDataReady, setIsRuntimeDataReady] = useState(false);
  const [isTitleThemeResolved, setIsTitleThemeResolved] = useState(false);
  const [isProviderIntroComplete, setIsProviderIntroComplete] = useState(false);
  const [isHowToPlayComplete, setIsHowToPlayComplete] = useState(false);
  const [titleThemeAssets, setTitleThemeAssets] = useState<Record<string, string>>({});
  const [titleThemeSkin, setTitleThemeSkin] = useState<TitleThemeSkin | null>(null);
  const [isBetHintActive, setIsBetHintActive] = useState(false);
  const [playerActivityTick, setPlayerActivityTick] = useState(0);
  const selectedGridSizeRef = useRef(25);
  const selectedMineCountRef = useRef(3);
  const betAmountRef = useRef("5");
  const accessSessionIdRef = useRef("");
  const accessSessionTitleCodeRef = useRef("");
  const accessSessionRequestRef = useRef<Promise<string> | null>(null);
  const accessSessionRequestTitleCodeRef = useRef("");
  const inactivityWarningTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inactivityExpiryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inactivityCountdownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [gameAudioPreferences, setGameAudioPreferences] = useState({
    muted: false,
    setMuted: (_value: boolean) => {},
    setVolume: (_value: number) => {},
    volume: 0.45,
  });
  const {
    status: bootStatus,
    markRuntimeReady,
    markFatal: markBootFatal,
  } = useGameLaunchContext({
    storageNamespace: MINES_GAME_STORAGE_NAMESPACE,
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
  const isAuthenticated = accessToken.length > 0 && !forceDemoMode;
  const isDemoMode = !isAuthenticated;
  const controlGridSize =
    currentSession?.status === "active" ? currentSession.grid_size : selectedGridSize;
  const controlMineCount =
    currentSession?.status === "active" ? currentSession.mine_count : selectedMineCount;
  const gridSizes = getVisibleGridSizes(runtimeConfig, controlGridSize);
  const mineOptions = getVisibleMineOptions(
    runtimeConfig,
    controlGridSize,
    controlMineCount,
  );
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const bonusWallet = wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null;
  const isActiveRound = currentSession?.status === "active";
  const activeWalletType: "cash" | "bonus" =
    currentSession?.wallet_type === "bonus" ? "bonus" : "cash";
  const effectiveWalletType = isActiveRound
    ? activeWalletType
    : tableSession?.wallet_type ?? selectedTableWalletType;
  const selectedWallet =
    effectiveWalletType === "bonus" ? bonusWallet ?? cashWallet : cashWallet;
  const isRealTableSessionActive =
    isAuthenticated && tableSession?.status === "active";
  const currentMode = isAuthenticated ? "real" : "demo";
  const minesCopy = createMinesCopyResolver(
    runtimeConfig?.presentation_config,
    currentMode,
  );
  const copy = minesCopy.t;
  const gameTitle = minesCopy.t("game.title");
  const formatChipValue = (value: string | number | null | undefined) =>
    formatWholeChipDisplay(value, copy("format.chip_suffix"));
  const formatGridLabel = (gridSize: number) =>
    formatGridChoiceLabel(gridSize, (cellCount) =>
      copy("format.cells", { count: cellCount }),
    );
  const visibleBalance =
    isDemoMode
      ? demoChipBalance
      : isRealTableSessionActive
      ? tableSession.table_balance_amount
      : isActiveRound
      ? currentSession.wallet_balance_after_start
      : selectedWallet?.balance_snapshot ?? "0";
  const visibleStatus = status?.kind === "error" ? status : null;
  const useMobileLayout = isMobileViewport;
  const tableEntryMaxAmount = tableSessionLimits?.max_table_amount ?? "0";
  const selectedTableWallet =
    selectedTableWalletType === "bonus" ? bonusWallet ?? null : cashWallet;
  const hasLockedTableWalletType = lockedTableWalletType !== null;
  const selectedTableWalletBalance =
    tableSessionLimits?.wallet_balance_available ?? selectedTableWallet?.balance_snapshot ?? "0";
  const numericTableEntryMaxAmount = Number.parseFloat(tableEntryMaxAmount || "0");
  const hasTableBudget =
    !isRealTableSessionActive ||
    Number.parseFloat(tableSession?.table_balance_amount ?? "0") > 0;
  const isAccessSessionWarningActive =
    inactivityCountdownSeconds !== null && !isAccessSessionExpired;
  const isFatalRuntimeBlocked = fatalRuntimeOverlay !== null;
  const isProviderIntroReady = isRuntimeReady || visibleStatus !== null || isFatalRuntimeBlocked;
  const isInteractionLocked =
    isSessionResumeLoading ||
    isAccessSessionWarningActive ||
    isAccessSessionExpired ||
    isFatalRuntimeBlocked;
  const shouldShowPreGameTableEntry =
    isLaunchContextReady &&
    isAuthenticated &&
    !isRealTableSessionActive &&
    !isActiveRound &&
    !isSessionResumeLoading;
  const shouldShowProviderIntro =
    (isLaunchContextReady || bootStatus.kind === "fatal") &&
    !shouldShowPreGameTableEntry &&
    !isProviderIntroComplete;
  const shouldShowHowToPlayGate =
    isRuntimeReady &&
    !shouldShowPreGameTableEntry &&
    isProviderIntroComplete &&
    !isHowToPlayComplete &&
    runtimeConfig !== null &&
    visibleStatus === null &&
    !isInteractionLocked;
  const isBetActionAvailable =
    isRuntimeReady &&
    !shouldShowPreGameTableEntry &&
    isProviderIntroComplete &&
    isHowToPlayComplete &&
    busyAction === null &&
    currentSession?.status !== "active" &&
    !isInteractionLocked &&
    hasTableBudget;
  const pageShellClassName = [
    "page-shell",
    "mines-page-shell",
    useMobileLayout ? "mines-page-shell-mobile" : null,
    isEmbeddedView ? "mines-page-shell-embedded" : null,
  ]
    .filter(Boolean)
    .join(" ");
  const productShellClassName = [
    "panel",
    "mines-product-shell",
    "mines-product-shell-clean",
    useMobileLayout ? "mines-product-shell-mobile" : null,
    isEmbeddedView ? "mines-product-shell-embedded" : null,
    titleThemeSkin ? "mines-product-shell-skinned" : null,
    titleThemeSkin ? `mines-button-density-${titleThemeSkin.button_density}` : null,
    titleThemeSkin ? `mines-button-radius-${titleThemeSkin.button_radius}` : null,
    titleThemeSkin ? `mines-button-style-${titleThemeSkin.button_style}` : null,
    titleThemeSkin ? `mines-button-emphasis-${titleThemeSkin.button_emphasis}` : null,
  ]
    .filter(Boolean)
    .join(" ");

  useEffect(() => {
    if (bootStatus.kind !== "launch_ready") {
      return;
    }

    const { request: bootRequest, storageSnapshot } = bootStatus;

    setRuntimeConfig(null);
    setIsRuntimeDataReady(false);
    setIsTitleThemeResolved(false);
    setLaunchTitleCode(bootRequest.titleCode);
    setForceDemoMode(bootRequest.forceDemoMode);
    setAdminPreviewToken(bootRequest.previewToken);
    setIsEmbeddedView(bootRequest.isEmbeddedView);
    setLockedTableWalletType(bootRequest.walletSource);
    if (bootRequest.walletSource) {
      setSelectedTableWalletType(bootRequest.walletSource);
    }

    setAccessToken(bootRequest.forceDemoMode ? "" : storageSnapshot.accessToken);
    if (storageSnapshot.gameLaunchTitleCode === bootRequest.titleCode) {
      setGameLaunchToken(storageSnapshot.gameLaunchToken);
      setGameLaunchTokenExpiresAt(storageSnapshot.gameLaunchTokenExpiresAt);
    } else {
      clearStoredRealLaunchToken(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    }
    const canReuseStoredDemoLaunchToken =
      Boolean(storageSnapshot.demoAnonToken) &&
      !bootRequest.previewToken &&
      storageSnapshot.demoGameLaunchTitleCode === bootRequest.titleCode;
    if (storageSnapshot.demoAnonToken) {
      setDemoAnonToken(storageSnapshot.demoAnonToken);
      if (canReuseStoredDemoLaunchToken) {
        setDemoGameLaunchToken(storageSnapshot.demoGameLaunchToken);
        setDemoGameLaunchTokenExpiresAt(storageSnapshot.demoGameLaunchTokenExpiresAt);
      }
    }
    if (!canReuseStoredDemoLaunchToken) {
      clearStoredDemoLaunchToken(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    }
    // Only restore the chip balance from localStorage if there is still a
    // valid (non-expired) launch token — i.e. an ongoing demo session.
    // Otherwise the next /demo/launch will reset the server session to 100,
    // so the cached balance is stale and we must show 100.
    if (
      storageSnapshot.demoChipBalance &&
      !bootRequest.previewToken &&
      storageSnapshot.demoGameLaunchToken &&
      storageSnapshot.demoGameLaunchTitleCode === bootRequest.titleCode &&
      !isExpiredIsoDate(storageSnapshot.demoGameLaunchTokenExpiresAt)
    ) {
      setDemoChipBalance(storageSnapshot.demoChipBalance);
    } else {
      clearStoredDemoChipBalance(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    }
    void loadRuntime(bootRequest.titleCode);
    if (storageSnapshot.accessToken && !bootRequest.forceDemoMode) {
      void refreshAuthenticatedState(storageSnapshot.accessToken, {
        preferredGameSessionId: storageSnapshot.sessionId,
        showResumeOverlay: true,
        tableWalletType: bootRequest.walletSource ?? selectedTableWalletType,
      });
    }
  }, [bootStatus]);

  useEffect(() => {
    setIsProviderIntroComplete(false);
    setIsHowToPlayComplete(false);
    setTitleThemeAssets({});
    setTitleThemeSkin(null);
    setIsTitleThemeResolved(false);
  }, [launchTitleCode]);

  useEffect(() => {
    if (bootStatus.kind === "launch_ready" && isRuntimeDataReady && isTitleThemeResolved) {
      markRuntimeReady();
    }
  }, [bootStatus.kind, isRuntimeDataReady, isTitleThemeResolved, markRuntimeReady]);

  useEffect(() => {
    const mediaQuery = window.matchMedia(MINES_STANDALONE_MEDIA_QUERY);
    const syncMobileViewport = () => {
      setIsMobileViewport(mediaQuery.matches);
    };

    syncMobileViewport();
    mediaQuery.addEventListener("change", syncMobileViewport);
    return () => {
      mediaQuery.removeEventListener("change", syncMobileViewport);
    };
  }, []);

  useEffect(() => {
    function handleHostFullscreenState(event: MessageEvent) {
      if (event.origin !== window.location.origin) {
        return;
      }
      if (
        !event.data ||
        typeof event.data !== "object" ||
        !("type" in event.data) ||
        event.data.type !== MINES_EMBED_FULLSCREEN_STATE_MESSAGE
      ) {
        return;
      }
      setIsHostFullscreen(Boolean("active" in event.data && event.data.active));
    }

    window.addEventListener("message", handleHostFullscreenState);
    return () => {
      window.removeEventListener("message", handleHostFullscreenState);
    };
  }, []);

  useEffect(() => {
    if (!isMobileViewport) {
      return;
    }

    const previousHtmlOverflow = document.documentElement.style.overflow;
    const previousBodyOverflow = document.body.style.overflow;
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
    return () => {
      document.documentElement.style.overflow = previousHtmlOverflow;
      document.body.style.overflow = previousBodyOverflow;
    };
  }, [isEmbeddedView, isMobileViewport]);

  useEffect(() => {
    if (!gridSizes.includes(selectedGridSize)) {
      updateSelectedGridSize(gridSizes[0] ?? 25);
      return;
    }
    const supportedMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!supportedMineOptions.includes(selectedMineCount)) {
      updateSelectedMineCount(
        getDefaultVisibleMineCount(runtimeConfig, selectedGridSize, selectedMineCount),
      );
    }
  }, [gridSizes, mineOptions, runtimeConfig, selectedGridSize, selectedMineCount]);

  useEffect(() => {
    if (!isBetActionAvailable || isBetHintActive) {
      return;
    }

    let pulseTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const idleTimeoutId = setTimeout(() => {
      setIsBetHintActive(true);
      pulseTimeoutId = setTimeout(() => {
        setIsBetHintActive(false);
      }, 1100);
    }, 10_000);

    return () => {
      clearTimeout(idleTimeoutId);
      if (pulseTimeoutId !== null) {
        clearTimeout(pulseTimeoutId);
      }
    };
  }, [isBetActionAvailable, isBetHintActive, playerActivityTick]);

  useEffect(() => {
    if (!accessToken) {
      clearAccessSessionState();
      return;
    }

    if (
      accessSessionIdRef.current &&
      accessSessionTitleCodeRef.current === launchTitleCode
    ) {
      return;
    }

    if (isAccessSessionExpired || isSessionResumeLoading) {
      return;
    }

    void createAccessSession(accessToken).catch((error) => {
      handleGameError(error, "create-access-session");
    });
  }, [accessToken, isAccessSessionExpired, isSessionResumeLoading, launchTitleCode]);

  useEffect(() => {
    if (!accessToken || !accessSessionId || isInteractionLocked) {
      return;
    }

    const intervalId = setInterval(() => {
      void pingAccessSession(accessToken, accessSessionId);
    }, ACCESS_SESSION_PING_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [accessSessionId, accessToken, isInteractionLocked]);

  useEffect(() => {
    return () => {
      clearInactivityTimers();
      accessSessionRequestRef.current = null;
      accessSessionRequestTitleCodeRef.current = "";
    };
  }, []);

  function updateSelectedGridSize(value: number) {
    notePlayerActivity();
    selectedGridSizeRef.current = value;
    setSelectedGridSize(value);
  }

  function updateSelectedMineCount(value: number) {
    notePlayerActivity();
    selectedMineCountRef.current = value;
    setSelectedMineCount(value);
  }

  function updateBetAmount(value: string) {
    notePlayerActivity();
    betAmountRef.current = value;
    setBetAmount(value);
  }

  function handleTableWalletTypeChange(walletType: TableWalletType) {
    if (busyAction !== null || isInteractionLocked || walletType === selectedTableWalletType) {
      return;
    }

    notePlayerActivity();
    setSelectedTableWalletType(walletType);
    setTableSessionLimits(null);
    setTableEntryAmount("");
    if (accessToken) {
      void loadTableSessionLimits(accessToken, walletType).catch((error) => {
        handleGameError(error, "refresh-auth-state");
      });
    }
  }

  function clearInactivityTimers() {
    if (inactivityWarningTimeoutRef.current !== null) {
      clearTimeout(inactivityWarningTimeoutRef.current);
      inactivityWarningTimeoutRef.current = null;
    }
    if (inactivityExpiryTimeoutRef.current !== null) {
      clearTimeout(inactivityExpiryTimeoutRef.current);
      inactivityExpiryTimeoutRef.current = null;
    }
    if (inactivityCountdownIntervalRef.current !== null) {
      clearInterval(inactivityCountdownIntervalRef.current);
      inactivityCountdownIntervalRef.current = null;
    }
  }

  function handleAccessSessionExpired() {
    clearInactivityTimers();
    setBusyAction(null);
    setInactivityCountdownSeconds(0);
    setIsAccessSessionExpired(true);
    setFatalRuntimeOverlay(null);
  }

  function resetInactivityTimer() {
    clearInactivityTimers();
    setInactivityCountdownSeconds(null);

    inactivityWarningTimeoutRef.current = setTimeout(() => {
      setInactivityCountdownSeconds(ACCESS_SESSION_COUNTDOWN_SECONDS);
      inactivityCountdownIntervalRef.current = setInterval(() => {
        setInactivityCountdownSeconds((currentCountdown) => {
          if (currentCountdown === null) {
            return null;
          }
          return currentCountdown > 0 ? currentCountdown - 1 : 0;
        });
      }, 1000);
    }, ACCESS_SESSION_WARNING_MS);

    inactivityExpiryTimeoutRef.current = setTimeout(() => {
      handleAccessSessionExpired();
    }, ACCESS_SESSION_EXPIRY_MS);
  }

  function notePlayerActivity() {
    setIsBetHintActive(false);
    setPlayerActivityTick((currentTick) => currentTick + 1);
  }

  function touchUserActivity() {
    notePlayerActivity();
    if (isAccessSessionExpired) {
      return;
    }

    setIsAccessSessionExpired(false);
    resetInactivityTimer();
  }

  function clearAccessSessionState() {
    clearInactivityTimers();
    accessSessionIdRef.current = "";
    accessSessionTitleCodeRef.current = "";
    accessSessionRequestRef.current = null;
    accessSessionRequestTitleCodeRef.current = "";
    setAccessSessionId("");
    setInactivityCountdownSeconds(null);
    setIsAccessSessionExpired(false);
  }

  async function createAccessSession(token: string): Promise<string> {
    if (
      accessSessionIdRef.current.length > 0 &&
      accessSessionTitleCodeRef.current === launchTitleCode
    ) {
      return accessSessionIdRef.current;
    }

    if (
      accessSessionRequestRef.current !== null &&
      accessSessionRequestTitleCodeRef.current === launchTitleCode
    ) {
      return accessSessionRequestRef.current;
    }

    accessSessionRequestTitleCodeRef.current = launchTitleCode;
    const request = apiRequest<AccessSessionResponse>(
      "/access-sessions",
      {
        method: "POST",
        body: JSON.stringify({
          game_code: ACCESS_SESSION_GAME_CODE,
          title_code: launchTitleCode,
          site_code: "casinoking",
        }),
      },
      token,
    )
      .then((sessionData) => {
        accessSessionIdRef.current = sessionData.id;
        accessSessionTitleCodeRef.current = sessionData.title_code;
        setAccessSessionId(sessionData.id);
        setIsAccessSessionExpired(false);
        resetInactivityTimer();
        return sessionData.id;
      })
      .finally(() => {
        accessSessionRequestRef.current = null;
        accessSessionRequestTitleCodeRef.current = "";
      });

    accessSessionRequestRef.current = request;
    return request;
  }

  async function pingAccessSession(token: string, sessionId: string) {
    try {
      await apiRequest<AccessSessionResponse>(
        `/access-sessions/${sessionId}/ping`,
        {
          method: "POST",
        },
        token,
      );
    } catch (error) {
      if (error instanceof ApiRequestError && error.code === "GAME_STATE_CONFLICT") {
        handleAccessSessionExpired();
        return;
      }

      handleGameError(error, "refresh-access-session");
    }
  }

  async function loadRuntime(titleCode = launchTitleCode) {
    try {
      const configParams = new URLSearchParams({
        title_code: titleCode,
      });
      const [runtimeData] = await Promise.all([
        apiRequest<MinesRuntimeConfig>(`/games/mines/config?${configParams.toString()}`),
        apiRequest<FairnessCurrentConfig>("/games/mines/fairness/current"),
      ]);
      setRuntimeConfig(runtimeData);
      setIsRuntimeDataReady(true);
    } catch (error) {
      handleGameError(error, "load-runtime");
      markBootFatal("runtime");
    }
  }

  async function loadTableSessionLimits(token: string, walletType: TableWalletType) {
    const limitsData = await apiRequest<TableSessionLimitsResponse>(
      `/table-sessions/limits?wallet_type=${walletType}`,
      {},
      token,
    );
    setTableSessionLimits(limitsData);
    setTableEntryAmount("");
    return limitsData;
  }

  async function refreshAuthenticatedState(
    token: string,
    options: RefreshAuthenticatedStateOptions = {},
  ) {
    const {
      preferredGameSessionId = null,
      showResumeOverlay = false,
      tableWalletType = selectedTableWalletType,
    } = options;

    if (showResumeOverlay) {
      setIsSessionResumeLoading(true);
    }

    try {
      const authenticatedRequests: [
        Promise<Wallet[]>,
        Promise<RecentSessionSummary[]>,
        Promise<TableSessionLimitsResponse>,
      ] = [
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<RecentSessionSummary[]>("/games/mines/sessions", {}, token),
        loadTableSessionLimits(token, tableWalletType),
      ];
      const [walletData, recentSessions, tableLimitsData] = await Promise.all(
        authenticatedRequests,
      );

      setWallets(walletData);
      setTableSessionLimits(tableLimitsData);

      const resumableGameSession = selectResumableGameSession(
        recentSessions,
        preferredGameSessionId,
      );
      const preferredSession = preferredGameSessionId
        ? recentSessions.find((session) => session.game_session_id === preferredGameSessionId)
        : null;
      const sessionToLoad =
        resumableGameSession ??
        (preferredSession
          ? {
              gameSessionId: preferredSession.game_session_id,
              titleCode: preferredSession.title_code,
            }
          : preferredGameSessionId
            ? { gameSessionId: preferredGameSessionId, titleCode: launchTitleCode }
            : null);

      if (sessionToLoad) {
        try {
          await loadSession(token, sessionToLoad.gameSessionId, sessionToLoad.titleCode);
        } catch (error) {
          handleGameError(error, "resume-session");
        }
      } else {
        setTableSession(null);
        clearCurrentSessionSnapshot();
      }
    } catch (error) {
      handleGameError(error, "refresh-auth-state");
    } finally {
      if (showResumeOverlay) {
        setIsSessionResumeLoading(false);
      }
    }
  }

  async function loadSession(token: string, sessionId: string, sessionTitleCode = launchTitleCode) {
    const launchToken = await ensureGameLaunchToken(
      token,
      sessionTitleCode,
      gameLaunchToken,
      gameLaunchTokenExpiresAt,
      setGameLaunchToken,
      setGameLaunchTokenExpiresAt,
    );
    const [sessionData] = await Promise.all([
      apiRequest<SessionSnapshot>(
        `/games/mines/session/${sessionId}`,
        { headers: { "X-Game-Launch-Token": launchToken } },
        token,
      ),
      apiRequest<unknown>(
        `/games/mines/session/${sessionId}/fairness`,
        { headers: { "X-Game-Launch-Token": launchToken } },
        token,
      ),
    ]);
    setCurrentSession(sessionData);
    if (sessionData.status === "active" && sessionData.access_session_id) {
      accessSessionIdRef.current = sessionData.access_session_id;
      accessSessionTitleCodeRef.current = sessionData.title_code;
      setAccessSessionId(sessionData.access_session_id);
      setIsAccessSessionExpired(false);
      resetInactivityTimer();
    }
    if (sessionData.table_session_id) {
      try {
        const tableSessionData = await apiRequest<TableSessionResponse>(
          `/table-sessions/${sessionData.table_session_id}`,
          {},
          token,
        );
        setTableSession(tableSessionData.status === "active" ? tableSessionData : null);
        setSelectedTableWalletType(tableSessionData.wallet_type);
      } catch {
        setTableSession(null);
      }
    } else {
      setTableSession(null);
    }
    setFatalRuntimeOverlay(null);
    setStatus(null);
    updateSelectedGridSize(sessionData.grid_size);
    updateSelectedMineCount(sessionData.mine_count);
    if (sessionData.status === "active") {
      writeStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE, sessionId);
    } else {
      clearStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    }
  }

  async function ensureDemoAnonToken(): Promise<string> {
    const stored = readGameStorageSnapshot(
      window.localStorage,
      MINES_GAME_STORAGE_NAMESPACE,
    ).demoAnonToken;
    if (stored) {
      if (!demoAnonToken) {
        setDemoAnonToken(stored);
      }
      return stored;
    }
    const data = await apiRequest<DemoTokenResponse>("/demo/token", { method: "POST" });
    writeStoredDemoAnonToken(
      window.localStorage,
      MINES_GAME_STORAGE_NAMESPACE,
      data.anonymous_token,
    );
    setDemoAnonToken(data.anonymous_token);
    return data.anonymous_token;
  }

  async function ensureDemoGameLaunchToken(anonToken: string): Promise<string> {
    if (
      demoGameLaunchToken &&
      demoGameLaunchTokenExpiresAt &&
      !adminPreviewToken &&
      !isExpiredIsoDate(demoGameLaunchTokenExpiresAt)
    ) {
      return demoGameLaunchToken;
    }
    const data = await apiRequest<DemoLaunchResponse>("/demo/launch", {
      method: "POST",
      headers: { "X-Demo-Token": anonToken },
      body: JSON.stringify({
        title_code: launchTitleCode,
        preview_token: adminPreviewToken || undefined,
      }),
    });
    writeStoredDemoLaunchToken(
      window.localStorage,
      MINES_GAME_STORAGE_NAMESPACE,
      data.game_launch_token,
      data.expires_at,
      launchTitleCode,
    );
    setDemoGameLaunchToken(data.game_launch_token);
    setDemoGameLaunchTokenExpiresAt(data.expires_at);
    if (data.balance_chips) {
      setDemoChipBalance(data.balance_chips);
      writeStoredDemoChipBalance(
        window.localStorage,
        MINES_GAME_STORAGE_NAMESPACE,
        data.balance_chips,
      );
    }
    return data.game_launch_token;
  }

  async function loadDemoSession(launchToken: string, sessionId: string) {
    const sessionData = await apiRequest<SessionSnapshot>(
      `/games/mines/session/${sessionId}`,
      { headers: { "X-Game-Launch-Token": launchToken } },
    );
    setCurrentSession(sessionData);
    setFatalRuntimeOverlay(null);
    setStatus(null);
    updateSelectedGridSize(sessionData.grid_size);
    updateSelectedMineCount(sessionData.mine_count);
    if (sessionData.status === "active") {
      writeStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE, sessionId);
    } else {
      clearStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    }
  }

  async function fetchGameReplay(sessionId: string): Promise<MinesRoundReplay> {
    try {
      const headers: Record<string, string> = {};
      let bearerToken: string | undefined;
      if (isDemoMode) {
        const anonToken = await ensureDemoAnonToken();
        headers["X-Game-Launch-Token"] =
          demoGameLaunchToken || (await ensureDemoGameLaunchToken(anonToken));
      } else {
        headers["X-Game-Launch-Token"] = await ensureGameLaunchToken(
          accessToken,
          launchTitleCode,
          gameLaunchToken,
          gameLaunchTokenExpiresAt,
          setGameLaunchToken,
          setGameLaunchTokenExpiresAt,
        );
        bearerToken = accessToken;
      }
      return await apiRequest<MinesRoundReplay>(
        `/games/mines/session/${sessionId}/replay`,
        { headers },
        bearerToken,
      );
    } catch (error) {
      throw new Error(readErrorMessage(error, "Replay mano non disponibile."));
    }
  }

  async function fetchLatestReplaySessions(): Promise<LatestAccessSessionHistory[]> {
    if (!accessToken || !isAuthenticated) {
      return [];
    }

    try {
      const launchToken = await ensureGameLaunchToken(
        accessToken,
        launchTitleCode,
        gameLaunchToken,
        gameLaunchTokenExpiresAt,
        setGameLaunchToken,
        setGameLaunchTokenExpiresAt,
      );
      return await apiRequest<LatestAccessSessionHistory[]>(
        "/games/mines/access-sessions/latest",
        { headers: { "X-Game-Launch-Token": launchToken } },
        accessToken,
      );
    } catch (error) {
      throw new Error(readErrorMessage(error, "Storico sessioni non disponibile."));
    }
  }

  function clearDemoState() {
    setDemoGameLaunchToken("");
    setDemoGameLaunchTokenExpiresAt("");
    setDemoChipBalance("100");
    clearStoredDemoLaunchToken(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    clearStoredDemoChipBalance(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    clearStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    clearCurrentSessionSnapshot();
  }

  async function handleCreateTableSession({
    tableEntryAmount: requestedTableEntryAmount,
    walletSource,
  }: GameTableBalanceConfirmParams) {
    if (!accessToken || isDemoMode || isInteractionLocked) {
      return;
    }

    touchUserActivity();
    setBusyAction("create-table-session");
    try {
      const normalizedRequestedTableEntryAmount =
        normalizeWholeChipInput(requestedTableEntryAmount);
      const numericRequestedTableEntryAmount = Number.parseFloat(
        normalizedRequestedTableEntryAmount || "0",
      );
      if (
        numericRequestedTableEntryAmount <= 0 ||
        numericRequestedTableEntryAmount > numericTableEntryMaxAmount
      ) {
        throw new Error("Invalid table entry amount.");
      }
      const currentAccessSessionId =
        accessSessionIdRef.current || (await createAccessSession(accessToken));
      const tableSessionData = await apiRequest<TableSessionResponse>(
        "/table-sessions",
        {
          method: "POST",
          body: JSON.stringify({
            game_code: ACCESS_SESSION_GAME_CODE,
            title_code: launchTitleCode,
            site_code: "casinoking",
            wallet_type: walletSource,
            table_budget_amount: normalizedRequestedTableEntryAmount,
            access_session_id: currentAccessSessionId,
          }),
        },
        accessToken,
      );
      setTableSession(tableSessionData);
      setSelectedTableWalletType(tableSessionData.wallet_type);
      setStatus(null);
    } catch (error) {
      handleGameError(error, "create-table-session");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleStartSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isInteractionLocked) {
      return;
    }

    touchUserActivity();
    setBusyAction("start-session");
    clearCurrentSessionSnapshot();
    try {
      if (!accessToken) {
        // Demo path — no Bearer token, use demo game launch token
        const anonToken = await ensureDemoAnonToken();
        const launchToken = await ensureDemoGameLaunchToken(anonToken);
        const startData = await apiRequest<DemoStartResponse>("/games/mines/start", {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
            "X-Game-Launch-Token": launchToken,
          },
          body: JSON.stringify({
            grid_size: selectedGridSizeRef.current,
            mine_count: selectedMineCountRef.current,
            bet_amount: normalizeWholeChipInput(betAmountRef.current),
            wallet_type: "demo",
          }),
        });
        setDemoChipBalance(startData.wallet_balance_after);
        writeStoredDemoChipBalance(
          window.localStorage,
          MINES_GAME_STORAGE_NAMESPACE,
          startData.wallet_balance_after,
        );
        await loadDemoSession(launchToken, startData.game_session_id);
        return;
      }

      // Real path
      const currentAccessSessionId =
        accessSessionIdRef.current || (await createAccessSession(accessToken));
      if (tableSession?.status !== "active") {
        throw new Error("Choose a table session limit before starting a round.");
      }
      if (Number.parseFloat(tableSession?.table_balance_amount ?? "0") <= 0) {
        throw new Error("The table session limit has been reached.");
      }
      const launchToken = await ensureGameLaunchToken(
        accessToken,
        launchTitleCode,
        gameLaunchToken,
        gameLaunchTokenExpiresAt,
        setGameLaunchToken,
        setGameLaunchTokenExpiresAt,
      );
      const startData = await apiRequest<StartSessionResponse>(
        "/games/mines/start",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
            "X-Game-Launch-Token": launchToken,
          },
          body: JSON.stringify({
            grid_size: selectedGridSizeRef.current,
            mine_count: selectedMineCountRef.current,
            bet_amount: normalizeWholeChipInput(betAmountRef.current),
            wallet_type: tableSession?.wallet_type ?? effectiveWalletType,
            access_session_id: currentAccessSessionId,
            table_session_id: tableSession?.id ?? null,
          }),
        },
        accessToken,
      );
      if (startData.table_session) {
        setTableSession(startData.table_session);
      }
      await refreshAuthenticatedState(accessToken, {
        preferredGameSessionId: startData.game_session_id,
      });
      setStatus(null);
    } catch (error) {
      handleGameError(error, "start-session");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRevealCell(cellIndex: number): Promise<MinesRevealResult | null> {
    if (!currentSession || currentSession.status !== "active" || isInteractionLocked) {
      return null;
    }

    touchUserActivity();
    setBusyAction(`reveal-${cellIndex}`);
    try {
      const revealData = await apiRequest<{
        result: "safe" | "mine";
        status?: "active" | "won" | "lost";
        mine_positions?: number[];
        payout_amount?: string;
      }>(
        "/games/mines/reveal",
        {
          method: "POST",
          headers: {
            "X-Game-Launch-Token": isDemoMode
              ? demoGameLaunchToken
              : await ensureGameLaunchToken(
                  accessToken,
                  currentSession.title_code,
                  gameLaunchToken,
                  gameLaunchTokenExpiresAt,
                  setGameLaunchToken,
                  setGameLaunchTokenExpiresAt,
                ),
          },
          body: JSON.stringify({
            game_session_id: currentSession.game_session_id,
            cell_index: cellIndex,
          }),
        },
        isDemoMode ? undefined : accessToken,
      );
      const minePositions =
        revealData.result === "mine"
          ? revealData.mine_positions && revealData.mine_positions.length > 0
            ? revealData.mine_positions
            : [cellIndex]
          : null;
      const result: MinesRevealResult = {
        outcome:
          revealData.result === "mine"
            ? "mine"
            : revealData.status === "won"
              ? "won"
              : "safe",
        minePositions:
          revealData.result === "mine"
            ? minePositions
            : revealData.status === "won"
              ? revealData.mine_positions ?? []
              : null,
        payout:
          revealData.result === "mine"
            ? "0"
            : revealData.status === "won"
              ? revealData.payout_amount ?? currentSession.potential_payout
              : null,
      };

      const refreshRequest = isDemoMode
        ? loadDemoSession(demoGameLaunchToken, currentSession.game_session_id)
        : refreshAuthenticatedState(accessToken, {
            preferredGameSessionId: currentSession.game_session_id,
          });
      void refreshRequest
        .catch((error) => {
          handleGameError(error, "reveal");
        })
        .finally(() => {
          setBusyAction(null);
        });
      return result;
    } catch (error) {
      handleGameError(error, "reveal");
      setBusyAction(null);
      return null;
    }
  }

  async function handleCashout(): Promise<MinesCashoutResult | null> {
    if (!currentSession || currentSession.status !== "active" || isInteractionLocked) {
      return null;
    }

    touchUserActivity();
    setBusyAction("cashout");
    try {
      const cashoutData = await apiRequest<{
        game_session_id: string;
        status: string;
        payout_amount: string;
        wallet_balance_after: string;
        mine_positions?: number[];
        mode?: "demo" | "real";
      }>(
        "/games/mines/cashout",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
            "X-Game-Launch-Token": isDemoMode
              ? demoGameLaunchToken
              : await ensureGameLaunchToken(
                  accessToken,
                  currentSession.title_code,
                  gameLaunchToken,
                  gameLaunchTokenExpiresAt,
                  setGameLaunchToken,
                  setGameLaunchTokenExpiresAt,
                ),
          },
          body: JSON.stringify({
            game_session_id: currentSession.game_session_id,
          }),
        },
        isDemoMode ? undefined : accessToken,
      );
      const result: MinesCashoutResult = {
        payout: cashoutData.payout_amount,
        minePositions: cashoutData.mine_positions ?? [],
      };
      if (isDemoMode) {
        setDemoChipBalance(cashoutData.wallet_balance_after);
        writeStoredDemoChipBalance(
          window.localStorage,
          MINES_GAME_STORAGE_NAMESPACE,
          cashoutData.wallet_balance_after,
        );
        setCurrentSession({
          ...currentSession,
          status: "won",
          potential_payout: cashoutData.payout_amount,
          closed_at: new Date().toISOString(),
        });
        clearStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
        setBusyAction(null);
        return result;
      } else {
        void refreshAuthenticatedState(accessToken, {
          preferredGameSessionId: currentSession.game_session_id,
        })
          .catch((error) => {
            handleGameError(error, "cashout");
          })
          .finally(() => {
            setBusyAction(null);
          });
        return result;
      }
    } catch (error) {
      handleGameError(error, "cashout");
      setBusyAction(null);
      return null;
    }
  }

  async function closeCurrentSession() {
    if (!accessToken) {
      return;
    }
    const currentAccessSessionId = accessSessionIdRef.current;
    if (!currentAccessSessionId) {
      setTableSession(null);
      return;
    }
    try {
      await apiRequest<AccessSessionResponse>(
        `/access-sessions/${currentAccessSessionId}/close`,
        { method: "POST" },
        accessToken,
      );
    } catch {
      // Exit should not be blocked by a close race with an active round.
    }
    setTableSession(null);
  }

  function handleGameError(error: unknown, context: GameErrorContext) {
    if (isBearerTokenAuthError(error)) {
      clearAuthState(false);
      setStatus({
        kind: "error",
        text: copy("errors.auth_invalid"),
      });
      return;
    }

    if (isSessionVoidedByOperatorError(error)) {
      clearCurrentSessionSnapshot();
      setBusyAction(null);
      setFatalRuntimeOverlay({
        title: copy("runtime.session_closed_title"),
        text: copy("runtime.session_closed_text"),
      });
      return;
    }

    if (isReloadRequiredRuntimeError(error)) {
      clearCurrentSessionSnapshot();
      setBusyAction(null);
      setFatalRuntimeOverlay({
        title: copy("runtime.reload_required_title"),
        text: copy("runtime.reload_required_text"),
      });
      return;
    }

    setStatus({
      kind: "error",
      text: buildFriendlyGameErrorMessage(error, context, copy),
    });
  }

  function clearCurrentSessionSnapshot() {
    setCurrentSession(null);
    clearStoredSessionId(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
  }

  function handleGridSizeChange(gridSize: number) {
    if (isInteractionLocked || isActiveRound || gridSize === selectedGridSize) {
      return;
    }

    updateSelectedGridSize(gridSize);
    updateSelectedMineCount(getDefaultVisibleMineCount(runtimeConfig, gridSize));
    clearCurrentSessionSnapshot();
  }

  async function handleExit() {
    if (isHostFullscreen) {
      clearAccessSessionState();
      return;
    }
    if (isDemoMode) {
      clearDemoState();
    } else {
      try {
        await closeCurrentSession();
      } finally {
        clearAccessSessionState();
        clearCurrentSessionSnapshot();
      }
    }
    if (isEmbeddedView && window.parent !== window) {
      window.parent.postMessage({ type: MINES_EMBED_CLOSE_MESSAGE }, window.location.origin);
      return;
    }
    window.location.assign("/");
  }

  function clearAuthState(removeStatus: boolean) {
    clearAccessSessionState();
    setAccessToken("");
    setGameLaunchToken("");
    setGameLaunchTokenExpiresAt("");
    setWallets([]);
    setCurrentSession(null);
    setTableSession(null);
    setTableSessionLimits(null);
    setTableEntryAmount("");
    setFatalRuntimeOverlay(null);
    setIsSessionResumeLoading(false);
    clearStoredAuthState(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
    if (!removeStatus) {
      return;
    }
    setStatus({
      kind: "info",
      text: copy("runtime.demo_closed_text"),
    });
  }

  const runtimeOverlay = isSessionResumeLoading
    ? {
        title: copy("runtime.restoring_title"),
        text: copy("runtime.restoring_text"),
      }
    : fatalRuntimeOverlay
      ? fatalRuntimeOverlay
      : isAccessSessionExpired
        ? {
            title: copy("runtime.session_expired_title"),
            text: copy("runtime.session_expired_text"),
          }
        : isAccessSessionWarningActive
          ? {
              title: copy("runtime.session_expiring_title"),
              text: copy("runtime.session_expiring_text", {
                seconds: inactivityCountdownSeconds ?? ACCESS_SESSION_COUNTDOWN_SECONDS,
              }),
            }
          : null;

  const tableEntryChoices = [25, 50, 100].filter(
    (amount) => amount <= numericTableEntryMaxAmount,
  );
  const errorDialog = visibleStatus ? (
    <div className="mines-error-dialog-overlay" role="presentation">
      <article
        className="mines-error-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="mines-error-dialog-title"
      >
        <h2 id="mines-error-dialog-title">{copy("errors.action_needed")}</h2>
        <p>{visibleStatus.text}</p>
        <button className="button" type="button" onClick={() => setStatus(null)}>
          {copy("actions.ok")}
        </button>
      </article>
    </div>
  ) : null;

  const canRenderBootSurface =
    isLaunchContextReady || (bootStatus.kind === "fatal" && "request" in bootStatus);

  const providerIntroOverlay = shouldShowProviderIntro ? (
    <GameProviderBootstrap
      ready={isProviderIntroReady}
      skipLabel={copy("provider_intro.skip")}
      onComplete={() => setIsProviderIntroComplete(true)}
    />
  ) : null;
  const howToPlayGate = shouldShowHowToPlayGate ? (
    <GameHowToPlayGate
      title={copy("how_to_play.title")}
      titleId="mines-how-to-play-title"
      intro={copy("how_to_play.intro")}
      continueLabel={copy("how_to_play.continue")}
      cards={[
        {
          title: copy("how_to_play.card_1_title"),
          text: copy("how_to_play.card_1_text"),
          visual: <MinesHowToPlayVisual index={0} />,
        },
        {
          title: copy("how_to_play.card_2_title"),
          text: copy("how_to_play.card_2_text"),
          visual: <MinesHowToPlayVisual index={1} />,
        },
        {
          title: copy("how_to_play.card_3_title"),
          text: copy("how_to_play.card_3_text"),
          visual: <MinesHowToPlayVisual index={2} />,
        },
      ]}
      onContinue={() => {
        touchUserActivity();
        setIsHowToPlayComplete(true);
      }}
    />
  ) : null;

  const tableGate = shouldShowPreGameTableEntry ? (
    <GameTableBalanceGate
      amount={tableEntryAmount}
      amountInputId="table-entry-amount"
      amountLabel={copy("launch.table_entry_amount")}
      amountPlaceholder={formatWholeChipInput(tableSessionLimits?.default_table_amount ?? "0")}
      availableBalanceAmount={formatWholeChipInput(selectedTableWalletBalance)}
      availableBalanceLabel={copy("launch.available_balance")}
      availableBalanceValue={formatChipValue(selectedTableWalletBalance)}
      busy={busyAction === "create-table-session"}
      busyLabel={copy("launch.entering")}
      closeAriaLabel={copy("actions.back_to_site_aria")}
      confirmLabel={copy("launch.enter_game")}
      disabled={busyAction !== null || isInteractionLocked}
      errorDialog={errorDialog}
      eyebrow={gameTitle}
      isReady={tableSessionLimits !== null}
      lockedWalletSource={hasLockedTableWalletType ? selectedTableWalletType : null}
      maximumAmount={tableEntryMaxAmount}
      maximumAmountLabel={formatChipValue(tableEntryMaxAmount)}
      maximumLabel={copy("launch.maximum")}
      onAmountChange={(amount) => setTableEntryAmount(normalizeWholeChipInput(amount))}
      onClose={handleExit}
      onConfirm={handleCreateTableSession}
      onWalletSourceChange={handleTableWalletTypeChange}
      preload={<GameProviderBootstrapPreload />}
      quickAmounts={filterSafeTableBalanceQuickAmounts(
        tableEntryChoices.map((amount) => ({ value: String(amount) })),
        tableEntryMaxAmount,
        selectedTableWalletBalance,
      )}
      selectedWalletSource={selectedTableWalletType}
      title={copy("launch.choose_table_balance")}
      walletGroupAriaLabel={copy("launch.balance_source_aria")}
      walletOptions={[
        {
          balanceLabel: formatChipValue(cashWallet?.balance_snapshot ?? "0"),
          label: copy("launch.real_money"),
          value: "cash",
        },
        {
          balanceLabel: formatChipValue(bonusWallet?.balance_snapshot ?? "0"),
          label: copy("launch.bonus"),
          value: "bonus",
        },
      ]}
    />
  ) : null;

  const gameplayContent = (
    <>
      <MinesGameplay
        useMobileLayout={useMobileLayout}
        gameTitle={gameTitle}
        copy={copy}
        locale={minesCopy.locale}
        runtimeConfig={runtimeConfig}
        currentSession={currentSession}
        titleThemeAssets={titleThemeAssets}
        titleThemeSkin={titleThemeSkin}
        audioPreferences={gameAudioPreferences}
        isDemoMode={isDemoMode}
        isAuthenticated={isAuthenticated}
        isEmbeddedView={isEmbeddedView}
        isHostFullscreen={isHostFullscreen}
        isInteractionLocked={isInteractionLocked}
        isSessionResumeLoading={isSessionResumeLoading}
        isAccessSessionExpired={isAccessSessionExpired}
        isFatalRuntimeBlocked={isFatalRuntimeBlocked}
        isActiveRound={isActiveRound}
        isBetHintActive={isBetHintActive}
        hasTableBudget={hasTableBudget}
        busyAction={busyAction}
        gridSizes={gridSizes}
        mineOptions={mineOptions}
        controlGridSize={controlGridSize}
        controlMineCount={controlMineCount}
        selectedGridSize={selectedGridSize}
        selectedMineCount={selectedMineCount}
        betAmount={betAmount}
        visibleBalance={visibleBalance}
        effectiveWalletType={effectiveWalletType}
        onStartSession={handleStartSession}
        onRevealCell={handleRevealCell}
        onCashout={handleCashout}
        onGridSizeChange={handleGridSizeChange}
        onMineCountChange={updateSelectedMineCount}
        onBetAmountChange={(amount) => updateBetAmount(normalizeWholeChipInput(amount))}
        onExit={handleExit}
        loadReplay={fetchGameReplay}
        loadLatestReplaySessions={fetchLatestReplaySessions}
        formatGridLabel={formatGridLabel}
      />
    </>
  );

  const runtimeOverlayNode = runtimeOverlay ? (
    <div className="mines-access-session-overlay" role="presentation">
      <article
        className="mines-access-session-modal"
        role="dialog"
        aria-modal="true"
        aria-live="assertive"
        aria-label={runtimeOverlay.title}
      >
        <p className="mines-access-session-copy">{runtimeOverlay.text}</p>
      </article>
    </div>
  ) : null;

  return (
    <GameBootShell
      titleCode={launchTitleCode}
      statusKind={bootStatus.kind}
      canRenderBootSurface={canRenderBootSurface}
      isRuntimeReady={isRuntimeReady}
      showTableBalanceGate={shouldShowPreGameTableEntry}
      showProviderIntroGate={shouldShowProviderIntro}
      showHowToPlayGate={shouldShowHowToPlayGate}
      tableGatePageShellClassName="page-shell game-table-balance-page"
      pageShellClassName={pageShellClassName}
      productShellClassName={productShellClassName}
      onThemeChange={handleTitleThemeChange}
      onAudioPreferencesChange={setGameAudioPreferences}
      tableGate={tableGate}
      providerIntro={providerIntroOverlay}
      howToPlay={howToPlayGate}
      errorDialog={errorDialog}
      runtimeOverlay={runtimeOverlayNode}
    >
      {gameplayContent}
    </GameBootShell>
  );
}

async function ensureGameLaunchToken(
  accessToken: string,
  titleCode: string,
  currentLaunchToken: string,
  currentLaunchTokenExpiresAt: string,
  setGameLaunchToken: (value: string) => void,
  setGameLaunchTokenExpiresAt: (value: string) => void,
): Promise<string> {
  if (
    currentLaunchToken &&
    currentLaunchTokenExpiresAt &&
    !isExpiredIsoDate(currentLaunchTokenExpiresAt)
  ) {
    try {
      const validation = await apiRequest<LaunchTokenValidationResponse>(
        "/games/mines/launch/validate",
        {
          method: "POST",
          body: JSON.stringify({ game_launch_token: currentLaunchToken }),
        },
      );
      if (validation.title_code !== titleCode) {
        throw new Error("Stored launch token is for a different title");
      }
      return currentLaunchToken;
    } catch {
      clearStoredRealLaunchToken(window.localStorage, MINES_GAME_STORAGE_NAMESPACE);
      setGameLaunchToken("");
      setGameLaunchTokenExpiresAt("");
    }
  }

  const issueData = await apiRequest<LaunchTokenResponse>(
    "/games/mines/launch-token",
    {
      method: "POST",
      body: JSON.stringify({ game_code: "mines", title_code: titleCode }),
    },
    accessToken,
  );

  await apiRequest<LaunchTokenValidationResponse>(
    "/games/mines/launch/validate",
    {
      method: "POST",
      body: JSON.stringify({ game_launch_token: issueData.game_launch_token }),
    },
  );

  writeStoredRealLaunchToken(
    window.localStorage,
    MINES_GAME_STORAGE_NAMESPACE,
    issueData.game_launch_token,
    issueData.expires_at,
    titleCode,
  );
  setGameLaunchToken(issueData.game_launch_token);
  setGameLaunchTokenExpiresAt(issueData.expires_at);
  return issueData.game_launch_token;
}

function readMinesNetworkAwareErrorMessage(
  error: unknown,
  fallback: string,
  networkSuffix: string,
): string {
  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (
      normalizedMessage.includes("networkerror") ||
      normalizedMessage.includes("failed to fetch") ||
      normalizedMessage.includes("fetch resource")
    ) {
      return `${fallback} ${networkSuffix}`;
    }
  }

  return readErrorMessage(error, fallback);
}

function formatWholeChipInput(value: string): string {
  const wholeValue = Math.floor(Number.parseFloat(value));
  return Number.isFinite(wholeValue) && wholeValue > 0 ? String(wholeValue) : "";
}

function selectResumableGameSession(
  sessions: RecentSessionSummary[],
  preferredGameSessionId?: string | null,
): ResumeSessionTarget | null {
  const activeSessions = sessions.filter((session) => session.status === "active");
  if (activeSessions.length === 0) {
    return null;
  }

  if (preferredGameSessionId) {
    const preferredActiveSession = activeSessions.find(
      (session) => session.game_session_id === preferredGameSessionId,
    );
    if (preferredActiveSession) {
      return {
        gameSessionId: preferredActiveSession.game_session_id,
        titleCode: preferredActiveSession.title_code,
      };
    }
  }

  const latestActiveSession = activeSessions[0];
  return latestActiveSession
    ? {
        gameSessionId: latestActiveSession.game_session_id,
        titleCode: latestActiveSession.title_code,
      }
    : null;
}

function isBearerTokenAuthError(error: unknown): boolean {
  if (!(error instanceof ApiRequestError)) {
    return false;
  }

  const normalizedMessage = error.message.toLowerCase();
  if (error.status === 401) {
    return (
      normalizedMessage.includes("bearer token") ||
      normalizedMessage.includes("authenticated user")
    );
  }

  return error.status === 403 && normalizedMessage.includes("account is not active");
}

function isSessionVoidedByOperatorError(error: unknown): boolean {
  return error instanceof ApiRequestError && error.code === "SESSION_VOIDED_BY_OPERATOR";
}

function isReloadRequiredRuntimeError(error: unknown): boolean {
  if (!(error instanceof ApiRequestError)) {
    return false;
  }

  if (error.code === "GAME_STATE_CONFLICT") {
    return true;
  }

  if (
    error.code === "GAME_LAUNCH_TOKEN_REQUIRED" ||
    error.code === "GAME_LAUNCH_TOKEN_INVALID"
  ) {
    return true;
  }

  if (error.status !== 401 && error.status !== 403) {
    return false;
  }

  const normalizedMessage = error.message.toLowerCase();
  return (
    normalizedMessage.includes("game launch token") ||
    normalizedMessage.includes("game-launch-token") ||
    normalizedMessage.includes("ownership is not valid")
  );
}

function buildFriendlyGameErrorMessage(
  error: unknown,
  context: GameErrorContext,
  copy: MinesCopyResolver["t"],
): string {
  if (isInsufficientBalanceError(error)) {
    return copy("errors.insufficient_balance");
  }

  if (isNetworkRequestFailure(error)) {
    switch (context) {
      case "start-session":
        return copy("errors.network_start");
      case "reveal":
      case "cashout":
        return copy("errors.network_play");
      case "refresh-auth-state":
      case "resume-session":
        return copy("errors.network_sync");
      case "create-access-session":
      case "create-table-session":
      case "refresh-access-session":
        return copy("errors.network_access");
      case "load-runtime":
        return copy("errors.network_load_runtime");
      case "start-demo":
        return copy("errors.network_start_demo");
      default:
        return copy("errors.network_generic");
    }
  }

  switch (context) {
    case "start-session":
      return copy("errors.start_failed");
    case "reveal":
    case "cashout":
      return copy("errors.action_failed");
    case "refresh-auth-state":
      return copy("errors.update_balance_failed");
    case "resume-session":
      return copy("errors.resume_failed");
    case "create-access-session":
    case "create-table-session":
    case "refresh-access-session":
      return copy("errors.open_table_failed");
    case "load-runtime":
      return copy("errors.network_load_runtime");
    case "start-demo":
      return copy("errors.network_start_demo");
    default:
      return readMinesNetworkAwareErrorMessage(
        error,
        copy("errors.operation_failed"),
        copy("errors.network_suffix"),
      );
  }
}

function isInsufficientBalanceError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }

  if (error instanceof ApiRequestError && error.code === "INSUFFICIENT_BALANCE") {
    return true;
  }

  const normalizedMessage = error.message.toLowerCase();
  return (
    normalizedMessage.includes("not enough") ||
    normalizedMessage.includes("insufficient") ||
    normalizedMessage.includes("available balance") ||
    normalizedMessage.includes("demo chips") ||
    normalizedMessage.includes("limit exceeded") ||
    normalizedMessage.includes("limit has been reached")
  );
}

function isNetworkRequestFailure(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }

  const normalizedMessage = error.message.toLowerCase();
  return (
    normalizedMessage.includes("networkerror") ||
    normalizedMessage.includes("failed to fetch") ||
    normalizedMessage.includes("fetch resource")
  );
}
