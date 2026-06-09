"use client";

import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { ApiRequestError, resolveBackendAssetUrl } from "@/app/lib/api";
import { GameActionError } from "../game-runtime/game-action-error";
import { GameActionButtons } from "../game-runtime/game-action-buttons";
import { GameBalanceFooter } from "../game-runtime/game-balance-footer";
import { GameBetPanel } from "../game-runtime/game-bet-panel";
import type { GameBootRequest } from "../game-runtime/game-boot-request";
import { GameControlRail } from "../game-runtime/game-control-rail";
import {
  buildGameErrorDiagnostic,
  buildGameErrorMessage,
  isBearerTokenAuthError,
  type GameErrorDiagnostic,
  type GameErrorCopyMap,
} from "../game-runtime/game-error-copy-adapter";
import { GameRuntimeTools } from "../game-runtime/game-top-bar";
import { GameMobileControlStack } from "../game-runtime/game-mobile-control-stack";
import { GameShortViewportGate } from "../game-runtime/game-short-viewport-gate";
import {
  clearStoredAuthState,
  clearStoredDemoAnonToken,
  clearStoredDemoLaunchToken,
  HI_LO_GAME_STORAGE_NAMESPACE,
  readGameStorageSnapshot,
  writeStoredDemoAnonToken,
  writeStoredDemoLaunchToken,
  writeStoredRealLaunchToken,
} from "../game-runtime/game-storage";
import type { TitleThemeSkin } from "@/app/lib/types";
import {
  cashoutHiLoRound,
  fetchHiLoLatestReplaySessions,
  getHiLoRoundReplay,
  issueHiLoDemoAnonToken,
  issueHiLoDemoLaunchToken,
  issueHiLoLaunchToken,
  loadHiLoWallets,
  predictHiLoRound,
  skipHiLoRound,
  startHiLoRound,
  type HiLoCard,
  type HiLoPredictionAction,
  type HiLoQuote,
  type HiLoRoundReplay,
  type HiLoRoundResponse,
  type HiLoRuntimeConfig,
  type HiLoTableSession,
  type HiLoWalletSource,
} from "./use-hi-lo-runtime";
import {
  GameLatestReplaySessionsPanel,
  type GameLatestAccessSessionHistory,
} from "../game-runtime/game-latest-replay-panel";
import {
  createHiLoCopyResolver,
  type HiLoCopyResolver,
} from "./hi-lo-i18n/hi-lo-copy-defaults";
import { HiLoReplayViewer } from "./hi-lo-replay-viewer";
import { HiLoRulesModal, type HiLoRulesModalTab } from "./hi-lo-rules-modal";
import { HiLoWinCelebration } from "./hi-lo-win-celebration";

const MAX_ACTION_RETRY_ATTEMPTS = 3;

const HI_LO_SKIN_OVERLAY: Record<TitleThemeSkin["game_area_overlay"], string> = {
  none: "rgba(0, 0, 0, 0)",
  light: "rgba(0, 0, 0, 0.16)",
  medium: "rgba(0, 0, 0, 0.34)",
  strong: "rgba(0, 0, 0, 0.54)",
};

type StoredHiLoLaunchToken = {
  token: string;
  expiresAt: string;
  titleCode: string;
};

type BusyAction = "start" | "predict" | "skip" | "cashout" | "retry" | null;

type WalletSummary = {
  wallet_type: string;
  balance_snapshot: string;
};

type HiLoHistoryItem = {
  id: string;
  label: string;
  card: HiLoCard | null;
  status: "start" | "correct" | "wrong" | "skip" | "cashout";
  multiplier: string;
  payout: string;
};

type RetryAction =
  | {
      type: "start";
      idempotencyKey: string;
      betAmount: string;
      walletSource: HiLoWalletSource;
    }
  | {
      type: "predict";
      idempotencyKey: string;
      roundId: string;
      action: HiLoPredictionAction;
    }
  | {
      type: "skip";
      idempotencyKey: string;
      roundId: string;
    }
  | {
      type: "cashout";
      idempotencyKey: string;
      roundId: string;
    };

type ReplayState =
  | { status: "idle" }
  | { status: "loading"; roundId: string }
  | { status: "ready"; roundId: string; replay: HiLoRoundReplay }
  | { status: "error"; roundId: string; message: string };

type LatestReplaySessionsState = {
  sessions: GameLatestAccessSessionHistory<HiLoRoundReplay>[];
  loading: boolean;
  error: string | null;
  selectedRoundId: string | null;
};

