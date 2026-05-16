"use client";

import { FormEvent, useEffect, useState, type CSSProperties } from "react";
import {
  formatWholeChipDisplay,
  getPayoutLadder,
  getRulesSections,
} from "@/app/lib/helpers";
import type {
  MinesRuntimeConfig,
  SessionSnapshot,
  TitleThemeSkin,
} from "@/app/lib/types";
import { resolveBackendAssetUrl } from "@/app/lib/api";
import { MinesActionButtons } from "./mines-action-buttons";
import { MinesBalanceFooter } from "./mines-balance-footer";
import { MinesBoard } from "./mines-board";
import { MinesMobileSettingsSheet } from "./mines-mobile-settings-sheet";
import { DEFAULT_MINES_REPLAY_COPY } from "./mines-replay-copy";
import { MinesReplayViewer, type MinesRoundReplay } from "./mines-replay-viewer";
import { MinesRulesModal, type MinesRulesModalTab } from "./mines-rules-modal";
import { MinesRuntimeTools } from "./mines-runtime-tools";
import { MinesStageHeader } from "./mines-stage-header";
import { useMinesSounds } from "./use-mines-sounds";
import { MinesWinCelebration } from "./mines-win-celebration";
import type { MinesCopyResolver } from "./i18n/mines-copy-resolver";
import type {
  LatestAccessSessionHistory,
  MinesCashoutResult,
  MinesRevealResult,
} from "./types";

