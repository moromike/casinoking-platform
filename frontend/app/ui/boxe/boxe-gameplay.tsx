"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ApiRequestError, readErrorMessage } from "@/app/lib/api";
import { GameActionButtons } from "@/app/ui/game-runtime/game-action-buttons";
import { GameBalanceFooter } from "@/app/ui/game-runtime/game-balance-footer";
import { GameBetPanel } from "@/app/ui/game-runtime/game-bet-panel";
import type { GameBootRequest } from "@/app/ui/game-runtime/game-boot-request";
import { GameControlRail } from "@/app/ui/game-runtime/game-control-rail";
import { GameShortViewportGate } from "@/app/ui/game-runtime/game-short-viewport-gate";
import { GameRuntimeTools, GameTopBar } from "@/app/ui/game-runtime/game-top-bar";
import { useBoxeAudio, type BoxeAudioPreferences } from "./use-boxe-audio";
import { BoxeWinCelebration } from "./boxe-win-celebration";
import {
  createBoxeCopyResolver,
  resolveBoxeLocale,
  type BoxeLocale,
} from "./boxe-i18n/boxe-copy-defaults";
import { BoxePayoutDisplay } from "./boxe-payout-display";
import { BoxePyramidBoard, type BoxeBoardPick } from "./boxe-pyramid-board";
import { BoxeSettingsPanel } from "./boxe-settings-panel";
import {
  cashoutBoxeRound,
  loadBoxeWallets,
  provisionBoxeDemoPlayer,
  revealBoxePick,
  startBoxeRound,
  type BoxeCashoutResponse,
  type BoxeRevealResponse,
  type BoxeRoundStatus,
  type BoxeRuntimeConfig,
  type BoxeStartRoundResponse,
  type BoxeTableSession,
  type BoxeWalletSource,
} from "./use-boxe-runtime";

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

type WalletSummary = {
  wallet_type: string;
  balance_snapshot: string;
};

const TERMINAL_STATUSES = new Set<BoxeRoundStatus>([
  "completed_cashout",
  "completed_top_row",
  "failed_mine",
  "expired",
  "quarantined",
]);

