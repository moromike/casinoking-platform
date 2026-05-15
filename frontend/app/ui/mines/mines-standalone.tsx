"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  extractValidationMessage,
  formatGridChoiceLabel,
  formatWholeChipDisplay,
  getDefaultVisibleMineCount,
  getMineOptions,
  getVisibleGridSizes,
  getVisibleMineOptions,
  getPayoutLadder,
  getRulesSections,
  isExpiredIsoDate,
  normalizeWholeChipInput,
  sessionStatusKind,
  shortId,
} from "@/app/lib/helpers";
import { MinesBoard } from "./mines-board";
import { MinesRulesModal, type MinesRulesModalTab } from "./mines-rules-modal";
import { MinesBalanceFooter } from "./mines-balance-footer";
import { MinesActionButtons } from "./mines-action-buttons";
import { MinesMobileSettingsSheet } from "./mines-mobile-settings-sheet";
import { MinesStageHeader } from "./mines-stage-header";
import { MinesWinCelebration } from "./mines-win-celebration";
import { DEFAULT_MINES_REPLAY_COPY } from "./mines-replay-copy";
import { MinesReplayViewer, type MinesRoundReplay } from "./mines-replay-viewer";
import {
  MinesProviderBootstrap,
  MinesProviderBootstrapPreload,
} from "./mines-provider-bootstrap";
import { MinesHowToPlayGate } from "./mines-how-to-play-gate";
import { MinesRuntimeTools } from "./mines-runtime-tools";
import { useMinesSounds } from "./use-mines-sounds";
import {
  createMinesCopyResolver,
  type MinesCopyResolver,
} from "./i18n/mines-copy-resolver";
import { GameBootShell } from "@/app/ui/game-runtime/game-boot-shell";
import { bootLog } from "@/app/ui/game-runtime/game-boot-log";
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
  SessionFairness,
  SessionSnapshot,
  StatusKind,
  StatusMessage,
  TitleTheme,
  Wallet,
} from "@/app/lib/types";
import { API_BASE_URL, ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";

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
  access_session_id: string | null;
  table_session_id?: string | null;
  access_session: {
    id: string;
    status: "active" | "closed" | "timed_out";
  } | null;
};

type LatestAccessSessionHistory = {
  id: string;
  game_code: string;
  title_code: string;
  site_code: string;
  status: "active" | "closed" | "timed_out";
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  rounds: MinesRoundReplay[];
};

type FatalRuntimeOverlay = {
  title: string;
  text: string;
};

type GameReplayState = {
  sessionId: string | null;
  replay: MinesRoundReplay | null;
  loading: boolean;
  error: string | null;
};