const MINES_SKIN_OVERLAY: Record<TitleThemeSkin["game_area_overlay"], string> = {
  none: "rgba(0, 0, 0, 0)",
  light: "rgba(0, 0, 0, 0.18)",
  medium: "rgba(0, 0, 0, 0.42)",
  strong: "rgba(0, 0, 0, 0.62)",
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

type MinesGameplayProps = {
  useMobileLayout: boolean;
  gameTitle: string;
  copy: MinesCopyResolver["t"];
  locale: MinesCopyResolver["locale"];
  runtimeConfig: MinesRuntimeConfig | null;
  currentSession: SessionSnapshot | null;
  titleThemeAssets: Record<string, string>;
  titleThemeSkin: TitleThemeSkin | null;
  audioPreferences: {
    muted: boolean;
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
    volume: number;
  };
  isDemoMode: boolean;
  isAuthenticated: boolean;
  isEmbeddedView: boolean;
  isHostFullscreen: boolean;
  isInteractionLocked: boolean;
  isSessionResumeLoading: boolean;
  isAccessSessionExpired: boolean;
  isFatalRuntimeBlocked: boolean;
  isActiveRound: boolean;
  isBetHintActive: boolean;
  hasTableBudget: boolean;
  busyAction: string | null;
  gridSizes: number[];
  mineOptions: number[];
  controlGridSize: number;
  controlMineCount: number;
  selectedGridSize: number;
  selectedMineCount: number;
  betAmount: string;
  visibleBalance: string;
  effectiveWalletType: "cash" | "bonus";
  onStartSession: (event: FormEvent<HTMLFormElement>) => void;
  onRevealCell: (cellIndex: number) => Promise<MinesRevealResult | null>;
  onCashout: () => Promise<MinesCashoutResult | null>;
  onGridSizeChange: (gridSize: number) => void;
  onMineCountChange: (mineCount: number) => void;
  onBetAmountChange: (amount: string) => void;
  onExit: () => void;
  loadReplay: (sessionId: string) => Promise<MinesRoundReplay>;
  loadLatestReplaySessions: () => Promise<LatestAccessSessionHistory[]>;
  formatGridLabel: (gridSize: number) => string;
};

export function MinesGameplay({
  useMobileLayout,
  gameTitle,
  copy,
  locale,
  runtimeConfig,
  currentSession,
  titleThemeAssets,
  titleThemeSkin,
  audioPreferences,
  isDemoMode,
  isAuthenticated,
  isEmbeddedView,
  isHostFullscreen,
  isInteractionLocked,
  isSessionResumeLoading,
  isAccessSessionExpired,
  isFatalRuntimeBlocked,
  isActiveRound,
  isBetHintActive,
  hasTableBudget,
  busyAction,
  gridSizes,
  mineOptions,
  controlGridSize,
  controlMineCount,
  selectedGridSize,
  selectedMineCount,
  betAmount,
  visibleBalance,
  effectiveWalletType,
  onStartSession,
  onRevealCell,
  onCashout,
  onGridSizeChange,
  onMineCountChange,
  onBetAmountChange,
  onExit,
  loadReplay,
  loadLatestReplaySessions,
  formatGridLabel,
}: MinesGameplayProps) {
  const [showRules, setShowRules] = useState(false);
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
  const [showMobileSettings, setShowMobileSettings] = useState(false);
  const [pendingWonRevealResult, setPendingWonRevealResult] =
    useState<MinesRevealResult | null>(null);
  const [pendingCashoutResult, setPendingCashoutResult] =
    useState<MinesCashoutResult | null>(null);

  const minesSounds = useMinesSounds(titleThemeAssets, audioPreferences);
  const playSound = minesSounds.play;
  const payoutLadder = getPayoutLadder(runtimeConfig, selectedGridSize, selectedMineCount);
  const rulesSections = getRulesSections(runtimeConfig);
  const visibleGridSize = currentSession ? currentSession.grid_size : selectedGridSize;
  const boardSide = Math.sqrt(visibleGridSize);
  const replayCandidateSessionId =
    currentSession && currentSession.status !== "active"
      ? currentSession.game_session_id
      : lastReplaySessionId;
  const visiblePayoutLadder = currentSession
    ? getPayoutLadder(runtimeConfig, currentSession.grid_size, currentSession.mine_count)
    : payoutLadder;
  const previewWindowStart = currentSession?.safe_reveals_count ?? 0;
  const previewMultipliers = visiblePayoutLadder.slice(previewWindowStart, previewWindowStart + 5);
  const visibleMinePositions =
    revealedMinePositions.length > 0
      ? revealedMinePositions
      : highlightedMineCell !== null
        ? [highlightedMineCell]
        : [];
  const potentialPayout =
    currentSession?.status === "active" && currentSession.safe_reveals_count > 0
      ? currentSession.potential_payout
      : null;
  const betButtonLabel =
    busyAction === "start-session" ? copy("actions.bet_loading") : copy("actions.bet");
  const collectButtonLabel =
    busyAction === "cashout" ? copy("actions.collect_loading") : copy("actions.collect");
  const isBetDisabled =
    busyAction !== null ||
    currentSession?.status === "active" ||
    isInteractionLocked ||
    !hasTableBudget;
  const isCollectDisabled =
    !currentSession ||
    currentSession.status !== "active" ||
    currentSession.safe_reveals_count <= 0 ||
    busyAction !== null ||
    isInteractionLocked;
  const formatChipValue = (value: string | number | null | undefined) =>
    formatWholeChipDisplay(value, copy("format.chip_suffix"));
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

  useEffect(() => {
    if (!useMobileLayout || isInteractionLocked) {
      setShowMobileSettings(false);
    }
  }, [isInteractionLocked, useMobileLayout]);

  useEffect(() => {
    if (currentSession !== null) {
      return;
    }
    clearRoundPresentation();
    resetGameReplayState({ clearLast: true });
  }, [currentSession]);

  useEffect(() => {
    if (currentSession?.status !== "won" || !pendingWonRevealResult) {
      return;
    }

    playSound("audio_win");
    setLastReplaySessionId(currentSession.game_session_id);
    setRevealedMinePositions(pendingWonRevealResult.minePositions ?? []);
    setWinCelebrationKey((currentKey) => currentKey + 1);
    setRoundResultNotice({
      kind: "won",
      payoutAmount: pendingWonRevealResult.payout ?? currentSession.potential_payout,
    });
    setPendingWonRevealResult(null);
  }, [
    currentSession?.game_session_id,
    currentSession?.potential_payout,
    currentSession?.status,
    pendingWonRevealResult,
    playSound,
  ]);

  useEffect(() => {
    if (currentSession?.status !== "won" || !pendingCashoutResult) {
      return;
    }

    setHighlightedMineCell(null);
    setRevealedMinePositions(pendingCashoutResult.minePositions);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    setWinCelebrationKey((currentKey) => currentKey + 1);
    setRoundResultNotice({
      kind: "won",
      payoutAmount: pendingCashoutResult.payout,
    });
    setPendingCashoutResult(null);
  }, [currentSession?.status, pendingCashoutResult]);

  function clearRoundPresentation() {
    setRoundResultNotice(null);
    setRevealedMinePositions([]);
    setHighlightedMineCell(null);
    setSafeEffectCell(null);
    setMineHitEffectCell(null);
    setPendingWonRevealResult(null);
    setPendingCashoutResult(null);
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

  function readReplayErrorMessage(error: unknown, fallback: string): string {
    return error instanceof Error && error.message ? error.message : fallback;
  }

  async function loadGameReplay(sessionId: string) {
    setGameReplayState((current) => ({
      sessionId,
      replay: current.sessionId === sessionId ? current.replay : null,
      loading: true,
      error: null,
    }));
    try {
      const replay = await loadReplay(sessionId);
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
        error: readReplayErrorMessage(error, "Replay mano non disponibile."),
      });
    }
  }

  async function loadLatestSessionsForReplay() {
    if (!isAuthenticated) {
      return;
    }

    setLatestReplaySessionsState((current) => ({
      ...current,
      loading: true,
      error: null,
    }));
    try {
      const sessions = await loadLatestReplaySessions();
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
        error: readReplayErrorMessage(error, "Storico sessioni non disponibile."),
      }));
    }
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
      void loadLatestSessionsForReplay();
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

  function handleStartSession(event: FormEvent<HTMLFormElement>) {
    clearRoundPresentation();
    resetGameReplayState({ clearLast: true });
    onStartSession(event);
  }

  async function handleRevealCell(cellIndex: number) {
    const result = await onRevealCell(cellIndex);
    if (!result) {
      return;
    }

    if (result.outcome === "mine") {
      playSound("audio_mine_hit");
      setLastReplaySessionId(currentSession?.game_session_id ?? null);
      setHighlightedMineCell(null);
      setRevealedMinePositions(result.minePositions ?? [cellIndex]);
      setSafeEffectCell(null);
      setMineHitEffectCell(cellIndex);
      setRoundResultNotice({
        kind: "lost",
        payoutAmount: "0",
      });
      return;
    }

    playSound("audio_safe_reveal");
    setHighlightedMineCell(null);
    setRevealedMinePositions([]);
    setSafeEffectCell(cellIndex);
    setMineHitEffectCell(null);
    if (result.outcome === "won") {
      setPendingWonRevealResult(result);
    }
  }

  async function handleCashout() {
    const result = await onCashout();
    if (!result) {
      return;
    }

    playSound("audio_collect");
    setLastReplaySessionId(currentSession?.game_session_id ?? null);
    setPendingCashoutResult(result);
  }

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

  const runtimeTools = (
    <MinesRuntimeTools
      locale={locale}
      audio={{
        hasAnySound: minesSounds.hasAnySound,
        muted: audioPreferences.muted,
        setMuted: audioPreferences.setMuted,
        setVolume: audioPreferences.setVolume,
        volume: audioPreferences.volume,
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

  const openRulesButton = (
    <button
      className="button-ghost mines-rules-trigger"
      type="button"
      disabled={isInteractionLocked}
      onClick={openRulesModal}
      aria-label={copy("actions.game_info")}
    >
      i
    </button>
  );
  const runtimeToolsNode = (
    <div className="mines-rail-tools">
      {openRulesButton}
      {runtimeTools}
    </div>
  );
  const railHeader = (
    <div className="list-row mines-rail-header">
      {runtimeToolsNode}
      {isDemoMode ? (
        <span className="status-badge info mines-mode-badge">{copy("mode.demo_badge")}</span>
      ) : null}
    </div>
  );
  const mobileStageTools = useMobileLayout ? (
    <div className="mines-mobile-stage-tools">
      {openRulesButton}
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
              onClick={() => onGridSizeChange(gridSize)}
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
              onClick={() => onMineCountChange(mineCount)}
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
        onChange={(event) => onBetAmountChange(event.target.value)}
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
            onClick={() => onBetAmountChange(amount)}
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
      isBetDisabled={isBetDisabled}
      isBetLoading={busyAction === "start-session"}
      isCollectDisabled={isCollectDisabled}
      isCollectLoading={busyAction === "cashout"}
      shouldPulseBetButton={isBetHintActive}
      onCashout={() => void handleCashout()}
    />
  );
  const balanceFooter = (
    <MinesBalanceFooter
      isDemoPlayer={isDemoMode}
      visibleBalance={visibleBalance}
      potentialPayout={potentialPayout}
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
  const boardSkinStyle =
    titleThemeSkin && (gameAreaBackgroundUrl || cellFaceDownBackgroundUrl)
      ? ({
          "--ck-game-area-background": gameAreaBackgroundUrl
            ? `url("${gameAreaBackgroundUrl}")`
            : undefined,
          "--ck-game-area-background-size": titleThemeSkin.game_area_background_fit,
          "--ck-game-area-background-position": titleThemeSkin.game_area_background_position,
          "--ck-game-area-overlay": MINES_SKIN_OVERLAY[titleThemeSkin.game_area_overlay],
          "--ck-cell-face-down-background": cellFaceDownBackgroundUrl
            ? `url("${cellFaceDownBackgroundUrl}")`
            : undefined,
        } as CSSProperties)
      : undefined;
  const boardShellClassName = [
    "board-shell",
    "mines-stage-board",
    gameAreaBackgroundUrl ? "has-skin-background" : null,
    cellFaceDownBackgroundUrl ? "has-cell-face-down-background" : null,
  ]
    .filter(Boolean)
    .join(" ");
  const stageHeader = (
    <MinesStageHeader
      gameTitle={gameTitle}
      titleLogoUrl={titleLogoUrl}
      titleRenderMode={titleThemeSkin?.title_render_mode ?? "text"}
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
      onExit={onExit}
    />
  );
  const boardSection = (
    <article className={boardShellClassName} style={boardSkinStyle}>
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

  return (
    <>
      {useMobileLayout ? (
        <form className="mines-mobile-layout" onSubmit={handleStartSession}>
          {stageHeader}
          {boardSection}
          <section className="mines-mobile-play-stack">
            <article className="mines-mobile-balance">{balanceFooter}</article>
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

              <article className="mines-rail-footer">{balanceFooter}</article>
            </form>
          </div>

          <div className="stack">
            {stageHeader}
            {boardSection}
          </div>
        </div>
      )}

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
    </>
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