export function BoxeGameplay({
  runtimeConfig,
  bootRequest,
  initialAccessToken,
  audioPreferences,
  accessSessionId,
  tableSession,
  onExit,
  onOpenGameInfo,
  onTableSessionChange,
}: {
  runtimeConfig: BoxeRuntimeConfig;
  bootRequest: GameBootRequest;
  initialAccessToken: string;
  audioPreferences: BoxeAudioPreferences & {
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
  };
  accessSessionId: string | null;
  tableSession: BoxeTableSession | null;
  onExit: () => void;
  onOpenGameInfo: () => void;
  onTableSessionChange: (tableSession: BoxeTableSession) => void;
}) {
  const [locale, setLocale] = useState<BoxeLocale>("it");
  const copy = useMemo(() => createBoxeCopyResolver(locale), [locale]);
  const [selectedRows, setSelectedRows] = useState(runtimeConfig.default_rows);
  const [selectedDifficulty, setSelectedDifficulty] = useState(
    runtimeConfig.default_difficulty,
  );
  const [betAmount, setBetAmount] = useState("5");
  const [authToken, setAuthToken] = useState(initialAccessToken);
  const [wallets, setWallets] = useState<WalletSummary[]>([]);
  const [walletError, setWalletError] = useState("");
  const [round, setRound] = useState<BoxeRound | null>(null);
  const [picks, setPicks] = useState<BoxeBoardPick[]>([]);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorText, setErrorText] = useState("");
  const [retryAction, setRetryAction] = useState<RetryAction | null>(null);
  const [celebration, setCelebration] = useState<{
    amount: string;
    kind: "cashout" | "top_row";
    id: number;
  } | null>(null);
  const boxeAudio = useBoxeAudio(audioPreferences);

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
  const balanceAmount = readBalanceAmount({
    walletSource,
    wallets,
  });
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

  useEffect(() => {
    setLocale(resolveBoxeLocale(window.navigator.language));
  }, []);

  useEffect(() => {
    if (walletSource === "demo" || !authToken) {
      setWallets([]);
      return;
    }
    let isMounted = true;
    loadBoxeWallets(authToken)
      .then((loadedWallets) => {
        if (isMounted) {
          setWallets(loadedWallets);
          setWalletError("");
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setWalletError(readErrorMessage(error, "Saldo non disponibile."));
        }
      });
    return () => {
      isMounted = false;
    };
  }, [authToken, walletSource]);

  useEffect(() => {
    if (runtimeConfig.rows_enabled.includes(selectedRows)) {
      return;
    }
    setSelectedRows(runtimeConfig.default_rows);
  }, [runtimeConfig.default_rows, runtimeConfig.rows_enabled, selectedRows]);

  useEffect(() => {
    if (runtimeConfig.difficulty_enabled.includes(selectedDifficulty)) {
      return;
    }
    setSelectedDifficulty(runtimeConfig.default_difficulty);
  }, [
    runtimeConfig.default_difficulty,
    runtimeConfig.difficulty_enabled,
    selectedDifficulty,
  ]);

  async function ensureActionToken(): Promise<string> {
    if (authToken) {
      return authToken;
    }
    if (!bootRequest.forceDemoMode) {
      throw new Error("Accedi per giocare con saldo reale.");
    }
    const demoAuth = await provisionBoxeDemoPlayer();
    setAuthToken(demoAuth.access_token);
    window.localStorage.setItem("casinoking.access_token", demoAuth.access_token);
    window.localStorage.setItem("casinoking.email", demoAuth.email);
    return demoAuth.access_token;
  }

  async function executeStart(action?: Extract<RetryAction, { type: "start" }>) {
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const rows = action?.rows ?? selectedRows;
    const difficulty = action?.difficulty ?? selectedDifficulty;
    const wager = normalizeBetAmount(action?.betAmount ?? betAmount);
    const source = action?.walletSource ?? walletSource;
    setBusyAction(action ? "retry" : "start");
    setErrorText("");
    setRetryAction(null);
    setPicks([]);
    try {
      const token = await ensureActionToken();
      const response = await startBoxeRound({
        titleCode: bootRequest.titleCode,
        rows,
        difficulty,
        betAmount: wager,
        walletSource: source,
        token,
        idempotencyKey,
        tableSessionId: source === "demo" ? null : tableSession?.id ?? null,
        accessSessionId: source === "demo" ? null : accessSessionId,
      });
      if (response.table_session) {
        onTableSessionChange(response.table_session);
      }
      boxeAudio.play("bet_placed");
      applyStartResponse(response, rows, difficulty);
      setBetAmount(wager);
    } catch (error) {
      setErrorText(readBoxeErrorMessage(error, copy("failure.generic")));
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
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.roundId ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "reveal");
    setErrorText("");
    setRetryAction(null);
    try {
      const token = await ensureActionToken();
      const response = await revealBoxePick({
        roundId: targetRoundId,
        row,
        position,
        token,
        idempotencyKey,
      });
      if (response.outcome === "mine") {
        boxeAudio.play("mine_reveal");
      } else if (response.outcome === "top_row") {
        boxeAudio.play("top_row_won");
      } else {
        boxeAudio.play("safe_reveal");
      }
      applyRevealResponse(response, row, position);
    } catch (error) {
      setErrorText(readBoxeErrorMessage(error, copy("failure.network")));
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
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.roundId ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "cashout");
    setErrorText("");
    setRetryAction(null);
    try {
      const token = await ensureActionToken();
      const response = await cashoutBoxeRound({
        roundId: targetRoundId,
        token,
        idempotencyKey,
      });
      boxeAudio.play("cashout_won");
      applyCashoutResponse(response);
    } catch (error) {
      setErrorText(readBoxeErrorMessage(error, copy("failure.network")));
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
  ) {
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
      return;
    }
    if (response.outcome === "top_row") {
      setCelebration({
        amount: response.payout,
        kind: "top_row",
        id: Date.now(),
      });
      return;
    }
  }

  function applyCashoutResponse(response: BoxeCashoutResponse) {
    setRound((currentRound) => currentRound
      ? {
          ...currentRound,
          status: response.status,
          collectAmount: response.payout,
        }
      : currentRound);
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

  function handleStartSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void executeStart();
  }

  const boxeSettings = (
    <BoxeSettingsPanel
      copy={copy}
      disabled={settingsDisabled}
      onDifficultyChange={setSelectedDifficulty}
      onRowsChange={setSelectedRows}
      runtimeConfig={runtimeConfig}
      selectedDifficulty={selectedDifficulty}
      selectedRows={selectedRows}
    />
  );
  const boxeActions = (
    <GameActionButtons
      betButtonLabel={busyAction === "start" ? "..." : copy("actions.bet")}
      collectButtonLabel={
        busyAction === "cashout"
          ? "..."
          : copy("actions.collect_with_amount", { amount: round?.collectAmount ?? "0" })
      }
      isBetDisabled={!canBet || isInteractionLocked}
      isBetLoading={busyAction === "start"}
      isCollectDisabled={!canCollect || isInteractionLocked}
      isCollectLoading={busyAction === "cashout"}
      className="boxe-action-buttons game-visual-action-buttons"
      betButtonClassName={!isRoundActive ? "boxe-primary-action game-action-primary" : undefined}
      collectButtonClassName={isRoundActive ? "boxe-primary-action game-action-primary" : undefined}
      betButtonTestId={!isRoundActive ? "boxe-primary-action" : undefined}
      collectButtonTestId={isRoundActive ? "boxe-primary-action" : undefined}
      onCollect={() => void executeCashout()}
    />
  );
  const boxeBetPanel = (
    <GameBetPanel
      label={copy("settings.bet_amount")}
      inputId="boxe-bet-input"
      inputTestId="boxe-bet-input"
      value={betAmount}
      onValueChange={(value) => setBetAmount(normalizeBetInput(value))}
      inputMode="decimal"
      disabled={isRoundActive || isInteractionLocked}
      quickChipAmounts={["1", "2", "5", "10", "25"]}
      actions={boxeActions}
      className="boxe-bet-panel"
      fieldClassName="boxe-bet-field"
      quickChipRowClassName="boxe-chip-row boxe-bet-chip-row"
      quickChipClassName="game-chip"
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
      walletType={walletSource === "bonus" ? "bonus" : "cash"}
      className="boxe-balance-footer game-visual-balance-footer"
    />
  );
  const modeLabel = walletSource === "demo"
    ? "DEMO MODE"
    : walletSource === "bonus"
      ? "BONUS MODE"
      : "REAL MODE";
  const railHeader = (
    <div className="game-rail-header boxe-rail-header">
      <div className="game-rail-tools boxe-rail-tools">
        <button
          className="button-ghost game-icon-button game-info-button"
          type="button"
          aria-label="Info gioco"
          onClick={onOpenGameInfo}
        >
          i
        </button>
        <GameRuntimeTools
          locale={locale}
          audio={{
            hasAnySound: false,
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
      </div>
      <span className="status-badge info game-mode-badge boxe-mode-badge">
        {modeLabel}
      </span>
    </div>
  );
  const closeButton = (
    <button
      className="button-ghost game-icon-button game-top-close"
      type="button"
      aria-label="Torna al sito"
      onClick={onExit}
    >
      X
    </button>
  );

  return (
    <section className="boxe-gameplay" data-testid="boxe-gameplay" aria-labelledby="boxe-gameplay-title">
      <GameShortViewportGate
        title="Ruota il dispositivo"
        description="BOXE richiede piu altezza per giocare in landscape."
      />

      <GameTopBar
        title="BOXE"
        titleId="boxe-gameplay-title"
        className="boxe-gameplay-header"
        trailing={closeButton}
      />

      <BoxePayoutDisplay
        activeRow={activeRow}
        currentStep={safePicksCount}
        multipliers={activeMultipliers}
      />

      <div className="boxe-play-surface">
        <GameControlRail
          headerTools={railHeader}
          settings={boxeSettings}
          betPanel={boxeBetPanel}
          footer={<article className="boxe-rail-footer">{boxeBalanceFooter}</article>}
          className="boxe-control-rail game-visual-control-rail"
          onSubmit={handleStartSubmit}
        />

        <BoxePyramidBoard
          activeRow={activeRow}
          disabled={isInteractionLocked}
          onPick={(row, position) => void executeReveal(row, position)}
          picks={picks}
          rows={round?.rows ?? selectedRows}
          terminalStatus={terminalStatus}
        />
      </div>
      {insufficientBalance ? (
        <p className="boxe-inline-warning">{copy("balance.insufficient")}</p>
      ) : null}

      {walletError ? <p className="boxe-inline-warning">{walletError}</p> : null}
      {errorText ? (
        <div className="boxe-error boxe-action-error" role="alert">
          <span>{errorText}</span>
          {retryAction ? (
            <button
              className="button-secondary"
              data-testid="boxe-retry-action"
              onClick={retryLastAction}
              type="button"
            >
              {copy("actions.retry")}
            </button>
          ) : null}
        </div>
      ) : null}
      {celebration ? (
        <BoxeWinCelebration
          amount={celebration.amount}
          key={celebration.id}
          kind={celebration.kind}
          onDismiss={() => setCelebration(null)}
        />
      ) : null}
    </section>
  );
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

function readBalanceAmount({
  walletSource,
  wallets,
}: {
  walletSource: BoxeWalletSource;
  wallets: WalletSummary[];
}) {
  if (walletSource === "demo") {
    return "100";
  }
  return wallets.find((wallet) => wallet.wallet_type === walletSource)?.balance_snapshot ?? "0";
}

function readBoxeErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiRequestError) {
    if (error.code === "ROUND_ALREADY_CLOSED") {
      return "La mano e' gia' conclusa.";
    }
    if (error.code === "INSUFFICIENT_BALANCE") {
      return "Saldo insufficiente.";
    }
    if (error.code === "BONUS_WALLET_EMPTY") {
      return "Saldo bonus vuoto.";
    }
    return `${fallback} ${error.message}`;
  }
  return readErrorMessage(error, fallback);
}