export function HiLoGameplay({
  runtimeConfig,
  titleThemeAssets,
  titleThemeSkin,
  bootRequest,
  initialAccessToken,
  audioPreferences,
  accessSessionId,
  initialRound,
  tableSession,
  onExit,
  onTableSessionChange,
}: {
  runtimeConfig: HiLoRuntimeConfig;
  titleThemeAssets: Record<string, string>;
  titleThemeSkin: TitleThemeSkin | null;
  bootRequest: GameBootRequest;
  initialAccessToken: string;
  audioPreferences: {
    muted: boolean;
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
    volume: number;
  };
  accessSessionId: string | null;
  initialRound: HiLoRoundResponse | null;
  tableSession: HiLoTableSession | null;
  onExit: () => void;
  onTableSessionChange: (tableSession: HiLoTableSession) => void;
}) {
  const [betAmount, setBetAmount] = useState("5");
  const [authToken, setAuthToken] = useState(initialAccessToken);
  const [gameLaunchState, setGameLaunchState] = useState(readHiLoStoredLaunchToken);
  const [demoAnonToken, setDemoAnonToken] = useState<string | null>(null);
  const [demoLaunchToken, setDemoLaunchToken] = useState<string | null>(null);
  const [wallets, setWallets] = useState<WalletSummary[]>([]);
  const [demoBalance, setDemoBalance] = useState("100");
  const [round, setRound] = useState<HiLoRoundResponse | null>(null);
  const [history, setHistory] = useState<HiLoHistoryItem[]>([]);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorText, setErrorText] = useState("");
  const [errorDiagnostic, setErrorDiagnostic] = useState<GameErrorDiagnostic | null>(null);
  const [retryAction, setRetryAction] = useState<RetryAction | null>(null);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [showRules, setShowRules] = useState(false);
  const [activeInfoTab, setActiveInfoTab] = useState<HiLoRulesModalTab>("rules");
  const [replayState, setReplayState] = useState<ReplayState>({ status: "idle" });
  const [winCelebrationKey, setWinCelebrationKey] = useState(0);
  const [celebrationAmount, setCelebrationAmount] = useState("0");
  const [isBetHintActive, setIsBetHintActive] = useState(false);
  const [playerActivityTick, setPlayerActivityTick] = useState(0);
  const [latestReplaySessionsState, setLatestReplaySessionsState] =
    useState<LatestReplaySessionsState>({
      sessions: [],
      loading: false,
      error: null,
      selectedRoundId: null,
    });
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const useMobileLayout = isMobileViewport;

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 960px), (pointer: coarse)");
    const update = (e: MediaQueryListEvent | MediaQueryList) => setIsMobileViewport(e.matches);
    update(mq);
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const walletSource: HiLoWalletSource = bootRequest.forceDemoMode
    ? "demo"
    : bootRequest.walletSource ?? "cash";
  const isDemoPlayer = walletSource === "demo";
  const isAuthenticated = !isDemoPlayer && !!authToken;
  const isRoundActive = round?.status === "active";
  const isTerminal = Boolean(round?.terminal);
  const isInteractionLocked = busyAction !== null;
  const visibleBalance = isDemoPlayer
    ? demoBalance
    : tableSession?.table_balance_amount ?? readBalanceAmount({ walletSource, wallets });
  const potentialPayout = round?.payout_current ?? null;
  const normalizedBet = normalizeBetAmount(betAmount);
  const isBetDisabled =
    isInteractionLocked ||
    isRoundActive ||
    parseChipAmount(normalizedBet) <= 0 ||
    (!isDemoPlayer && !tableSession);

  useEffect(() => {
    if (isBetDisabled || isBetHintActive) {
      return;
    }
    let pulseTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const idleTimeoutId = setTimeout(() => {
      setIsBetHintActive(true);
      pulseTimeoutId = setTimeout(() => setIsBetHintActive(false), 1100);
    }, 10_000);
    return () => {
      clearTimeout(idleTimeoutId);
      if (pulseTimeoutId !== null) clearTimeout(pulseTimeoutId);
    };
  }, [isBetDisabled, isBetHintActive, playerActivityTick]);

  const isCollectDisabled =
    isInteractionLocked ||
    !isRoundActive ||
    !round ||
    parseChipAmount(round.payout_current) <= 0;
  const canSkip =
    isRoundActive &&
    round !== null &&
    round.active_skip_count < round.active_skip_limit &&
    !isInteractionLocked;
  const runtimeLocale = runtimeConfig.presentation_config?.default_locale ?? "it";
  const runtimeCopy = runtimeConfig.presentation_config?.copy?.[runtimeLocale];
  const rulesCopy = createHiLoCopyResolver(runtimeLocale, runtimeCopy);
  const gameErrorCopyMap = createHiLoGameErrorCopyMap(rulesCopy);
  const actionLabels = createHiLoActionLabels(rulesCopy);
  const statusLabel = round
    ? round.terminal
      ? round.outcome === "cashout"
        ? rulesCopy("runtime.status.cashout")
        : rulesCopy("runtime.status.loss")
      : rulesCopy("runtime.status.streak", {
          count: String(round.correct_predictions_count),
        })
    : rulesCopy("runtime.status.ready");
  const modeLabel = isDemoPlayer
    ? rulesCopy("runtime.mode.demo")
    : walletSource === "bonus"
      ? rulesCopy("runtime.mode.bonus")
      : rulesCopy("runtime.mode.real");

  useEffect(() => {
    setAuthToken(initialAccessToken);
  }, [initialAccessToken]);

  useEffect(() => {
    if (!initialRound) {
      return;
    }
    setRound(initialRound);
    setBetAmount(initialRound.bet_amount);
    setHistory([
      {
        id: `resume:${initialRound.round_id}`,
        label: initialRound.correct_predictions_count > 0 ? "resume" : "start",
        card: initialRound.current_card,
        status: initialRound.correct_predictions_count > 0 ? "correct" : "start",
        multiplier: initialRound.multiplier_current,
        payout: initialRound.payout_current,
      },
    ]);
    if (initialRound.table_session) {
      onTableSessionChange(initialRound.table_session);
    }
  }, [initialRound, onTableSessionChange]);

  useEffect(() => {
    if (!round?.terminal) {
      setReplayState({ status: "idle" });
    }
  }, [round?.round_id, round?.terminal]);

  useEffect(() => {
    if (isDemoPlayer || !authToken) {
      return;
    }
    let isMounted = true;
    loadHiLoWallets(authToken)
      .then((nextWallets) => {
        if (isMounted) {
          setWallets(nextWallets);
        }
      })
      .catch(() => {
        if (isMounted) {
          setWallets([]);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [authToken, isDemoPlayer]);

  useEffect(() => {
    if (!isTerminal || isInteractionLocked || isBetDisabled) {
      return;
    }

    function handleRebetShortcut(event: KeyboardEvent) {
      if (event.code !== "Space") {
        return;
      }
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, button, [contenteditable='true']")) {
        return;
      }
      event.preventDefault();
      void executeStart();
    }

    window.addEventListener("keydown", handleRebetShortcut);
    return () => window.removeEventListener("keydown", handleRebetShortcut);
  }, [isBetDisabled, isInteractionLocked, isTerminal]);

  async function ensureActionToken(): Promise<string | null> {
    if (authToken) {
      return authToken;
    }
    if (!bootRequest.forceDemoMode) {
      throw new Error(rulesCopy("runtime.error.auth_invalid"));
    }
    return null;
  }

  async function ensureHiLoLaunchToken(source: HiLoWalletSource): Promise<string | null> {
    if (source === "demo") {
      if (demoLaunchToken) {
        return demoLaunchToken;
      }
      try {
        const anonToken = await issueHiLoDemoAnonToken();
        setDemoAnonToken(anonToken.anonymous_token);
        writeStoredDemoAnonToken(
          window.localStorage,
          HI_LO_GAME_STORAGE_NAMESPACE,
          anonToken.anonymous_token,
        );
        const launchData = await issueHiLoDemoLaunchToken(
          anonToken.anonymous_token,
          bootRequest.titleCode,
        );
        setDemoLaunchToken(launchData.game_launch_token);
        writeStoredDemoLaunchToken(
          window.localStorage,
          HI_LO_GAME_STORAGE_NAMESPACE,
          launchData.game_launch_token,
          launchData.expires_at,
          bootRequest.titleCode,
        );
        return launchData.game_launch_token;
      } catch {
        return null;
      }
    }
    if (
      gameLaunchState.token &&
      gameLaunchState.expiresAt &&
      gameLaunchState.titleCode === bootRequest.titleCode &&
      !isExpiredIsoDate(gameLaunchState.expiresAt)
    ) {
      return gameLaunchState.token;
    }

    const bearerToken = await ensureActionToken();
    if (!bearerToken) {
      throw new Error(rulesCopy("runtime.error.auth_invalid"));
    }
    const issueData = await issueHiLoLaunchToken({
      titleCode: bootRequest.titleCode,
      token: bearerToken,
    });
    writeStoredRealLaunchToken(
      window.localStorage,
      HI_LO_GAME_STORAGE_NAMESPACE,
      issueData.game_launch_token,
      issueData.expires_at,
      bootRequest.titleCode,
    );
    setGameLaunchState({
      token: issueData.game_launch_token,
      expiresAt: issueData.expires_at,
      titleCode: bootRequest.titleCode,
    });
    return issueData.game_launch_token;
  }

  async function runHiLoActionWithDemoTokenRecovery<T>(
    action: (token: string | null, launchToken: string | null) => Promise<T>,
  ): Promise<T> {
    const token = await ensureActionToken();
    const launchToken = await ensureHiLoLaunchToken(walletSource);
    try {
      return await action(token, launchToken);
    } catch (error) {
      if (bootRequest.forceDemoMode) {
        if (error instanceof ApiRequestError && error.status === 401) {
          clearStoredDemoLaunchToken(window.localStorage, HI_LO_GAME_STORAGE_NAMESPACE);
          setDemoLaunchToken(null);
          const newLaunchToken = await ensureHiLoLaunchToken(walletSource);
          return await action(null, newLaunchToken);
        }
        throw error;
      }
      if (!isBearerTokenAuthError(error)) {
        throw error;
      }
      clearStoredAuthState(window.localStorage, HI_LO_GAME_STORAGE_NAMESPACE);
      setAuthToken("");
      const newToken = await ensureActionToken();
      if (!newToken) {
        throw new Error(rulesCopy("runtime.error.auth_invalid"));
      }
      const newLaunchToken = await ensureHiLoLaunchToken(walletSource);
      return await action(newToken, newLaunchToken);
    }
  }

  function notePlayerActivity() {
    setIsBetHintActive(false);
    setPlayerActivityTick((currentTick) => currentTick + 1);
  }

  async function executeStart(action?: Extract<RetryAction, { type: "start" }>) {
    notePlayerActivity();
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const wager = normalizeBetAmount(action?.betAmount ?? betAmount);
    const source = action?.walletSource ?? walletSource;
    setBusyAction(action ? "retry" : "start");
    clearActionError();
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token, launchToken) =>
        startHiLoRound({
          titleCode: bootRequest.titleCode,
          betAmount: wager,
          walletSource: source,
          token: token ?? undefined,
          idempotencyKey,
          tableSessionId: source === "demo" ? null : tableSession?.id ?? null,
          accessSessionId: source === "demo" ? null : accessSessionId,
          launchToken: launchToken ?? undefined,
        }),
      );
      if (response.table_session) {
        onTableSessionChange(response.table_session);
      }
      setRound(response);
      setBetAmount(wager);
      if (source === "demo") {
        setDemoBalance((current) => formatChipAmount(parseChipAmount(current) - parseChipAmount(wager)));
      }
      setRetryAttempts(0);
      setHistory([
        {
          id: `start:${response.round_id}`,
          label: rulesCopy("runtime.status.ready"),
          card: response.current_card,
          status: "start",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "start",
        idempotencyKey,
        betAmount: wager,
        walletSource: source,
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function executePrediction(
    predictionAction: HiLoPredictionAction,
    action?: Extract<RetryAction, { type: "predict" }>,
  ) {
    notePlayerActivity();
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const selectedAction = action?.action ?? predictionAction;
    setBusyAction(action ? "retry" : "predict");
    clearActionError();
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token, launchToken) =>
        predictHiLoRound({
          roundId: targetRoundId,
          action: selectedAction,
          token: token ?? undefined,
          idempotencyKey,
          launchToken: launchToken ?? undefined,
        }),
      );
      setRound(response);
      setRetryAttempts(0);
      setHistory((current) => [
        ...current,
        {
          id: `prediction:${idempotencyKey}`,
          label: response.prediction?.label ?? actionLabels[selectedAction],
          card: response.current_card,
          status: response.prediction?.success ? "correct" : "wrong",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "predict",
        idempotencyKey,
        roundId: targetRoundId,
        action: selectedAction,
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function executeSkip(action?: Extract<RetryAction, { type: "skip" }>) {
    notePlayerActivity();
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "skip");
    clearActionError();
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token, launchToken) =>
        skipHiLoRound({
          roundId: targetRoundId,
          token: token ?? undefined,
          idempotencyKey,
          launchToken: launchToken ?? undefined,
        }),
      );
      setRound(response);
      setRetryAttempts(0);
      setHistory((current) => [
        ...current,
        {
          id: `skip:${idempotencyKey}`,
          label: rulesCopy("runtime.action.skip"),
          card: response.current_card,
          status: "skip",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "skip",
        idempotencyKey,
        roundId: targetRoundId,
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function executeCashout(action?: Extract<RetryAction, { type: "cashout" }>) {
    notePlayerActivity();
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "cashout");
    clearActionError();
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token, launchToken) =>
        cashoutHiLoRound({
          roundId: targetRoundId,
          token: token ?? undefined,
          idempotencyKey,
          launchToken: launchToken ?? undefined,
        }),
      );
      setRound(response);
      setRetryAttempts(0);
      if (isDemoPlayer && response.final_payout_amount) {
        setDemoBalance((current) =>
          formatChipAmount(parseChipAmount(current) + parseChipAmount(response.final_payout_amount ?? "0")),
        );
      }
      setHistory((current) => [
        ...current,
        {
          id: `cashout:${idempotencyKey}`,
          label: rulesCopy("runtime.action.collect"),
          card: response.current_card,
          status: "cashout",
          multiplier: response.multiplier_current,
          payout: response.final_payout_amount ?? response.payout_current,
        },
      ]);
      const payout = parseChipAmount(response.final_payout_amount ?? response.payout_current);
      if (payout > 0) {
        setCelebrationAmount(response.final_payout_amount ?? response.payout_current);
        setWinCelebrationKey((currentKey) => currentKey + 1);
      }
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "cashout",
        idempotencyKey,
        roundId: targetRoundId,
      });
    } finally {
      setBusyAction(null);
    }
  }

  function retryLastAction() {
    if (!retryAction) {
      return;
    }
    if (retryAttempts >= MAX_ACTION_RETRY_ATTEMPTS) {
      return;
    }
    setRetryAttempts((current) => Math.min(current + 1, MAX_ACTION_RETRY_ATTEMPTS));
    if (retryAction.type === "start") {
      void executeStart(retryAction);
      return;
    }
    if (retryAction.type === "predict") {
      void executePrediction(retryAction.action, retryAction);
      return;
    }
    if (retryAction.type === "skip") {
      void executeSkip(retryAction);
      return;
    }
    void executeCashout(retryAction);
  }

  async function loadReplayForCurrentRound() {
    if (!round?.terminal) {
      return;
    }
    const roundId = round.round_id;
    if (
      (replayState.status === "ready" || replayState.status === "loading") &&
      replayState.roundId === roundId
    ) {
      return;
    }
    setReplayState({ status: "loading", roundId });
    try {
      const replay = await runHiLoActionWithDemoTokenRecovery((token, launchToken) =>
        getHiLoRoundReplay({
          roundId,
          token: token ?? undefined,
          launchToken: launchToken ?? undefined,
        }),
      );
      setReplayState({ status: "ready", roundId, replay });
    } catch (error) {
      setReplayState({
        status: "error",
        roundId,
        message: buildGameErrorMessage(error, gameErrorCopyMap),
      });
    }
  }

  async function loadLatestSessionsForReplay() {
    if (!isAuthenticated || !authToken) {
      return;
    }
    setLatestReplaySessionsState((current) => ({
      ...current,
      loading: true,
      error: null,
    }));
    try {
      const sessions = await fetchHiLoLatestReplaySessions({
        titleCode: runtimeConfig.title_code,
        token: authToken,
      });
      const roundIds = new Set(
        sessions.flatMap((session) => session.rounds.map((round) => round.round_id)),
      );
      setLatestReplaySessionsState((current) => {
        const selectedRoundId =
          current.selectedRoundId && roundIds.has(current.selectedRoundId)
            ? current.selectedRoundId
            : sessions.flatMap((session) => session.rounds)[0]?.round_id ?? null;
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
        error: buildGameErrorMessage(error, gameErrorCopyMap),
      }));
    }
  }

  const latestReplayRounds = latestReplaySessionsState.sessions.flatMap(
    (session) => session.rounds,
  );
  const selectedLatestReplayRound =
    latestReplayRounds.find(
      (round) => round.round_id === latestReplaySessionsState.selectedRoundId,
    ) ??
    latestReplayRounds[0] ??
    null;
  const selectedLatestReplayIndex = selectedLatestReplayRound
    ? latestReplayRounds.findIndex(
        (round) => round.round_id === selectedLatestReplayRound.round_id,
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
    selectLatestReplayRound(nextRound.round_id);
  }

  const latestReplaySessionsPanel = (
    <GameLatestReplaySessionsPanel
      sessions={latestReplaySessionsState.sessions}
      loading={latestReplaySessionsState.loading}
      error={latestReplaySessionsState.error}
      selectedRoundId={latestReplaySessionsState.selectedRoundId}
      onSelectRound={selectLatestReplayRound}
      onSelectPrevious={() => selectLatestReplayRoundByOffset(-1)}
      onSelectNext={() => selectLatestReplayRoundByOffset(1)}
      canSelectPrevious={canSelectPreviousLatestReplay}
      canSelectNext={canSelectNextLatestReplay}
      renderViewer={(round) => <HiLoReplayViewer replay={round} copy={rulesCopy} />}
      getRoundId={(round) => round.round_id}
      formatDateTime={formatReplayDateTime}
      formatStatus={(round) => round.status}
      formatChipValue={formatChipValue}
      getBetAmount={(round) => round.bet_amount}
      getPayoutAmount={(round) => round.final_payout_amount}
      getRoundDate={(round) => round.closed_at ?? round.created_at}
    />
  );

  function handleInfoTabChange(tab: HiLoRulesModalTab) {
    setActiveInfoTab(tab);
    if (tab === "replay") {
      if (isAuthenticated) {
        void loadLatestSessionsForReplay();
      } else {
        void loadReplayForCurrentRound();
      }
    }
  }

  function dismissActionErrorToSite() {
    clearActionError();
    setRetryAction(null);
    setRetryAttempts(0);
    onExit();
  }

  function handleStartSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isBetDisabled) {
      void executeStart();
    }
  }

  const railHeader = (
    <div className="list-row hi-lo-rail-header">
      <div className="hi-lo-rail-tools">
        <button
          className="button-ghost game-icon-button game-info-button hi-lo-info-trigger"
          type="button"
          disabled={isInteractionLocked}
          aria-label={rulesCopy("runtime.action.game_info")}
          onClick={() => {
            setActiveInfoTab("rules");
            setShowRules(true);
          }}
        >
          i
        </button>
        <GameRuntimeTools
          audio={{
            hasAnySound: false,
            muted: audioPreferences.muted,
            setMuted: audioPreferences.setMuted,
            setVolume: audioPreferences.setVolume,
            volume: audioPreferences.volume,
          }}
          copy={{
            effectsAria: rulesCopy("runtime.audio.effects_aria"),
            effectsLabel: rulesCopy("runtime.audio.effects_label"),
            effectsOn: rulesCopy("runtime.audio.effects_on"),
            effectsOff: rulesCopy("runtime.audio.effects_off"),
            volume: rulesCopy("runtime.audio.volume"),
          }}
        />
      </div>
      <span className="status-badge info game-mode-badge hi-lo-mode-badge">
        {modeLabel}
      </span>
    </div>
  );

  const betPanel = (
    <GameBetPanel
      label={rulesCopy("runtime.balance.bet_label")}
      inputId="hi-lo-bet"
      value={betAmount}
      onValueChange={(value) => { notePlayerActivity(); setBetAmount(normalizeBetInput(value)); }}
      disabled={isRoundActive || isInteractionLocked}
      placeholder="5"
      inputMode="decimal"
      quickChipAmounts={["1", "2", "5", "10", "25"]}
      fieldClassName="hi-lo-bet-field"
      quickChipClassName="game-chip hi-lo-quick-chip"
      quickChipActiveClassName="active"
    />
  );

  const actionButtons = (
    <GameActionButtons
      useMobileLayout={useMobileLayout}
      desktopClassName="hi-lo-desktop-actions"
      mobileClassName="hi-lo-mobile-actions"
      betButtonLabel={
        isTerminal ? rulesCopy("runtime.action.new_hand") : rulesCopy("runtime.action.bet")
      }
      collectButtonLabel={rulesCopy("runtime.action.collect")}
      isBetDisabled={isBetDisabled}
      isCollectDisabled={isCollectDisabled}
      isBetLoading={busyAction === "start" || busyAction === "retry"}
      isCollectLoading={busyAction === "cashout"}
      betButtonClassName={`game-action-primary hi-lo-bet-action${isBetHintActive ? " hi-lo-bet-idle-pulse" : ""}`}
      collectButtonClassName="hi-lo-collect-action"
      betButtonTestId="hi-lo-bet-button"
      collectButtonTestId="hi-lo-collect-button"
      shouldPulseBetButton={isBetHintActive}
      onCollect={() => void executeCashout()}
    />
  );

  const balanceFooter = (
    <GameBalanceFooter
      isDemoPlayer={isDemoPlayer}
      visibleBalance={visibleBalance}
      potentialPayout={potentialPayout}
      copy={{
        demoBalance: rulesCopy("runtime.balance.demo"),
        defaultBalance: rulesCopy("runtime.balance.default"),
        walletBalance: (walletType) =>
          walletType === "bonus"
            ? rulesCopy("runtime.balance.bonus")
            : rulesCopy("runtime.balance.real"),
        win: rulesCopy("runtime.balance.win"),
        zeroChips: rulesCopy("runtime.balance.zero_chips"),
        chipSuffix: rulesCopy("runtime.balance.chip_suffix"),
      }}
      walletType={walletSource === "bonus" ? "bonus" : "cash"}
      className="game-visual-balance-footer hi-lo-balance-footer"
    />
  );

  const titleLogoUrl =
    titleThemeSkin?.title_render_mode === "image" && titleThemeAssets.title_logo
      ? resolveThemeAsset(titleThemeAssets.title_logo)
      : null;
  const stageClasses = [
    "hi-lo-stage",
    titleThemeSkin ? "hi-lo-stage-skinned" : null,
    titleThemeSkin ? `hi-lo-skin-density-${titleThemeSkin.button_density}` : null,
    titleThemeSkin ? `hi-lo-skin-radius-${titleThemeSkin.button_radius}` : null,
    titleThemeSkin ? `hi-lo-skin-button-${titleThemeSkin.button_style}` : null,
    titleThemeSkin ? `hi-lo-skin-emphasis-${titleThemeSkin.button_emphasis}` : null,
  ].filter(Boolean).join(" ");
  const currentCard = round?.current_card ?? null;
  const stageStyle = buildHiLoStageStyle(titleThemeAssets, titleThemeSkin);
  const quotesByAction = new Map((round?.quotes ?? []).map((quote) => [quote.action, quote]));

  const stageHeader = (
    <header className="hi-lo-stage-header">
      <h1 id="hi-lo-gameplay-title">
        {titleLogoUrl ? (
          <img className="hi-lo-stage-title-logo" src={titleLogoUrl} alt={rulesCopy("game.title")} />
        ) : (
          rulesCopy("game.title")
        )}
      </h1>
      {!useMobileLayout && (
        <button
          className="button-ghost hi-lo-close"
          type="button"
          aria-label={rulesCopy("runtime.action.close_aria")}
          onClick={onExit}
        >
          X
        </button>
      )}
    </header>
  );
  const boardSection = (
    <>
      <div className="hi-lo-play-surface">
        <HistoryList
          currentMultiplier={round?.multiplier_current ?? "1"}
          currentMultiplierLabel={rulesCopy("runtime.current_multiplier_aria")}
          emptyLabel={rulesCopy("runtime.history.empty")}
          history={history}
        />

        <div className="hi-lo-action-column hi-lo-action-column-left" aria-label={rulesCopy("runtime.prediction.red_black_aria")}>
          {renderPredictionControl("red", quotesByAction, actionLabels, isRoundActive, isInteractionLocked, executePrediction)}
          {renderPredictionControl("black", quotesByAction, actionLabels, isRoundActive, isInteractionLocked, executePrediction)}
        </div>

        <div className="hi-lo-card-stack">
          <PlayingCard card={currentCard} initialAriaLabel={rulesCopy("runtime.card.initial_aria")} />
          <div className="hi-lo-card-actions" aria-label={rulesCopy("runtime.card.actions_aria")}>
            <button
              className="button-secondary hi-lo-skip-action"
              type="button"
              disabled={!canSkip}
              onClick={() => void executeSkip()}
            >
              {rulesCopy("runtime.action.skip")}
            </button>
            <button
              className="button-secondary hi-lo-card-collect-action"
              type="button"
              disabled={isCollectDisabled}
              onClick={() => void executeCashout()}
            >
              {rulesCopy("runtime.action.collect")}
            </button>
            <button
              className={`button-secondary hi-lo-rebet-action${isTerminal ? "" : " is-reserved"}`}
              type="button"
              disabled={!isTerminal || isBetDisabled}
              aria-hidden={!isTerminal}
              tabIndex={isTerminal ? 0 : -1}
              onClick={() => void executeStart()}
            >
              {rulesCopy("runtime.action.rebet")}
            </button>
          </div>
        </div>

        <div className="hi-lo-action-column hi-lo-action-column-right" aria-label={rulesCopy("runtime.prediction.up_down_aria")}>
          {renderPredictionControl("up", quotesByAction, actionLabels, isRoundActive, isInteractionLocked, executePrediction)}
          {renderPredictionControl("down", quotesByAction, actionLabels, isRoundActive, isInteractionLocked, executePrediction)}
        </div>
      </div>
      {winCelebrationKey > 0 ? (
        <HiLoWinCelebration
          key={winCelebrationKey}
          amount={celebrationAmount}
          onDismiss={() => setWinCelebrationKey(0)}
        />
      ) : null}
    </>
  );

  const canRetryActionError = retryAction !== null && retryAttempts < MAX_ACTION_RETRY_ATTEMPTS;
  const retryExhausted = retryAction !== null && retryAttempts >= MAX_ACTION_RETRY_ATTEMPTS;
  const actionErrorMessage = retryExhausted
    ? `${errorText} ${rulesCopy("runtime.error.retry_exhausted_suffix")}`
    : errorText;
  const replayContent = isAuthenticated ? (
    latestReplaySessionsPanel
  ) : replayState.status === "ready" ? (
    <HiLoReplayViewer copy={rulesCopy} replay={replayState.replay} />
  ) : replayState.status === "loading" ? (
    <p className="empty-state">{rulesCopy("rules.replay_loading")}</p>
  ) : replayState.status === "error" ? (
    <p className="empty-state">{replayState.message}</p>
  ) : (
    <p className="empty-state">{rulesCopy("rules.replay_unavailable")}</p>
  );

  return (
    <section className="hi-lo-gameplay" data-testid="hi-lo-gameplay" aria-labelledby="hi-lo-gameplay-title">
      {useMobileLayout ? (
        <form className="mines-mobile-layout hi-lo-mobile-layout" onSubmit={handleStartSubmit}>
          {stageHeader}
          <article className={stageClasses} style={stageStyle}>
            {boardSection}
          </article>
          <GameMobileControlStack
            className="mines-mobile-play-stack hi-lo-mobile-play-stack"
            balance={<article className="mines-mobile-balance hi-lo-mobile-balance">{balanceFooter}</article>}
            betPanel={
              <section className="session-actions mines-control-rail mines-control-rail-clean mines-mobile-bet-panel hi-lo-mobile-bet-panel">
                {betPanel}
              </section>
            }
            actions={actionButtons}
          >
            <div className="hi-lo-round-metrics" aria-label={rulesCopy("runtime.history.aria_label")}>
              <div>
                <span className="list-muted">{rulesCopy("runtime.status.state_label")}</span>
                <strong>{statusLabel}</strong>
              </div>
              <div>
                <span className="list-muted">{rulesCopy("runtime.status.skip_label")}</span>
                <strong>{round ? `${round.active_skip_count}/${round.active_skip_limit}` : `0/${runtimeConfig.active_skip_limit}`}</strong>
              </div>
            </div>
          </GameMobileControlStack>
          <GameShortViewportGate
            title={rulesCopy("runtime.viewport.short_title")}
            description={rulesCopy("runtime.viewport.short_description")}
          />
        </form>
      ) : (
        <div className="hi-lo-grid">
          <GameControlRail
            headerTools={railHeader}
            betPanel={betPanel}
            footer={<article className="hi-lo-rail-footer">{balanceFooter}</article>}
            className="session-actions game-visual-control-rail hi-lo-control-rail"
            onSubmit={handleStartSubmit}
          >
            {actionButtons}
            <div className="hi-lo-round-metrics" aria-label={rulesCopy("runtime.history.aria_label")}>
              <div>
                <span className="list-muted">{rulesCopy("runtime.status.state_label")}</span>
                <strong>{statusLabel}</strong>
              </div>
              <div>
                <span className="list-muted">{rulesCopy("runtime.status.skip_label")}</span>
                <strong>{round ? `${round.active_skip_count}/${round.active_skip_limit}` : `0/${runtimeConfig.active_skip_limit}`}</strong>
              </div>
            </div>
          </GameControlRail>

          <article className={stageClasses} style={stageStyle}>
            {stageHeader}
            {boardSection}
          </article>
        </div>
      )}

      {errorText ? (
        <GameActionError
          actionLabel={
            canRetryActionError
              ? rulesCopy("runtime.action.retry_numbered", {
                  attempt: String(retryAttempts + 1),
                  max: String(MAX_ACTION_RETRY_ATTEMPTS),
                })
              : retryExhausted
                ? rulesCopy("runtime.action.retry")
                : rulesCopy("runtime.action.ok")
          }
          code={errorDiagnostic?.code}
          dismissLabel={rulesCopy("runtime.action.back_to_site")}
          message={actionErrorMessage}
          onAction={
            canRetryActionError
              ? retryLastAction
              : retryExhausted
                ? () => window.location.reload()
                : clearActionError
          }
          onDismiss={retryAction ? dismissActionErrorToSite : undefined}
          requestId={errorDiagnostic?.requestId}
          supportId={errorDiagnostic?.supportId}
          testId="hi-lo-action-error-dialog"
          title={rulesCopy("runtime.error.title")}
        />
      ) : null}

      {showRules ? (
        <HiLoRulesModal
          activeTab={activeInfoTab}
          copy={rulesCopy}
          gameTitle={rulesCopy("game.title")}
          locale={runtimeLocale}
          replayAvailable={isAuthenticated || Boolean(round?.terminal)}
          replayContent={replayContent}
          runtimeConfig={runtimeConfig}
          onClose={() => setShowRules(false)}
          onTabChange={handleInfoTabChange}
        />
      ) : null}
    </section>
  );

  function clearActionError() {
    setErrorText("");
    setErrorDiagnostic(null);
  }

  function setActionGameError(error: unknown) {
    setErrorText(buildGameErrorMessage(error, gameErrorCopyMap));
    setErrorDiagnostic(buildGameErrorDiagnostic(error));
  }
}

