"use client";

import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { resolveBackendAssetUrl } from "@/app/lib/api";
import { GameActionError } from "@/app/ui/game-runtime/game-action-error";
import { GameActionButtons } from "@/app/ui/game-runtime/game-action-buttons";
import { GameBalanceFooter } from "@/app/ui/game-runtime/game-balance-footer";
import { GameBetPanel } from "@/app/ui/game-runtime/game-bet-panel";
import type { GameBootRequest } from "@/app/ui/game-runtime/game-boot-request";
import { GameControlRail } from "@/app/ui/game-runtime/game-control-rail";
import {
  buildGameErrorMessage,
  isBearerTokenAuthError,
  type GameErrorCopyMap,
} from "@/app/ui/game-runtime/game-error-copy-adapter";
import { GameRuntimeTools } from "@/app/ui/game-runtime/game-top-bar";
import { GameShortViewportGate } from "@/app/ui/game-runtime/game-short-viewport-gate";
import {
  clearStoredAuthState,
  HI_LO_GAME_STORAGE_NAMESPACE,
} from "@/app/ui/game-runtime/game-storage";
import type { TitleThemeSkin } from "@/app/lib/types";
import {
  cashoutHiLoRound,
  getHiLoRoundReplay,
  loadHiLoWallets,
  predictHiLoRound,
  provisionHiLoDemoPlayer,
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
import { createHiLoCopyResolver } from "./hi-lo-i18n/hi-lo-copy-defaults";
import { HiLoReplayViewer } from "./hi-lo-replay-viewer";
import { HiLoRulesModal, type HiLoRulesModalTab } from "./hi-lo-rules-modal";

const HI_LO_GAME_ERROR_COPY_MAP = {
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

const ACTION_LABELS: Record<HiLoPredictionAction, string> = {
  black: "Black",
  red: "Red",
  down: "Down",
  up: "Up",
};

const MAX_ACTION_RETRY_ATTEMPTS = 3;

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
  const [wallets, setWallets] = useState<WalletSummary[]>([]);
  const [demoBalance, setDemoBalance] = useState("100");
  const [round, setRound] = useState<HiLoRoundResponse | null>(null);
  const [history, setHistory] = useState<HiLoHistoryItem[]>([]);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorText, setErrorText] = useState("");
  const [retryAction, setRetryAction] = useState<RetryAction | null>(null);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [showRules, setShowRules] = useState(false);
  const [activeInfoTab, setActiveInfoTab] = useState<HiLoRulesModalTab>("rules");
  const [replayState, setReplayState] = useState<ReplayState>({ status: "idle" });

  const walletSource: HiLoWalletSource = bootRequest.forceDemoMode
    ? "demo"
    : bootRequest.walletSource ?? "cash";
  const isDemoPlayer = walletSource === "demo";
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
  const statusLabel = round
    ? round.terminal
      ? round.outcome === "cashout"
        ? "Cashout"
        : "Loss"
      : `Streak ${round.correct_predictions_count}`
    : "Ready";
  const modeLabel = isDemoPlayer
    ? "DEMO MODE"
    : walletSource === "bonus"
      ? "BONUS MODE"
      : "REAL MODE";
  const runtimeLocale = runtimeConfig.presentation_config?.default_locale ?? "it";
  const runtimeCopy = runtimeConfig.presentation_config?.copy?.[runtimeLocale];
  const rulesCopy = createHiLoCopyResolver(runtimeLocale, runtimeCopy);

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
        label: initialRound.correct_predictions_count > 0 ? "Resume" : "Start",
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

  async function ensureActionToken(): Promise<string> {
    if (authToken) {
      return authToken;
    }
    if (!bootRequest.forceDemoMode) {
      throw new Error("Accedi per giocare con saldo reale.");
    }
    const demoAuth = await provisionHiLoDemoPlayer();
    storeHiLoDemoAuth(demoAuth);
    return demoAuth.access_token;
  }

  function storeHiLoDemoAuth(demoAuth: Awaited<ReturnType<typeof provisionHiLoDemoPlayer>>) {
    setAuthToken(demoAuth.access_token);
    window.localStorage.setItem("casinoking.access_token", demoAuth.access_token);
    window.localStorage.setItem("casinoking.email", demoAuth.email);
  }

  async function runHiLoActionWithDemoTokenRecovery<T>(
    action: (token: string) => Promise<T>,
  ): Promise<T> {
    const token = await ensureActionToken();
    try {
      return await action(token);
    } catch (error) {
      if (!bootRequest.forceDemoMode || !isBearerTokenAuthError(error)) {
        throw error;
      }
      clearStoredAuthState(window.localStorage, HI_LO_GAME_STORAGE_NAMESPACE);
      setAuthToken("");
      const demoAuth = await provisionHiLoDemoPlayer();
      storeHiLoDemoAuth(demoAuth);
      return action(demoAuth.access_token);
    }
  }

  async function executeStart(action?: Extract<RetryAction, { type: "start" }>) {
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const wager = normalizeBetAmount(action?.betAmount ?? betAmount);
    const source = action?.walletSource ?? walletSource;
    setBusyAction(action ? "retry" : "start");
    setErrorText("");
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    setHistory([]);
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token) =>
        startHiLoRound({
          titleCode: bootRequest.titleCode,
          betAmount: wager,
          walletSource: source,
          token,
          idempotencyKey,
          tableSessionId: source === "demo" ? null : tableSession?.id ?? null,
          accessSessionId: source === "demo" ? null : accessSessionId,
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
          label: "Start",
          card: response.current_card,
          status: "start",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, HI_LO_GAME_ERROR_COPY_MAP));
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
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    const selectedAction = action?.action ?? predictionAction;
    setBusyAction(action ? "retry" : "predict");
    setErrorText("");
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token) =>
        predictHiLoRound({
          roundId: targetRoundId,
          action: selectedAction,
          token,
          idempotencyKey,
        }),
      );
      setRound(response);
      setRetryAttempts(0);
      setHistory((current) => [
        ...current,
        {
          id: `prediction:${idempotencyKey}`,
          label: response.prediction?.label ?? ACTION_LABELS[selectedAction],
          card: response.current_card,
          status: response.prediction?.success ? "correct" : "wrong",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, HI_LO_GAME_ERROR_COPY_MAP));
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
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "skip");
    setErrorText("");
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token) =>
        skipHiLoRound({
          roundId: targetRoundId,
          token,
          idempotencyKey,
        }),
      );
      setRound(response);
      setRetryAttempts(0);
      setHistory((current) => [
        ...current,
        {
          id: `skip:${idempotencyKey}`,
          label: "Skip",
          card: response.current_card,
          status: "skip",
          multiplier: response.multiplier_current,
          payout: response.payout_current,
        },
      ]);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, HI_LO_GAME_ERROR_COPY_MAP));
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
    if (!round && !action) {
      return;
    }
    const targetRoundId = action?.roundId ?? round?.round_id ?? "";
    const idempotencyKey = action?.idempotencyKey ?? createIdempotencyKey();
    setBusyAction(action ? "retry" : "cashout");
    setErrorText("");
    setRetryAction(null);
    if (!action) {
      setRetryAttempts(0);
    }
    try {
      const response = await runHiLoActionWithDemoTokenRecovery((token) =>
        cashoutHiLoRound({
          roundId: targetRoundId,
          token,
          idempotencyKey,
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
          label: "Collect",
          card: response.current_card,
          status: "cashout",
          multiplier: response.multiplier_current,
          payout: response.final_payout_amount ?? response.payout_current,
        },
      ]);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, HI_LO_GAME_ERROR_COPY_MAP));
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

  async function openReplayForCurrentRound() {
    if (!round?.terminal) {
      return;
    }
    const roundId = round.round_id;
    setReplayState({ status: "loading", roundId });
    setActiveInfoTab("replay");
    setShowRules(true);
    try {
      const token = await ensureActionToken();
      const replay = await getHiLoRoundReplay({ roundId, token });
      setReplayState({ status: "ready", roundId, replay });
    } catch (error) {
      setReplayState({
        status: "error",
        roundId,
        message: buildGameErrorMessage(error, HI_LO_GAME_ERROR_COPY_MAP),
      });
    }
  }

  function dismissActionErrorToSite() {
    setErrorText("");
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
          aria-label="Game info"
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
            effectsAria: "Audio effetti",
            effectsLabel: "Effetti",
            effectsOn: "On",
            effectsOff: "Off",
            volume: "Volume",
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
      label="Puntata"
      inputId="hi-lo-bet"
      value={betAmount}
      onValueChange={(value) => setBetAmount(normalizeBetInput(value))}
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
      betButtonLabel={isTerminal ? "Nuova mano" : "Punta"}
      collectButtonLabel="Incassa"
      isBetDisabled={isBetDisabled}
      isCollectDisabled={isCollectDisabled}
      isBetLoading={busyAction === "start" || busyAction === "retry"}
      isCollectLoading={busyAction === "cashout"}
      betButtonClassName="game-action-primary hi-lo-bet-action"
      collectButtonClassName="hi-lo-collect-action"
      betButtonTestId="hi-lo-bet-button"
      collectButtonTestId="hi-lo-collect-button"
      onCollect={() => void executeCashout()}
    />
  );

  const balanceFooter = (
    <GameBalanceFooter
      isDemoPlayer={isDemoPlayer}
      visibleBalance={visibleBalance}
      potentialPayout={potentialPayout}
      copy={{
        demoBalance: "Saldo demo",
        defaultBalance: "Saldo",
        walletBalance: (walletType) => walletType === "bonus" ? "Bonus" : "Saldo reale",
        win: "Win",
        zeroChips: "0 CHIP",
        chipSuffix: "CHIP",
      }}
      walletType={walletSource === "bonus" ? "bonus" : "cash"}
      className="game-visual-balance-footer hi-lo-balance-footer"
    />
  );

  const stageClasses = [
    "hi-lo-stage",
    titleThemeSkin ? "hi-lo-stage-skinned" : null,
  ].filter(Boolean).join(" ");
  const currentCard = round?.current_card ?? null;
  const stageStyle = buildHiLoStageStyle(titleThemeAssets, titleThemeSkin);
  const cardBackSrc = resolveThemeAsset(titleThemeAssets.cell_face_down_background);
  const quotesByAction = new Map((round?.quotes ?? []).map((quote) => [quote.action, quote]));
  const canRetryActionError = retryAction !== null && retryAttempts < MAX_ACTION_RETRY_ATTEMPTS;
  const retryExhausted = retryAction !== null && retryAttempts >= MAX_ACTION_RETRY_ATTEMPTS;
  const actionErrorMessage = retryExhausted
    ? `${errorText} Ricarica il gioco o torna al sito e riapri la mano.`
    : errorText;
  const replayContent =
    replayState.status === "ready" ? (
      <HiLoReplayViewer replay={replayState.replay} />
    ) : replayState.status === "loading" ? (
      <p className="empty-state">{rulesCopy("rules.replay_loading")}</p>
    ) : replayState.status === "error" ? (
      <p className="empty-state">{replayState.message}</p>
    ) : null;

  return (
    <section className="hi-lo-gameplay" data-testid="hi-lo-gameplay" aria-labelledby="hi-lo-gameplay-title">
      <div className="hi-lo-grid">
        <GameControlRail
          headerTools={railHeader}
          betPanel={betPanel}
          footer={<article className="hi-lo-rail-footer">{balanceFooter}</article>}
          className="session-actions game-visual-control-rail hi-lo-control-rail"
          onSubmit={handleStartSubmit}
        >
          {actionButtons}
          <div className="hi-lo-round-metrics" aria-label="Round status">
            <div>
              <span className="list-muted">Stato</span>
              <strong>{statusLabel}</strong>
            </div>
            <div>
              <span className="list-muted">Skip</span>
              <strong>{round ? `${round.active_skip_count}/${round.active_skip_limit}` : `0/${runtimeConfig.active_skip_limit}`}</strong>
            </div>
          </div>
        </GameControlRail>

        <article className={stageClasses} style={stageStyle}>
          <header className="hi-lo-stage-header">
            <h1 id="hi-lo-gameplay-title">HI-LO</h1>
            {!bootRequest.isEmbeddedView ? (
              <button
                className="button-ghost hi-lo-close"
                type="button"
                aria-label="Torna al sito"
                onClick={onExit}
              >
                X
              </button>
            ) : null}
          </header>

          <div className="hi-lo-play-surface">
            <HistoryList history={history} />

            <div className="hi-lo-action-column hi-lo-action-column-left" aria-label="Black and down predictions">
              {renderPredictionControl("black", quotesByAction, isRoundActive, isInteractionLocked, executePrediction)}
              {renderPredictionControl("down", quotesByAction, isRoundActive, isInteractionLocked, executePrediction)}
            </div>

            <div className="hi-lo-card-zone">
              <PlayingCard card={currentCard} cardBackSrc={cardBackSrc} />
              <div className="hi-lo-card-actions" aria-label="Card actions">
                {isRoundActive ? (
                  <button
                    className="button-secondary hi-lo-skip-action"
                    type="button"
                    disabled={!canSkip}
                    onClick={() => void executeSkip()}
                  >
                    Skip
                  </button>
                ) : null}
                {isTerminal ? (
                  <button
                    className="button-secondary hi-lo-rebet-action"
                    type="button"
                    disabled={isBetDisabled}
                    onClick={() => void executeStart()}
                  >
                    Rebet
                  </button>
                ) : null}
                {isTerminal && round ? (
                  <button
                    className="button-secondary hi-lo-replay-action"
                    type="button"
                    disabled={replayState.status === "loading"}
                    onClick={() => void openReplayForCurrentRound()}
                  >
                    {replayState.status === "loading" ? "Replay..." : "Replay mano"}
                  </button>
                ) : null}
              </div>
            </div>

            <div className="hi-lo-action-column hi-lo-action-column-right" aria-label="Red and up predictions">
              {renderPredictionControl("red", quotesByAction, isRoundActive, isInteractionLocked, executePrediction)}
              {renderPredictionControl("up", quotesByAction, isRoundActive, isInteractionLocked, executePrediction)}
            </div>

            {(!round || (!round.terminal && round.quotes.length === 0)) ? (
              <div className="hi-lo-choice-empty">
                <strong>Punta per iniziare</strong>
                <span>Le opzioni arrivano dal backend dopo la carta iniziale.</span>
              </div>
            ) : null}
          </div>
        </article>
      </div>

      <GameShortViewportGate
        title="Schermo troppo basso"
        description="Ruota il dispositivo o aumenta l'altezza per giocare."
      />

      {errorText ? (
        <GameActionError
          actionLabel={
            canRetryActionError
              ? `Riprova ${retryAttempts + 1}/${MAX_ACTION_RETRY_ATTEMPTS}`
              : retryExhausted
                ? "Ricarica"
                : "OK"
          }
          dismissLabel="Torna al sito"
          message={actionErrorMessage}
          onAction={
            canRetryActionError
              ? retryLastAction
              : retryExhausted
                ? () => window.location.reload()
                : () => setErrorText("")
          }
          onDismiss={retryAction ? dismissActionErrorToSite : undefined}
          testId="hi-lo-action-error-dialog"
          title="Azione richiesta"
        />
      ) : null}

      {showRules ? (
        <HiLoRulesModal
          activeTab={activeInfoTab}
          copy={rulesCopy}
          gameTitle={rulesCopy("game.title")}
          locale={runtimeLocale}
          replayAvailable={replayState.status !== "idle"}
          replayContent={replayContent}
          runtimeConfig={runtimeConfig}
          onClose={() => setShowRules(false)}
          onTabChange={setActiveInfoTab}
        />
      ) : null}
    </section>
  );
}

