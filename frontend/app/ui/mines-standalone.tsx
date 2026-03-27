"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  extractValidationMessage,
  formatDateTime,
  getGridSizes,
  getMineOptions,
  getPayoutLadder,
  shortId,
} from "./casinoking-console.helpers";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const STORAGE_KEYS = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.current_session_id",
} as const;

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
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
  fairness_version: string;
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

type SessionHistoryItem = {
  game_session_id: string;
  status: "active" | "won" | "lost";
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
  safe_reveals_count: number;
  multiplier_current: string;
  potential_payout: string;
  created_at: string;
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
  const [currentEmail, setCurrentEmail] = useState("");
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [runtimeConfig, setRuntimeConfig] = useState<MinesRuntimeConfig | null>(null);
  const [currentFairness, setCurrentFairness] = useState<FairnessCurrentConfig | null>(null);
  const [currentSession, setCurrentSession] = useState<SessionSnapshot | null>(null);
  const [currentSessionFairness, setCurrentSessionFairness] = useState<SessionFairness | null>(
    null,
  );
  const [sessionHistory, setSessionHistory] = useState<SessionHistoryItem[]>([]);
  const [selectedGridSize, setSelectedGridSize] = useState(25);
  const [selectedMineCount, setSelectedMineCount] = useState(3);
  const [betAmount, setBetAmount] = useState("5");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [highlightedMineCell, setHighlightedMineCell] = useState<number | null>(null);

  const gridSizes = getGridSizes(runtimeConfig);
  const mineOptions = getMineOptions(runtimeConfig, selectedGridSize);
  const payoutLadder = getPayoutLadder(runtimeConfig, selectedGridSize, selectedMineCount);
  const visibleGridSize =
    currentSession && currentSession.status === "active"
      ? currentSession.grid_size
      : selectedGridSize;
  const boardSide = Math.sqrt(visibleGridSize);
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const isDemoPlayer = currentEmail.endsWith("@casinoking.local");
  const visibleBalance =
    currentSession && currentSession.status === "active"
      ? currentSession.wallet_balance_after_start
      : cashWallet?.balance_snapshot ?? "1000";

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEYS.accessToken) ?? "";
    const storedEmail = window.localStorage.getItem(STORAGE_KEYS.email) ?? "";
    const storedSessionId = window.localStorage.getItem(STORAGE_KEYS.sessionId);

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);
    void loadRuntime();
    if (storedToken) {
      void refreshAuthenticatedState(storedToken, storedSessionId);
    }
  }, []);

  useEffect(() => {
    if (!gridSizes.includes(selectedGridSize)) {
      setSelectedGridSize(gridSizes[0] ?? 25);
      return;
    }
    const nextMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!nextMineOptions.includes(selectedMineCount)) {
      setSelectedMineCount(nextMineOptions[0] ?? 3);
    }
  }, [gridSizes, runtimeConfig, selectedGridSize, selectedMineCount]);

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
      const [walletData, historyData] = await Promise.all([
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<SessionHistoryItem[]>("/games/mines/sessions", {}, token),
      ]);
      setWallets(walletData);
      setSessionHistory(historyData);
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
    const [sessionData, fairnessData] = await Promise.all([
      apiRequest<SessionSnapshot>(`/games/mines/session/${sessionId}`, {}, token),
      apiRequest<SessionFairness>(`/games/mines/session/${sessionId}/fairness`, {}, token),
    ]);
    setCurrentSession(sessionData);
    setCurrentSessionFairness(fairnessData);
    if (sessionData.status === "active") {
      window.localStorage.setItem(STORAGE_KEYS.sessionId, sessionId);
    } else {
      window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    }
  }

  async function handleStartDemoMode() {
    if (accessToken) {
      return;
    }
    setBusyAction("demo-mode");
    try {
      const demoData = await apiRequest<DemoAuthResponse>("/auth/demo", {
        method: "POST",
      });
      setAccessToken(demoData.access_token);
      setCurrentEmail(demoData.email);
      window.localStorage.setItem(STORAGE_KEYS.accessToken, demoData.access_token);
      window.localStorage.setItem(STORAGE_KEYS.email, demoData.email);
      window.localStorage.removeItem(STORAGE_KEYS.sessionId);
      await refreshAuthenticatedState(demoData.access_token, null);
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
    if (!accessToken) {
      await handleStartDemoMode();
      return;
    }

    setBusyAction("start-session");
    try {
      const startData = await apiRequest<StartSessionResponse>(
        "/games/mines/start",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
          },
          body: JSON.stringify({
            grid_size: selectedGridSize,
            mine_count: selectedMineCount,
            bet_amount: normalizeWholeChipInput(betAmount),
            wallet_type: "cash",
          }),
        },
        accessToken,
      );
      setHighlightedMineCell(null);
      await refreshAuthenticatedState(accessToken, startData.game_session_id);
      setStatus({
        kind: "success",
        text: `Round ${shortId(startData.game_session_id)} started.`,
      });
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
      const revealData = await apiRequest<{ result: "safe" | "mine" }>(
        "/games/mines/reveal",
        {
          method: "POST",
          body: JSON.stringify({
            game_session_id: currentSession.game_session_id,
            cell_index: cellIndex,
          }),
        },
        accessToken,
      );
      setHighlightedMineCell(revealData.result === "mine" ? cellIndex : null);
      await refreshAuthenticatedState(accessToken, currentSession.game_session_id);
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
      await apiRequest(
        "/games/mines/cashout",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
          },
          body: JSON.stringify({
            game_session_id: currentSession.game_session_id,
          }),
        },
        accessToken,
      );
      await refreshAuthenticatedState(accessToken, currentSession.game_session_id);
      setHighlightedMineCell(null);
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Cash out failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleExit() {
    if (isDemoPlayer) {
      clearAuthState(true);
    } else {
      setCurrentSession(null);
      setCurrentSessionFairness(null);
      setHighlightedMineCell(null);
      window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    }
    window.location.assign("/");
  }

  function clearAuthState(removeStatus: boolean) {
    setAccessToken("");
    setCurrentEmail("");
    setWallets([]);
    setSessionHistory([]);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    window.localStorage.removeItem(STORAGE_KEYS.accessToken);
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
    const isMine = highlightedMineCell === cellIndex;
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

  return (
    <main className="page-shell">
      <section className="panel mines-product-shell mines-product-shell-clean">
        {status ? <div className={`status-banner ${status.kind}`}>{status.text}</div> : null}
        <div className="mines-grid">
          <div className="stack">
            <form
              className="session-actions mines-control-rail mines-control-rail-clean"
              onSubmit={handleStartSession}
            >
              <div className="list-row mines-rail-header">
                <h3>{currentSession?.status === "active" ? "Live round" : "New round"}</h3>
                <button
                  className="button-ghost mines-exit-button"
                  type="button"
                  onClick={handleExit}
                >
                  Exit
                </button>
              </div>
              <div className="stack mines-control-stack">
                <div className="field">
                  <label>Grid size</label>
                  <div className="choice-chip-row">
                    {gridSizes.map((gridSize) => (
                      <button
                        key={gridSize}
                        className={selectedGridSize === gridSize ? "choice-chip active" : "choice-chip"}
                        type="button"
                        disabled={busyAction !== null}
                        onClick={() => setSelectedGridSize(gridSize)}
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
                        disabled={busyAction !== null}
                        onClick={() => setSelectedMineCount(mineCount)}
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
                    onChange={(event) => setBetAmount(normalizeWholeChipInput(event.target.value))}
                    inputMode="numeric"
                    placeholder="5"
                  />
                  <div className="quick-chip-row">
                    {["1", "2", "5", "10", "25"].map((amount) => (
                      <button
                        key={amount}
                        className={betAmount === amount ? "quick-chip active" : "quick-chip"}
                        type="button"
                        onClick={() => setBetAmount(amount)}
                      >
                        {amount}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="actions">
                <button className="button" type="submit" disabled={busyAction !== null}>
                  {!accessToken
                    ? busyAction === "demo-mode"
                      ? "Preparing demo..."
                      : "Open demo"
                    : busyAction === "start-session"
                      ? "Betting..."
                      : "Bet"}
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
                  {busyAction === "cashout" ? "Collecting..." : "Collect"}
                </button>
              </div>

              <article className="mines-rail-footer">
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
              </article>
            </form>
          </div>

          <div className="stack">
            <article className="mines-stage-card">
              <div className="mines-stage-topbar">
                <div className="mines-stage-heading">
                  <h3 className="mines-wordmark">MINES</h3>
                </div>
                <div className="mines-stage-actions">
                  <button
                    className="button-ghost mines-info-button"
                    type="button"
                    onClick={() => setShowRules(true)}
                    aria-label="Apri regole Mines"
                  >
                    i
                  </button>
                  <button
                    className="button-ghost mines-icon-close"
                    type="button"
                    onClick={handleExit}
                    aria-label="Exit Mines"
                  >
                    x
                  </button>
                </div>
              </div>
            </article>

            <article className="board-shell mines-stage-board">
              <div
                className="mines-board"
                style={{ gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))` }}
              >
                {boardCells}
              </div>
            </article>

            {!isDemoPlayer && accessToken && sessionHistory.length > 0 ? (
              <article className="session-card mines-hand-report-card">
                <div className="panel-header compact">
                  <div>
                    <h3>Report mani precedenti</h3>
                    <p>Le ultime mani concluse del giocatore loggato.</p>
                  </div>
                  <span className="status-badge info">{sessionHistory.length} tracked</span>
                </div>
                <div className="history-list">
                  {sessionHistory.slice(0, 4).map((entry) => (
                    <article className="history-card" key={entry.game_session_id}>
                      <div className="list-row">
                        <span className="mono">{shortId(entry.game_session_id)}</span>
                        <span className={`status-inline ${sessionStatusKind(entry.status)}`}>
                          {entry.status}
                        </span>
                      </div>
                      <p className="helper">
                        {entry.grid_size} cells · {entry.mine_count} mines · bet {entry.bet_amount} CHIP
                      </p>
                      <p className="helper">
                        {formatDateTime(entry.created_at)} · payout {entry.potential_payout} CHIP
                      </p>
                    </article>
                  ))}
                </div>
              </article>
            ) : null}
          </div>
        </div>

        {showRules ? (
          <div className="modal-backdrop" role="presentation" onClick={() => setShowRules(false)}>
            <article
              className="modal-card mines-rules-modal"
              role="dialog"
              aria-modal="true"
              aria-label="Game info Mines"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="panel-header compact">
                <div>
                  <h3>GAME INFO - MINES</h3>
                  <p>Schermata regole separata dal tavolo, come nel gioco.</p>
                </div>
                <button className="button-ghost" type="button" onClick={() => setShowRules(false)}>
                  Close
                </button>
              </div>
              <div className="stack">
                <section>
                  <h4>Ways to win</h4>
                  <p>Pick at least one safe diamond and collect before revealing a mine.</p>
                </section>
                <section>
                  <h4>Payout display</h4>
                  <p>The official payout table updates instantly when grid size or mine count changes.</p>
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
                  <h4>General</h4>
                  <p>
                    Mines is server-authoritative. Outcome, board, payout, nonce and fairness hashes always come from the backend.
                  </p>
                </section>
                <section>
                  <h4>History</h4>
                  <p>
                    Closed hands remain available to authenticated players with setup, payout, result and fairness metadata.
                  </p>
                </section>
                {currentFairness ? (
                  <section>
                    <h4>Fairness</h4>
                    <p>
                      Version {currentFairness.fairness_version} · phase {currentFairness.fairness_phase} ·
                      {currentFairness.user_verifiable ? " player verifiable" : " admin audit only"}
                    </p>
                  </section>
                ) : null}
                {currentSessionFairness ? (
                  <section>
                    <h4>Current session proof</h4>
                    <p>
                      Seed hash {truncateValue(currentSessionFairness.server_seed_hash, 18)} · board hash{" "}
                      {truncateValue(currentSessionFairness.board_hash, 18)} · nonce {currentSessionFairness.nonce}
                    </p>
                  </section>
                ) : null}
              </div>
            </article>
          </div>
        ) : null}
      </section>
    </main>
  );
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

function sessionStatusKind(status: SessionSnapshot["status"] | SessionHistoryItem["status"]): StatusKind {
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
  return `${Math.max(0, Math.trunc(safeValue))} CHIP`;
}

function formatGridChoiceLabel(gridSize: number): string {
  const side = Math.sqrt(gridSize);
  return Number.isInteger(side) ? `${side}x${side}` : `${gridSize} cells`;
}

function truncateValue(value: string, size: number): string {
  if (value.length <= size) {
    return value;
  }
  return `${value.slice(0, size)}...`;
}