function renderPredictionControl(
  action: HiLoPredictionAction,
  quotesByAction: Map<HiLoPredictionAction, HiLoQuote>,
  actionLabels: Record<HiLoPredictionAction, string>,
  isRoundActive: boolean,
  isInteractionLocked: boolean,
  executePrediction: (action: HiLoPredictionAction) => Promise<void>,
) {
  const quote = quotesByAction.get(action);
  return (
    <PredictionButton
      action={action}
      disabled={!quote || !isRoundActive || isInteractionLocked}
      key={action}
      label={actionLabels[action]}
      quote={quote}
      onChoose={() => {
        if (quote) {
          void executePrediction(action);
        }
      }}
    />
  );
}

function PredictionButton({
  action,
  disabled,
  label,
  quote,
  onChoose,
}: {
  action: HiLoPredictionAction;
  disabled: boolean;
  label: string;
  quote: HiLoQuote | undefined;
  onChoose: () => void;
}) {
  return (
    <button
      className={`hi-lo-prediction hi-lo-prediction-${action}${quote ? "" : " is-placeholder"}`}
      type="button"
      disabled={disabled}
      onClick={onChoose}
    >
      <span className="hi-lo-prediction-label">
        <span className="hi-lo-prediction-icon" aria-hidden="true">
          {readPredictionIcon(action)}
        </span>
        <span>{label}</span>
      </span>
      <strong>{quote ? `${formatMultiplierDisplay(quote.multiplier)}x` : "--"}</strong>
    </button>
  );
}