function renderPredictionControl(
  action: HiLoPredictionAction,
  quotesByAction: Map<HiLoPredictionAction, HiLoQuote>,
  isRoundActive: boolean,
  isInteractionLocked: boolean,
  executePrediction: (action: HiLoPredictionAction) => Promise<void>,
) {
  const quote = quotesByAction.get(action);
  if (!quote) {
    return null;
  }
  return (
    <PredictionButton
      disabled={!isRoundActive || isInteractionLocked}
      key={quote.action}
      quote={quote}
      onChoose={() => void executePrediction(quote.action)}
    />
  );
}

function PredictionButton({
  disabled,
  quote,
  onChoose,
}: {
  disabled: boolean;
  quote: HiLoQuote;
  onChoose: () => void;
}) {
  return (
    <button
      className={`hi-lo-prediction hi-lo-prediction-${quote.action}`}
      type="button"
      disabled={disabled}
      onClick={onChoose}
    >
      <span className="hi-lo-prediction-label">
        <span className="hi-lo-prediction-icon" aria-hidden="true">
          {readPredictionIcon(quote.action)}
        </span>
        <span>{ACTION_LABELS[quote.action]}</span>
      </span>
      <strong>{quote.multiplier}x</strong>
    </button>
  );
}

function readPredictionIcon(action: HiLoPredictionAction) {
  if (action === "black") {
    return "●";
  }
  if (action === "red") {
    return "●";
  }
  if (action === "down") {
    return "↓";
  }
  return "↑";
}

