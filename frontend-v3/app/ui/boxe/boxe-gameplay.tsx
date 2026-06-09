"use client";

import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react";
import { apiRequest, ApiRequestError, resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleThemeSkin } from "@/app/lib/types";
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
import { GameMobileControlStack } from "../game-runtime/game-mobile-control-stack";
import { GameMobileSettingsSheet } from "../game-runtime/game-mobile-settings-sheet";
import { GameShortViewportGate } from "../game-runtime/game-short-viewport-gate";
import {
  BOXE_GAME_STORAGE_NAMESPACE,
  clearStoredAuthState,
  clearStoredDemoAnonToken,
  clearStoredDemoLaunchToken,
  readGameStorageSnapshot,
  writeStoredDemoAnonToken,
  writeStoredDemoLaunchToken,
  writeStoredRealLaunchToken,
} from "../game-runtime/game-storage";
import { GameRuntimeTools } from "../game-runtime/game-top-bar";
import { useBoxeAudio, type BoxeAudioPreferences } from "./use-boxe-audio";
import {
  createBoxeCopyResolver,
  resolveBoxeLocale,
  type BoxeLocale,
} from "./boxe-i18n/boxe-copy-defaults";
import { BoxePyramidBoard, type BoxeBoardPick } from "./boxe-pyramid-board";
import { BoxeReplayViewer } from "./boxe-replay-viewer";
import { BoxeRulesModal, type BoxeRulesModalTab } from "./boxe-rules-modal";
import { BoxeSettingsPanel } from "./boxe-settings-panel";
import {
  cashoutBoxeRound,
  fetchBoxeLatestReplaySessions,
  getBoxeReplay,
  issueBoxeDemoAnonToken,
  issueBoxeDemoLaunchToken,
  revealBoxePick,
  startBoxeRound,
  type BoxeCashoutResponse,
  type BoxePyramidFullReveal,
  type BoxeRevealResponse,
  type BoxeRoundReplay,
  type BoxeRoundStatus,
  type BoxeRuntimeConfig,
  type BoxeStartRoundResponse,
  type BoxeTableSession,
  type BoxeWalletSource,
} from "./use-boxe-runtime";
import {
  GameLatestReplaySessionsPanel,
  type GameLatestAccessSessionHistory,
} from "../game-runtime/game-latest-replay-panel";

const BOXE_STANDALONE_MEDIA_QUERY = "(max-width: 960px), (pointer: coarse)";
const BOXE_SKIN_OVERLAY: Record<TitleThemeSkin["game_area_overlay"], string> = {
  none: "transparent",
  light: "rgba(0, 0, 0, 0.12)",
  medium: "rgba(0, 0, 0, 0.28)",
  strong: "rgba(0, 0, 0, 0.46)",
};
const BOXE_CLOSED_CELL_DOMINANCE: Record<
  NonNullable<TitleThemeSkin["closed_cell_background_dominance"]>,
  { surfaceMix: string; textureOpacity: string }
> = {
  subtle: { surfaceMix: "72%", textureOpacity: "0.32" },
  balanced: { surfaceMix: "52%", textureOpacity: "0.58" },
  strong: { surfaceMix: "32%", textureOpacity: "0.78" },
  solid: { surfaceMix: "100%", textureOpacity: "0" },
};

type BoxeRound = {
  sessionId: string;
  roundId: string;
  rows: number;
  difficulty: string;
  multipliers: string[];
  status: BoxeRoundStatus;
  serverSeedHash: string;
  collectAmount: string;
};

type BusyAction = "start" | "reveal" | "cashout" | "retry" | null;

type RetryAction =
  | {
      type: "start";
      idempotencyKey: string;
      rows: number;
      difficulty: string;
      betAmount: string;
      walletSource: BoxeWalletSource;
    }
  | {
      type: "reveal";
      idempotencyKey: string;
      roundId: string;
      row: number;
      position: number;
    }
  | {
      type: "cashout";
      idempotencyKey: string;
      roundId: string;
    };

type BoxeReplayState = {
  roundId: string | null;
  replay: BoxeRoundReplay | null;
  loading: boolean;
  error: string | null;
};

type LatestReplaySessionsState = {
  sessions: GameLatestAccessSessionHistory<BoxeRoundReplay>[];
  loading: boolean;
  error: string | null;
  selectedRoundId: string | null;
};

const TERMINAL_STATUSES = new Set<BoxeRoundStatus>([
  "completed_cashout",
  "completed_top_row",
  "failed_mine",
  "expired",
  "quarantined",
]);