function readPredictionIcon(action: HiLoPredictionAction) {
  if (action === "black") {
    return "";
  }
  if (action === "red") {
    return "";
  }
  if (action === "down") {
    return "\u2193";
  }
  return "\u2191";
}

function PlayingCard({
  card,
  initialAriaLabel,
}: {
  card: HiLoCard | null;
  initialAriaLabel: string;
}) {
  const suit = card?.suit ?? "clubs";
  const color = card?.color ?? "black";
  const suitSymbol = card ? readSuitSymbol(card.suit) : null;
  return (
    <div
      className={`hi-lo-card is-${color} suit-${suit}${card ? "" : " is-placeholder"}`}
      aria-label={card ? `${card.rank_label} ${suit}` : initialAriaLabel}
    >
      {card ? (
        <>
          <strong className={`hi-lo-card-rank${card.rank_label.length > 1 ? " is-wide" : ""}`}>
            {card.rank_label}
          </strong>
          <span className="hi-lo-card-suit-symbol">{suitSymbol}</span>
        </>
      ) : (
        <strong className="hi-lo-card-rank">?</strong>
      )}
    </div>
  );
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

function formatChipValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "0";
  }
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(num)) {
    return "0";
  }
  return num.toFixed(2);
}

function readSuitSymbol(suit: HiLoCard["suit"]) {
  if (suit === "clubs") {
    return "♣";
  }
  if (suit === "spades") {
    return "♠";
  }
  if (suit === "hearts") {
    return "♥";
  }
  return "♦";
}