function PlayingCard({
  card,
  cardBackSrc,
}: {
  card: HiLoCard | null;
  cardBackSrc: string | null;
}) {
  const suit = card?.suit ?? "clubs";
  const color = card?.color ?? "black";
  const suitSymbol = card ? readSuitSymbol(card.suit) : null;
  const cardBackStyle = cardBackSrc
    ? ({
        "--hi-lo-card-back-image": `url("${cardBackSrc}")`,
      } as CSSProperties)
    : undefined;
  return (
    <div className={`hi-lo-card is-${color} suit-${suit}`} aria-label={card ? `${card.rank_label} ${suit}` : "Card back"}>
      {card ? (
        <>
          <strong className="hi-lo-card-rank">{card.rank_label}</strong>
          <span className="hi-lo-card-suit-symbol">{suitSymbol}</span>
          <span className="hi-lo-card-suit">{readSuitLabel(card.suit)}</span>
        </>
      ) : (
        <span className="hi-lo-card-back" style={cardBackStyle}>HI-LO</span>
      )}
    </div>
  );
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

function readSuitLabel(suit: HiLoCard["suit"]) {
  if (suit === "clubs") {
    return "Clubs";
  }
  if (suit === "spades") {
    return "Spades";
  }
  if (suit === "hearts") {
    return "Hearts";
  }
  return "Diamonds";
}

function buildHiLoStageStyle(
  titleThemeAssets: Record<string, string>,
  titleThemeSkin: TitleThemeSkin | null,
): CSSProperties | undefined {
  const backgroundSrc = resolveThemeAsset(titleThemeAssets.game_area_background);
  if (!backgroundSrc) {
    return undefined;
  }
  return {
    "--hi-lo-game-area-background-image": `url("${backgroundSrc}")`,
    "--hi-lo-game-area-background-size": titleThemeSkin?.game_area_background_fit ?? "cover",
    "--hi-lo-game-area-background-position":
      titleThemeSkin?.game_area_background_position ?? "center",
  } as CSSProperties;
}

function resolveThemeAsset(value: string | undefined) {
  return value ? resolveBackendAssetUrl(value) : null;
}

function HistoryList({ history }: { history: HiLoHistoryItem[] }) {
  return (
    <div className="hi-lo-history">
      <div className="hi-lo-history-list">
        {history.length === 0 ? (
          <span className="hi-lo-history-empty">History</span>
        ) : (
          history.slice(-5).map((item) => (
            <div className={`hi-lo-history-item is-${item.status}`} key={item.id}>
              <strong className={item.card ? `is-${item.card.color}` : undefined}>
                {item.card ? `${item.card.rank_label}${readSuitSymbol(item.card.suit)}` : "-"}
              </strong>
              <small>{item.multiplier}x</small>
            </div>
          ))
        )}
      </div>
    </div>
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

function createIdempotencyKey() {
  if (typeof window !== "undefined" && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `hi-lo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
