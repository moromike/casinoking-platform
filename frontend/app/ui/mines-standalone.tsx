"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  extractValidationMessage,
  getDefaultVisibleMineCount,
  getModeUiLabels,
  getMineOptions,
  getVisibleGridSizes,
  getVisibleMineOptions,
  getPayoutLadder,
  getRulesSections,
  shortId,
} from "./casinoking-console.helpers";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

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

type StatusKind = "success" | "error" | "info";

type StatusMessage = {
  kind: StatusKind;
  text: string;
};

type Wallet = {
  wallet_type: string;
  balance_snapshot: string;
};

type MinesRuntimeConfig = {
  game_code?: string;
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
  payout_runtime_file?: string;
  fairness_version: string;
  presentation_config?: {
    rules_sections: Record<string, string>;
    published_grid_sizes: number[];
    published_mine_counts: Record<string, number[]>;
    default_mine_counts: Record<string, number>;
    ui_labels: Record<string, Record<string, string>>;
  };
};

type FairnessCurrentConfig = {
  fairness_version: string;
  fairness_phase: string;
  active_server_seed_hash: string;
  user_verifiable: boolean;
};

type SessionSnapshot = {
  game_session_id: string;
  status: "active" | "won" | "lost";
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
  safe_reveals_count: number;
  revealed_cells: number[];
  multiplier_current: string;
  potential_payout: string;
  wallet_balance_after_start: string;
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  ledger_transaction_id: string;
  created_at: string;
  closed_at: string | null;
};

type SessionFairness = {
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  user_verifiable: boolean;
};

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

type ApiErrorShape = {
  code: string;
  message: string;
};

type ApiEnvelope<T> =
  | { success: true; data: T }
  | { success: false; error: ApiErrorShape; detail?: unknown };

class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