function buildHiLoStageStyle(
  titleThemeAssets: Record<string, string>,
  titleThemeSkin: TitleThemeSkin | null,
): CSSProperties | undefined {
  const backgroundSrc = resolveThemeAsset(titleThemeAssets.game_area_background);
  if (!backgroundSrc && !titleThemeSkin) {
    return undefined;
  }
  return {
    "--hi-lo-game-area-background-image": backgroundSrc ? `url("${backgroundSrc}")` : undefined,
    "--hi-lo-game-area-background-size": titleThemeSkin?.game_area_background_fit ?? "cover",
    "--hi-lo-game-area-background-position":
      titleThemeSkin?.game_area_background_position ?? "center",
    "--hi-lo-game-area-overlay": titleThemeSkin
      ? HI_LO_SKIN_OVERLAY[titleThemeSkin.game_area_overlay]
      : "rgba(0, 0, 0, 0)",
  } as CSSProperties;
}

function resolveThemeAsset(value: string | undefined) {
  return value ? resolveBackendAssetUrl(value) : null;
}

function readHiLoStoredLaunchToken(): StoredHiLoLaunchToken {
  if (typeof window === "undefined") {
    return { token: "", expiresAt: "", titleCode: "" };
  }
  const snapshot = readGameStorageSnapshot(window.localStorage, HI_LO_GAME_STORAGE_NAMESPACE);
  return {
    token: snapshot.gameLaunchToken,
    expiresAt: snapshot.gameLaunchTokenExpiresAt,
    titleCode: snapshot.gameLaunchTitleCode,
  };
}

