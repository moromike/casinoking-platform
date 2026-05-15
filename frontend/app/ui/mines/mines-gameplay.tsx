import type { FormEvent, ReactNode } from "react";
import type { MinesRuntimeConfig, SessionSnapshot } from "@/app/lib/types";
import { MinesActionButtons } from "./mines-action-buttons";
import { MinesBalanceFooter } from "./mines-balance-footer";
import { MinesBoard } from "./mines-board";
import { MinesMobileSettingsSheet } from "./mines-mobile-settings-sheet";
import { MinesStageHeader } from "./mines-stage-header";
import type { MinesCopyResolver } from "./i18n/mines-copy-resolver";

type MinesGameplayProps = {
  useMobileLayout: boolean;
  runtimeTools: ReactNode;
  gameTitle: string;
  copy: MinesCopyResolver["t"];
  runtimeConfig: MinesRuntimeConfig | null;
  currentSession: SessionSnapshot | null;
  visibleGridSize: number;
  boardSide: number;
  visibleMinePositions: number[];
  safeEffectCell: number | null;
  mineHitEffectCell: number | null;
  winCelebration: ReactNode;
  isDemoMode: boolean;
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
  selectedMineCount: number;
  betAmount: string;
  visibleBalance: string;
  effectiveWalletType: "cash" | "bonus";
  stageSubtitle: string | null;
  stageSubtitleTone: "won" | "lost" | null;
  previewMultipliers: string[];
  previewWindowStart: number;
  showMobileSettings: boolean;
  onStartSession: (event: FormEvent<HTMLFormElement>) => void;
  onRevealCell: (cellIndex: number) => void;
  onCashout: () => void;
  onGridSizeChange: (gridSize: number) => void;
  onMineCountChange: (mineCount: number) => void;
  onBetAmountChange: (amount: string) => void;
  onOpenRulesModal: () => void;
  onOpenMobileSettings: () => void;
  onCloseMobileSettings: () => void;
  onExit: () => void;
  formatGridLabel: (gridSize: number) => string;
};

export function MinesGameplay({
  useMobileLayout,
  runtimeTools,
  gameTitle,
  copy,
  runtimeConfig,
  currentSession,
  visibleGridSize,
  boardSide,
  visibleMinePositions,
  safeEffectCell,
  mineHitEffectCell,
  winCelebration,
  isDemoMode,
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
  selectedMineCount,
  betAmount,
  visibleBalance,
  effectiveWalletType,
  stageSubtitle,
  stageSubtitleTone,
  previewMultipliers,
  previewWindowStart,
  showMobileSettings,
  onStartSession,
  onRevealCell,
  onCashout,
  onGridSizeChange,
  onMineCountChange,
  onBetAmountChange,
  onOpenRulesModal,
  onOpenMobileSettings,
  onCloseMobileSettings,
  onExit,
  formatGridLabel,
}: MinesGameplayProps) {
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

  const openRulesButton = (
    <button
      className="button-ghost mines-rules-trigger"
      type="button"
      disabled={isInteractionLocked}
      onClick={onOpenRulesModal}
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
        onClick={onOpenMobileSettings}
      >
        {formatGridLabel(controlGridSize)}
      </button>
      <button
        className="choice-chip active mines-mobile-settings-chip"
        type="button"
        disabled={isInteractionLocked}
        onClick={onOpenMobileSettings}
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
      onCashout={onCashout}
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
      onExit={onExit}
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
        onRevealCell={onRevealCell}
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
      {winCelebration}
    </article>
  );

  return (
    <>
      {useMobileLayout ? (
        <form className="mines-mobile-layout" onSubmit={onStartSession}>
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
              onSubmit={onStartSession}
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
          onClose={onCloseMobileSettings}
        >
          {configFields}
        </MinesMobileSettingsSheet>
      ) : null}
    </>
  );
}
