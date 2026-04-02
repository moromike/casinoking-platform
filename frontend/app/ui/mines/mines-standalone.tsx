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
  const [showMobileSettings, setShowMobileSettings] = useState(false);
  const selectedGridSizeRef = useRef(25);
  const selectedMineCountRef = useRef(3);
  const betAmountRef = useRef("5");
  const statusTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  const betButtonLabel =
    busyAction === "start-session"
      ? modeUiLabels.bet_loading ?? "Betting..."
      : modeUiLabels.bet ?? "Bet";
  const collectButtonLabel =
    busyAction === "cashout"
      ? modeUiLabels.collect_loading ?? "Collecting..."
      : modeUiLabels.collect ?? "Collect";
  const visibleStatus = status?.kind === "error" ? status : null;
  const useMobileLayout = isMobileViewport;
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
        text: readMinesNetworkAwareErrorMessage(error, "Round launch failed."),
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

  const mobileStageTools = useMobileLayout ? (
    <div className="mines-mobile-stage-tools">
      <button
        className="button-ghost mines-rules-trigger"
        type="button"
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
        onClick={() => setShowMobileSettings(true)}
      >
        {formatGridChoiceLabel(controlGridSize)}
      </button>
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        onClick={() => setShowMobileSettings(true)}
      >
        {controlMineCount} mines
      </button>
    </div>
  ) : null;

  const configFields = (
    <div className="stack mines-control-stack mines-config-sections">
      <div className="field mines-config-section">
        <label>Grid size</label>
        <div className="mines-config-options-grid">
          {gridSizes.map((gridSize) => (
            <button
              key={gridSize}
              className={controlGridSize === gridSize ? "choice-chip active" : "choice-chip"}
              type="button"
              disabled={busyAction !== null || isActiveRound}
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
              disabled={busyAction !== null || isActiveRound}
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
  );

  const actionButtons = (
    <MinesActionButtons
      useMobileLayout={useMobileLayout}
      betButtonLabel={betButtonLabel}
      collectButtonLabel={collectButtonLabel}
      isBetDisabled={busyAction !== null || currentSession?.status === "active"}
      isCollectDisabled={
        !currentSession ||
        currentSession.status !== "active" ||
        currentSession.safe_reveals_count <= 0 ||
        busyAction !== null
      }
      onCashout={() => void handleCashout()}
    />
  );

  const balanceFooter = (
    <MinesBalanceFooter
      isDemoPlayer={isDemoPlayer}
      visibleBalance={visibleBalance}
      potentialPayout={currentSession ? currentSession.potential_payout : null}
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
        busy={busyAction !== null}
        isInteractiveRound={Boolean(currentSession && currentSession.status === "active")}
        onRevealCell={(cellIndex) => void handleRevealCell(cellIndex)}
        assets={runtimeConfig?.presentation_config?.board_assets}
        closed={currentSession?.status !== "active" && currentSession !== null}
      />
    </article>
  );

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