function isExpiredIsoDate(isoDate: string): boolean {
  return new Date(isoDate).getTime() <= Date.now();
}

function HistoryList({
  currentMultiplier,
  currentMultiplierLabel,
  emptyLabel,
  history,
}: {
  currentMultiplier: string;
  currentMultiplierLabel: string;
  emptyLabel: string;
  history: HiLoHistoryItem[];
}) {
  return (
    <div className="hi-lo-history">
      <div className="hi-lo-history-list">
        {history.length === 0 ? (
          <span className="hi-lo-history-empty">{emptyLabel}</span>
        ) : (
          history.slice(-5).map((item) => (
            <div className={`hi-lo-history-item is-${item.status}`} key={item.id}>
              <strong className={item.card ? `is-${item.card.color}` : undefined}>
                {item.card ? `${item.card.rank_label}${readSuitSymbol(item.card.suit)}` : "-"}
              </strong>
              <small>{formatMultiplierDisplay(item.multiplier)}x</small>
            </div>
          ))
        )}
      </div>
      <CurrentExposureBadge label={currentMultiplierLabel} multiplier={currentMultiplier} />
    </div>
  );
}

function CurrentExposureBadge({ label, multiplier }: { label: string; multiplier: string }) {
  return (
    <aside className="hi-lo-current-exposure" aria-label={label}>
      <strong>{formatMultiplierDisplay(multiplier)}x</strong>
    </aside>
  );
}