type LatestReplaySessionsState = {
  sessions: LatestAccessSessionHistory[];
  loading: boolean;
  error: string | null;
  selectedRoundId: string | null;
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
  const [currentEmail, setCurrentEmail] = useState("");
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [runtimeConfig, setRuntimeConfig] = useState<MinesRuntimeConfig | null>(null);
  const [currentFairness, setCurrentFairness] = useState<FairnessCurrentConfig | null>(null);
  const [currentSession, setCurrentSession] = useState<SessionSnapshot | null>(null);
  const [tableSession, setTableSession] = useState<TableSessionResponse | null>(null);
  const [tableSessionLimits, setTableSessionLimits] = useState<TableSessionLimitsResponse | null>(
    null,
  );
  const [selectedTableWalletType, setSelectedTableWalletType] =
    useState<TableWalletType>("cash");
  const [lockedTableWalletType, setLockedTableWalletType] = useState<TableWalletType | null>(null);
  const [tableEntryAmount, setTableEntryAmount] = useState("100");
  const [currentSessionFairness, setCurrentSessionFairness] = useState<SessionFairness | null>(
    null,
  );
  const [selectedGridSize, setSelectedGridSize] = useState(25);
  const [selectedMineCount, setSelectedMineCount] = useState(3);
  const [betAmount, setBetAmount] = useState("5");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [inactivityCountdownSeconds, setInactivityCountdownSeconds] = useState<number | null>(
    null,
  );
  const [isAccessSessionExpired, setIsAccessSessionExpired] = useState(false);
  const [roundResultNotice, setRoundResultNotice] = useState<{
    kind: "won" | "lost";
    payoutAmount: string;
  } | null>(null);
  const [lastReplaySessionId, setLastReplaySessionId] = useState<string | null>(null);
  const [rulesModalTab, setRulesModalTab] = useState<MinesRulesModalTab>("rules");
  const [gameReplayState, setGameReplayState] = useState<GameReplayState>({
    sessionId: null,
    replay: null,
    loading: false,
    error: null,
  });
  const [latestReplaySessionsState, setLatestReplaySessionsState] =
    useState<LatestReplaySessionsState>({
      sessions: [],
      loading: false,
      error: null,
      selectedRoundId: null,
    });
  const [revealedMinePositions, setRevealedMinePositions] = useState<number[]>([]);
  const [highlightedMineCell, setHighlightedMineCell] = useState<number | null>(null);
  const [safeEffectCell, setSafeEffectCell] = useState<number | null>(null);
  const [mineHitEffectCell, setMineHitEffectCell] = useState<number | null>(null);
  const [winCelebrationKey, setWinCelebrationKey] = useState(0);
  const [isEmbeddedView, setIsEmbeddedView] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isHostFullscreen, setIsHostFullscreen] = useState(false);
  const [showMobileSettings, setShowMobileSettings] = useState(false);
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
  const bootLoggedEventsRef = useRef<Set<string>>(new Set());
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
  const minesSounds = useMinesSounds(titleThemeAssets, gameAudioPreferences);
  const logBootEvent = useCallback((event: string) => {
    if (event !== "title_parsed" && !bootLoggedEventsRef.current.has("title_parsed")) {
      return;
    }
    if (bootLoggedEventsRef.current.has(event)) {
      return;
    }
    bootLoggedEventsRef.current.add(event);
    bootLog(event);
  }, []);
  const handleTitleThemeChange = useCallback((theme: TitleTheme | null) => {
    setTitleThemeAssets(theme?.assets ?? {});
    setIsTitleThemeResolved(true);
    logBootEvent("theme_loaded");
  }, [logBootEvent]);

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
  const payoutLadder = getPayoutLadder(runtimeConfig, selectedGridSize, selectedMineCount);
  const visibleGridSize = currentSession ? currentSession.grid_size : selectedGridSize;
  const boardSide = Math.sqrt(visibleGridSize);
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const bonusWallet = wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null;
  const isActiveRound = currentSession?.status === "active";
  const replayCandidateSessionId =
    currentSession && currentSession.status !== "active"
      ? currentSession.game_session_id
      : lastReplaySessionId;
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
  const rulesSections = getRulesSections(runtimeConfig);
  const visiblePayoutLadder = currentSession
    ? getPayoutLadder(runtimeConfig, currentSession.grid_size, currentSession.mine_count)
    : payoutLadder;
  const visibleBalance =
    isDemoMode
      ? demoChipBalance
      : isRealTableSessionActive
      ? tableSession.table_balance_amount
      : isActiveRound
      ? currentSession.wallet_balance_after_start
      : selectedWallet?.balance_snapshot ?? "0";
  const previewWindowStart = currentSession?.safe_reveals_count ?? 0;
  const previewMultipliers = visiblePayoutLadder.slice(previewWindowStart, previewWindowStart + 5);
  const stageSubtitle =
    roundResultNotice?.kind === "won"
      ? copy("round.won_notice", {
          amount: formatChipValue(roundResultNotice.payoutAmount),
        })
      : roundResultNotice?.kind === "lost"
        ? copy("round.lost_notice")
        : null;
  const stageSubtitleTone =
    roundResultNotice?.kind === "won"
      ? "won"
      : roundResultNotice?.kind === "lost"
        ? "lost"
        : null;
  const visibleMinePositions =
    revealedMinePositions.length > 0
      ? revealedMinePositions
      : highlightedMineCell !== null
        ? [highlightedMineCell]
        : [];
  const betButtonLabel =
    busyAction === "start-session" ? copy("actions.bet_loading") : copy("actions.bet");
  const collectButtonLabel =
    busyAction === "cashout" ? copy("actions.collect_loading") : copy("actions.collect");
  const visibleStatus = status?.kind === "error" ? status : null;
  const useMobileLayout = isMobileViewport;
  const tableEntryMaxAmount = tableSessionLimits?.max_table_amount ?? "0";
  const selectedTableWallet =
    selectedTableWalletType === "bonus" ? bonusWallet ?? null : cashWallet;
  const hasLockedTableWalletType = lockedTableWalletType !== null;
  const selectedTableWalletBalance =
    tableSessionLimits?.wallet_balance_available ?? selectedTableWallet?.balance_snapshot ?? "0";
  const normalizedTableEntryAmount = normalizeWholeChipInput(tableEntryAmount);
  const numericTableEntryAmount = Number.parseFloat(normalizedTableEntryAmount || "0");
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
  ]
    .filter(Boolean)
    .join(" ");

  useEffect(() => {
    if (bootStatus.kind !== "launch_ready") {
      return;
    }

    const { request: bootRequest, storageSnapshot } = bootStatus;

    logBootEvent("title_parsed");
    setRuntimeConfig(null);
    setCurrentFairness(null);
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
    setCurrentEmail(storageSnapshot.email);
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
    logBootEvent("token_validated");
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
    setIsTitleThemeResolved(false);
  }, [launchTitleCode]);

  useEffect(() => {
    if (bootStatus.kind === "launch_ready" && isRuntimeDataReady && isTitleThemeResolved) {
      markRuntimeReady();
    }
  }, [bootStatus.kind, isRuntimeDataReady, isTitleThemeResolved, markRuntimeReady]);

  useEffect(() => {
    if (shouldShowProviderIntro) {
      logBootEvent("intro_started");
    }
  }, [logBootEvent, shouldShowProviderIntro]);

  useEffect(() => {
    if (shouldShowHowToPlayGate) {
      logBootEvent("how_to_play_shown");
    }
  }, [logBootEvent, shouldShowHowToPlayGate]);

  useEffect(() => {
    if (
      isRuntimeReady &&
      !shouldShowPreGameTableEntry &&
      isProviderIntroComplete &&
      isHowToPlayComplete
    ) {
      logBootEvent("gameplay_mounted");
    }
  }, [
    isHowToPlayComplete,
    isProviderIntroComplete,
    isRuntimeReady,
    logBootEvent,
    shouldShowPreGameTableEntry,
  ]);

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
    if (!useMobileLayout) {
      setShowMobileSettings(false);
    }
  }, [useMobileLayout]);

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
    setTableEntryAmount("100");
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
    setShowMobileSettings(false);
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
      const [runtimeData, fairnessData] = await Promise.all([
        apiRequest<MinesRuntimeConfig>(`/games/mines/config?${configParams.toString()}`),
        apiRequest<FairnessCurrentConfig>("/games/mines/fairness/current"),
      ]);
      setRuntimeConfig(runtimeData);
      setCurrentFairness(fairnessData);
      setIsRuntimeDataReady(true);
      logBootEvent("config_loaded");
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
    setTableEntryAmount(formatWholeChipInput(limitsData.default_table_amount));
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

      const resumableGameSessionId = selectResumableGameSessionId(
        recentSessions,
        preferredGameSessionId,
      );
      const sessionIdToLoad = resumableGameSessionId ?? preferredGameSessionId ?? null;

      if (sessionIdToLoad) {
        try {
          await loadSession(token, sessionIdToLoad);
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

  async function loadSession(token: string, sessionId: string) {
    const launchToken = await ensureGameLaunchToken(
      token,
      launchTitleCode,
      gameLaunchToken,
      gameLaunchTokenExpiresAt,
      setGameLaunchToken,
      setGameLaunchTokenExpiresAt,
    );
    const [sessionData, fairnessData] = await Promise.all([
      apiRequest<SessionSnapshot>(
        `/games/mines/session/${sessionId}`,
        { headers: { "X-Game-Launch-Token": launchToken } },
        token,
      ),
      apiRequest<SessionFairness>(
        `/games/mines/session/${sessionId}/fairness`,
        { headers: { "X-Game-Launch-Token": launchToken } },
        token,
      ),
    ]);
    setRoundResultNotice(null);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    if (sessionData.status !== "lost") {
      setRevealedMinePositions([]);
    }
    setCurrentSession(sessionData);
    setCurrentSessionFairness(fairnessData);
    if (sessionData.status !== "active") {
      setLastReplaySessionId(sessionData.game_session_id);
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
    setCurrentSessionFairness(null);
    if (sessionData.status !== "active") {
      setLastReplaySessionId(sessionData.game_session_id);
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

  async function loadGameReplay(sessionId: string) {
    setGameReplayState((current) => ({
      sessionId,
      replay: current.sessionId === sessionId ? current.replay : null,
      loading: true,
      error: null,
    }));
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
      const replay = await apiRequest<MinesRoundReplay>(
        `/games/mines/session/${sessionId}/replay`,
        { headers },
        bearerToken,
      );
      setGameReplayState({
        sessionId,
        replay,
        loading: false,
        error: null,
      });
    } catch (error) {
      setGameReplayState({
        sessionId,
        replay: null,
        loading: false,
        error: readErrorMessage(error, "Replay mano non disponibile."),
      });
    }
  }

  async function loadLatestReplaySessions() {
    if (!accessToken || !isAuthenticated) {
      return;
    }

    setLatestReplaySessionsState((current) => ({
      ...current,
      loading: true,
      error: null,
    }));
    try {
      const launchToken = await ensureGameLaunchToken(
        accessToken,
        launchTitleCode,
        gameLaunchToken,
        gameLaunchTokenExpiresAt,
        setGameLaunchToken,
        setGameLaunchTokenExpiresAt,
      );
      const sessions = await apiRequest<LatestAccessSessionHistory[]>(
        "/games/mines/access-sessions/latest",
        { headers: { "X-Game-Launch-Token": launchToken } },
        accessToken,
      );
      const roundIds = new Set(
        sessions.flatMap((session) => session.rounds.map((round) => round.game_session_id)),
      );
      setLatestReplaySessionsState((current) => {
        const selectedRoundId =
          current.selectedRoundId && roundIds.has(current.selectedRoundId)
            ? current.selectedRoundId
            : sessions.flatMap((session) => session.rounds)[0]?.game_session_id ?? null;

        return {
          sessions,
          loading: false,
          error: null,
          selectedRoundId,
        };
      });
    } catch (error) {
      setLatestReplaySessionsState((current) => ({
        ...current,
        loading: false,
        error: readErrorMessage(error, "Storico sessioni non disponibile."),
      }));
    }
  }

  function resetGameReplayState({ clearLast = false }: { clearLast?: boolean } = {}) {
    if (clearLast) {
      setLastReplaySessionId(null);
      setRulesModalTab("rules");
    }
    setGameReplayState({
      sessionId: null,
      replay: null,
      loading: false,
      error: null,
    });
    setLatestReplaySessionsState({
      sessions: [],
      loading: false,
      error: null,
      selectedRoundId: null,
    });
  }

  function openRulesModal() {
    setRulesModalTab("rules");
    setShowRules(true);
  }

  function handleRulesModalTabChange(tab: MinesRulesModalTab) {
    setRulesModalTab(tab);
    if (tab !== "replay" || isInteractionLocked) {
      return;
    }
    if (isAuthenticated) {
      void loadLatestReplaySessions();
      return;
    }
    if (!replayCandidateSessionId) {
      return;
    }
    if (
      gameReplayState.sessionId !== replayCandidateSessionId ||
      (!gameReplayState.replay && !gameReplayState.loading)
    ) {
      void loadGameReplay(replayCandidateSessionId);
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

  async function handleCreateTableSession() {
    if (!accessToken || isDemoMode || isInteractionLocked) {
      return;
    }

    touchUserActivity();
    setBusyAction("create-table-session");
    try {
      if (numericTableEntryAmount <= 0 || numericTableEntryAmount > numericTableEntryMaxAmount) {
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
            wallet_type: selectedTableWalletType,
            table_budget_amount: normalizedTableEntryAmount,
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
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    resetGameReplayState({ clearLast: true });
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
        setHighlightedMineCell(null);
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
      setHighlightedMineCell(null);
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

  async function handleRevealCell(cellIndex: number) {
    if (!currentSession || currentSession.status !== "active" || isInteractionLocked) {
      return;
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
                    launchTitleCode,
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
          : [];
      if (revealData.result === "mine") {
        minesSounds.play("audio_mine_hit");
        setLastReplaySessionId(currentSession.game_session_id);
        setHighlightedMineCell(null);
        setRevealedMinePositions(minePositions);
        setSafeEffectCell(null);
        setMineHitEffectCell(cellIndex);
        setRoundResultNotice({
          kind: "lost",
          payoutAmount: "0",
        });
      } else {
        minesSounds.play("audio_safe_reveal");
        setHighlightedMineCell(null);
        setRevealedMinePositions([]);
        setSafeEffectCell(cellIndex);
        setMineHitEffectCell(null);
      }

      if (isDemoMode) {
        await loadDemoSession(demoGameLaunchToken, currentSession.game_session_id);
      } else {
        await refreshAuthenticatedState(accessToken, {
          preferredGameSessionId: currentSession.game_session_id,
        });
      }

      if (revealData.status === "won") {
        minesSounds.play("audio_win");
        setLastReplaySessionId(currentSession.game_session_id);
        setRevealedMinePositions(revealData.mine_positions ?? []);
        setWinCelebrationKey((currentKey) => currentKey + 1);
        setRoundResultNotice({
          kind: "won",
          payoutAmount: revealData.payout_amount ?? currentSession.potential_payout,
        });
      }
    } catch (error) {
      handleGameError(error, "reveal");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCashout() {
    if (!currentSession || currentSession.status !== "active" || isInteractionLocked) {
      return;
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
                    launchTitleCode,
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
      if (isDemoMode) {
        minesSounds.play("audio_collect");
        setLastReplaySessionId(currentSession.game_session_id);
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
      } else {
        minesSounds.play("audio_collect");
        setLastReplaySessionId(currentSession.game_session_id);
        await refreshAuthenticatedState(accessToken, {
          preferredGameSessionId: currentSession.game_session_id,
        });
      }
      setHighlightedMineCell(null);
      setRevealedMinePositions(cashoutData.mine_positions ?? []);
      setSafeEffectCell(null);
      setMineHitEffectCell(null);
      setWinCelebrationKey((currentKey) => currentKey + 1);
      setRoundResultNotice({
        kind: "won",
        payoutAmount: cashoutData.payout_amount,
      });
    } catch (error) {
      handleGameError(error, "cashout");
    } finally {
      setBusyAction(null);
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
      setShowMobileSettings(false);
      setFatalRuntimeOverlay({
        title: copy("runtime.session_closed_title"),
        text: copy("runtime.session_closed_text"),
      });
      return;
    }

    if (isReloadRequiredRuntimeError(error)) {
      clearCurrentSessionSnapshot();
      setBusyAction(null);
      setShowMobileSettings(false);
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
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    resetGameReplayState({ clearLast: true });
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
    setCurrentEmail("");
    setWallets([]);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setTableSession(null);
    setTableSessionLimits(null);
    setTableEntryAmount("100");
    setHighlightedMineCell(null);
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    resetGameReplayState({ clearLast: true });
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

  const runtimeTools = (
    <MinesRuntimeTools
      locale={minesCopy.locale}
      audio={{
        hasAnySound: minesSounds.hasAnySound,
        muted: gameAudioPreferences.muted,
        setMuted: gameAudioPreferences.setMuted,
        setVolume: gameAudioPreferences.setVolume,
        volume: gameAudioPreferences.volume,
      }}
      copy={{
        effectsAria: copy("audio.effects_aria"),
        effectsLabel: copy("audio.effects_label"),
        effectsOn: copy("audio.effects_on"),
        effectsOff: copy("audio.effects_off"),
        volume: copy("audio.volume"),
      }}
    />
  );

  const railHeader = (
    <div className="list-row mines-rail-header">
      <div className="mines-rail-tools">
        <button
          className="button-ghost mines-rules-trigger"
          type="button"
          disabled={isInteractionLocked}
          onClick={openRulesModal}
          aria-label={copy("actions.game_info")}
        >
          i
        </button>
        {runtimeTools}
      </div>
      {isDemoMode ? (
        <span className="status-badge info mines-mode-badge">{copy("mode.demo_badge")}</span>
      ) : null}
    </div>
  );

  const mobileStageTools = useMobileLayout ? (
    <div className="mines-mobile-stage-tools">
      <button
        className="button-ghost mines-rules-trigger"
        type="button"
        disabled={isInteractionLocked}
        onClick={openRulesModal}
        aria-label={copy("actions.game_info")}
      >
        i
      </button>
      {runtimeTools}
    </div>
  ) : null;

  const mobileSettingsSummary = useMobileLayout ? (
    <div className="mines-mobile-settings-summary">
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={isInteractionLocked}
        onClick={() => setShowMobileSettings(true)}
      >
        {formatGridLabel(controlGridSize)}
      </button>
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={isInteractionLocked}
        onClick={() => setShowMobileSettings(true)}
      >
        {copy("settings.mines_count_label", { count: controlMineCount })}
      </button>
    </div>
  ) : null;

  const configFields = (
    <div className="stack mines-control-stack mines-config-sections">
      <div className="field mines-config-section">
        <label>{copy("settings.grid_size")}</label>
        <div className="mines-config-options-grid">
          {gridSizes.map((gridSize) => (
            <button
              key={gridSize}
              className={controlGridSize === gridSize ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound || isInteractionLocked}
              onClick={() => handleGridSizeChange(gridSize)}
            >
              {formatGridLabel(gridSize)}
            </button>
          ))}
        </div>
      </div>

      <div className="field mines-config-section">
        <label>{copy("settings.mines")}</label>
        <div className="mines-config-options-grid">
          {mineOptions.map((mineCount) => (
            <button
              key={mineCount}
              className={controlMineCount === mineCount ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound || isInteractionLocked}
              onClick={() => updateSelectedMineCount(mineCount)}
            >
              {mineCount}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const betField = (
    <div className="field mines-bet-field">
      <label htmlFor="bet-amount-standalone">{copy("settings.bet_amount")}</label>
      <input
        id="bet-amount-standalone"
        value={betAmount}
        onChange={(event) => updateBetAmount(normalizeWholeChipInput(event.target.value))}
        inputMode="numeric"
        placeholder="5"
        disabled={busyAction !== null || isInteractionLocked || isActiveRound}
      />
      <div className="quick-chip-row">
        {["1", "2", "5", "10", "25"].map((amount) => (
          <button
            key={amount}
            className={betAmount === amount ? "quick-chip active" : "quick-chip"}
            type="button"
            disabled={busyAction !== null || isInteractionLocked || isActiveRound}
            onClick={() => updateBetAmount(amount)}
          >
            {amount}
          </button>
        ))}
      </div>
    </div>
  );

  const actionButtons = (
    <MinesActionButtons
      useMobileLayout={useMobileLayout}
      betButtonLabel={betButtonLabel}
      collectButtonLabel={collectButtonLabel}
      isBetDisabled={
        busyAction !== null ||
        currentSession?.status === "active" ||
        isInteractionLocked ||
        !hasTableBudget
      }
      isBetLoading={busyAction === "start-session"}
      isCollectDisabled={
        !currentSession ||
        currentSession.status !== "active" ||
        currentSession.safe_reveals_count <= 0 ||
        busyAction !== null ||
        isInteractionLocked
      }
      isCollectLoading={busyAction === "cashout"}
      shouldPulseBetButton={isBetHintActive}
      onCashout={() => void handleCashout()}
    />
  );

  const balanceFooter = (
    <MinesBalanceFooter
      isDemoPlayer={isDemoMode}
      visibleBalance={visibleBalance}
      potentialPayout={
        currentSession?.status === "active" && currentSession.safe_reveals_count > 0
          ? currentSession.potential_payout
          : null
      }
      copy={{
        demoBalance: copy("balance.demo"),
        defaultBalance: copy("balance.default"),
        walletBalance: (walletType) => copy("balance.wallet", { walletType }),
        win: copy("balance.win"),
        zeroChips: copy("balance.zero_chips"),
        chipSuffix: copy("format.chip_suffix"),
      }}
      balanceLabel={isDemoMode ? undefined : copy("balance.table")}
      walletType={effectiveWalletType}
    />
  );

  const stageHeader = (
    <MinesStageHeader
      gameTitle={gameTitle}
      exitAriaLabel={copy("actions.exit_aria", { gameTitle })}
      stageSubtitle={stageSubtitle}
      stageSubtitleTone={stageSubtitleTone}
      previewMultipliers={previewMultipliers}
      multiplierSuffix={copy("format.multiplier_suffix")}
      previewWindowStart={previewWindowStart}
      visibleGridSize={visibleGridSize}
      selectedMineCount={selectedMineCount}
      currentSession={currentSession}
      isEmbeddedView={isEmbeddedView}
      isHostFullscreen={isHostFullscreen}
      useMobileLayout={useMobileLayout}
      mobileStageTools={mobileStageTools}
      onExit={handleExit}
    />
  );

  const boardSection = (
    <article className="board-shell mines-stage-board">
      <MinesBoard
        cellCount={visibleGridSize}
        boardSide={boardSide}
        revealedCells={currentSession?.revealed_cells ?? []}
        minePositions={visibleMinePositions}
        busy={busyAction !== null || isInteractionLocked}
        isInteractiveRound={Boolean(currentSession && currentSession.status === "active" && !isInteractionLocked)}
        onRevealCell={(cellIndex) => void handleRevealCell(cellIndex)}
        assets={runtimeConfig?.presentation_config?.board_assets}
        safeEffectCell={safeEffectCell}
        mineHitEffectCell={mineHitEffectCell}
        copy={{
          mineAriaLabel: (cell) => copy("board.aria.mine", { cell }),
          safeAriaLabel: (cell) => copy("board.aria.safe", { cell }),
          hiddenAriaLabel: (cell) => copy("board.aria.hidden", { cell }),
          mineFace: copy("board.face.mine"),
          safeFace: copy("board.face.safe"),
          hiddenFace: copy("board.face.hidden"),
        }}
        closed={
          isSessionResumeLoading ||
          isAccessSessionExpired ||
          isFatalRuntimeBlocked ||
          (currentSession?.status !== "active" && currentSession !== null)
        }
      />
      {winCelebrationKey > 0 ? <MinesWinCelebration key={winCelebrationKey} /> : null}
    </article>
  );

  const latestReplayRounds = latestReplaySessionsState.sessions.flatMap(
    (session) => session.rounds,
  );
  const selectedLatestReplayRound =
    latestReplayRounds.find(
      (round) => round.game_session_id === latestReplaySessionsState.selectedRoundId,
    ) ??
    latestReplayRounds[0] ??
    null;
  const selectedLatestReplayIndex = selectedLatestReplayRound
    ? latestReplayRounds.findIndex(
        (round) => round.game_session_id === selectedLatestReplayRound.game_session_id,
      )
    : -1;
  const canSelectPreviousLatestReplay = selectedLatestReplayIndex > 0;
  const canSelectNextLatestReplay =
    selectedLatestReplayIndex >= 0 && selectedLatestReplayIndex < latestReplayRounds.length - 1;

  function selectLatestReplayRound(roundId: string) {
    setLatestReplaySessionsState((current) => ({
      ...current,
      selectedRoundId: roundId,
    }));
  }

  function selectLatestReplayRoundByOffset(offset: number) {
    const nextRound = latestReplayRounds[selectedLatestReplayIndex + offset];
    if (!nextRound) {
      return;
    }
    selectLatestReplayRound(nextRound.game_session_id);
  }

  const latestReplaySessionsPanel = (
    <div className="mines-latest-replay-panel">
      {latestReplaySessionsState.loading ? (
        <p className="empty-state">Caricamento ultime sessioni...</p>
      ) : latestReplaySessionsState.error ? (
        <p className="status-line">{latestReplaySessionsState.error}</p>
      ) : latestReplaySessionsState.sessions.length === 0 ? (
        <p className="empty-state">Nessuna sessione Mines trovata per questo Title.</p>
      ) : (
        <div className="mines-latest-replay-layout">
          <div className="mines-latest-session-list">
            {latestReplaySessionsState.sessions.map((session, sessionIndex) => (
              <article className="mines-latest-session-card" key={session.id}>
                <header className="mines-latest-session-header">
                  <div>
                    <span>Sessione {sessionIndex + 1}</span>
                    <strong>{formatReplayDateTime(session.started_at)}</strong>
                  </div>
                  <span className="mines-latest-session-count">
                    {session.rounds.length} mani
                  </span>
                </header>
                {session.rounds.length > 0 ? (
                  <div className="mines-latest-round-list">
                    {session.rounds.map((round) => {
                      const isSelected =
                        selectedLatestReplayRound?.game_session_id === round.game_session_id;
                      return (
                        <button
                          className={`mines-latest-round-button${isSelected ? " is-active" : ""}`}
                          type="button"
                          key={round.game_session_id}
                          onClick={() => selectLatestReplayRound(round.game_session_id)}
                        >
                          <span>{formatReplayDateTime(round.closed_at ?? round.created_at)}</span>
                          <strong>{DEFAULT_MINES_REPLAY_COPY.formatStatus(round.status)}</strong>
                          <span>
                            Bet {formatChipValue(round.bet_amount)} / Win{" "}
                            {formatChipValue(round.payout_amount)}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="empty-state">Nessuna mano in questa sessione.</p>
                )}
              </article>
            ))}
          </div>

          <div className="mines-latest-replay-preview">
            {selectedLatestReplayRound ? (
              <>
                <MinesReplayViewer
                  replay={selectedLatestReplayRound}
                  copy={DEFAULT_MINES_REPLAY_COPY}
                />
                <div className="mines-latest-replay-nav" aria-label="Scorri mani replay">
                  <button
                    type="button"
                    aria-label="Mano precedente"
                    disabled={!canSelectPreviousLatestReplay}
                    onClick={() => selectLatestReplayRoundByOffset(-1)}
                  >
                    &larr;
                  </button>
                  <button
                    type="button"
                    aria-label="Mano successiva"
                    disabled={!canSelectNextLatestReplay}
                    onClick={() => selectLatestReplayRoundByOffset(1)}
                  >
                    &rarr;
                  </button>
                </div>
              </>
            ) : (
              <p className="empty-state">Seleziona una mano chiusa.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const singleReplayContent = replayCandidateSessionId ? (
    gameReplayState.loading ? (
      <p className="empty-state">Caricamento replay mano...</p>
    ) : gameReplayState.error ? (
      <p className="status-line">{gameReplayState.error}</p>
    ) : gameReplayState.replay ? (
      <MinesReplayViewer
        replay={gameReplayState.replay}
        copy={DEFAULT_MINES_REPLAY_COPY}
      />
    ) : (
      <p className="empty-state">Seleziona Replay per caricare la mano chiusa.</p>
    )
  ) : (
    <p className="empty-state">Replay disponibile dopo una mano chiusa.</p>
  );
  const rulesReplayContent = isAuthenticated ? latestReplaySessionsPanel : singleReplayContent;

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
  const isTableEntryDisabled =
    busyAction !== null ||
    isInteractionLocked ||
    tableSessionLimits === null ||
    numericTableEntryAmount <= 0 ||
    numericTableEntryAmount > numericTableEntryMaxAmount;
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
    <MinesProviderBootstrap
      ready={isProviderIntroReady}
      skipLabel={copy("provider_intro.skip")}
      onComplete={() => {
        logBootEvent("intro_ended");
        setIsProviderIntroComplete(true);
      }}
    />
  ) : null;
  const howToPlayGate = shouldShowHowToPlayGate ? (
    <MinesHowToPlayGate
      copy={{
        title: copy("how_to_play.title"),
        intro: copy("how_to_play.intro"),
        continueLabel: copy("how_to_play.continue"),
        cards: [
          {
            title: copy("how_to_play.card_1_title"),
            text: copy("how_to_play.card_1_text"),
          },
          {
            title: copy("how_to_play.card_2_title"),
            text: copy("how_to_play.card_2_text"),
          },
          {
            title: copy("how_to_play.card_3_title"),
            text: copy("how_to_play.card_3_text"),
          },
        ],
      }}
      onContinue={() => {
        touchUserActivity();
        setIsHowToPlayComplete(true);
      }}
    />
  ) : null;

  const tableGate = shouldShowPreGameTableEntry ? (
    <section className="panel mines-launch-gate">
      <MinesProviderBootstrapPreload />
      <button
        className="button-ghost mines-launch-gate-close"
        type="button"
        aria-label={copy("actions.back_to_site_aria")}
        onClick={handleExit}
      >
        X
      </button>
      {errorDialog}
      <form className="mines-launch-gate-form" onSubmit={(event) => {
        event.preventDefault();
        void handleCreateTableSession();
      }}>
        <div className="mines-launch-gate-heading">
          <span className="eyebrow">{gameTitle}</span>
          <h1>{copy("launch.choose_table_balance")}</h1>
        </div>
        {hasLockedTableWalletType ? (
          <div className="mines-launch-source-summary">
            <span>{copy("launch.balance_source_aria")}</span>
            <strong>
              {selectedTableWalletType === "bonus"
                ? copy("launch.bonus")
                : copy("launch.real_money")}
            </strong>
          </div>
        ) : (
          <div className="mines-wallet-choice" role="group" aria-label={copy("launch.balance_source_aria")}>
            <button
              className={
                selectedTableWalletType === "cash"
                  ? "mines-wallet-choice-button active"
                  : "mines-wallet-choice-button"
              }
              type="button"
              disabled={busyAction !== null || isInteractionLocked}
              onClick={() => handleTableWalletTypeChange("cash")}
            >
              <span>{copy("launch.real_money")}</span>
              <strong>{formatChipValue(cashWallet?.balance_snapshot ?? "0")}</strong>
            </button>
            <button
              className={
                selectedTableWalletType === "bonus"
                  ? "mines-wallet-choice-button active"
                  : "mines-wallet-choice-button"
              }
              type="button"
              disabled={busyAction !== null || isInteractionLocked}
              onClick={() => handleTableWalletTypeChange("bonus")}
            >
              <span>{copy("launch.bonus")}</span>
              <strong>{formatChipValue(bonusWallet?.balance_snapshot ?? "0")}</strong>
            </button>
          </div>
        )}
        <div className="mines-launch-gate-metrics">
          <div>
            <span className="list-muted">{copy("launch.available_balance")}</span>
            <strong>{formatChipValue(selectedTableWalletBalance)}</strong>
          </div>
          <div>
            <span className="list-muted">{copy("launch.maximum")}</span>
            <strong>{formatChipValue(tableEntryMaxAmount)}</strong>
          </div>
        </div>
        <div className="field mines-table-entry-field">
          <label htmlFor="table-entry-amount">{copy("launch.table_entry_amount")}</label>
          <input
            id="table-entry-amount"
            value={tableEntryAmount}
            onChange={(event) => setTableEntryAmount(normalizeWholeChipInput(event.target.value))}
            inputMode="numeric"
            placeholder={formatWholeChipInput(tableSessionLimits?.default_table_amount ?? "0")}
            disabled={busyAction !== null || isInteractionLocked}
            autoFocus
          />
        </div>
        {tableEntryChoices.length > 0 ? (
          <div className="quick-chip-row">
            {tableEntryChoices.map((amount) => (
              <button
                key={amount}
                className={tableEntryAmount === String(amount) ? "quick-chip active" : "quick-chip"}
                type="button"
                disabled={busyAction !== null || isInteractionLocked}
                onClick={() => setTableEntryAmount(String(amount))}
              >
                {amount}
              </button>
            ))}
          </div>
        ) : null}
        <button className="button" type="submit" disabled={isTableEntryDisabled}>
          {busyAction === "create-table-session"
            ? copy("launch.entering")
            : copy("launch.enter_game")}
        </button>
      </form>
    </section>
  ) : null;

  const gameplayContent = (
    <>
        {useMobileLayout ? (
          <form className="mines-mobile-layout" onSubmit={handleStartSession}>
            {stageHeader}
            {boardSection}
            <section className="mines-mobile-play-stack">
              <article className="mines-mobile-balance">
                {balanceFooter}
              </article>
              <section className="session-actions mines-control-rail mines-control-rail-clean mines-mobile-bet-panel">
                {betField}
              </section>
              {actionButtons}
              {mobileSettingsSummary}
            </section>
          </form>
        ) : (
          <div className="mines-grid">
            <div className="stack">
              <form
                className="session-actions mines-control-rail mines-control-rail-clean"
                onSubmit={handleStartSession}
              >
                {railHeader}
                {configFields}
                {betField}
                {actionButtons}

                <article className="mines-rail-footer">
                  {balanceFooter}
                </article>
              </form>
            </div>

            <div className="stack">
              {stageHeader}
              {boardSection}
            </div>
          </div>
        )}

        {showRules ? (
          <MinesRulesModal
            rulesSections={rulesSections}
            payoutLadder={payoutLadder}
            selectedGridSize={selectedGridSize}
            selectedMineCount={selectedMineCount}
            activeTab={rulesModalTab}
            onTabChange={handleRulesModalTabChange}
            isReplayAvailable={isAuthenticated || Boolean(replayCandidateSessionId)}
            replayContent={rulesReplayContent}
            copy={{
              dialogAriaLabel: copy("rules.dialog_aria", { gameTitle }),
              title: copy("rules.header_title", { gameTitle }),
              intro: copy("rules.intro"),
              closeAriaLabel: copy("rules.close_aria"),
              rulesTab: "REGOLE",
              replayTab: "REPLAY",
              replayUnavailable: "Replay disponibile dopo una mano chiusa.",
              waysToWin: copy("rules.ways_to_win"),
              payoutDisplay: copy("rules.payout_display"),
              safeRevealLabel: (step) =>
                copy("rules.safe_reveal", { step: String(step).padStart(2, "0") }),
              multiplierSuffix: copy("format.multiplier_suffix"),
              settingsMenu: copy("rules.settings_menu"),
              betCollect: copy("rules.bet_collect"),
            }}
            onClose={() => setShowRules(false)}
          />
        ) : null}

        {useMobileLayout && showMobileSettings ? (
          <MinesMobileSettingsSheet
            isDemoPlayer={isDemoMode}
            title={copy("settings.game_settings")}
            doneLabel={copy("actions.done")}
            demoBadgeLabel={copy("mode.demo_badge")}
            onClose={() => setShowMobileSettings(false)}
          >
            {configFields}
          </MinesMobileSettingsSheet>
        ) : null}
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
      showTableGate={shouldShowPreGameTableEntry}
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

function formatReplayDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function selectResumableGameSessionId(
  sessions: RecentSessionSummary[],
  preferredGameSessionId?: string | null,
): string | null {
  const activeSessions = sessions.filter((session) => session.status === "active");
  if (activeSessions.length === 0) {
    return null;
  }

  if (preferredGameSessionId) {
    const preferredActiveSession = activeSessions.find(
      (session) => session.game_session_id === preferredGameSessionId,
    );
    if (preferredActiveSession) {
      return preferredActiveSession.game_session_id;
    }
  }

  return activeSessions[0]?.game_session_id ?? null;
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
