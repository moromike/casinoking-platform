"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  extractValidationMessage,
  formatGridChoiceLabel,
  formatWholeChipDisplay,
  getDefaultVisibleMineCount,
  getModeUiLabels,
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
import { MinesRulesModal } from "./mines-rules-modal";
import { MinesBalanceFooter } from "./mines-balance-footer";
import { MinesActionButtons } from "./mines-action-buttons";
import { MinesMobileSettingsSheet } from "./mines-mobile-settings-sheet";
import { MinesStageHeader } from "./mines-stage-header";
import type {
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  SessionFairness,
  SessionSnapshot,
  StatusKind,
  StatusMessage,
  Wallet,
} from "@/app/lib/types";
import { API_BASE_URL, ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";

const STORAGE_KEYS = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.current_session_id",
  gameLaunchToken: "casinoking.mines_launch_token",
  gameLaunchTokenExpiresAt: "casinoking.mines_launch_token_expires_at",
} as const;

const MINES_EMBED_CLOSE_MESSAGE = "casinoking:mines-close";
const MINES_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:mines-fullscreen-state";
const MINES_STANDALONE_MEDIA_QUERY = "(max-width: 960px), (pointer: coarse)";
const ACCESS_SESSION_GAME_CODE = "mines";
const ACCESS_SESSION_PING_INTERVAL_MS = 30_000;
const ACCESS_SESSION_WARNING_MS = 170_000;
const ACCESS_SESSION_EXPIRY_MS = 180_000;
const ACCESS_SESSION_COUNTDOWN_SECONDS = 10;

type DemoAuthResponse = {
  access_token: string;
  email: string;
};

type LaunchTokenResponse = {
  game_code: string;
  game_launch_token: string;
  platform_session_id: string;
  play_session_id: string;
  game_play_session_id: string;
  expires_at: string;
};

type LaunchTokenValidationResponse = {
  game_code: string;
  player_id: string;
  platform_session_id: string;
  play_session_id: string;
  game_play_session_id: string;
  expires_at: string;
};

type StartSessionResponse = {
  game_session_id: string;
};

type AccessSessionResponse = {
  id: string;
  user_id: string;
  game_code: string;
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  status: "active" | "closed" | "timed_out";
};

type RecentSessionSummary = {
  game_session_id: string;
  status: "active" | "won" | "lost";
  access_session_id: string | null;
  access_session: {
    id: string;
    status: "active" | "closed" | "timed_out";
  } | null;
};

type FatalRuntimeOverlay = {
  title: string;
  text: string;
};

type RefreshAuthenticatedStateOptions = {
  preferredGameSessionId?: string | null;
  showResumeOverlay?: boolean;
};

