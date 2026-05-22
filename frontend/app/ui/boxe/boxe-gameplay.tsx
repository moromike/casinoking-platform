"use client";

import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from "react";
import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleThemeSkin } from "@/app/lib/types";
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
import { GameMobileControlStack } from "@/app/ui/game-runtime/game-mobile-control-stack";
import { GameMobileSettingsSheet } from "@/app/ui/game-runtime/game-mobile-settings-sheet";
import { GameShortViewportGate } from "@/app/ui/game-runtime/game-short-viewport-gate";
import {
  BOXE_GAME_STORAGE_NAMESPACE,
  clearStoredAuthState,
} from "@/app/ui/game-runtime/game-storage";
import { GameRuntimeTools } from "@/app/ui/game-runtime/game-top-bar";
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
  getBoxeReplay,
  loadBoxeWallets,
  provisionBoxeDemoPlayer,
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

type WalletSummary = {
  wallet_type: string;
  balance_snapshot: string;
};

type BoxeReplayState = {
  roundId: string | null;
  replay: BoxeRoundReplay | null;
  loading: boolean;
  error: string | null;
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

export function BoxeGameplay({
  runtimeConfig,
  titleThemeAssets,
  titleThemeSkin,
  bootRequest,
  initialAccessToken,
  audioPreferences,
  accessSessionId,
  tableSession,
  onExit,
  onTableSessionChange,
}: {
  runtimeConfig: BoxeRuntimeConfig;
  titleThemeAssets: Record<string, string>;
  titleThemeSkin: TitleThemeSkin | null;
  bootRequest: GameBootRequest;
  initialAccessToken: string;
  audioPreferences: BoxeAudioPreferences & {
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
  };
  accessSessionId: string | null;
  tableSession: BoxeTableSession | null;
  onExit: () => void;
  onTableSessionChange: (tableSession: BoxeTableSession) => void;
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
  const [wallets, setWallets] = useState<WalletSummary[]>([]);
  const [demoBalance, setDemoBalance] = useState("100");
  const [walletError, setWalletError] = useState("");
  const [round, setRound] = useState<BoxeRound | null>(null);
  const [picks, setPicks] = useState<BoxeBoardPick[]>([]);
  const [pyramidFullReveal, setPyramidFullReveal] =
    useState<BoxePyramidFullReveal | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [errorText, setErrorText] = useState("");
  const [retryAction, setRetryAction] = useState<RetryAction | null>(null);
  const [infoTab, setInfoTab] = useState<BoxeRulesModalTab>("rules");
  const [replayState, setReplayState] = useState<BoxeReplayState>({
    roundId: null,
    replay: null,
    loading: false,
    error: null,
  });
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [showMobileSettings, setShowMobileSettings] = useState(false);
  const [showRules, setShowRules] = useState(false);
  const [celebration, setCelebration] = useState<{
    amount: string;
    kind: "cashout" | "top_row";
    id: number;
  } | null>(null);
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
      : readBalanceAmount({
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
          setWalletError(buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP));
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
    if (!showRules || infoTab !== "replay" || !round?.roundId) {
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
    runBoxeActionWithDemoTokenRecovery((token) =>
      getBoxeReplay({
        roundId: round.roundId,
        token,
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
  }, [infoTab, round?.roundId, showRules]);

  async function ensureActionToken(): Promise<string> {
    if (authToken) {
      return authToken;
    }
    if (!bootRequest.forceDemoMode) {
      throw new Error("Accedi per giocare con saldo reale.");
    }
    const demoAuth = await provisionBoxeDemoPlayer();
    storeBoxeDemoAuth(demoAuth);
    return demoAuth.access_token;
  }

  function storeBoxeDemoAuth(demoAuth: Awaited<ReturnType<typeof provisionBoxeDemoPlayer>>) {
    setAuthToken(demoAuth.access_token);
    window.localStorage.setItem("casinoking.access_token", demoAuth.access_token);
    window.localStorage.setItem("casinoking.email", demoAuth.email);
  }

  async function runBoxeActionWithDemoTokenRecovery<T>(
    action: (token: string) => Promise<T>,
  ): Promise<T> {
    const token = await ensureActionToken();
    try {
      return await action(token);
    } catch (error) {
      if (!bootRequest.forceDemoMode || !isBearerTokenAuthError(error)) {
        throw error;
      }
      clearStoredAuthState(window.localStorage, BOXE_GAME_STORAGE_NAMESPACE);
      setAuthToken("");
      const demoAuth = await provisionBoxeDemoPlayer();
      storeBoxeDemoAuth(demoAuth);
      return action(demoAuth.access_token);
    }
  }

  function clearTerminalRoundForConfigChange() {
    setRound(null);
    setPicks([]);
    setPyramidFullReveal(null);
    setReplayState({ roundId: null, replay: null, loading: false, error: null });
    setCelebration(null);
    setErrorText("");
    setRetryAction(null);
    setInfoTab("rules");
  }

  function handleRowsChange(rows: number) {
    if (settingsDisabled || rows === selectedRows) {
      return;
    }
    setSelectedRows(rows);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
  }

  function handleDifficultyChange(difficulty: string) {
    if (settingsDisabled || difficulty === selectedDifficulty) {
      return;
    }
    setSelectedDifficulty(difficulty);
    if (terminalStatus !== null) {
      clearTerminalRoundForConfigChange();
    }
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
    setPyramidFullReveal(null);
    setReplayState({ roundId: null, replay: null, loading: false, error: null });
    try {
      const response = await runBoxeActionWithDemoTokenRecovery((token) =>
        startBoxeRound({
          titleCode: bootRequest.titleCode,
          rows,
          difficulty,
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
      boxeAudio.play("bet_placed");
      applyStartResponse(response, rows, difficulty, wager);
      setBetAmount(wager);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP));
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
      const response = await runBoxeActionWithDemoTokenRecovery((token) =>
        revealBoxePick({
          roundId: targetRoundId,
          row,
          position,
          token,
          idempotencyKey,
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
      setErrorText(buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP));
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
      const response = await runBoxeActionWithDemoTokenRecovery((token) =>
        cashoutBoxeRound({
          roundId: targetRoundId,
          token,
          idempotencyKey,
        }),
      );
      boxeAudio.play("cashout_won");
      applyCashoutResponse(response);
    } catch (error) {
      setErrorText(buildGameErrorMessage(error, BOXE_GAME_ERROR_COPY_MAP));
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
      setDemoBalance((currentBalance) =>
        formatChipAmount(parseChipAmount(currentBalance) - parseChipAmount(wager)),
      );
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
      setDemoBalance((currentBalance) =>
        formatChipAmount(parseChipAmount(currentBalance) + parseChipAmount(response.payout)),
      );
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
      onCollect={() => void executeCashout()}
    />
  );
  const boxeDesktopBetPanel = (
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
      onValueChange={(value) => setBetAmount(normalizeBetInput(value))}
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
        {!bootRequest.isEmbeddedView && !useMobileLayout ? (
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

      {walletError ? <p className="boxe-inline-warning">{walletError}</p> : null}
      {errorText ? (
        <GameActionError
          actionLabel={retryAction ? copy("actions.retry") : "OK"}
          actionTestId={retryAction ? "boxe-retry-action" : undefined}
          message={errorText}
          onAction={retryAction ? retryLastAction : () => setErrorText("")}
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
          replayAvailable={Boolean(round?.roundId)}
          replayContent={
            replayState.loading ? (
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

function formatChipAmount(value: number) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  return value.toFixed(2).replace(/\.00$/, "");
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