export function MinesStandalone() {
  const [accessToken, setAccessToken] = useState("");
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
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [roundResultNotice, setRoundResultNotice] = useState<{
    kind: "won" | "lost";
    payoutAmount: string;
  } | null>(null);
  const [revealedMinePositions, setRevealedMinePositions] = useState<number[]>([]);
  const [highlightedMineCell, setHighlightedMineCell] = useState<number | null>(null);
  const [isEmbeddedView, setIsEmbeddedView] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isHostFullscreen, setIsHostFullscreen] = useState(false);
  const selectedGridSizeRef = useRef(25);
  const selectedMineCountRef = useRef(3);
  const betAmountRef = useRef("5");

  const gridSizes = getVisibleGridSizes(runtimeConfig, selectedGridSize);
  const mineOptions = getVisibleMineOptions(
    runtimeConfig,
    selectedGridSize,
    selectedMineCount,
  );
  const payoutLadder = getPayoutLadder(runtimeConfig, selectedGridSize, selectedMineCount);
  const isAuthenticated = accessToken.length > 0;
  const visibleGridSize = currentSession ? currentSession.grid_size : selectedGridSize;
  const boardSide = Math.sqrt(visibleGridSize);
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const isDemoPlayer = currentEmail.endsWith("@casinoking.local");
  const isActiveRound = currentSession?.status === "active";
  const currentMode = isAuthenticated && !isDemoPlayer ? "real" : "demo";
  const modeUiLabels = getModeUiLabels(runtimeConfig, currentMode);
  const rulesSections = getRulesSections(runtimeConfig);
  const visiblePayoutLadder = currentSession
    ? getPayoutLadder(runtimeConfig, currentSession.grid_size, currentSession.mine_count)
    : payoutLadder;
  const visibleBalance =
    isActiveRound
      ? currentSession.wallet_balance_after_start
      : cashWallet?.balance_snapshot ?? "1000";
  const previewWindowStart = currentSession?.safe_reveals_count ?? 0;
  const previewMultipliers = visiblePayoutLadder.slice(previewWindowStart, previewWindowStart + 5);
  const stageSubtitle =
    roundResultNotice?.kind === "won"
      ? `Hai vinto. ${formatWholeChipDisplay(roundResultNotice.payoutAmount)}. Premi di nuovo Bet per la prossima mano.`
      : roundResultNotice?.kind === "lost"
        ? "Hai perso :("
        : isActiveRound
          ? `Round ${shortId(currentSession.game_session_id)} live`
          : isAuthenticated
            ? "Choose the setup and place the next bet."
            : "Open demo to enter the game instantly with 1000 CHIP.";
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
  const visibleMinePositionSet = new Set(visibleMinePositions);
  const betButtonLabel =
    busyAction === "start-session"
      ? modeUiLabels.bet_loading ?? "Betting..."
      : modeUiLabels.bet ?? "Bet";
  const collectButtonLabel =
    busyAction === "cashout"
      ? modeUiLabels.collect_loading ?? "Collecting..."
      : modeUiLabels.collect ?? "Collect";
  const visibleStatus = status?.kind === "error" ? status : null;

  useEffect(() => {
    setIsEmbeddedView(new URLSearchParams(window.location.search).get("embed") === "1");
    const storedToken = window.localStorage.getItem(STORAGE_KEYS.accessToken) ?? "";
    const storedLaunchToken =
      window.localStorage.getItem(STORAGE_KEYS.gameLaunchToken) ?? "";
    const storedLaunchTokenExpiresAt =
      window.localStorage.getItem(STORAGE_KEYS.gameLaunchTokenExpiresAt) ?? "";
    const storedEmail = window.localStorage.getItem(STORAGE_KEYS.email) ?? "";
    const storedSessionId = window.localStorage.getItem(STORAGE_KEYS.sessionId);

    setAccessToken(storedToken);
    setGameLaunchToken(storedLaunchToken);
    setGameLaunchTokenExpiresAt(storedLaunchTokenExpiresAt);
    setCurrentEmail(storedEmail);
    void loadRuntime();
    if (storedToken) {
      void refreshAuthenticatedState(storedToken, storedSessionId);
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

  async function loadRuntime() {
    try {
      const [runtimeData, fairnessData] = await Promise.all([
        apiRequest<MinesRuntimeConfig>("/games/mines/config"),
        apiRequest<FairnessCurrentConfig>("/games/mines/fairness/current"),
      ]);
      setRuntimeConfig(runtimeData);
      setCurrentFairness(fairnessData);
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Unable to load the Mines runtime."),
      });
    }
  }

  async function refreshAuthenticatedState(token: string, sessionId?: string | null) {
    try {
      await ensureGameLaunchToken(
        token,
        gameLaunchToken,
        gameLaunchTokenExpiresAt,
        setGameLaunchToken,
        setGameLaunchTokenExpiresAt,
      );
      const walletData = await apiRequest<Wallet[]>("/wallets", {}, token);
      setWallets(walletData);
      if (sessionId) {
        await loadSession(token, sessionId);
      }
    } catch (error) {
      clearAuthState(false);
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "The player session is no longer valid."),
      });
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
    await refreshAuthenticatedState(demoData.access_token, null);
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
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Demo mode could not start."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleStartSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("start-session");
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    try {
      const token = accessToken || (await prepareDemoAccessToken());
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
            wallet_type: "cash",
          }),
        },
        token,
      );
      setHighlightedMineCell(null);
      await refreshAuthenticatedState(token, startData.game_session_id);
      setStatus(null);
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Round launch failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRevealCell(cellIndex: number) {
    if (!accessToken || !currentSession || currentSession.status !== "active") {
      return;
    }
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
      await refreshAuthenticatedState(accessToken, currentSession.game_session_id);
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
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Reveal failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCashout() {
    if (!accessToken || !currentSession || currentSession.status !== "active") {
      return;
    }
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
      await refreshAuthenticatedState(accessToken, currentSession.game_session_id);
      setHighlightedMineCell(null);
      setRevealedMinePositions([]);
      setRoundResultNotice({
        kind: "won",
        payoutAmount: cashoutData.payout_amount,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Cash out failed."),
      });
    } finally {
      setBusyAction(null);
    }
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
    if (isActiveRound || gridSize === selectedGridSize) {
      return;
    }

    updateSelectedGridSize(gridSize);
    updateSelectedMineCount(getDefaultVisibleMineCount(runtimeConfig, gridSize));
    clearCurrentSessionSnapshot();
  }

  function handleExit() {
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
    setAccessToken("");
    setGameLaunchToken("");
    setCurrentEmail("");
    setWallets([]);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
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

  const boardCells = Array.from({ length: visibleGridSize }, (_, cellIndex) => {
    const isSessionBoard = Boolean(currentSession && currentSession.status === "active");
    const isRevealed = currentSession?.revealed_cells.includes(cellIndex) ?? false;
    const isMine = visibleMinePositionSet.has(cellIndex);
    let className = "board-cell";
    if (isMine) {
      className += " revealed-mine";
    } else if (isRevealed) {
      className += " revealed-safe";
    }

    return (
      <button
        key={`${visibleGridSize}-${cellIndex}`}
        className={className}
        type="button"
        disabled={!isSessionBoard || isRevealed || busyAction !== null}
        onClick={() => void handleRevealCell(cellIndex)}
      >
        <span className="board-cell-index">{String(cellIndex + 1).padStart(2, "0")}</span>
        <span className="board-cell-face">
          {isMine ? "MINE" : isRevealed ? "SAFE" : "PICK"}
        </span>
      </button>
    );
  });

  const railHeader = (
    <div className="list-row mines-rail-header">
      <button
        className="button-ghost mines-rules-trigger"
        type="button"
        onClick={() => setShowRules(true)}
        aria-label="Game info"
      >
        i
      </button>
      {isDemoPlayer ? <span className="status-badge info mines-mode-badge">DEMO MODE</span> : null}
    </div>
  );

  const configFields = (
    <div className="stack mines-control-stack">
      <div className="field">
        <label>Grid size</label>
        <div className="choice-chip-row">
          {gridSizes.map((gridSize) => (
            <button
              key={gridSize}
              className={selectedGridSize === gridSize ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound}
              onClick={() => handleGridSizeChange(gridSize)}
            >
              {formatGridChoiceLabel(gridSize)}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Mines</label>
        <div className="choice-chip-row">
          {mineOptions.map((mineCount) => (
            <button
              key={mineCount}
              className={selectedMineCount === mineCount ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound}
              onClick={() => updateSelectedMineCount(mineCount)}
            >
              {mineCount}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="bet-amount-standalone">Bet amount</label>
        <input
          id="bet-amount-standalone"
          value={betAmount}
          onChange={(event) => updateBetAmount(normalizeWholeChipInput(event.target.value))}
          inputMode="numeric"
          placeholder="5"
        />
        <div className="quick-chip-row">
          {["1", "2", "5", "10", "25"].map((amount) => (
            <button
              key={amount}
              className={betAmount === amount ? "quick-chip active" : "quick-chip"}
              type="button"
              onClick={() => updateBetAmount(amount)}
            >
              {amount}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const actionButtons = (
    <div className="actions mines-mobile-actions">
      <button
        className="button"
        type="submit"
        disabled={busyAction !== null || currentSession?.status === "active"}
      >
        {betButtonLabel}
      </button>
      <button
        className="button-secondary"
        type="button"
        disabled={
          !currentSession ||
          currentSession.status !== "active" ||
          currentSession.safe_reveals_count <= 0 ||
          busyAction !== null
        }
        onClick={() => void handleCashout()}
      >
        {collectButtonLabel}
      </button>
    </div>
  );

  const balanceFooter = (
    <div className="mines-balance-footer">
      <div>
        <span className="list-muted">{isDemoPlayer ? "Demo balance" : "Balance"}</span>
        <strong>{formatWholeChipDisplay(visibleBalance)}</strong>
      </div>
      <div>
        <span className="list-muted">Win</span>
        <strong>
          {currentSession
            ? formatWholeChipDisplay(currentSession.potential_payout)
            : "0 CHIP"}
        </strong>
      </div>
    </div>
  );

  const stageHeader = (
    <article className="mines-stage-card">
      <div className="mines-stage-topbar">
        <div className="mines-stage-heading">
          <h3 className="mines-wordmark">MINES</h3>
          <p className={stageSubtitleTone ? `mines-stage-subtitle mines-stage-subtitle-${stageSubtitleTone}` : "mines-stage-subtitle"}>
            {stageSubtitle}
          </p>
          <div className="mines-stage-quickbar">
            <div className="mines-payout-preview">
              {previewMultipliers.map((multiplier, index) => (
                <span
                  className={
                    index === 0
                      ? "mines-preview-chip active"
                      : "mines-preview-chip"
                  }
                  key={`${visibleGridSize}-${currentSession?.mine_count ?? selectedMineCount}-${previewWindowStart + index}`}
                >
                  {multiplier}x
                </span>
              ))}
            </div>
          </div>
        </div>
        {!isEmbeddedView && !isHostFullscreen ? (
          <div className="mines-stage-actions">
            <button
              className="button-ghost mines-icon-close"
              type="button"
              onClick={handleExit}
              aria-label="Exit Mines"
            >
              x
            </button>
          </div>
        ) : null}
      </div>
    </article>
  );

  const boardSection = (
    <article className="board-shell mines-stage-board">
      <div
        className="mines-board"
        style={{ gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))` }}
      >
        {boardCells}
      </div>
    </article>
  );

  return (
    <main
      className={
        isEmbeddedView
          ? "page-shell mines-page-shell mines-page-shell-embedded"
          : isMobileViewport
            ? "page-shell mines-page-shell mines-page-shell-mobile"
            : "page-shell mines-page-shell"
      }
    >
      <section
        className={
          isEmbeddedView
            ? "panel mines-product-shell mines-product-shell-clean mines-product-shell-embedded"
            : isMobileViewport
              ? "panel mines-product-shell mines-product-shell-clean mines-product-shell-mobile"
              : "panel mines-product-shell mines-product-shell-clean"
        }
      >
        {visibleStatus ? <div className={`status-banner ${visibleStatus.kind}`}>{visibleStatus.text}</div> : null}
        {isMobileViewport && !isEmbeddedView ? (
          <form className="mines-mobile-layout" onSubmit={handleStartSession}>
            {stageHeader}
            {boardSection}
            <article className="mines-mobile-balance">
              {balanceFooter}
            </article>
            {actionButtons}
            <section className="session-actions mines-control-rail mines-control-rail-clean mines-mobile-config">
              {railHeader}
              {configFields}
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
                {actionButtons}

                <article className="mines-rail-footer">
                  <p className="helper">
                    {!accessToken
                      ? "Guest entry opens a fresh demo player with 1000 CHIP and immediately places the selected bet."
                      : isDemoPlayer
                        ? "Demo player active. Closing the game resets the demo bankroll to 1000 CHIP on the next entry."
                        : "Authenticated player active. History and fairness stay linked to your account."}
                  </p>
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
          <div className="mines-rules-overlay" role="presentation" onClick={() => setShowRules(false)}>
            <article
              className="mines-rules-modal"
              role="dialog"
              aria-modal="true"
              aria-label="Game info Mines"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mines-rules-header">
                <div>
                  <h3>GAME INFO - MINES</h3>
                  <p>Rules readable from the table, focused on actual gameplay.</p>
                </div>
                <button className="button-ghost mines-rules-close" type="button" onClick={() => setShowRules(false)}>
                  x
                </button>
              </div>
              <div className="mines-rules-body">
                <section>
                  <h4>Ways to win</h4>
                  <div dangerouslySetInnerHTML={{ __html: rulesSections.ways_to_win ?? "" }} />
                </section>
                <section>
                  <h4>Payout display</h4>
                  <div dangerouslySetInnerHTML={{ __html: rulesSections.payout_display ?? "" }} />
                  <div className="payout-ladder-list">
                    {payoutLadder.slice(0, 8).map((multiplier, index) => (
                      <article className="payout-ladder-row" key={`${selectedGridSize}-${selectedMineCount}-${index}`}>
                        <span className="list-muted">Safe reveal {String(index + 1).padStart(2, "0")}</span>
                        <strong>{multiplier}x</strong>
                      </article>
                    ))}
                  </div>
                </section>
                <section>
                  <h4>Settings menu</h4>
                  <div dangerouslySetInnerHTML={{ __html: rulesSections.settings_menu ?? "" }} />
                </section>
                <section>
                  <h4>Bet & collect</h4>
                  <div dangerouslySetInnerHTML={{ __html: rulesSections.bet_collect ?? "" }} />
                </section>
              </div>
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

async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    payload = null;
  }

  if (!response.ok || !payload || payload.success === false) {
    if (!response.ok && payload && typeof payload === "object" && "detail" in payload) {
      throw new ApiRequestError(
        extractValidationMessage(payload.detail),
        "VALIDATION_ERROR",
        response.status,
      );
    }
    throw new ApiRequestError(
      payload && payload.success === false ? payload.error.message : "Unexpected API response",
      payload && payload.success === false ? payload.error.code : "API_ERROR",
      response.status,
    );
  }

  return payload.data;
}

function readErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    return `${fallback} ${error.message}`;
  }
  if (error instanceof Error) {
    return `${fallback} ${error.message}`;
  }
  return fallback;
}

function sessionStatusKind(status: SessionSnapshot["status"]): StatusKind {
  if (status === "won") {
    return "success";
  }
  if (status === "lost") {
    return "error";
  }
  return "info";
}

function normalizeWholeChipInput(value: string): string {
  const digitsOnly = value.replace(/[^\d]/g, "");
  return digitsOnly.replace(/^0+(?=\d)/, "").slice(0, 6);
}

function formatWholeChipDisplay(value: string | number | null | undefined): string {
  const numericValue =
    typeof value === "number" ? value : value ? Number.parseFloat(value) : 0;
  const safeValue = Number.isFinite(numericValue) ? numericValue : 0;
  return `${Math.max(0, safeValue).toFixed(2)} CHIP`;
}

function formatGridChoiceLabel(gridSize: number): string {
  const side = Math.sqrt(gridSize);
  return Number.isInteger(side) ? `${side}x${side}` : `${gridSize} cells`;
}

function isExpiredIsoDate(value: string): boolean {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return true;
  }
  return parsed <= Date.now();
}