function readBalanceAmount({
  walletSource,
  wallets,
}: {
  walletSource: HiLoWalletSource;
  wallets: WalletSummary[];
}) {
  const wallet = wallets.find((candidate) => candidate.wallet_type === walletSource);
  return wallet?.balance_snapshot ?? "0";
}

function normalizeBetInput(value: string) {
  const normalized = value.replace(",", ".").replace(/[^\d.]/g, "");
  const firstDot = normalized.indexOf(".");
  if (firstDot === -1) {
    return normalized;
  }
  return `${normalized.slice(0, firstDot + 1)}${normalized.slice(firstDot + 1).replace(/\./g, "")}`;
}

function normalizeBetAmount(value: string) {
  const numeric = parseChipAmount(value);
  if (numeric <= 0) {
    return "0";
  }
  return value.trim() || "0";
}

function parseChipAmount(value: string) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatChipAmount(value: number) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  return value.toFixed(2).replace(/\.00$/, "");
}

function formatMultiplierDisplay(value: string) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return value;
  }
  return parsed.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function createHiLoActionLabels(copy: HiLoCopyResolver): Record<HiLoPredictionAction, string> {
  return {
    black: copy("runtime.prediction.black"),
    red: copy("runtime.prediction.red"),
    down: copy("runtime.prediction.down"),
    up: copy("runtime.prediction.up"),
  };
}

function createHiLoGameErrorCopyMap(copy: HiLoCopyResolver): GameErrorCopyMap {
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

function createIdempotencyKey() {
  if (typeof window !== "undefined" && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `hi-lo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