const BOXE_GAME_ERROR_COPY_MAP = {
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

type LaunchTokenResponse = {
  game_launch_token: string;
  expires_at: string;
  title_code: string;
  site_code: string;
  player_id: string;
  mode: string;
};

function isExpiredIsoDate(isoDate: string): boolean {
  return new Date(isoDate).getTime() <= Date.now();
}

export function BoxeGameplay({
  runtimeConfig,
  titleThemeAssets,
  titleThemeSkin,
  bootRequest,
  initialAccessToken,
  initialGameLaunchToken,
  initialGameLaunchTokenExpiresAt,
  onGameLaunchTokenChange,
  onGameLaunchTokenExpiresAtChange,
  audioPreferences,
  accessSessionId,
  tableSession,
  onExit,
  onTableSessionChange,
  isHostFullscreen,
}: {
  runtimeConfig: BoxeRuntimeConfig;
  titleThemeAssets: Record<string, string>;
  titleThemeSkin: TitleThemeSkin | null;
  bootRequest: GameBootRequest;
  initialAccessToken: string;
  initialGameLaunchToken: string;
  initialGameLaunchTokenExpiresAt: string;
  onGameLaunchTokenChange: (value: string) => void;
  onGameLaunchTokenExpiresAtChange: (value: string) => void;
  audioPreferences: BoxeAudioPreferences & {
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
  };
  accessSessionId: string | null;
  tableSession: BoxeTableSession | null;
  onExit: () => void;
  onTableSessionChange: (tableSession: BoxeTableSession) => void;
  isHostFullscreen: boolean;
}) {
  const [locale, setLocale] = useState<BoxeLocale>(() =>
    resolveBoxeLocale(runtimeConfig.presentation_config?.default_locale),
  );
  const copy = useMemo(
    () => createBoxeCopyResolver(locale, runtimeConfig.presentation_config?.copy),
    [locale, runtimeConfig.presentation_config?.copy],
  );
  const [selectedRows, setSelectedRows] = useState(runtimeConfig.default_rows);
  const [selectedDifficulty, setSelectedDifficulty] = useState(
    runtimeConfig.default_difficulty,
  );
  const [betAmount, setBetAmount] = useState("5");
  const [authToken, setAuthToken] = useState(initialAccessToken);
  const isDemoMode = bootRequest.forceDemoMode;
  const isAuthenticated = !isDemoMode && !!authToken;
  const [gameLaunchToken, setGameLaunchToken] = useState(initialGameLaunchToken);
  const [gameLaunchTokenExpiresAt, setGameLaunchTokenExpiresAt] = useState(initialGameLaunchTokenExpiresAt);
  const [demoAnonToken, setDemoAnonToken] = useState<string | null>(null);
  const [demoLaunchToken, setDemoLaunchToken] = useState<string | null>(null);
  const [demoBalance, setDemoBalance] = useState("100");
  const [round, setRound] = useState<BoxeRound | null>(null);
  const [picks, setPicks] = useState<BoxeBoardPick[]>([]);
  const [pyramidFullReveal, setPyramidFullReveal] =
    useState<BoxePyramidFullReveal | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorText, setErrorText] = useState("");
  const [errorDiagnostic, setErrorDiagnostic] = useState<GameErrorDiagnostic | null>(null);
  const [retryAction, setRetryAction] = useState<RetryAction | null>(null);
  const [infoTab, setInfoTab] = useState<BoxeRulesModalTab>("rules");
  const [replayState, setReplayState] = useState<BoxeReplayState>({
    roundId: null,
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
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [showMobileSettings, setShowMobileSettings] = useState(false);
  const [showRules, setShowRules] = useState(false);
  const [celebration, setCelebration] = useState<{
    amount: string;
    kind: "cashout" | "top_row";
    id: number;
  } | null>(null);
  const [isBetHintActive, setIsBetHintActive] = useState(false);
  const [playerActivityTick, setPlayerActivityTick] = useState(0);
  const boxeAudio = useBoxeAudio(audioPreferences, titleThemeAssets);

  const walletSource: BoxeWalletSource = bootRequest.forceDemoMode
    ? "demo"
    : bootRequest.walletSource ?? "cash";
  const activeMultipliers =
    round?.multipliers ??
    runtimeConfig.multiplier_paths[String(selectedRows)]?.[selectedDifficulty] ??
    [];
  const safePicksCount = picks.filter((pick) => pick.outcome === "safe").length;
  const terminalStatus = readTerminalStatus(round?.status ?? null);
  const isRoundActive = round !== null && terminalStatus === null;
  const isInteractionLocked = busyAction !== null;
  const activeRow =
    isRoundActive && safePicksCount < (round?.rows ?? selectedRows)
      ? safePicksCount
      : null;
  const balanceAmount =
    walletSource === "demo"
      ? demoBalance
      : tableSession?.table_balance_amount
        ?? "0";
  const insufficientBalance =
    !isRoundActive && parseChipAmount(betAmount) > parseChipAmount(balanceAmount);
  const canBet =
    parseChipAmount(betAmount) > 0 &&
    !insufficientBalance &&
    !isInteractionLocked &&
    (round === null || terminalStatus !== null);
  const canCollect =
    isRoundActive &&
    safePicksCount > 0 &&
    parseChipAmount(round?.collectAmount ?? "0") > 0 &&
    !isInteractionLocked;
  const settingsDisabled = isRoundActive || isInteractionLocked;
  const useMobileLayout = isMobileViewport;

  useEffect(() => {
    setLocale(resolveBoxeLocale(runtimeConfig.presentation_config?.default_locale));
  }, [runtimeConfig.presentation_config?.default_locale]);

  useEffect(() => {
    const mediaQuery = window.matchMedia(BOXE_STANDALONE_MEDIA_QUERY);
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
    if (!useMobileLayout || settingsDisabled) {
      setShowMobileSettings(false);
    }
  }, [settingsDisabled, useMobileLayout]);

  useEffect(() => {
    if (!canBet || isBetHintActive) {
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
  }, [canBet, isBetHintActive, playerActivityTick]);

  useEffect(() => {
    if (runtimeConfig.rows_enabled.includes(selectedRows)) {
      return;
    }
    setSelectedRows(runtimeConfig.default_rows);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
  }, [
    runtimeConfig.default_rows,
    runtimeConfig.rows_enabled,
    selectedRows,
    terminalStatus,
  ]);

  useEffect(() => {
    if (runtimeConfig.difficulty_enabled.includes(selectedDifficulty)) {
      return;
    }
    setSelectedDifficulty(runtimeConfig.default_difficulty);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
  }, [
    runtimeConfig.default_difficulty,
    runtimeConfig.difficulty_enabled,
    selectedDifficulty,
    terminalStatus,
  ]);

  useEffect(() => {
    if (!showRules || infoTab !== "replay") {
      return;
    }
    if (isAuthenticated) {
      void loadLatestSessionsForReplay();
      return;
    }
    if (!round?.roundId) {
      return;
    }
    if (replayState.roundId === round.roundId && (replayState.replay || replayState.loading)) {
      return;
    }

    let isMounted = true;
    setReplayState({
      roundId: round.roundId,
      replay: null,
      loading: true,
      error: null,
    });
    runBoxeActionWithDemoTokenRecovery((token, launchToken) =>
      getBoxeReplay({
        roundId: round.roundId,
        token: token ?? undefined,
        launchToken: launchToken ?? undefined,
      }),
    )
      .then((replay) => {
        if (isMounted) {
          setReplayState({
            roundId: replay.round_id,
            replay,
            loading: false,
            error: null,
          });
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setReplayState({
            roundId: round.roundId,
            replay: null,
            loading: false,
            error: buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP),
          });
        }
      });
    return () => {
      isMounted = false;
    };
  }, [infoTab, round?.roundId, showRules, isAuthenticated]);

  async function ensureActionToken(): Promise<string | null> {
    if (authToken) {
      return authToken;
    }
    if (!bootRequest.forceDemoMode) {
      throw new Error("Accedi per giocare con saldo reale.");
    }
    return null;
  }

  async function ensureBoxeLaunchToken(): Promise<string | null> {
    if (bootRequest.forceDemoMode) {
      if (demoLaunchToken) {
        return demoLaunchToken;
      }
      try {
        const anonToken = await issueBoxeDemoAnonToken();
        setDemoAnonToken(anonToken.anonymous_token);
        writeStoredDemoAnonToken(
          window.localStorage,
          BOXE_GAME_STORAGE_NAMESPACE,
          anonToken.anonymous_token,
        );
        const launchData = await issueBoxeDemoLaunchToken(
          anonToken.anonymous_token,
          bootRequest.titleCode,
        );
        setDemoLaunchToken(launchData.game_launch_token);
        writeStoredDemoLaunchToken(
          window.localStorage,
          BOXE_GAME_STORAGE_NAMESPACE,
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
      gameLaunchToken &&
      gameLaunchTokenExpiresAt &&
      !isExpiredIsoDate(gameLaunchTokenExpiresAt)
    ) {
      return gameLaunchToken;
    }
    try {
      const bearerToken = await ensureActionToken();
      if (!bearerToken) {
        throw new Error("Accedi per giocare con saldo reale.");
      }
      const issueData = await apiRequest<LaunchTokenResponse>(
        "/games/boxe/launch-token",
        {
          method: "POST",
          body: JSON.stringify({
            game_code: "boxe",
            title_code: bootRequest.titleCode,
          }),
        },
        bearerToken,
      );
      writeStoredRealLaunchToken(
        window.localStorage,
        BOXE_GAME_STORAGE_NAMESPACE,
        issueData.game_launch_token,
        issueData.expires_at,
        bootRequest.titleCode,
      );
      setGameLaunchToken(issueData.game_launch_token);
      setGameLaunchTokenExpiresAt(issueData.expires_at);
      onGameLaunchTokenChange(issueData.game_launch_token);
      onGameLaunchTokenExpiresAtChange(issueData.expires_at);
      return issueData.game_launch_token;
    } catch {
      return null;
    }
  }

  async function runBoxeActionWithDemoTokenRecovery<T>(
    action: (token: string | null, launchToken: string | null) => Promise<T>,
  ): Promise<T> {
    const token = await ensureActionToken();
    const launchToken = await ensureBoxeLaunchToken();
    try {
      return await action(token, launchToken);
    } catch (error) {
      if (bootRequest.forceDemoMode) {
        if (error instanceof ApiRequestError && error.status === 401) {
          clearStoredDemoLaunchToken(window.localStorage, BOXE_GAME_STORAGE_NAMESPACE);
          setDemoLaunchToken(null);
          const newLaunchToken = await ensureBoxeLaunchToken();
          return await action(null, newLaunchToken);
        }
        throw error;
      }
      if (!isBearerTokenAuthError(error)) {
        throw error;
      }
      clearStoredAuthState(window.localStorage, BOXE_GAME_STORAGE_NAMESPACE);
      setAuthToken("");
      const newToken = await ensureActionToken();
      if (!newToken) {
        throw new Error("Accedi per giocare con saldo reale.");
      }
      const newLaunchToken = await ensureBoxeLaunchToken();
      return await action(newToken, newLaunchToken);
    }
  }

  function clearTerminalRoundForConfigChange() {
    setRound(null);
    setPicks([]);
    setPyramidFullReveal(null);
    setReplayState({ roundId: null, replay: null, loading: false, error: null });
    setCelebration(null);
    clearActionError();
    setRetryAction(null);
    setInfoTab("rules");
  }

  function notePlayerActivity() {
    setIsBetHintActive(false);
    setPlayerActivityTick((currentTick) => currentTick + 1);
  }

  function handleRowsChange(rows: number) {
    if (settingsDisabled || rows === selectedRows) {
      return;
    }
    notePlayerActivity();
    setSelectedRows(rows);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
  }

  function handleDifficultyChange(difficulty: string) {
    if (settingsDisabled || difficulty === selectedDifficulty) {
      return;
    }
    notePlayerActivity();
    setSelectedDifficulty(difficulty);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
  }

  async function executeStart(action?: Extract<RetryAction, { type: "start" }>) {
    notePlayerActivity();
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const rows = action?.rows ?? selectedRows;
    const difficulty = action?.difficulty ?? selectedDifficulty;
    const wager = normalizeBetAmount(action?.betAmount ?? betAmount);
    const source = action?.walletSource ?? walletSource;
    setBusyAction(action ? "retry" : "start");
    clearActionError();
    setRetryAction(null);
    setPicks([]);
    setPyramidFullReveal(null);
    setReplayState({ roundId: null, replay: null, loading: false, error: null });
    try {
      const response = await runBoxeActionWithDemoTokenRecovery((token, launchToken) =>
        startBoxeRound({
          titleCode: bootRequest.titleCode,
          rows,
          difficulty,
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
      boxeAudio.play("bet_placed");
      applyStartResponse(response, rows, difficulty, wager);
      setBetAmount(wager);
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "start",
        idempotencyKey,
        rows,
        difficulty,
        betAmount: wager,
        walletSource: source,
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function executeReveal(
    row: number,
    position: number,
    action?: Extract<RetryAction, { type: "reveal" }>,
  ) {
    notePlayerActivity();
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.roundId ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "reveal");
    clearActionError();
    setRetryAction(null);
    try {
      const response = await runBoxeActionWithDemoTokenRecovery((token, launchToken) =>
        revealBoxePick({
          roundId: targetRoundId,
          row,
          position,
          token: token ?? undefined,
          idempotencyKey,
          launchToken: launchToken ?? undefined,
        }),
      );
      if (response.outcome === "mine") {
        boxeAudio.play("mine_reveal");
      } else if (response.outcome === "top_row") {
        boxeAudio.play("top_row_won");
      } else {
        boxeAudio.play("safe_reveal");
      }
      applyRevealResponse(response, row, position);
    } catch (error) {
      setActionGameError(error);
      setRetryAction({
        type: "reveal",
        idempotencyKey,
        roundId: targetRoundId,
        row,
        position,
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
    const targetRoundId = action?.roundId ?? round?.roundId ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "cashout");
    clearActionError();
    setRetryAction(null);
    try {
      const response = await runBoxeActionWithDemoTokenRecovery((token, launchToken) =>
        cashoutBoxeRound({
          roundId: targetRoundId,
          token: token ?? undefined,
          idempotencyKey,
          launchToken: launchToken ?? undefined,
        }),
      );
      boxeAudio.play("cashout_won");
      applyCashoutResponse(response);
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

  function applyStartResponse(
    response: BoxeStartRoundResponse,
    rows: number,
    difficulty: string,
    wager: string,
  ) {
    if (walletSource === "demo") {
      if (response.wallet_balance_after_start) {
        setDemoBalance(formatChipAmount(parseChipAmount(response.wallet_balance_after_start)));
      } else {
        setDemoBalance((currentBalance) =>
          formatChipAmount(parseChipAmount(currentBalance) - parseChipAmount(wager)),
        );
      }
    }
    setRound({
      sessionId: response.session_id,
      roundId: response.round_id,
      rows,
      difficulty,
      multipliers: response.multipliers,
      status: response.status,
      serverSeedHash: response.server_seed_hash,
      collectAmount: "0",
    });
  }

  function applyRevealResponse(
    response: BoxeRevealResponse,
    row: number,
    position: number,
  ) {
    const pickOutcome = response.outcome === "mine" ? "mine" : "safe";
    if (response.table_session) {
      onTableSessionChange(response.table_session);
    }
    if (walletSource === "demo" && response.settlement?.wallet_balance_after) {
      setDemoBalance(formatChipAmount(parseChipAmount(response.settlement.wallet_balance_after)));
    }
    setPicks((currentPicks) => [
      ...currentPicks.filter((pick) => !(pick.row === row && pick.position === position)),
      {
        row,
        position,
        outcome: pickOutcome,
        multiplier: response.multiplier,
        payout: response.payout,
      },
    ]);
    setRound((currentRound) => currentRound
      ? {
          ...currentRound,
          status: response.status,
          collectAmount: response.outcome === "mine" ? "0" : response.payout,
        }
      : currentRound);

    if (response.outcome === "mine") {
      setPyramidFullReveal(response.pyramid_full_reveal ?? null);
      return;
    }
    if (response.outcome === "top_row") {
      setPyramidFullReveal(response.pyramid_full_reveal ?? null);
      setCelebration({
        amount: response.payout,
        kind: "top_row",
        id: Date.now(),
      });
      return;
    }
  }

  function applyCashoutResponse(response: BoxeCashoutResponse) {
    if (walletSource === "demo") {
      if (response.settlement?.wallet_balance_after) {
        setDemoBalance(formatChipAmount(parseChipAmount(response.settlement.wallet_balance_after)));
      } else {
        setDemoBalance((currentBalance) =>
          formatChipAmount(parseChipAmount(currentBalance) + parseChipAmount(response.payout)),
        );
      }
    }
    if (response.table_session) {
      onTableSessionChange(response.table_session);
    }
    setRound((currentRound) => currentRound
      ? {
          ...currentRound,
          status: response.status,
          collectAmount: response.payout,
        }
      : currentRound);
    setPyramidFullReveal(response.pyramid_full_reveal);
    setCelebration({
      amount: response.payout,
      kind: "cashout",
      id: Date.now(),
    });
  }

  function retryLastAction() {
    if (!retryAction) {
      return;
    }
    if (retryAction.type === "start") {
      void executeStart(retryAction);
      return;
    }
    if (retryAction.type === "reveal") {
      void executeReveal(retryAction.row, retryAction.position, retryAction);
      return;
    }
    void executeCashout(retryAction);
  }

  function openInfoModal() {
    setInfoTab("rules");
    setShowRules(true);
  }

  function handleStartSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void executeStart();
  }

  const boxeSettings = (
    <BoxeSettingsPanel
      copy={copy}
      disabled={settingsDisabled}
      onDifficultyChange={handleDifficultyChange}
      onRowsChange={handleRowsChange}
      runtimeConfig={runtimeConfig}
      selectedDifficulty={selectedDifficulty}
      selectedRows={selectedRows}
    />
  );
  const boxeActions = (
    <GameActionButtons
      useMobileLayout={useMobileLayout}
      betButtonLabel={busyAction === "start" ? "..." : copy("actions.bet")}
      collectButtonLabel={
        busyAction === "cashout" ? "..." : copy("actions.collect")
      }
      isBetDisabled={!canBet || isInteractionLocked}
      isBetLoading={busyAction === "start"}
      isCollectDisabled={!canCollect || isInteractionLocked}
      isCollectLoading={busyAction === "cashout"}
      className="boxe-action-buttons mines-action-buttons"
      desktopClassName="mines-desktop-actions"
      mobileClassName="mines-mobile-actions"
      betButtonTestId={!isRoundActive ? "boxe-primary-action" : undefined}
      collectButtonTestId={isRoundActive ? "boxe-primary-action" : undefined}
      shouldPulseBetButton={isBetHintActive}
      betButtonClassName={isBetHintActive ? "boxe-bet-idle-pulse" : undefined}
      onCollect={() => void executeCashout()}
    />
  );
  const boxeDesktopBetPanel = (
    <GameBetPanel
      label={copy("settings.bet_amount")}
      inputId="boxe-bet-input"
      inputTestId="boxe-bet-input"
      value={betAmount}
      onValueChange={(value) => { notePlayerActivity(); setBetAmount(normalizeBetInput(value)); }}
      inputMode="decimal"
      disabled={isRoundActive || isInteractionLocked}
      quickChipAmounts={["1", "2", "5", "10", "25"]}
      actions={boxeActions}
      className="boxe-bet-panel mines-bet-panel"
      fieldClassName="mines-bet-field boxe-bet-field"
      quickChipRowClassName="quick-chip-row boxe-bet-chip-row"
      quickChipClassName="quick-chip"
    />
  );
  const boxeMobileBetPanel = (
    <GameBetPanel
      label={copy("settings.bet_amount")}
      inputId="boxe-bet-input-mobile"
      inputTestId="boxe-bet-input-mobile"
      value={betAmount}
      onValueChange={(value) => { notePlayerActivity(); setBetAmount(normalizeBetInput(value)); }}
      inputMode="decimal"
      disabled={isRoundActive || isInteractionLocked}
      quickChipAmounts={["1", "2", "5", "10", "25"]}
      fieldClassName="mines-bet-field boxe-bet-field"
      quickChipRowClassName="quick-chip-row boxe-bet-chip-row"
      quickChipClassName="quick-chip"
    />
  );
  const boxeBalanceFooter = (
    <GameBalanceFooter
      isDemoPlayer={walletSource === "demo"}
      visibleBalance={balanceAmount}
      potentialPayout={isRoundActive ? round?.collectAmount ?? "0" : null}
      copy={{
        demoBalance: copy("balance.demo"),
        defaultBalance: copy("balance.label"),
        walletBalance: () => copy("balance.label"),
        win: "Win",
        zeroChips: "0 CHIP",
        chipSuffix: "CHIP",
      }}
      balanceLabel={walletSource === "demo" ? undefined : copy("balance.table")}
      walletType={walletSource === "bonus" ? "bonus" : "cash"}
      className="mines-balance-footer boxe-balance-footer"
    />
  );
  const modeLabel = walletSource === "demo"
    ? "DEMO MODE"
    : walletSource === "bonus"
      ? "BONUS MODE"
      : "REAL MODE";
  const renderInfoButton = () => (
    <button
      className="button-ghost mines-rules-trigger boxe-rules-trigger"
      type="button"
      disabled={isInteractionLocked}
      aria-label={copy("actions.game_info")}
      onClick={openInfoModal}
    >
      i
    </button>
  );
  const renderRuntimeTools = () => (
    <GameRuntimeTools
      locale={locale}
      audio={{
        hasAnySound: boxeAudio.hasAnySound,
        muted: audioPreferences.muted,
        setMuted: audioPreferences.setMuted,
        setVolume: audioPreferences.setVolume,
        volume: audioPreferences.volume,
      }}
      copy={{
        effectsAria: "Audio effetti",
        effectsLabel: "Effetti",
        effectsOn: "On",
        effectsOff: "Off",
        volume: "Volume",
      }}
    />
  );
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
      const sessions = await fetchBoxeLatestReplaySessions({
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
        error: buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP),
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
      renderViewer={(round) => <BoxeReplayViewer replay={round} />}
      getRoundId={(round) => round.round_id}
      formatDateTime={formatReplayDateTime}
      formatStatus={(round) => round.status}
      formatChipValue={formatChipValue}
      getBetAmount={(round) => round.bet_amount}
      getPayoutAmount={(round) => round.payout_amount}
      getRoundDate={(round) => round.closed_at ?? round.created_at}
    />
  );

  const railHeader = (
    <div className="list-row mines-rail-header boxe-rail-header">
      <div className="mines-rail-tools boxe-rail-tools">
        {renderInfoButton()}
        {renderRuntimeTools()}
      </div>
      <span className="status-badge info mines-mode-badge boxe-mode-badge">
        {modeLabel}
      </span>
    </div>
  );
  const mobileStageTools = useMobileLayout ? (
    <div className="mines-mobile-stage-tools boxe-mobile-stage-tools">
      {renderInfoButton()}
      {renderRuntimeTools()}
    </div>
  ) : null;
  const visiblePayoutStart = safePicksCount;
  const visibleMultipliers = activeMultipliers.slice(visiblePayoutStart, visiblePayoutStart + 5);
  const stageSubtitle = celebration
    ? copy("round.won_amount", { amount: celebration.amount })
    : "\u00A0";
  const gameTitle = copy("game.title");
  const titleLogoUrl =
    titleThemeSkin?.title_render_mode === "image" && titleThemeAssets.title_logo
      ? resolveBackendAssetUrl(titleThemeAssets.title_logo)
      : null;
  const gameAreaBackgroundUrl =
    titleThemeSkin && titleThemeAssets.game_area_background
      ? resolveBackendAssetUrl(titleThemeAssets.game_area_background)
      : null;
  const cellFaceDownBackgroundUrl =
    titleThemeSkin && titleThemeAssets.cell_face_down_background
      ? resolveBackendAssetUrl(titleThemeAssets.cell_face_down_background)
      : null;
  const safeIconSrc = titleThemeAssets.symbol_safe
    ? resolveBackendAssetUrl(titleThemeAssets.symbol_safe)
    : undefined;
  const mineIconSrc = titleThemeAssets.symbol_mine
    ? resolveBackendAssetUrl(titleThemeAssets.symbol_mine)
    : undefined;
  const boardSkinStyle =
    titleThemeSkin && (gameAreaBackgroundUrl || cellFaceDownBackgroundUrl)
      ? ({
          "--ck-game-area-background": gameAreaBackgroundUrl
            ? `url("${gameAreaBackgroundUrl}")`
            : undefined,
          "--ck-game-area-background-size": titleThemeSkin.game_area_background_fit,
          "--ck-game-area-background-position": titleThemeSkin.game_area_background_position,
          "--ck-game-area-overlay": BOXE_SKIN_OVERLAY[titleThemeSkin.game_area_overlay],
          "--ck-closed-cell-surface-mix":
            BOXE_CLOSED_CELL_DOMINANCE[
              titleThemeSkin.closed_cell_background_dominance ?? "balanced"
            ].surfaceMix,
          "--ck-closed-cell-texture-opacity":
            BOXE_CLOSED_CELL_DOMINANCE[
              titleThemeSkin.closed_cell_background_dominance ?? "balanced"
            ].textureOpacity,
          "--ck-cell-face-down-background": cellFaceDownBackgroundUrl
            ? `url("${cellFaceDownBackgroundUrl}")`
            : undefined,
        } as CSSProperties)
      : undefined;
  const boardShellClassName = [
    "board-shell",
    "mines-stage-board",
    "boxe-stage-board",
    gameAreaBackgroundUrl ? "has-skin-background" : null,
    cellFaceDownBackgroundUrl ? "has-cell-face-down-background" : null,
  ]
    .filter(Boolean)
    .join(" ");
  const stageHeader = (
    <article className="mines-stage-card boxe-stage-card">
      <div className="mines-stage-topbar boxe-stage-topbar">
        <div className="mines-stage-heading boxe-stage-heading">
          {mobileStageTools}
          <h3
            className={titleLogoUrl ? "mines-wordmark boxe-wordmark boxe-wordmark-logo" : "mines-wordmark boxe-wordmark"}
            id="boxe-gameplay-title"
          >
            {titleLogoUrl ? (
              <>
                <img className="mines-title-logo boxe-title-logo" src={titleLogoUrl} alt="" aria-hidden="true" />
                <span className="boxe-title-text">{gameTitle}</span>
              </>
            ) : (
              gameTitle
            )}
          </h3>
          <p className={celebration ? "mines-stage-subtitle boxe-stage-subtitle is-visible" : "mines-stage-subtitle boxe-stage-subtitle"}>
            {stageSubtitle}
          </p>
          <div className="mines-stage-quickbar boxe-stage-quickbar">
            <div className="mines-payout-preview boxe-payout-preview">
              {visibleMultipliers.map((multiplier, index) => (
                <span
                  className={index === 0 ? "mines-preview-chip boxe-preview-chip active" : "mines-preview-chip boxe-preview-chip"}
                  key={`${selectedRows}-${selectedDifficulty}-${visiblePayoutStart + index}`}
                >
                  {multiplier}x
                </span>
              ))}
            </div>
          </div>
        </div>
        {!isHostFullscreen && !useMobileLayout ? (
          <div className="mines-stage-actions boxe-stage-actions">
            <button
              className="button-ghost mines-icon-close boxe-icon-close"
              type="button"
              aria-label={copy("actions.back_to_site_aria")}
              onClick={onExit}
            >
              X
            </button>
          </div>
        ) : null}
      </div>
    </article>
  );
  const boardSection = (
    <article className={boardShellClassName} style={boardSkinStyle}>
      <BoxePyramidBoard
        activeRow={activeRow}
        disabled={isInteractionLocked}
        onPick={(row, position) => void executeReveal(row, position)}
        picks={picks}
        pyramidFullReveal={pyramidFullReveal}
        rows={round?.rows ?? selectedRows}
        safeIconSrc={safeIconSrc}
        mineIconSrc={mineIconSrc}
        terminalStatus={terminalStatus}
      />
    </article>
  );
  const mobileSettingsSummary = useMobileLayout ? (
    <div className="mines-mobile-settings-summary boxe-mobile-settings-summary">
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={settingsDisabled}
        onClick={() => setShowMobileSettings(true)}
      >
        {selectedRows} rows
      </button>
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={settingsDisabled}
        onClick={() => setShowMobileSettings(true)}
      >
        {selectedDifficulty.toUpperCase()}
      </button>
    </div>
  ) : null;

  return (
    <section className="boxe-gameplay" data-testid="boxe-gameplay" aria-labelledby="boxe-gameplay-title">
      {useMobileLayout ? (
        <form className="mines-mobile-layout boxe-mobile-layout" onSubmit={handleStartSubmit}>
          {stageHeader}
          {boardSection}
          <GameMobileControlStack
            className="mines-mobile-play-stack boxe-mobile-play-stack"
            balance={<article className="mines-mobile-balance boxe-mobile-balance">{boxeBalanceFooter}</article>}
            betPanel={
              <section className="session-actions mines-control-rail mines-control-rail-clean mines-mobile-bet-panel boxe-mobile-bet-panel">
                {boxeMobileBetPanel}
              </section>
            }
            actions={boxeActions}
            settingsSummary={mobileSettingsSummary}
          />
          <GameShortViewportGate />
        </form>
      ) : (
        <div className="mines-grid boxe-grid">
          <div className="stack">
            <GameControlRail
              headerTools={railHeader}
              settings={boxeSettings}
              betPanel={boxeDesktopBetPanel}
              footer={<article className="mines-rail-footer boxe-rail-footer">{boxeBalanceFooter}</article>}
              className="session-actions mines-control-rail mines-control-rail-clean boxe-control-rail"
              onSubmit={handleStartSubmit}
            />
          </div>

          <div className="stack boxe-stage-stack">
            {stageHeader}
            {boardSection}
          </div>
        </div>
      )}

      {showMobileSettings ? (
        <GameMobileSettingsSheet
          isDemoPlayer={walletSource === "demo"}
          title="Game settings"
          doneLabel="Done"
          demoBadgeLabel={modeLabel}
          onClose={() => setShowMobileSettings(false)}
          overlayClassName="mines-mobile-settings-overlay"
          sheetClassName="mines-control-rail mines-control-rail-clean mines-mobile-settings-sheet boxe-mobile-settings-sheet"
          headerClassName="mines-mobile-settings-header"
          closeButtonClassName="mines-mobile-settings-close"
          demoBadgeClassName="mines-mode-badge"
        >
          {boxeSettings}
        </GameMobileSettingsSheet>
      ) : null}

      {insufficientBalance ? (
        <p className="boxe-inline-warning">{copy("balance.insufficient")}</p>
      ) : null}

      {errorText ? (
        <GameActionError
          actionLabel={retryAction ? copy("actions.retry") : "OK"}
          actionTestId={retryAction ? "boxe-retry-action" : undefined}
          code={errorDiagnostic?.code}
          message={errorText}
          onAction={retryAction ? retryLastAction : clearActionError}
          requestId={errorDiagnostic?.requestId}
          supportId={errorDiagnostic?.supportId}
          testId="boxe-action-error-dialog"
          title="Azione richiesta"
        />
      ) : null}
      {showRules ? (
        <BoxeRulesModal
          activeTab={infoTab}
          copy={copy}
          gameTitle={gameTitle}
          locale={locale}
          onTabChange={setInfoTab}
          replayAvailable={isAuthenticated || Boolean(round?.roundId)}
          replayContent={
            isAuthenticated ? (
              latestReplaySessionsPanel
            ) : replayState.loading ? (
              <p className="empty-state">{copy("rules.replay_loading")}</p>
            ) : replayState.error ? (
              <p className="empty-state">{replayState.error}</p>
            ) : replayState.replay ? (
              <BoxeReplayViewer replay={replayState.replay} />
            ) : (
              <p className="empty-state">{copy("rules.replay_unavailable")}</p>
            )
          }
          runtimeConfig={runtimeConfig}
          onClose={() => setShowRules(false)}
        />
      ) : null}
    </section>
  );

  function clearActionError() {
    setErrorText("");
    setErrorDiagnostic(null);
  }

  function setActionGameError(error: unknown) {
    setErrorText(buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP));
    setErrorDiagnostic(buildGameErrorDiagnostic(error));
  }
}

function readTerminalStatus(status: BoxeRoundStatus | null) {
  if (!status || !TERMINAL_STATUSES.has(status)) {
    return null;
  }
  if (status === "completed_cashout" || status === "completed_top_row" || status === "failed_mine") {
    return status;
  }
  return null;
}

function createIdempotencyKey() {
  if (typeof window !== "undefined" && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `boxe-${Date.now()}-${Math.random().toString(16).slice(2)}`;
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
  return formatChipAmount(num);
}

function formatChipAmount(value: number) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  return value.toFixed(2).replace(/\.00$/, "");
}