type GameErrorContext =
  | "load-runtime"
  | "create-access-session"
  | "refresh-access-session"
  | "refresh-auth-state"
  | "resume-session"
  | "start-demo"
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
  const [currentSessionFairness, setCurrentSessionFairness] = useState<SessionFairness | null>(
    null,
  );
  const [selectedGridSize, setSelectedGridSize] = useState(25);
  const [selectedMineCount, setSelectedMineCount] = useState(3);
  const [betAmount, setBetAmount] = useState("5");
  const [selectedWalletType, setSelectedWalletType] = useState<"cash" | "bonus">("cash");
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
  const [revealedMinePositions, setRevealedMinePositions] = useState<number[]>([]);
  const [highlightedMineCell, setHighlightedMineCell] = useState<number | null>(null);
  const [isEmbeddedView, setIsEmbeddedView] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isHostFullscreen, setIsHostFullscreen] = useState(false);
  const [showMobileSettings, setShowMobileSettings] = useState(false);
  const [isSessionResumeLoading, setIsSessionResumeLoading] = useState(false);
  const [fatalRuntimeOverlay, setFatalRuntimeOverlay] = useState<FatalRuntimeOverlay | null>(null);
  const selectedGridSizeRef = useRef(25);
  const selectedMineCountRef = useRef(3);
  const betAmountRef = useRef("5");
  const statusTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const accessSessionIdRef = useRef("");
  const accessSessionRequestRef = useRef<Promise<string> | null>(null);
  const inactivityWarningTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inactivityExpiryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inactivityCountdownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isAuthenticated = accessToken.length > 0;
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
  const isDemoPlayer = currentEmail.endsWith("@casinoking.local");
  const isActiveRound = currentSession?.status === "active";
  const activeWalletType: "cash" | "bonus" =
    currentSession?.wallet_type === "bonus" ? "bonus" : "cash";
  const effectiveWalletType = isActiveRound ? activeWalletType : selectedWalletType;
  const selectedWallet = effectiveWalletType === "bonus" ? bonusWallet : cashWallet;
  const currentMode = isAuthenticated && !isDemoPlayer ? "real" : "demo";
  const modeUiLabels = getModeUiLabels(runtimeConfig, currentMode);
  const rulesSections = getRulesSections(runtimeConfig);
  const visiblePayoutLadder = currentSession
    ? getPayoutLadder(runtimeConfig, currentSession.grid_size, currentSession.mine_count)
    : payoutLadder;
  const visibleBalance =
    isActiveRound
      ? currentSession.wallet_balance_after_start
      : selectedWallet?.balance_snapshot ?? "0";
  const previewWindowStart = currentSession?.safe_reveals_count ?? 0;
  const previewMultipliers = visiblePayoutLadder.slice(previewWindowStart, previewWindowStart + 5);
  const stageSubtitle =
    roundResultNotice?.kind === "won"
      ? `Hai vinto. ${formatWholeChipDisplay(roundResultNotice.payoutAmount)}. Premi di nuovo Bet per la prossima mano.`
      : roundResultNotice?.kind === "lost"
        ? "Hai perso :("
        : null;
  const stageSubtitleTone =
    roundResultNotice?.kind === "won"
      ? "won"
      : roundResultNotice?.kind === "lost"
        ? "lost"
        : null;
  const visibleMinePositions =
    currentSession?.status === "lost"
      ? revealedMinePositions
      : highlightedMineCell !== null
        ? [highlightedMineCell]
        : [];
  const betButtonLabel = modeUiLabels.bet ?? "Bet";
  const collectButtonLabel = modeUiLabels.collect ?? "Collect";
  const visibleStatus = status?.kind === "error" ? status : null;
  const useMobileLayout = isMobileViewport;
  const isAccessSessionWarningActive =
    inactivityCountdownSeconds !== null && !isAccessSessionExpired;
  const isFatalRuntimeBlocked = fatalRuntimeOverlay !== null;
  const isInteractionLocked =
    isSessionResumeLoading ||
    isAccessSessionWarningActive ||
    isAccessSessionExpired ||
    isFatalRuntimeBlocked;
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
    setIsEmbeddedView(new URLSearchParams(window.location.search).get("embed") === "1");
    const storedToken = window.localStorage.getItem(STORAGE_KEYS.accessToken) ?? "";
    const storedLaunchToken =
      window.localStorage.getItem(STORAGE_KEYS.gameLaunchToken) ?? "";
    const storedLaunchTokenExpiresAt =
      window.localStorage.getItem(STORAGE_KEYS.gameLaunchTokenExpiresAt) ?? "";
    const storedEmail = window.localStorage.getItem(STORAGE_KEYS.email) ?? "";
    const storedGameSessionId = window.localStorage.getItem(STORAGE_KEYS.sessionId);

    setAccessToken(storedToken);
    setGameLaunchToken(storedLaunchToken);
    setGameLaunchTokenExpiresAt(storedLaunchTokenExpiresAt);
    setCurrentEmail(storedEmail);
    void loadRuntime();
    if (storedToken) {
      void refreshAuthenticatedState(storedToken, {
        preferredGameSessionId: storedGameSessionId,
        showResumeOverlay: true,
      });
    }
  }, []);

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
    if (statusTimeoutRef.current !== null) {
      clearTimeout(statusTimeoutRef.current);
      statusTimeoutRef.current = null;
    }

    if (status?.kind !== "error") {
      return;
    }

    statusTimeoutRef.current = setTimeout(() => {
      setStatus((currentStatus) => (currentStatus?.kind === "error" ? null : currentStatus));
      statusTimeoutRef.current = null;
    }, 5000);

    return () => {
      if (statusTimeoutRef.current !== null) {
        clearTimeout(statusTimeoutRef.current);
        statusTimeoutRef.current = null;
      }
    };
  }, [status]);

  useEffect(() => {
    if (!accessToken) {
      clearAccessSessionState();
      return;
    }

    if (accessSessionIdRef.current || isAccessSessionExpired || isSessionResumeLoading) {
      return;
    }

    void createAccessSession(accessToken).catch((error) => {
      handleGameError(error, "create-access-session");
    });
  }, [accessToken, isAccessSessionExpired, isSessionResumeLoading]);

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
    };
  }, []);

  function updateSelectedGridSize(value: number) {
    selectedGridSizeRef.current = value;
    setSelectedGridSize(value);
  }

  function updateSelectedMineCount(value: number) {
    selectedMineCountRef.current = value;
    setSelectedMineCount(value);
  }

  function updateBetAmount(value: string) {
    betAmountRef.current = value;
    setBetAmount(value);
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

  function touchUserActivity() {
    if (isAccessSessionExpired) {
      return;
    }

    setIsAccessSessionExpired(false);
    resetInactivityTimer();
  }

  function clearAccessSessionState() {
    clearInactivityTimers();
    accessSessionIdRef.current = "";
    accessSessionRequestRef.current = null;
    setAccessSessionId("");
    setInactivityCountdownSeconds(null);
    setIsAccessSessionExpired(false);
  }

  async function createAccessSession(token: string): Promise<string> {
    if (accessSessionIdRef.current.length > 0) {
      return accessSessionIdRef.current;
    }

    if (accessSessionRequestRef.current !== null) {
      return accessSessionRequestRef.current;
    }

    const request = apiRequest<AccessSessionResponse>(
      "/access-sessions",
      {
        method: "POST",
        body: JSON.stringify({ game_code: ACCESS_SESSION_GAME_CODE }),
      },
      token,
    )
      .then((sessionData) => {
        accessSessionIdRef.current = sessionData.id;
        setAccessSessionId(sessionData.id);
        setIsAccessSessionExpired(false);
        resetInactivityTimer();
        return sessionData.id;
      })
      .finally(() => {
        accessSessionRequestRef.current = null;
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

  async function loadRuntime() {
    try {
      const [runtimeData, fairnessData] = await Promise.all([
        apiRequest<MinesRuntimeConfig>("/games/mines/config"),
        apiRequest<FairnessCurrentConfig>("/games/mines/fairness/current"),
      ]);
      setRuntimeConfig(runtimeData);
      setCurrentFairness(fairnessData);
    } catch (error) {
      handleGameError(error, "load-runtime");
    }
  }

  async function refreshAuthenticatedState(
    token: string,
    options: RefreshAuthenticatedStateOptions = {},
  ) {
    const { preferredGameSessionId = null, showResumeOverlay = false } = options;

    if (showResumeOverlay) {
      setIsSessionResumeLoading(true);
    }

    try {
      const [walletData, recentSessions] = await Promise.all([
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<RecentSessionSummary[]>("/games/mines/sessions", {}, token),
      ]);

      setWallets(walletData);

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
    setRevealedMinePositions([]);
    setCurrentSession(sessionData);
    setCurrentSessionFairness(fairnessData);
    setFatalRuntimeOverlay(null);
    setStatus(null);
    updateSelectedGridSize(sessionData.grid_size);
    updateSelectedMineCount(sessionData.mine_count);
    if (sessionData.status === "active") {
      window.localStorage.setItem(STORAGE_KEYS.sessionId, sessionId);
    } else {
      window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    }
  }

  async function prepareDemoAccessToken() {
    const demoData = await apiRequest<DemoAuthResponse>("/auth/demo", {
      method: "POST",
    });
    setAccessToken(demoData.access_token);
    setCurrentEmail(demoData.email);
    window.localStorage.setItem(STORAGE_KEYS.accessToken, demoData.access_token);
    window.localStorage.setItem(STORAGE_KEYS.email, demoData.email);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    await refreshAuthenticatedState(demoData.access_token);
    return demoData.access_token;
  }

  async function handleStartDemoMode() {
    if (accessToken) {
      return;
    }
    setBusyAction("demo-mode");
    try {
      await prepareDemoAccessToken();
      setStatus({
        kind: "success",
        text: "Demo mode ready with 1000 CHIP.",
      });
    } catch (error) {
      handleGameError(error, "start-demo");
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
    try {
      const token = accessToken || (await prepareDemoAccessToken());
      const currentAccessSessionId =
        accessSessionIdRef.current || (await createAccessSession(token));
      const launchToken = await ensureGameLaunchToken(
        token,
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
            wallet_type: selectedWalletType,
            access_session_id: currentAccessSessionId,
          }),
        },
        token,
      );
      setHighlightedMineCell(null);
      await refreshAuthenticatedState(token, {
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
    if (
      !accessToken ||
      !currentSession ||
      currentSession.status !== "active" ||
      isInteractionLocked
    ) {
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
            "X-Game-Launch-Token": await ensureGameLaunchToken(
              accessToken,
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
        accessToken,
      );
      setHighlightedMineCell(revealData.result === "mine" ? cellIndex : null);
      await refreshAuthenticatedState(accessToken, {
        preferredGameSessionId: currentSession.game_session_id,
      });
      if (revealData.result === "mine") {
        setRevealedMinePositions(revealData.mine_positions ?? [cellIndex]);
        setRoundResultNotice({
          kind: "lost",
          payoutAmount: "0",
        });
      } else if (revealData.status === "won") {
        setRevealedMinePositions([]);
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
    if (
      !accessToken ||
      !currentSession ||
      currentSession.status !== "active" ||
      isInteractionLocked
    ) {
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
      }>(
        "/games/mines/cashout",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
            "X-Game-Launch-Token": await ensureGameLaunchToken(
              accessToken,
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
        accessToken,
      );
      await refreshAuthenticatedState(accessToken, {
        preferredGameSessionId: currentSession.game_session_id,
      });
      setHighlightedMineCell(null);
      setRevealedMinePositions([]);
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

  function handleGameError(error: unknown, context: GameErrorContext) {
    if (isBearerTokenAuthError(error)) {
      clearAuthState(false);
      setStatus({
        kind: "error",
        text: "La sessione di accesso non è più valida. Effettua di nuovo il login per continuare.",
      });
      return;
    }

    if (isReloadRequiredRuntimeError(error)) {
      clearCurrentSessionSnapshot();
      setBusyAction(null);
      setShowMobileSettings(false);
      setFatalRuntimeOverlay({
        title: "Ricarica richiesta",
        text: "La sessione di gioco non è più allineata con il server. Ricarica la pagina per continuare in sicurezza.",
      });
      return;
    }

    setStatus({
      kind: "error",
      text: buildFriendlyGameErrorMessage(error, context),
    });
  }

  function clearCurrentSessionSnapshot() {
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
  }

  function handleGridSizeChange(gridSize: number) {
    if (isInteractionLocked || isActiveRound || gridSize === selectedGridSize) {
      return;
    }

    updateSelectedGridSize(gridSize);
    updateSelectedMineCount(getDefaultVisibleMineCount(runtimeConfig, gridSize));
    clearCurrentSessionSnapshot();
  }

  function handleExit() {
    clearAccessSessionState();
    if (isHostFullscreen) {
      return;
    }
    if (isDemoPlayer) {
      clearAuthState(true);
    } else {
      clearCurrentSessionSnapshot();
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
    setHighlightedMineCell(null);
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    setFatalRuntimeOverlay(null);
    setIsSessionResumeLoading(false);
    window.localStorage.removeItem(STORAGE_KEYS.accessToken);
    window.localStorage.removeItem(STORAGE_KEYS.gameLaunchToken);
    window.localStorage.removeItem(STORAGE_KEYS.gameLaunchTokenExpiresAt);
    window.localStorage.removeItem(STORAGE_KEYS.email);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    if (!removeStatus) {
      return;
    }
    setStatus({
      kind: "info",
      text: "Demo session closed. The next demo entry will start again from 1000 CHIP.",
    });
  }

  const railHeader = (
    <div className="list-row mines-rail-header">
      <button
        className="button-ghost mines-rules-trigger"
        type="button"
        disabled={isInteractionLocked}
        onClick={() => setShowRules(true)}
        aria-label="Game info"
      >
        i
      </button>
      {isDemoPlayer ? <span className="status-badge info mines-mode-badge">DEMO MODE</span> : null}
    </div>
  );

  const mobileStageTools = useMobileLayout ? (
    <div className="mines-mobile-stage-tools">
      <button
        className="button-ghost mines-rules-trigger"
        type="button"
        disabled={isInteractionLocked}
        onClick={() => setShowRules(true)}
        aria-label="Game info"
      >
        i
      </button>
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
        {formatGridChoiceLabel(controlGridSize)}
      </button>
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={isInteractionLocked}
        onClick={() => setShowMobileSettings(true)}
      >
        {controlMineCount} mines
      </button>
    </div>
  ) : null;

  const configFields = (
    <div className="stack mines-control-stack mines-config-sections">
      {isAuthenticated && !isDemoPlayer ? (
        <div className="field mines-config-section">
          <label>Wallet</label>
          <div className="mines-config-options-grid">
            {(["cash", "bonus"] as const).map((wt) => {
              return (
                <button
                  key={wt}
                  className={effectiveWalletType === wt ? "choice-chip active" : "choice-chip"}
                  type="button"
                  disabled={busyAction !== null || isActiveRound || isInteractionLocked}
                  onClick={() => setSelectedWalletType(wt)}
                >
                  {wt.toUpperCase()}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="field mines-config-section">
        <label>Grid size</label>
        <div className="mines-config-options-grid">
          {gridSizes.map((gridSize) => (
            <button
              key={gridSize}
              className={controlGridSize === gridSize ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound || isInteractionLocked}
              onClick={() => handleGridSizeChange(gridSize)}
            >
              {formatGridChoiceLabel(gridSize)}
            </button>
          ))}
        </div>
      </div>

      <div className="field mines-config-section">
        <label>Mines</label>
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
      <label htmlFor="bet-amount-standalone">Bet amount</label>
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
      isBetDisabled={busyAction !== null || currentSession?.status === "active" || isInteractionLocked}
      isBetLoading={busyAction === "start-session"}
      isCollectDisabled={
        !currentSession ||
        currentSession.status !== "active" ||
        currentSession.safe_reveals_count <= 0 ||
        busyAction !== null ||
        isInteractionLocked
      }
      isCollectLoading={busyAction === "cashout"}
      onCashout={() => void handleCashout()}
    />
  );

  const balanceFooter = (
    <MinesBalanceFooter
      isDemoPlayer={isDemoPlayer}
      visibleBalance={visibleBalance}
      potentialPayout={currentSession ? currentSession.potential_payout : null}
      walletType={isDemoPlayer ? undefined : effectiveWalletType}
    />
  );

  const stageHeader = (
    <MinesStageHeader
      stageSubtitle={stageSubtitle}
      stageSubtitleTone={stageSubtitleTone}
      previewMultipliers={previewMultipliers}
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
        closed={
          isSessionResumeLoading ||
          isAccessSessionExpired ||
          isFatalRuntimeBlocked ||
          (currentSession?.status !== "active" && currentSession !== null)
        }
      />
    </article>
  );

  const runtimeOverlay = isSessionResumeLoading
    ? {
        title: "Ripristino partita",
        text: "Sto riallineando la mano con il server. Attendi qualche istante.",
      }
    : fatalRuntimeOverlay
      ? fatalRuntimeOverlay
      : isAccessSessionExpired
        ? {
            title: "Sessione scaduta",
            text: "Sessione inattiva scaduta. Ricarica la pagina per continuare.",
          }
        : isAccessSessionWarningActive
          ? {
              title: "Sessione in scadenza",
              text: `Sessione in scadenza per inattività. Eventuali puntate aperte verranno gestite dal server tra ${inactivityCountdownSeconds ?? ACCESS_SESSION_COUNTDOWN_SECONDS} secondi.`,
            }
          : null;

  return (
    <main className={pageShellClassName}>
      <section className={productShellClassName}>
        {visibleStatus ? <div className={`status-banner ${visibleStatus.kind}`}>{visibleStatus.text}</div> : null}
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
            onClose={() => setShowRules(false)}
          />
        ) : null}

        {useMobileLayout && showMobileSettings ? (
          <MinesMobileSettingsSheet
            isDemoPlayer={isDemoPlayer}
            onClose={() => setShowMobileSettings(false)}
          >
            {configFields}
          </MinesMobileSettingsSheet>
        ) : null}

        {runtimeOverlay ? (
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
        ) : null}

      </section>
    </main>
  );
}

async function ensureGameLaunchToken(
  accessToken: string,
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
      await apiRequest<LaunchTokenValidationResponse>(
        "/games/mines/launch/validate",
        {
          method: "POST",
          body: JSON.stringify({ game_launch_token: currentLaunchToken }),
        },
      );
      return currentLaunchToken;
    } catch {
      window.localStorage.removeItem(STORAGE_KEYS.gameLaunchToken);
      window.localStorage.removeItem(STORAGE_KEYS.gameLaunchTokenExpiresAt);
      setGameLaunchToken("");
      setGameLaunchTokenExpiresAt("");
    }
  }

  const issueData = await apiRequest<LaunchTokenResponse>(
    "/games/mines/launch-token",
    {
      method: "POST",
      body: JSON.stringify({ game_code: "mines" }),
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

  window.localStorage.setItem(STORAGE_KEYS.gameLaunchToken, issueData.game_launch_token);
  window.localStorage.setItem(STORAGE_KEYS.gameLaunchTokenExpiresAt, issueData.expires_at);
  setGameLaunchToken(issueData.game_launch_token);
  setGameLaunchTokenExpiresAt(issueData.expires_at);
  return issueData.game_launch_token;
}

function readMinesNetworkAwareErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (
      normalizedMessage.includes("networkerror") ||
      normalizedMessage.includes("failed to fetch") ||
      normalizedMessage.includes("fetch resource")
    ) {
      return `${fallback} Could not reach the server. Please try again.`;
    }
  }

  return readErrorMessage(error, fallback);
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

function isReloadRequiredRuntimeError(error: unknown): boolean {
  if (!(error instanceof ApiRequestError)) {
    return false;
  }

  if (error.code === "GAME_STATE_CONFLICT") {
    return true;
  }

  if (error.status !== 401 && error.status !== 403) {
    return false;
  }

  const normalizedMessage = error.message.toLowerCase();
  return (
    normalizedMessage.includes("game launch token") ||
    normalizedMessage.includes("ownership is not valid")
  );
}

function buildFriendlyGameErrorMessage(error: unknown, context: GameErrorContext): string {
  if (isNetworkRequestFailure(error)) {
    switch (context) {
      case "start-session":
        return "Impossibile avviare la mano. Verifica la connessione e riprova.";
      case "reveal":
      case "cashout":
        return "Errore di comunicazione col server. La tua giocata è al sicuro. Riprova tra poco.";
      case "refresh-auth-state":
      case "resume-session":
        return "Impossibile riallineare la partita con il server. Ricarica la pagina e riprova.";
      case "create-access-session":
      case "refresh-access-session":
        return "Impossibile mantenere attiva la sessione di gioco. Ricarica la pagina e riprova.";
      case "load-runtime":
        return "Impossibile caricare Mines in questo momento. Ricarica la pagina.";
      case "start-demo":
        return "Impossibile avviare la demo in questo momento. Riprova tra poco.";
      default:
        return "Si è verificato un problema di connessione. Riprova tra poco.";
    }
  }

  switch (context) {
    case "start-session":
      return "Impossibile avviare la mano. Controlla importo e configurazione, poi riprova.";
    case "reveal":
    case "cashout":
      return "Impossibile completare l'azione in questo momento. Attendi qualche istante e riprova.";
    case "refresh-auth-state":
      return "Impossibile aggiornare saldo e stato della partita. Ricarica la pagina.";
    case "resume-session":
      return "Impossibile riprendere la partita in corso. Ricarica la pagina per riallineare lo stato.";
    case "create-access-session":
    case "refresh-access-session":
      return "Impossibile mantenere attiva la sessione di gioco. Ricarica la pagina e riprova.";
    case "load-runtime":
      return "Impossibile caricare Mines in questo momento. Ricarica la pagina.";
    case "start-demo":
      return "Impossibile avviare la demo in questo momento. Riprova tra poco.";
    default:
      return readMinesNetworkAwareErrorMessage(error, "Operazione non riuscita.");
  }
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
