"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const STORAGE_KEYS = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.current_session_id",
  launchPreset: "casinoking.launch_preset",
} as const;

type StatusKind = "success" | "error" | "info";

type StatusMessage = {
  kind: StatusKind;
  text: string;
};

type PlayerView = "lobby" | "account" | "mines";

type Wallet = {
  wallet_type: string;
  currency_code: string;
  balance_snapshot: string;
  status: string;
  ledger_account_code: string;
};

type LedgerTransaction = {
  id: string;
  transaction_type: string;
  reference_type: string | null;
  reference_id: string | null;
  idempotency_key: string;
  created_at: string;
};

type LedgerTransactionDetail = {
  id: string;
  transaction_type: string;
  reference_type: string | null;
  reference_id: string | null;
  idempotency_key: string | null;
  created_at: string;
  entries: Array<{
    id: string;
    ledger_account_code: string;
    entry_side: string;
    amount: string;
    created_at: string;
  }>;
};

type MinesRuntimeConfig = {
  game_code: string;
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
  payout_runtime_file: string;
  fairness_version: string;
};

type FairnessCurrentConfig = {
  game_code: string;
  fairness_version: string;
  fairness_phase: string;
  random_source: string;
  board_hash_persisted: boolean;
  server_seed_hash_persisted: boolean;
  active_server_seed_hash: string;
  seed_activated_at: string;
  user_verifiable: boolean;
  payout_runtime_file: string;
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
  revealed_cells_count: number;
  multiplier_current: string;
  potential_payout: string;
  created_at: string;
  closed_at: string | null;
};

type SessionFairness = {
  game_session_id: string;
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  user_verifiable: boolean;
};

type LaunchPreset = {
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
};

type AccountOverview = {
  totalRounds: number;
  wins: number;
  losses: number;
  activeRounds: number;
  totalStaked: string;
  totalReturned: string;
  recentWalletMoves: number;
  lastRoundAt: string | null;
};

type StartSessionResponse = {
  game_session_id: string;
  status: string;
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  safe_reveals_count: number;
  multiplier_current: string;
  wallet_balance_after: string;
  ledger_transaction_id: string;
};

type AdminUser = {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
};

type AdminLedgerReport = {
  summary: {
    recent_transaction_count: number;
    balanced_transaction_count: number;
    wallet_count: number;
    wallets_with_drift_count: number;
  };
  recent_transactions: Array<{
    id: string;
    user_id: string | null;
    user_email: string | null;
    transaction_type: string;
    reference_type: string | null;
    reference_id: string | null;
    idempotency_key: string | null;
    entry_count: number;
    total_debit: string;
    total_credit: string;
    created_at: string;
  }>;
  wallet_reconciliation: Array<{
    wallet_account_id: string;
    user_id: string;
    user_email: string;
    wallet_type: string;
    currency_code: string;
    balance_snapshot: string;
    ledger_balance: string;
    drift: string;
  }>;
};

type FairnessRotateResponse = {
  game_code: string;
  fairness_version: string;
  previous_server_seed_hash: string | null;
  active_server_seed_hash: string;
  activated_at: string;
};

type FairnessVerifyResult = {
  game_session_id: string;
  status: string;
  fairness_version: string;
  nonce: number;
  stored_server_seed_hash: string;
  computed_server_seed_hash: string;
  stored_board_hash: string;
  computed_board_hash: string;
  stored_mine_positions: number[];
  computed_mine_positions: number[];
  rng_material: string;
  server_seed_hash_match: boolean;
  board_hash_match: boolean;
  mine_positions_match: boolean;
  verified: boolean;
};

type AdminActionResponse = {
  target_user_id: string;
  wallet_type: string;
  direction: string;
  amount: string;
  wallet_balance_after: string;
  ledger_transaction_id: string;
  admin_action_id: string;
};

type ApiEnvelope<T> =
  | {
      success: true;
      data: T;
    }
  | {
      success: false;
      error: {
        code: string;
        message: string;
      };
    };

class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export function CasinoKingConsole({
  area = "player",
  view = "lobby",
}: {
  area?: "player" | "admin";
  view?: PlayerView;
}) {
  const [status, setStatus] = useState<StatusMessage | null>({
    kind: "info",
    text:
      area === "admin"
        ? "Admin backoffice connected to the local backend."
        : "Player lobby connected to the local backend. Sign in, fund your demo account, and launch Mines.",
  });
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [siteAccessPassword, setSiteAccessPassword] = useState("");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");

  const [accessToken, setAccessToken] = useState("");
  const [currentEmail, setCurrentEmail] = useState("");
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [selectedWalletDetail, setSelectedWalletDetail] =
    useState<Wallet | null>(null);
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [sessionHistory, setSessionHistory] = useState<SessionHistoryItem[]>([]);
  const [selectedTransactionDetail, setSelectedTransactionDetail] =
    useState<LedgerTransactionDetail | null>(null);
  const [runtimeConfig, setRuntimeConfig] = useState<MinesRuntimeConfig | null>(
    null,
  );
  const [selectedGridSize, setSelectedGridSize] = useState<number>(25);
  const [selectedMineCount, setSelectedMineCount] = useState<number>(3);
  const [betAmount, setBetAmount] = useState("5.000000");
  const [walletType, setWalletType] = useState("cash");
  const [currentSession, setCurrentSession] = useState<SessionSnapshot | null>(
    null,
  );
  const [currentSessionFairness, setCurrentSessionFairness] =
    useState<SessionFairness | null>(null);
  const [highlightedMineCell, setHighlightedMineCell] = useState<number | null>(
    null,
  );
  const [runtimeLoaded, setRuntimeLoaded] = useState(false);
  const [adminEmailFilter, setAdminEmailFilter] = useState("");
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [selectedAdminUserId, setSelectedAdminUserId] = useState("");
  const [adminLedgerTransactions, setAdminLedgerTransactions] = useState<
    LedgerTransaction[]
  >([]);
  const [adminLedgerReport, setAdminLedgerReport] =
    useState<AdminLedgerReport | null>(null);
  const [adminFairnessCurrent, setAdminFairnessCurrent] =
    useState<FairnessCurrentConfig | null>(null);
  const [verifySessionId, setVerifySessionId] = useState("");
  const [fairnessVerifyResult, setFairnessVerifyResult] =
    useState<FairnessVerifyResult | null>(null);
  const [adminSessionSnapshot, setAdminSessionSnapshot] =
    useState<SessionSnapshot | null>(null);
  const [bonusAmount, setBonusAmount] = useState("10.000000");
  const [bonusReason, setBonusReason] = useState("manual_bonus");
  const [adjustmentWalletType, setAdjustmentWalletType] = useState("bonus");
  const [adjustmentDirection, setAdjustmentDirection] = useState("credit");
  const [adjustmentAmount, setAdjustmentAmount] = useState("5.000000");
  const [adjustmentReason, setAdjustmentReason] =
    useState("manual_adjustment");
  const [adminLastAction, setAdminLastAction] = useState<{
    label: string;
    result: AdminActionResponse;
  } | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_KEYS.accessToken) ?? "";
    const storedEmail = window.localStorage.getItem(STORAGE_KEYS.email) ?? "";
    const storedSessionId =
      window.localStorage.getItem(STORAGE_KEYS.sessionId) ?? "";
    const storedLaunchPreset = parseLaunchPreset(
      window.localStorage.getItem(STORAGE_KEYS.launchPreset),
    );

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);
    setLoginEmail(storedEmail);
    if (storedLaunchPreset) {
      applyLaunchPreset(storedLaunchPreset);
    }

    void loadRuntimeConfig();

    if (storedToken) {
      void refreshAuthenticatedState({
        token: storedToken,
        sessionId: storedSessionId || null,
      });
    }
  }, []);

  const gridSizes = getGridSizes(runtimeConfig);
  const mineOptions = getMineOptions(runtimeConfig, selectedGridSize);
  const boardSide = currentSession
    ? Math.sqrt(currentSession.grid_size)
    : Math.sqrt(selectedGridSize);
  const activeGridSize = currentSession?.grid_size ?? selectedGridSize;
  const activeMineCount = currentSession?.mine_count ?? selectedMineCount;
  const selectedPayoutLadder = getPayoutLadder(
    runtimeConfig,
    selectedGridSize,
    selectedMineCount,
  );
  const activePayoutLadder = getPayoutLadder(
    runtimeConfig,
    activeGridSize,
    activeMineCount,
  );
  const currentRevealStep = currentSession?.safe_reveals_count ?? 0;
  const currentLadderValue =
    currentSession && currentRevealStep > 0
      ? activePayoutLadder[currentRevealStep - 1] ?? null
      : null;
  const nextLadderValue =
    currentSession && currentSession.status === "active"
      ? activePayoutLadder[currentRevealStep] ?? null
      : selectedPayoutLadder[0] ?? null;
  const activeSafeCellCount = activeGridSize - activeMineCount;
  const revealProgressPercent = currentSession
    ? Math.round(
        (currentSession.safe_reveals_count / Math.max(activeSafeCellCount, 1)) * 100,
      )
    : 0;
  const remainingSafeCells = currentSession
    ? Math.max(activeSafeCellCount - currentSession.safe_reveals_count, 0)
    : activeSafeCellCount;
  const cashoutReady = Boolean(
    currentSession &&
      currentSession.status === "active" &&
      currentSession.safe_reveals_count > 0,
  );
  const nextSafeChance =
    currentSession && currentSession.status === "active"
      ? Math.max(
          ((currentSession.grid_size -
            currentSession.mine_count -
            currentSession.safe_reveals_count) /
            Math.max(
              currentSession.grid_size - currentSession.safe_reveals_count,
              1,
            )) *
            100,
          0,
        )
      : null;
  const nextMineRisk = nextSafeChance === null ? null : Math.max(100 - nextSafeChance, 0);
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const bonusWallet = wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null;
  const accountOverview = buildAccountOverview(sessionHistory, transactions);
  const selectedAdminUser =
    adminUsers.find((user) => user.id === selectedAdminUserId) ?? null;
  const isAdminArea = area === "admin";
  const playerView = isAdminArea ? null : view;
  const showPlayerRegistration = !isAdminArea && playerView !== "mines";
  const showWalletAndLedger = !isAdminArea && playerView === "account";
  const showAdminPanel = isAdminArea;
  const showMinesPanel = !isAdminArea && playerView === "mines";
  const showPlayerLobby = !isAdminArea && playerView === "lobby";

  useEffect(() => {
    if (!runtimeConfig) {
      return;
    }

    const firstGridSize = gridSizes[0];
    if (!gridSizes.includes(selectedGridSize)) {
      setSelectedGridSize(firstGridSize);
      return;
    }

    const nextMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!nextMineOptions.includes(selectedMineCount)) {
      setSelectedMineCount(nextMineOptions[0]);
    }
  }, [gridSizes, runtimeConfig, selectedGridSize, selectedMineCount]);

  async function loadRuntimeConfig() {
    try {
      const data = await apiRequest<MinesRuntimeConfig>("/games/mines/config");
      setRuntimeConfig(data);
      setRuntimeLoaded(true);
      const fairnessData = await apiRequest<FairnessCurrentConfig>(
        "/games/mines/fairness/current",
      );
      setAdminFairnessCurrent(fairnessData);
    } catch (error) {
      setRuntimeLoaded(false);
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Unable to load the official Mines runtime."),
      });
    }
  }

  async function refreshAuthenticatedState({
    token,
    sessionId,
  }: {
    token: string;
    sessionId?: string | null;
  }) {
    try {
      const [walletData, transactionData, sessionHistoryData] = await Promise.all([
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<LedgerTransaction[]>("/ledger/transactions", {}, token),
        apiRequest<SessionHistoryItem[]>("/games/mines/sessions", {}, token),
      ]);

      setWallets(walletData);
      setTransactions(transactionData);
      setSessionHistory(sessionHistoryData);
      if (selectedWalletDetail) {
        const nextWalletDetail =
          walletData.find(
            (wallet) => wallet.wallet_type === selectedWalletDetail.wallet_type,
          ) ?? null;
        setSelectedWalletDetail(nextWalletDetail);
      }

      if (sessionId) {
        try {
          await loadSession(token, sessionId, false);
        } catch {
          setCurrentSession(null);
          setCurrentSessionFairness(null);
          setHighlightedMineCell(null);
          window.localStorage.removeItem(STORAGE_KEYS.sessionId);
        }
      }
    } catch (error) {
      clearAuthState();
      setStatus({
        kind: "error",
        text: readErrorMessage(
          error,
          "The local player session is no longer valid. Please sign in again.",
        ),
      });
    }
  }

  async function loadSession(
    token: string,
    sessionId: string,
    announce = true,
  ) {
    const [sessionData, fairnessData] = await Promise.all([
      apiRequest<SessionSnapshot>(
        `/games/mines/session/${sessionId}`,
        {},
        token,
      ),
      apiRequest<SessionFairness>(
        `/games/mines/session/${sessionId}/fairness`,
        {},
        token,
      ),
    ]);
    setCurrentSession(sessionData);
    setCurrentSessionFairness(fairnessData);
    setSessionHistory((currentHistory) =>
      mergeSessionHistory(currentHistory, sessionData),
    );
    if (sessionData.status === "active") {
      window.localStorage.setItem(STORAGE_KEYS.sessionId, sessionId);
    } else {
      window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    }
    if (announce) {
      setStatus({
        kind: "info",
        text: `Session ${shortId(sessionId)} reloaded from the backend.`,
      });
    }
  }

  function applyLaunchPreset(preset: LaunchPreset) {
    setSelectedGridSize(preset.grid_size);
    setSelectedMineCount(preset.mine_count);
    setBetAmount(preset.bet_amount);
    setWalletType(preset.wallet_type);
  }

  function rememberLaunchPreset(
    preset: LaunchPreset,
    sourceLabel: string,
  ) {
    applyLaunchPreset(preset);
    window.localStorage.setItem(STORAGE_KEYS.launchPreset, JSON.stringify(preset));
    setStatus({
      kind: "info",
      text: `${sourceLabel} is ready to replay in Mines. The launch form has been prefilled with the same setup.`,
    });
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("register");

    try {
      const data = await apiRequest<{
        user_id: string;
        bootstrap_transaction_id: string;
      }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          site_access_password: siteAccessPassword,
        }),
      });

      setLoginEmail(registerEmail.trim().toLowerCase());
      setLoginPassword(registerPassword);
      setStatus({
        kind: "success",
        text: `Registration completed. Player ${shortId(data.user_id)} was created and the initial demo credit is ready.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Registration failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("login");

    try {
      const data = await apiRequest<{ access_token: string; token_type: string }>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: loginEmail,
            password: loginPassword,
          }),
        },
      );

      const normalizedEmail = loginEmail.trim().toLowerCase();
      setAccessToken(data.access_token);
      setCurrentEmail(normalizedEmail);
      window.localStorage.setItem(STORAGE_KEYS.accessToken, data.access_token);
      window.localStorage.setItem(STORAGE_KEYS.email, normalizedEmail);

      await refreshAuthenticatedState({
        token: data.access_token,
        sessionId: window.localStorage.getItem(STORAGE_KEYS.sessionId),
      });

      setStatus({
        kind: "success",
        text: "Sign-in completed. Wallets, account activity, and the current session were synchronized.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Sign-in failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleVerifySiteAccess() {
    setBusyAction("site-access");

    try {
      await apiRequest<{ access_granted: boolean }>("/site/access", {
        method: "POST",
        body: JSON.stringify({ password: siteAccessPassword }),
      });
      setStatus({
        kind: "success",
        text: "Site access password accepted. You can now complete player registration.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Site access password is not valid."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRefreshAccount() {
    if (!accessToken) {
      return;
    }
    setBusyAction("refresh");

    try {
      const sessionId = currentSession?.game_session_id ?? null;
      await refreshAuthenticatedState({ token: accessToken, sessionId });
      setStatus({
        kind: "info",
        text: "Wallet balances, account activity, and the current session were refreshed.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Account refresh failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadAdminUsers() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token valido prima di usare il backoffice admin.",
      });
      return;
    }

    setBusyAction("admin-users");
    try {
      const query = adminEmailFilter.trim()
        ? `?email=${encodeURIComponent(adminEmailFilter.trim())}`
        : "";
      const data = await apiRequest<AdminUser[]>(
        `/admin/users${query}`,
        {},
        accessToken,
      );
      setAdminUsers(data);
      if (
        data.length > 0 &&
        (!selectedAdminUserId || !data.some((user) => user.id === selectedAdminUserId))
      ) {
        setSelectedAdminUserId(data[0].id);
      }
      setStatus({
        kind: "info",
        text: `Backoffice utenti riallineato. Record caricati: ${data.length}.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento utenti admin non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadTransactionDetail(transactionId: string) {
    if (!accessToken) {
      return;
    }

    setBusyAction(`ledger-detail-${transactionId}`);
    try {
      const data = await apiRequest<LedgerTransactionDetail>(
        `/ledger/transactions/${transactionId}`,
        {},
        accessToken,
      );
      setSelectedTransactionDetail(data);
      setStatus({
        kind: "info",
        text: `Dettaglio transaction ${shortId(transactionId)} caricato dal backend.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento dettaglio transaction non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadWalletDetail(walletType: string) {
    if (!accessToken) {
      return;
    }

    setBusyAction(`wallet-detail-${walletType}`);
    try {
      const data = await apiRequest<Wallet>(
        `/wallets/${encodeURIComponent(walletType)}`,
        {},
        accessToken,
      );
      setSelectedWalletDetail(data);
      setStatus({
        kind: "info",
        text: `Dettaglio wallet ${walletType} caricato dal backend.`,
      });
    } catch (error) {
      setSelectedWalletDetail(null);
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento dettaglio wallet non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleOpenHistorySession(sessionId: string) {
    if (!accessToken) {
      return;
    }

    setBusyAction(`history-session-${sessionId}`);
    try {
      setHighlightedMineCell(null);
      await loadSession(accessToken, sessionId, false);
      setStatus({
        kind: "info",
        text: `Session ${shortId(sessionId)} loaded from your recent Mines history.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Unable to load the selected session."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function reloadAdminUsers(token: string) {
    const query = adminEmailFilter.trim()
      ? `?email=${encodeURIComponent(adminEmailFilter.trim())}`
      : "";
    const data = await apiRequest<AdminUser[]>(
      `/admin/users${query}`,
      {},
      token,
    );
    setAdminUsers(data);
    if (
      data.length > 0 &&
      (!selectedAdminUserId || !data.some((user) => user.id === selectedAdminUserId))
    ) {
      setSelectedAdminUserId(data[0].id);
    }
    if (data.length === 0) {
      setSelectedAdminUserId("");
    }
    return data;
  }

  async function handleLoadLedgerReport() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token valido prima di usare il report ledger admin.",
      });
      return;
    }

    setBusyAction("admin-ledger-report");
    try {
      const data = await apiRequest<AdminLedgerReport>(
        "/admin/reports/ledger",
        {},
        accessToken,
      );
      setAdminLedgerReport(data);
      setSelectedTransactionDetail(null);
      setStatus({
        kind: "info",
        text: `Report ledger admin aggiornato. ${data.recent_transactions.length} transazioni recenti e ${data.wallet_reconciliation.length} righe di riconciliazione.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento report ledger non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadAdminLedgerTransactions() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di usare lo storico ledger.",
      });
      return;
    }

    setBusyAction("admin-ledger-transactions");
    try {
      const data = await apiRequest<LedgerTransaction[]>(
        "/ledger/transactions",
        {},
        accessToken,
      );
      setAdminLedgerTransactions(data);
      setStatus({
        kind: "info",
        text: `Storico ledger admin aggiornato. ${data.length} transazioni recenti caricate.`,
      });
    } catch (error) {
      setAdminLedgerTransactions([]);
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento storico ledger non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRefreshFairnessCurrent() {
    setBusyAction("admin-fairness-current");
    try {
      const data = await apiRequest<FairnessCurrentConfig>(
        "/games/mines/fairness/current",
      );
      setAdminFairnessCurrent(data);
      setStatus({
        kind: "info",
        text: "Configurazione fairness corrente riallineata.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento fairness current non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRotateFairness() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin per ruotare il seed fairness.",
      });
      return;
    }

    setBusyAction("admin-fairness-rotate");
    try {
      const data = await apiRequest<FairnessRotateResponse>(
        "/games/mines/fairness/rotate",
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
          },
        },
        accessToken,
      );
      const currentData = await apiRequest<FairnessCurrentConfig>(
        "/games/mines/fairness/current",
      );
      setAdminFairnessCurrent(currentData);
      setStatus({
        kind: "success",
        text: `Rotate fairness completata. Nuovo seed hash attivo: ${truncateValue(data.active_server_seed_hash, 18)}.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Rotate fairness non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleVerifyFairness(sessionId?: string) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin per verificare una sessione Mines.",
      });
      return;
    }
    const effectiveSessionId = sessionId?.trim() || verifySessionId.trim();
    if (!effectiveSessionId) {
      setStatus({
        kind: "error",
        text: "Inserisci un game session id prima di lanciare la verifica fairness.",
      });
      return;
    }

    setBusyAction("admin-fairness-verify");
    try {
      const data = await apiRequest<FairnessVerifyResult>(
        `/games/mines/verify?session_id=${encodeURIComponent(effectiveSessionId)}`,
        {},
        accessToken,
      );
      if (sessionId) {
        setVerifySessionId(effectiveSessionId);
      }
      setFairnessVerifyResult(data);
      setStatus({
        kind: data.verified ? "success" : "error",
        text: data.verified
          ? `Verifica fairness positiva per la sessione ${shortId(data.game_session_id)}.`
          : `Verifica fairness negativa per la sessione ${shortId(data.game_session_id)}.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Verifica fairness non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadAdminSessionSnapshot() {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin per caricare una sessione Mines.",
      });
      return;
    }
    if (!verifySessionId.trim()) {
      setStatus({
        kind: "error",
        text: "Inserisci un game session id prima di caricare la sessione.",
      });
      return;
    }

    setBusyAction("admin-session-snapshot");
    try {
      const data = await apiRequest<SessionSnapshot>(
        `/games/mines/session/${encodeURIComponent(verifySessionId.trim())}`,
        {},
        accessToken,
      );
      setAdminSessionSnapshot(data);
      setStatus({
        kind: "info",
        text: `Snapshot sessione ${shortId(data.game_session_id)} caricato dal backend.`,
      });
    } catch (error) {
      setAdminSessionSnapshot(null);
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento sessione Mines non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCreateBonusGrant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di creare un bonus grant.",
      });
      return;
    }
    if (!selectedAdminUserId) {
      setStatus({
        kind: "error",
        text: "Seleziona prima un utente target dal pannello admin.",
      });
      return;
    }
    if (!isValidAmount(bonusAmount.trim())) {
      setStatus({
        kind: "error",
        text: "Bonus amount non valido. Usa un numero positivo con punto decimale.",
      });
      return;
    }
    if (!bonusReason.trim()) {
      setStatus({
        kind: "error",
        text: "Il reason del bonus grant e' obbligatorio.",
      });
      return;
    }

    setBusyAction("admin-bonus-grant");
    try {
      const data = await apiRequest<AdminActionResponse>(
        `/admin/users/${selectedAdminUserId}/bonus-grants`,
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
          },
          body: JSON.stringify({
            amount: bonusAmount.trim(),
            reason: bonusReason.trim(),
          }),
        },
        accessToken,
      );
      setAdminLastAction({
        label: "bonus_grant",
        result: data,
      });
      setAdjustmentWalletType("bonus");
      const [, reportData] = await Promise.all([
        reloadAdminUsers(accessToken),
        apiRequest<AdminLedgerReport>("/admin/reports/ledger", {}, accessToken),
      ]);
      setAdminLedgerReport(reportData);
      setSelectedTransactionDetail(null);
      if (currentEmail && selectedAdminUser?.email === currentEmail) {
        await refreshAuthenticatedState({
          token: accessToken,
          sessionId: currentSession?.game_session_id ?? null,
        });
      }
      setStatus({
        kind: "success",
        text: `Bonus grant registrato su ${selectedAdminUser?.email ?? shortId(selectedAdminUserId)}. Wallet after: ${data.wallet_balance_after} CHIP.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Bonus grant non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCreateAdjustment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di creare un adjustment.",
      });
      return;
    }
    if (!selectedAdminUserId) {
      setStatus({
        kind: "error",
        text: "Seleziona prima un utente target dal pannello admin.",
      });
      return;
    }
    if (!isValidAmount(adjustmentAmount.trim())) {
      setStatus({
        kind: "error",
        text: "Adjustment amount non valido. Usa un numero positivo con punto decimale.",
      });
      return;
    }
    if (!adjustmentReason.trim()) {
      setStatus({
        kind: "error",
        text: "Il reason dell'adjustment e' obbligatorio.",
      });
      return;
    }

    setBusyAction("admin-adjustment");
    try {
      const data = await apiRequest<AdminActionResponse>(
        `/admin/users/${selectedAdminUserId}/adjustments`,
        {
          method: "POST",
          headers: {
            "Idempotency-Key": window.crypto.randomUUID(),
          },
          body: JSON.stringify({
            wallet_type: adjustmentWalletType,
            direction: adjustmentDirection,
            amount: adjustmentAmount.trim(),
            reason: adjustmentReason.trim(),
          }),
        },
        accessToken,
      );
      setAdminLastAction({
        label: "admin_adjustment",
        result: data,
      });
      const [, reportData] = await Promise.all([
        reloadAdminUsers(accessToken),
        apiRequest<AdminLedgerReport>("/admin/reports/ledger", {}, accessToken),
      ]);
      setAdminLedgerReport(reportData);
      setSelectedTransactionDetail(null);
      if (currentEmail && selectedAdminUser?.email === currentEmail) {
        await refreshAuthenticatedState({
          token: accessToken,
          sessionId: currentSession?.game_session_id ?? null,
        });
      }
      setStatus({
        kind: "success",
        text: `Adjustment ${adjustmentDirection} registrato su ${selectedAdminUser?.email ?? shortId(selectedAdminUserId)}. Wallet after: ${data.wallet_balance_after} CHIP.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Adjustment admin non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRequestPasswordReset() {
    if (!resetEmail.trim()) {
      setStatus({
        kind: "error",
        text: "Enter the email of the account you want to recover first.",
      });
      return;
    }

    setBusyAction("password-forgot");
    try {
      const data = await apiRequest<{
        request_accepted: boolean;
        reset_token?: string | null;
      }>("/auth/password/forgot", {
        method: "POST",
        body: JSON.stringify({
          email: resetEmail.trim(),
        }),
      });

      if (data.reset_token) {
        setResetToken(data.reset_token);
      }
      setLoginEmail(resetEmail.trim().toLowerCase());
      setStatus({
        kind: "success",
        text: data.reset_token
          ? "A reset token was issued by the local backend. You can now choose a new password."
          : "Password reset request accepted. No token is exposed for this account or environment.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Password reset request failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCompletePasswordReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!resetToken.trim()) {
      setStatus({
        kind: "error",
        text: "Enter the reset token returned by the backend first.",
      });
      return;
    }
    if (resetNewPassword.trim().length < 8) {
      setStatus({
        kind: "error",
        text: "The new password must contain at least 8 characters.",
      });
      return;
    }

    setBusyAction("password-reset");
    try {
      await apiRequest<{ password_reset: boolean }>("/auth/password/reset", {
        method: "POST",
        body: JSON.stringify({
          token: resetToken.trim(),
          new_password: resetNewPassword.trim(),
        }),
      });
      setLoginEmail(resetEmail.trim().toLowerCase() || loginEmail);
      setLoginPassword(resetNewPassword.trim());
      setResetNewPassword("");
      setStatus({
        kind: "success",
        text: "Password updated. You can sign in right away with the new credentials.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Password reset failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleSuspendSelectedUser(targetUserId?: string) {
    const effectiveTargetUserId = targetUserId ?? selectedAdminUserId;
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di sospendere un account.",
      });
      return;
    }
    if (!effectiveTargetUserId) {
      setStatus({
        kind: "error",
        text: "Seleziona prima un utente target dal pannello admin.",
      });
      return;
    }

    setBusyAction("admin-suspend");
    try {
      const data = await apiRequest<AdminUser>(
        `/admin/users/${effectiveTargetUserId}/suspend`,
        {
          method: "POST",
        },
        accessToken,
      );
      const isCurrentUser = currentEmail && data.email === currentEmail;
      if (isCurrentUser) {
        clearAuthState();
        setStatus({
          kind: "success",
          text: `Account ${data.email} sospeso. La sessione admin locale e' stata chiusa.`,
        });
        return;
      }

      await reloadAdminUsers(accessToken);
      setSelectedAdminUserId(effectiveTargetUserId);
      setStatus({
        kind: "success",
        text: `Account ${data.email} sospeso correttamente dal backoffice.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Sospensione utente non riuscita."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleStartSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "You need to sign in before launching a round.",
      });
      return;
    }
    if (!runtimeConfig) {
      setStatus({
        kind: "error",
        text: "The official Mines runtime is still loading. Please wait a moment and try again.",
      });
      return;
    }

    const supportedGridSizes = getGridSizes(runtimeConfig);
    if (!supportedGridSizes.includes(selectedGridSize)) {
      setStatus({
        kind: "error",
        text: "The selected grid size is not supported by the official runtime.",
      });
      return;
    }

    const supportedMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!supportedMineOptions.includes(selectedMineCount)) {
      setStatus({
        kind: "error",
        text: "The selected mine count is not supported for this grid.",
      });
      return;
    }

    const normalizedBetAmount = betAmount.trim();
    if (!isValidAmount(normalizedBetAmount)) {
      setStatus({
        kind: "error",
        text: "Invalid bet amount. Use a positive number with a decimal point, for example 5.000000.",
      });
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
            bet_amount: normalizedBetAmount,
            wallet_type: walletType,
          }),
        },
        accessToken,
      );

      setHighlightedMineCell(null);
      await refreshAuthenticatedState({
        token: accessToken,
        sessionId: startData.game_session_id,
      });
      setStatus({
        kind: "success",
        text: `Round launched. Session ${shortId(startData.game_session_id)} is active and the bet was recorded in the ledger.`,
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
    if (!accessToken || !currentSession) {
      return;
    }

    setBusyAction(`reveal-${cellIndex}`);

    try {
      const revealData = await apiRequest<{
        game_session_id: string;
        status: string;
        result: "safe" | "mine";
        safe_reveals_count: number;
        multiplier_current?: string;
        potential_payout?: string;
      }>(
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
      await loadSession(accessToken, currentSession.game_session_id, false);
      setStatus({
        kind: revealData.result === "safe" ? "success" : "error",
        text:
          revealData.result === "safe"
            ? `Safe reveal completed. Potential payout moved to ${revealData.potential_payout ?? currentSession.potential_payout} CHIP.`
            : "You hit a mine. The backend closed the session in loss.",
      });
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
    if (!accessToken || !currentSession) {
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
          },
          body: JSON.stringify({
            game_session_id: currentSession.game_session_id,
          }),
        },
        accessToken,
      );

      await refreshAuthenticatedState({
        token: accessToken,
        sessionId: currentSession.game_session_id,
      });
      setHighlightedMineCell(null);
      setStatus({
        kind: "success",
        text: `Cash out completed. Payout ${cashoutData.payout_amount} CHIP was recorded and the wallet snapshot is updated.`,
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

  function prepareReplayFromCurrentSession() {
    if (!currentSession) {
      return;
    }

    setSelectedGridSize(currentSession.grid_size);
    setSelectedMineCount(currentSession.mine_count);
    setBetAmount(currentSession.bet_amount);
    setWalletType(currentSession.wallet_type);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    setStatus({
      kind: "info",
      text: "The previous setup has been copied back into the launch panel. You can replay the round with the same configuration.",
    });
  }

  function handleLogout() {
    clearAuthState();
    setStatus({
      kind: "info",
      text: "Local session closed. Your data stays on the backend and you can sign in again at any time.",
    });
  }

  function clearCurrentSessionSnapshot() {
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    setStatus({
      kind: "info",
      text: "Local session snapshot cleared. You can launch a new round or reload another session.",
    });
  }

  function clearAuthState() {
    setAccessToken("");
    setCurrentEmail("");
    setWallets([]);
    setSelectedWalletDetail(null);
    setTransactions([]);
    setSessionHistory([]);
    setSelectedTransactionDetail(null);
    setAdminLedgerTransactions([]);
    setAdminSessionSnapshot(null);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    setAdminUsers([]);
    setSelectedAdminUserId("");
    setAdminLedgerReport(null);
    setFairnessVerifyResult(null);
    setAdminLastAction(null);
    window.localStorage.removeItem(STORAGE_KEYS.accessToken);
    window.localStorage.removeItem(STORAGE_KEYS.email);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
  }

  return (
    <main className="page-shell">
      {!isAdminArea ? (
        <section className="product-topbar">
          <div>
            <p className="eyebrow">CasinoKing</p>
            <h2>Private Demo Casino</h2>
          </div>
          <div className="product-topbar-nav">
            <Link
              className={playerView === "lobby" ? "button" : "button-secondary"}
              href="/"
            >
              Lobby
            </Link>
            <Link
              className={playerView === "mines" ? "button" : "button-secondary"}
              href="/mines"
            >
              Mines
            </Link>
            <Link
              className={playerView === "account" ? "button" : "button-secondary"}
              href="/account"
            >
              Account
            </Link>
          </div>
          <div className="product-topbar-status">
            {currentSession?.status === "active" ? (
              <Link className="status-badge success" href="/mines">
                Active run {shortId(currentSession.game_session_id)}
              </Link>
            ) : null}
            <span className={`status-badge ${accessToken ? "success" : "info"}`}>
              {accessToken ? currentEmail || "Player signed in" : "Guest player"}
            </span>
          </div>
        </section>
      ) : null}

      <section className={`hero ${!isAdminArea ? "player-hero" : ""}`}>
        <div className="hero-grid">
          <div>
            <p className="eyebrow">CasinoKing</p>
            <h1>
              {isAdminArea
                ? "Local admin backoffice"
                : playerView === "mines"
                  ? "Mines, presented like a real game surface"
                  : playerView === "account"
                    ? "Player account, wallets, and session history"
                    : "A real private casino flow, not just a demo console"}
            </h1>
            <p className="lead">
              {isAdminArea
                ? "This area is dedicated to admin operations, user controls, ledger reporting, and internal fairness tools."
                : playerView === "mines"
                  ? "Launch a round from a dedicated game route, track the live state, and cash out from a server-authoritative Mines surface."
                  : playerView === "account"
                    ? "Review balances, recent wallet movements, and your current game state from a dedicated player account area."
                    : "Enter through a focused player lobby, open Mines from a dedicated game card, and keep your account flow separate from the backoffice."}
            </p>
            <div className="hero-meta">
              {isAdminArea ? (
                <>
                  <span className="meta-pill">Backoffice Admin</span>
                  <span className="meta-pill">Ledger reporting</span>
                  <span className="meta-pill">Fairness controls</span>
                </>
              ) : (
                <>
                  <span className="meta-pill">Private access demo</span>
                  <span className="meta-pill">Cash + Bonus wallets</span>
                  <span className="meta-pill">Mines first release</span>
                </>
              )}
            </div>
            {isAdminArea ? (
              <div className="route-switch">
                <Link className="button-secondary" href="/">
                  Player Lobby
                </Link>
                <Link className="button" href="/admin">
                  Admin
                </Link>
              </div>
            ) : showPlayerLobby ? (
              <div className="route-switch">
                <Link className="button" href="/mines">
                  Open Mines
                </Link>
                <Link className="button-secondary" href="/account">
                  Open account
                </Link>
                <Link className="button-ghost" href="/admin">
                  Admin backoffice
                </Link>
              </div>
            ) : null}
          </div>
          <aside className="hero-note">
            <p>
              {isAdminArea
                ? "Admin actions remain server-side and require an authenticated admin account. Financial logic never runs in the client."
                : playerView === "lobby"
                  ? "The player path is now split into lobby, game, and account. Admin is kept outside the primary player journey."
                  : playerView === "mines"
                    ? "The frontend never decides outcome, board, or payout. Sensitive game state still comes from the backend session snapshot."
                    : "Wallet balances are snapshots derived from the ledger, and the account area stays owner-only through the backend APIs."}
            </p>
          </aside>
        </div>

        {status ? (
          <div className="status-line">
            <span className={`status-badge ${status.kind}`}>{status.text}</span>
          </div>
        ) : null}
      </section>

      <div className="dashboard-grid">
        <div className="stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>
                  {isAdminArea
                    ? "Accesso admin"
                    : playerView === "mines"
                      ? "Player session"
                      : "Access & account"}
                </h2>
                <p>
                  {isAdminArea
                    ? "Login dedicato al backoffice admin. Nessuna registrazione player o flusso Mines e' esposto qui."
                    : playerView === "mines"
                      ? "Keep the game route focused: sign in here, then continue inside the dedicated Mines surface."
                    : "Player sign up, sign in, and password reset stay connected to the backend while the lobby, game, and account routes remain separate."}
                </p>
              </div>
              {accessToken ? (
                <span className="status-badge success">
                  {isAdminArea ? "Sessione autenticata" : "Player autenticato"}
                </span>
              ) : (
                <span className="status-badge info">Guest</span>
              )}
            </div>

            <div className="auth-forms">
              {showPlayerRegistration ? (
                <form className="form-card" onSubmit={handleRegister}>
                  <h3>Registration</h3>
                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="register-email">Email</label>
                      <input
                        id="register-email"
                        type="email"
                        autoComplete="email"
                        value={registerEmail}
                        onChange={(event) => setRegisterEmail(event.target.value)}
                        placeholder="player@example.com"
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="register-password">Password</label>
                      <input
                        id="register-password"
                        type="password"
                        autoComplete="new-password"
                        value={registerPassword}
                        onChange={(event) => setRegisterPassword(event.target.value)}
                        placeholder="at least 8 characters"
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="site-access-password">
                        Site access password
                      </label>
                      <input
                        id="site-access-password"
                        type="password"
                        value={siteAccessPassword}
                        onChange={(event) =>
                          setSiteAccessPassword(event.target.value)
                        }
                        placeholder="required for private access"
                      />
                      <span className="helper">
                        This private demo uses a site-wide password before a new
                        player account can be created.
                      </span>
                    </div>
                  </div>
                  <div className="actions">
                    <button
                      className="button"
                      type="submit"
                      disabled={busyAction !== null}
                    >
                      {busyAction === "register"
                        ? "Creating player..."
                        : "Create player"}
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={busyAction !== null || !siteAccessPassword}
                      onClick={handleVerifySiteAccess}
                    >
                      {busyAction === "site-access"
                        ? "Checking..."
                        : "Check site access"}
                    </button>
                  </div>
                </form>
              ) : null}

              <form className="form-card" onSubmit={handleLogin}>
                <h3>{isAdminArea ? "Login admin" : "Login"}</h3>
                <div className="field-grid">
                  <div className="field">
                    <label htmlFor="login-email">Email</label>
                    <input
                      id="login-email"
                      type="email"
                      autoComplete="email"
                      value={loginEmail}
                      onChange={(event) => setLoginEmail(event.target.value)}
                      placeholder="player@example.com"
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="login-password">Password</label>
                    <input
                      id="login-password"
                      type="password"
                      autoComplete="current-password"
                      value={loginPassword}
                      onChange={(event) => setLoginPassword(event.target.value)}
                    />
                  </div>
                </div>
                <div className="actions">
                  <button
                    className="button"
                    type="submit"
                    disabled={busyAction !== null}
                  >
                    {busyAction === "login" ? "Signing in..." : "Sign in"}
                  </button>
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={!accessToken}
                    onClick={handleLogout}
                  >
                    Sign out
                  </button>
                </div>
                {currentEmail ? (
                  <p className="helper">Signed in as {currentEmail}</p>
                ) : playerView === "mines" ? (
                  <p className="helper">
                    Need a new player account? Return to the <Link href="/">lobby</Link>{" "}
                    to register and unlock private access.
                  </p>
                ) : null}
              </form>

              {showPlayerRegistration ? (
                <form className="form-card" onSubmit={handleCompletePasswordReset}>
                  <h3>Password reset</h3>
                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="reset-email">Account email</label>
                      <input
                        id="reset-email"
                        type="email"
                        autoComplete="email"
                        value={resetEmail}
                        onChange={(event) => setResetEmail(event.target.value)}
                        placeholder="player@example.com"
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="reset-token">Reset token</label>
                      <input
                        id="reset-token"
                        value={resetToken}
                        onChange={(event) => setResetToken(event.target.value)}
                        placeholder="backend-issued reset token"
                      />
                      <span className="helper">
                        In local mode the backend returns the token directly to
                        support this reset flow.
                      </span>
                    </div>
                    <div className="field">
                      <label htmlFor="reset-new-password">New password</label>
                      <input
                        id="reset-new-password"
                        type="password"
                        autoComplete="new-password"
                        value={resetNewPassword}
                        onChange={(event) => setResetNewPassword(event.target.value)}
                        placeholder="at least 8 characters"
                      />
                    </div>
                  </div>
                  <div className="actions">
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={busyAction !== null || !resetEmail.trim()}
                      onClick={() => void handleRequestPasswordReset()}
                    >
                      {busyAction === "password-forgot"
                        ? "Requesting..."
                        : "Request reset token"}
                    </button>
                    <button
                      className="button"
                      type="submit"
                      disabled={busyAction !== null}
                    >
                      {busyAction === "password-reset"
                        ? "Updating..."
                        : "Update password"}
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          </section>

          {showPlayerLobby ? (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Player lobby</h2>
                  <p>
                    Launch the first game from a dedicated card, keep your account
                    route separate, and return to an active run when one is already
                    open.
                  </p>
                </div>
                <span className="status-badge info">Private access</span>
              </div>

              <div className="lobby-grid">
                <article className="lobby-card lobby-card-primary">
                  <p className="eyebrow">Game launch</p>
                  <h3>Mines</h3>
                  <p className="helper">
                    Instant game, server-authoritative, powered by the official
                    runtime configuration.
                  </p>
                  <div className="lobby-chip-row">
                    <span className="meta-pill">Grid sizes {gridSizes.join(", ")}</span>
                    <span className="meta-pill">
                      {runtimeLoaded && runtimeConfig
                        ? runtimeConfig.fairness_version
                        : "Runtime loading"}
                    </span>
                  </div>
                  <div className="actions">
                    <Link className="button" href="/mines">
                      {currentSession?.status === "active"
                        ? "Resume active run"
                        : "Open Mines"}
                    </Link>
                    <Link className="button-secondary" href="/account">
                      View account
                    </Link>
                  </div>
                </article>

                <article className="lobby-card">
                  <p className="eyebrow">Account snapshot</p>
                  <h3>
                    {accessToken ? "Player account ready" : "Sign in to unlock play"}
                  </h3>
                  <div className="lobby-stat-list">
                    <div className="list-row">
                      <span className="list-muted">Cash</span>
                      <span className="list-strong">
                        {cashWallet ? `${cashWallet.balance_snapshot} CHIP` : "Locked"}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Bonus</span>
                      <span className="list-strong">
                        {bonusWallet ? `${bonusWallet.balance_snapshot} CHIP` : "Locked"}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Recent wallet moves</span>
                      <span className="list-strong">{transactions.length}</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Session state</span>
                      <span className="list-strong">
                        {currentSession ? currentSession.status : "No active run"}
                      </span>
                    </div>
                  </div>
                  {currentSession ? (
                    <p className="helper">
                      Session {shortId(currentSession.game_session_id)} is ready to be
                      reopened from the dedicated game route.
                    </p>
                  ) : (
                    <p className="helper">
                      Once you sign in, your wallets, movements, and game history
                      live in the separate account route.
                    </p>
                  )}
                </article>
              </div>
            </section>
          ) : null}

          {showWalletAndLedger ? (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Wallets & activity</h2>
                  <p>
                    Review the player balances derived from the ledger and inspect
                    the latest owner-only wallet activity.
                  </p>
                </div>
                <div className="inline-actions">
                  <button
                    className="button-secondary"
                    type="button"
                    onClick={handleRefreshAccount}
                    disabled={!accessToken || busyAction !== null}
                  >
                    {busyAction === "refresh" ? "Refreshing..." : "Refresh account"}
                  </button>
                </div>
              </div>

              {accessToken ? (
                  <div className="account-grid">
                  <article className="session-card account-overview-card">
                    <div className="panel-header compact">
                      <div>
                        <h3>Account recap</h3>
                        <p>
                          A player-facing summary of wallets, rounds, and the next
                          useful action between account review and Mines play.
                        </p>
                      </div>
                      <span className="status-badge info">
                        {accountOverview.totalRounds} rounds
                      </span>
                    </div>

                    <div className="account-overview-grid">
                      <article className="overview-tile">
                        <span className="list-muted">Cash available</span>
                        <strong>
                          {cashWallet
                            ? `${cashWallet.balance_snapshot} ${cashWallet.currency_code}`
                            : "Locked"}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Bonus available</span>
                        <strong>
                          {bonusWallet
                            ? `${bonusWallet.balance_snapshot} ${bonusWallet.currency_code}`
                            : "Locked"}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Won / lost</span>
                        <strong>
                          {accountOverview.wins} / {accountOverview.losses}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Still active</span>
                        <strong>{accountOverview.activeRounds}</strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Total staked</span>
                        <strong>{accountOverview.totalStaked} CHIP</strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Total returned</span>
                        <strong>{accountOverview.totalReturned} CHIP</strong>
                      </article>
                    </div>

                    <div className="account-recap-strip">
                      <span className="meta-pill">
                        Wallet movements {accountOverview.recentWalletMoves}
                      </span>
                      <span className="meta-pill">
                        {accountOverview.lastRoundAt
                          ? `Last round ${formatDateTime(accountOverview.lastRoundAt)}`
                          : "No rounds yet"}
                      </span>
                      <span className="meta-pill">
                        {currentSession?.status === "active"
                          ? `Resume ${shortId(currentSession.game_session_id)}`
                          : "Ready for a new launch"}
                      </span>
                    </div>

                    <div className="actions">
                      <Link className="button" href="/mines">
                        {currentSession?.status === "active"
                          ? "Resume Mines"
                          : "Open Mines"}
                      </Link>
                      <button
                        className="button-secondary"
                        type="button"
                        onClick={handleRefreshAccount}
                        disabled={!accessToken || busyAction !== null}
                      >
                        {busyAction === "refresh"
                          ? "Refreshing..."
                          : "Refresh recap"}
                      </button>
                    </div>
                  </article>

                  <div className="wallet-grid">
                    {wallets.map((wallet) => (
                      <article className="wallet-card" key={wallet.wallet_type}>
                        <h3>{wallet.wallet_type.toUpperCase()} wallet</h3>
                        <div className="list-row">
                          <span className="list-muted">Balance</span>
                          <span className="list-strong">
                            {wallet.balance_snapshot} {wallet.currency_code}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Status</span>
                          <span className="list-strong">{wallet.status}</span>
                        </div>
                      </article>
                    ))}
                  </div>

                  <div className="transaction-list">
                    {transactions.slice(0, 8).map((transaction) => (
                      <article className="transaction-card" key={transaction.id}>
                        <div className="list-row">
                          <h3>{transaction.transaction_type}</h3>
                          <span className="mono">{shortId(transaction.id)}</span>
                        </div>
                        <p className="helper">
                          {formatDateTime(transaction.created_at)} ·{" "}
                          {transaction.reference_type ?? "n/a"}
                        </p>
                        <p className="helper">
                          reference{" "}
                          <span className="mono">
                            {transaction.reference_id
                              ? shortId(transaction.reference_id)
                              : "n/a"}
                          </span>
                        </p>
                        <div className="actions">
                          <button
                            className="button-secondary"
                            type="button"
                            disabled={!accessToken || busyAction !== null}
                            onClick={() =>
                              void handleLoadTransactionDetail(transaction.id)
                            }
                          >
                            {busyAction === `ledger-detail-${transaction.id}`
                              ? "Loading..."
                              : "Open detail"}
                          </button>
                        </div>
                      </article>
                    ))}
                    {transactions.length === 0 ? (
                      <p className="empty-state">No wallet activity available yet.</p>
                    ) : null}
                  </div>

                  <article className="session-card">
                    <h3>Current game state</h3>
                    {currentSession ? (
                      <>
                        <div className="list-row">
                          <span className="list-muted">Session</span>
                          <span className="mono">
                            {shortId(currentSession.game_session_id)}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Status</span>
                          <span className="list-strong">{currentSession.status}</span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Potential payout</span>
                          <span className="list-strong">
                            {currentSession.potential_payout} CHIP
                          </span>
                        </div>
                        <div className="actions">
                          <Link className="button" href="/mines">
                            Resume in Mines
                          </Link>
                        </div>
                      </>
                    ) : (
                      <p className="empty-state">
                        No active run is stored locally right now.
                      </p>
                    )}
                  </article>

                  <article className="session-card">
                    <div className="list-row">
                      <h3>Loaded round detail</h3>
                      {currentSession ? (
                        <span
                          className={`status-inline ${sessionStatusKind(currentSession.status)}`}
                        >
                          {currentSession.status}
                        </span>
                      ) : null}
                    </div>
                    {currentSession ? (
                      <>
                        <div className="history-detail-grid">
                          <div className="list-row">
                            <span className="list-muted">Session</span>
                            <span className="mono">
                              {shortId(currentSession.game_session_id)}
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Setup</span>
                            <span className="list-strong">
                              {currentSession.grid_size} cells · {currentSession.mine_count} mines
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Stake</span>
                            <span className="list-strong">
                              {currentSession.bet_amount} CHIP · {currentSession.wallet_type}
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Live multiplier</span>
                            <span className="list-strong">
                              {currentSession.multiplier_current}x
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Reveals</span>
                            <span className="list-strong">
                              {currentSession.safe_reveals_count} safe · {currentSession.revealed_cells.length} opened
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Outcome snapshot</span>
                            <span className="list-strong">
                              {describeSessionOutcome(currentSession)}
                            </span>
                          </div>
                        </div>
                        <p className="helper">
                          Started {formatDateTime(currentSession.created_at)}
                          {currentSession.closed_at
                            ? ` · Closed ${formatDateTime(currentSession.closed_at)}`
                            : " · Still active in the backend"}
                        </p>
                        {currentSessionFairness ? (
                          <p className="helper">
                            Fairness {currentSessionFairness.fairness_version} · nonce{" "}
                            <span className="mono">{currentSessionFairness.nonce}</span>
                          </p>
                        ) : null}
                        <div className="actions">
                          <Link className="button" href="/mines">
                            {currentSession.status === "active"
                              ? "Resume this round in Mines"
                              : "Open Mines"}
                          </Link>
                          <button
                            className="button-secondary"
                            type="button"
                            disabled={busyAction !== null}
                            onClick={() =>
                              rememberLaunchPreset(
                                {
                                  grid_size: currentSession.grid_size,
                                  mine_count: currentSession.mine_count,
                                  bet_amount: currentSession.bet_amount,
                                  wallet_type: currentSession.wallet_type,
                                },
                                `Round ${shortId(currentSession.game_session_id)}`,
                              )
                            }
                          >
                            Replay this setup
                          </button>
                          <button
                            className="button-ghost"
                            type="button"
                            disabled={!accessToken || busyAction !== null}
                            onClick={() =>
                              void handleLoadTransactionDetail(
                                currentSession.ledger_transaction_id,
                              )
                            }
                          >
                            {busyAction ===
                            `ledger-detail-${currentSession.ledger_transaction_id}`
                              ? "Loading..."
                              : "Open start transaction"}
                          </button>
                        </div>
                      </>
                    ) : (
                      <p className="empty-state">
                        Load a round from your history or resume an active session to
                        inspect the full account-side detail here.
                      </p>
                    )}
                  </article>

                  <article className="session-card">
                    <h3>Recent Mines rounds</h3>
                    {sessionHistory.length > 0 ? (
                      <div className="history-list">
                        {sessionHistory.slice(0, 6).map((entry) => (
                          <article
                            className="history-card"
                            key={entry.game_session_id}
                          >
                            <div className="list-row">
                              <span className="mono">
                                {shortId(entry.game_session_id)}
                              </span>
                              <span
                                className={`status-inline ${sessionStatusKind(entry.status)}`}
                              >
                                {entry.status}
                              </span>
                            </div>
                            <p className="helper">
                              {entry.grid_size} cells · {entry.mine_count} mines ·{" "}
                              {entry.wallet_type} wallet
                            </p>
                            <div className="history-meta">
                              <span>Bet {entry.bet_amount} CHIP</span>
                              <span>Payout {entry.potential_payout} CHIP</span>
                              <span>Reveals {entry.safe_reveals_count}</span>
                              <span>{describeSessionOutcome(entry)}</span>
                            </div>
                            <p className="helper">
                              Started {formatDateTime(entry.created_at)}
                              {entry.closed_at
                                ? ` · Closed ${formatDateTime(entry.closed_at)}`
                                : " · Still active"}
                            </p>
                            <div className="actions">
                              <button
                                className="button-secondary"
                                type="button"
                                disabled={!accessToken || busyAction !== null}
                                onClick={() =>
                                  void handleOpenHistorySession(
                                    entry.game_session_id,
                                  )
                                }
                              >
                                {busyAction ===
                                `history-session-${entry.game_session_id}`
                                  ? "Loading..."
                                  : "Load detail"}
                              </button>
                              <button
                                className="button-ghost"
                                type="button"
                                disabled={busyAction !== null}
                                onClick={() =>
                                  rememberLaunchPreset(
                                    {
                                      grid_size: entry.grid_size,
                                      mine_count: entry.mine_count,
                                      bet_amount: entry.bet_amount,
                                      wallet_type: entry.wallet_type,
                                    },
                                    `Round ${shortId(entry.game_session_id)}`,
                                  )
                                }
                              >
                                Replay setup
                              </button>
                              <Link className="button-ghost" href="/mines">
                                Open Mines
                              </Link>
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-state">
                        No Mines rounds have been recorded for this player yet.
                      </p>
                    )}
                  </article>

                  <article className="session-card">
                    <h3>Wallet detail</h3>
                    {selectedWalletDetail ? (
                      <>
                        <div className="list-row">
                          <span className="list-muted">Wallet type</span>
                          <span className="list-strong">
                            {selectedWalletDetail.wallet_type}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Balance</span>
                          <span className="list-strong">
                            {selectedWalletDetail.balance_snapshot}{" "}
                            {selectedWalletDetail.currency_code}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Status</span>
                          <span className="list-strong">
                            {selectedWalletDetail.status}
                          </span>
                        </div>
                        <div className="actions">
                          <button
                            className="button-ghost"
                            type="button"
                            disabled={!accessToken || busyAction !== null}
                            onClick={() =>
                              void handleLoadWalletDetail(selectedWalletDetail.wallet_type)
                            }
                          >
                            {busyAction ===
                            `wallet-detail-${selectedWalletDetail.wallet_type}`
                              ? "Loading..."
                              : "Reload detail"}
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <p className="empty-state">
                          Select a wallet to inspect the latest balance snapshot.
                        </p>
                        <div className="actions">
                          {wallets.map((wallet) => (
                            <button
                              key={wallet.wallet_type}
                              className="button-secondary"
                              type="button"
                              disabled={!accessToken || busyAction !== null}
                              onClick={() => void handleLoadWalletDetail(wallet.wallet_type)}
                            >
                              {busyAction === `wallet-detail-${wallet.wallet_type}`
                                ? `Loading ${wallet.wallet_type}...`
                                : `${wallet.wallet_type} detail`}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </article>

                  <article className="session-card">
                    <h3>Transaction detail</h3>
                    {selectedTransactionDetail ? (
                      <>
                        <div className="list-row">
                          <span className="list-muted">Type</span>
                          <span className="list-strong">
                            {selectedTransactionDetail.transaction_type}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Reference</span>
                          <span className="mono">
                            {selectedTransactionDetail.reference_type ?? "n/a"}{" "}
                            {selectedTransactionDetail.reference_id
                              ? shortId(selectedTransactionDetail.reference_id)
                              : ""}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Entry count</span>
                          <span className="list-strong">
                            {selectedTransactionDetail.entries.length}
                          </span>
                        </div>
                        <div className="admin-list">
                          {selectedTransactionDetail.entries.map((entry) => (
                            <article className="admin-list-card" key={entry.id}>
                              <div className="list-row">
                                <span className="mono">
                                  {entry.ledger_account_code}
                                </span>
                                <span
                                  className={
                                    entry.entry_side === "credit"
                                      ? "status-inline success"
                                      : "status-inline info"
                                  }
                                >
                                  {entry.entry_side}
                                </span>
                              </div>
                              <p className="helper">
                                {entry.amount} CHIP ·{" "}
                                {formatDateTime(entry.created_at)}
                              </p>
                            </article>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="empty-state">
                        Select a transaction to inspect the ledger entries behind it.
                      </p>
                    )}
                  </article>
                </div>
              ) : (
                <p className="empty-state">
                  Sign in to unlock wallet balances, recent account activity, and
                  ledger-backed transaction detail.
                </p>
              )}
            </section>
          ) : null}

          {showAdminPanel ? (
            <section className="panel">
            <div className="panel-header">
              <div>
                <h2>Backoffice Admin</h2>
                <p>
                  Console operativa minima per utenti, ledger report e fairness.
                  Richiede un token admin; con un token player il backend
                  risponde correttamente con <span className="mono">403</span>.
                </p>
              </div>
              <span className="status-badge info">Admin API</span>
            </div>

            <div className="stack">
              <div className="admin-surface">
                <div className="field-grid two-up">
                  <div className="field">
                    <label htmlFor="admin-email-filter">Filtro utenti</label>
                    <input
                      id="admin-email-filter"
                      value={adminEmailFilter}
                      onChange={(event) => setAdminEmailFilter(event.target.value)}
                      placeholder="email o frammento email"
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="verify-session-id">Verify session id</label>
                    <input
                      id="verify-session-id"
                      value={verifySessionId}
                      onChange={(event) => setVerifySessionId(event.target.value)}
                      placeholder="uuid sessione Mines"
                    />
                  </div>
                </div>

                <div className="actions">
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleLoadAdminUsers()}
                  >
                    {busyAction === "admin-users"
                      ? "Carico utenti..."
                      : "Carica utenti"}
                  </button>
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleLoadLedgerReport()}
                  >
                    {busyAction === "admin-ledger-report"
                      ? "Carico report..."
                      : "Report ledger"}
                  </button>
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleLoadAdminLedgerTransactions()}
                  >
                    {busyAction === "admin-ledger-transactions"
                      ? "Carico storico..."
                      : "Storico ledger"}
                  </button>
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={busyAction !== null}
                    onClick={() => void handleRefreshFairnessCurrent()}
                  >
                    {busyAction === "admin-fairness-current"
                      ? "Ricarico fairness..."
                      : "Fairness current"}
                  </button>
                  <button
                    className="button"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleRotateFairness()}
                  >
                    {busyAction === "admin-fairness-rotate"
                      ? "Rotate..."
                      : "Rotate fairness"}
                  </button>
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleVerifyFairness()}
                  >
                    {busyAction === "admin-fairness-verify"
                      ? "Verify..."
                      : "Verify session"}
                  </button>
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={!accessToken || busyAction !== null}
                    onClick={() => void handleLoadAdminSessionSnapshot()}
                  >
                    {busyAction === "admin-session-snapshot"
                      ? "Load..."
                      : "Load session"}
                  </button>
                </div>
              </div>

              <div className="admin-grid">
                <article className="admin-card">
                  <h3>Fairness attiva</h3>
                  {adminFairnessCurrent ? (
                    <>
                      <div className="list-row">
                        <span className="list-muted">Versione</span>
                        <span className="list-strong">
                          {adminFairnessCurrent.fairness_version}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Fase</span>
                        <span className="list-strong">
                          {adminFairnessCurrent.fairness_phase}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Random source</span>
                        <span className="mono">
                          {adminFairnessCurrent.random_source}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Seed hash attivo</span>
                        <span className="mono">
                          {truncateValue(
                            adminFairnessCurrent.active_server_seed_hash,
                            18,
                          )}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Attivato</span>
                        <span className="list-strong">
                          {formatDateTime(adminFairnessCurrent.seed_activated_at)}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">User verifiable</span>
                        <span className="list-strong">
                          {adminFairnessCurrent.user_verifiable ? "yes" : "no"}
                        </span>
                      </div>
                      <p className="helper">
                        Runtime file{" "}
                        <span className="mono">
                          {adminFairnessCurrent.payout_runtime_file}
                        </span>
                      </p>
                    </>
                  ) : (
                    <p className="empty-state">
                      Configurazione fairness non ancora caricata.
                    </p>
                  )}
                </article>

                <article className="admin-card">
                  <h3>Verify fairness</h3>
                  {fairnessVerifyResult ? (
                    <>
                      <div className="list-row">
                        <span className="list-muted">Sessione</span>
                        <span className="mono">
                          {shortId(fairnessVerifyResult.game_session_id)}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Esito</span>
                        <span className="list-strong">
                          {fairnessVerifyResult.verified ? "verified" : "mismatch"}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Seed hash</span>
                        <span className="list-strong">
                          {fairnessVerifyResult.server_seed_hash_match ? "ok" : "ko"}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Board hash</span>
                        <span className="list-strong">
                          {fairnessVerifyResult.board_hash_match ? "ok" : "ko"}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Mine positions</span>
                        <span className="list-strong">
                          {fairnessVerifyResult.mine_positions_match ? "ok" : "ko"}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Fairness version</span>
                        <span className="list-strong">
                          {fairnessVerifyResult.fairness_version}
                        </span>
                      </div>
                      <p className="helper">
                        Nonce <span className="mono">{fairnessVerifyResult.nonce}</span> ·
                        seed hash{" "}
                        <span className="mono">
                          {truncateValue(
                            fairnessVerifyResult.stored_server_seed_hash,
                            18,
                          )}
                        </span>
                      </p>
                      <div className="field-grid two-up">
                        <div className="runtime-card">
                          <h4>Seed hash</h4>
                          <p className="helper">
                            stored{" "}
                            <span className="mono">
                              {truncateValue(
                                fairnessVerifyResult.stored_server_seed_hash,
                                32,
                              )}
                            </span>
                          </p>
                          <p className="helper">
                            computed{" "}
                            <span className="mono">
                              {truncateValue(
                                fairnessVerifyResult.computed_server_seed_hash,
                                32,
                              )}
                            </span>
                          </p>
                        </div>
                        <div className="runtime-card">
                          <h4>Board hash</h4>
                          <p className="helper">
                            stored{" "}
                            <span className="mono">
                              {truncateValue(
                                fairnessVerifyResult.stored_board_hash,
                                32,
                              )}
                            </span>
                          </p>
                          <p className="helper">
                            computed{" "}
                            <span className="mono">
                              {truncateValue(
                                fairnessVerifyResult.computed_board_hash,
                                32,
                              )}
                            </span>
                          </p>
                        </div>
                      </div>
                      <p className="helper">
                        Mine stored{" "}
                        <span className="mono">
                          {formatMinePositions(
                            fairnessVerifyResult.stored_mine_positions,
                          )}
                        </span>
                      </p>
                      <p className="helper">
                        Mine computed{" "}
                        <span className="mono">
                          {formatMinePositions(
                            fairnessVerifyResult.computed_mine_positions,
                          )}
                        </span>
                      </p>
                    </>
                  ) : (
                    <p className="empty-state">
                      Inserisci una sessione Mines e lancia la verifica admin.
                    </p>
                  )}
                </article>
              </div>

              <article className="admin-card">
                <h3>Session snapshot</h3>
                {adminSessionSnapshot ? (
                  <>
                    <div className="list-row">
                      <span className="list-muted">Sessione</span>
                      <span className="mono">
                        {shortId(adminSessionSnapshot.game_session_id)}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Status</span>
                      <span className="list-strong">
                        {adminSessionSnapshot.status}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Bet / wallet</span>
                      <span className="mono">
                        {adminSessionSnapshot.bet_amount} CHIP ·{" "}
                        {adminSessionSnapshot.wallet_type}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Grid / mine</span>
                      <span className="mono">
                        {adminSessionSnapshot.grid_size} /{" "}
                        {adminSessionSnapshot.mine_count}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Reveals</span>
                      <span className="list-strong">
                        {adminSessionSnapshot.safe_reveals_count}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Fairness</span>
                      <span className="mono">
                        {adminSessionSnapshot.fairness_version} · nonce{" "}
                        {adminSessionSnapshot.nonce}
                      </span>
                    </div>
                    <p className="helper">
                      Created {formatDateTime(adminSessionSnapshot.created_at)}
                      {adminSessionSnapshot.closed_at
                        ? ` · closed ${formatDateTime(
                            adminSessionSnapshot.closed_at,
                          )}`
                        : " · sessione ancora aperta"}
                    </p>
                    <p className="helper">
                      Ledger tx{" "}
                      <span className="mono">
                        {shortId(adminSessionSnapshot.ledger_transaction_id)}
                      </span>
                    </p>
                    <div className="field-grid two-up">
                      <div className="runtime-card">
                        <h4>Seed hash</h4>
                        <p className="helper">
                          <span className="mono">
                            {truncateValue(
                              adminSessionSnapshot.server_seed_hash,
                              32,
                            )}
                          </span>
                        </p>
                      </div>
                      <div className="runtime-card">
                        <h4>Board hash</h4>
                        <p className="helper">
                          <span className="mono">
                            {truncateValue(adminSessionSnapshot.board_hash, 32)}
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="actions">
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={!accessToken || busyAction !== null}
                        onClick={() =>
                          void handleLoadTransactionDetail(
                            adminSessionSnapshot.ledger_transaction_id,
                          )
                        }
                      >
                        {busyAction ===
                        `ledger-detail-${adminSessionSnapshot.ledger_transaction_id}`
                          ? "Carico tx..."
                          : "Apri ledger tx"}
                      </button>
                      <button
                        className="button-ghost"
                        type="button"
                        disabled={!accessToken || busyAction !== null}
                        onClick={() =>
                          void handleVerifyFairness(adminSessionSnapshot.game_session_id)
                        }
                      >
                        {busyAction === "admin-fairness-verify"
                          ? "Verify..."
                          : "Verifica fairness"}
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="empty-state">
                    Carica una sessione Mines per vedere uno snapshot read-only.
                  </p>
                )}
              </article>

              <div className="admin-grid">
                <article className="admin-card">
                  <h3>Azioni admin</h3>
                  {selectedAdminUser ? (
                    <>
                      <p className="helper">
                        Target attuale:{" "}
                        <span className="mono">{selectedAdminUser.email}</span>
                      </p>
                      <div className="admin-action-stack">
                        <form className="admin-form" onSubmit={handleCreateBonusGrant}>
                          <h4>Bonus grant</h4>
                          <div className="field-grid two-up">
                            <div className="field">
                              <label htmlFor="bonus-amount">Amount</label>
                              <input
                                id="bonus-amount"
                                value={bonusAmount}
                                onChange={(event) => setBonusAmount(event.target.value)}
                                inputMode="decimal"
                                placeholder="10.000000"
                              />
                            </div>
                            <div className="field">
                              <label htmlFor="bonus-reason">Reason</label>
                              <input
                                id="bonus-reason"
                                value={bonusReason}
                                onChange={(event) => setBonusReason(event.target.value)}
                                placeholder="manual_bonus"
                              />
                            </div>
                          </div>
                          <div className="actions">
                            <button
                              className="button"
                              type="submit"
                              disabled={!accessToken || busyAction !== null}
                            >
                              {busyAction === "admin-bonus-grant"
                                ? "Invio bonus..."
                                : "Invia bonus"}
                            </button>
                          </div>
                        </form>

                        <form className="admin-form" onSubmit={handleCreateAdjustment}>
                          <h4>Adjustment</h4>
                          <div className="field-grid two-up">
                            <div className="field">
                              <label htmlFor="adjustment-wallet-type">Wallet</label>
                              <select
                                id="adjustment-wallet-type"
                                value={adjustmentWalletType}
                                onChange={(event) =>
                                  setAdjustmentWalletType(event.target.value)
                                }
                              >
                                <option value="cash">cash</option>
                                <option value="bonus">bonus</option>
                              </select>
                            </div>
                            <div className="field">
                              <label htmlFor="adjustment-direction">Direction</label>
                              <select
                                id="adjustment-direction"
                                value={adjustmentDirection}
                                onChange={(event) =>
                                  setAdjustmentDirection(event.target.value)
                                }
                              >
                                <option value="credit">credit</option>
                                <option value="debit">debit</option>
                              </select>
                            </div>
                            <div className="field">
                              <label htmlFor="adjustment-amount">Amount</label>
                              <input
                                id="adjustment-amount"
                                value={adjustmentAmount}
                                onChange={(event) =>
                                  setAdjustmentAmount(event.target.value)
                                }
                                inputMode="decimal"
                                placeholder="5.000000"
                              />
                            </div>
                            <div className="field">
                              <label htmlFor="adjustment-reason">Reason</label>
                              <input
                                id="adjustment-reason"
                                value={adjustmentReason}
                                onChange={(event) =>
                                  setAdjustmentReason(event.target.value)
                                }
                                placeholder="manual_adjustment"
                              />
                            </div>
                          </div>
                          <div className="actions">
                            <button
                              className="button-secondary"
                              type="submit"
                              disabled={!accessToken || busyAction !== null}
                            >
                              {busyAction === "admin-adjustment"
                                ? "Invio adjustment..."
                                : "Invia adjustment"}
                            </button>
                          </div>
                        </form>
                      </div>
                    </>
                  ) : (
                    <p className="empty-state">
                      Carica prima gli utenti admin e seleziona un target per bonus o
                      adjustment.
                    </p>
                  )}
                </article>

                <article className="admin-card">
                  <h3>Ultima azione admin</h3>
                  {adminLastAction ? (
                    <>
                      <div className="list-row">
                        <span className="list-muted">Tipo</span>
                        <span className="list-strong">{adminLastAction.label}</span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Wallet</span>
                        <span className="list-strong">
                          {adminLastAction.result.wallet_type}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Direction</span>
                        <span className="list-strong">
                          {adminLastAction.result.direction}
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Amount</span>
                        <span className="list-strong">
                          {adminLastAction.result.amount} CHIP
                        </span>
                      </div>
                      <div className="list-row">
                        <span className="list-muted">Wallet after</span>
                        <span className="list-strong">
                          {adminLastAction.result.wallet_balance_after} CHIP
                        </span>
                      </div>
                      <p className="helper">
                        tx <span className="mono">{shortId(adminLastAction.result.ledger_transaction_id)}</span>
                        {" · "}
                        action{" "}
                        <span className="mono">{shortId(adminLastAction.result.admin_action_id)}</span>
                      </p>
                    </>
                  ) : (
                    <p className="empty-state">
                      Nessun bonus grant o adjustment inviato dal frontend in questa
                      sessione locale.
                    </p>
                  )}
                </article>
              </div>

              <div className="admin-grid">
                <article className="admin-card">
                  <div className="list-row">
                    <h3>Storico ledger</h3>
                    <span className="list-muted">
                      {adminLedgerTransactions.length > 0
                        ? `${adminLedgerTransactions.length} tx`
                        : "n/a"}
                    </span>
                  </div>
                  {adminLedgerTransactions.length > 0 ? (
                    <div className="admin-list">
                      {adminLedgerTransactions.slice(0, 6).map((transaction) => (
                        <article className="admin-list-card" key={transaction.id}>
                          <div className="list-row">
                            <span className="list-strong">
                              {transaction.transaction_type}
                            </span>
                            <span className="mono">{shortId(transaction.id)}</span>
                          </div>
                          <p className="helper">
                            {formatDateTime(transaction.created_at)} ·{" "}
                            {transaction.reference_type ?? "n/a"}
                          </p>
                          <p className="helper">
                            ref{" "}
                            <span className="mono">
                              {transaction.reference_id
                                ? shortId(transaction.reference_id)
                                : "n/a"}
                            </span>{" "}
                            · key{" "}
                            {truncateValue(transaction.idempotency_key ?? "n/a", 44)}
                          </p>
                          <div className="actions">
                            <button
                              className="button-secondary"
                              type="button"
                              disabled={!accessToken || busyAction !== null}
                              onClick={() =>
                                void handleLoadTransactionDetail(transaction.id)
                              }
                            >
                              {busyAction === `ledger-detail-${transaction.id}`
                                ? "Carico..."
                                : "Dettaglio"}
                            </button>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">
                      Carica lo storico per vedere le transaction ledger recenti.
                    </p>
                  )}
                </article>

                <article className="admin-card">
                  <div className="list-row">
                    <h3>Utenti</h3>
                    <span className="list-muted">{adminUsers.length}</span>
                  </div>
                  <div className="admin-list">
                    {adminUsers.length > 0 ? (
                      adminUsers.slice(0, 8).map((user) => (
                        <article className="admin-list-card" key={user.id}>
                          <div className="list-row">
                            <span className="list-strong">{user.email}</span>
                            <span className="mono">{user.role}</span>
                          </div>
                          <p className="helper">
                            {user.status} · {formatDateTime(user.created_at)}
                          </p>
                          <div className="actions">
                            <button
                              className={
                                user.id === selectedAdminUserId
                                  ? "button"
                                  : "button-secondary"
                              }
                              type="button"
                              disabled={busyAction !== null}
                              onClick={() => setSelectedAdminUserId(user.id)}
                            >
                              {user.id === selectedAdminUserId
                                ? "Target selezionato"
                                : "Seleziona target"}
                            </button>
                            <button
                              className="button-ghost"
                              type="button"
                              disabled={
                                busyAction !== null || user.status === "suspended"
                              }
                              onClick={() => {
                                setSelectedAdminUserId(user.id);
                                void handleSuspendSelectedUser(user.id);
                              }}
                            >
                              {user.status === "suspended"
                                ? "Gia' sospeso"
                                : busyAction === "admin-suspend" &&
                                    user.id === selectedAdminUserId
                                  ? "Sospensione..."
                                  : "Sospendi utente"}
                            </button>
                          </div>
                        </article>
                      ))
                    ) : (
                      <p className="empty-state">
                        Nessun risultato ancora caricato dal backoffice.
                      </p>
                    )}
                  </div>
                </article>

                <article className="admin-card">
                  <div className="list-row">
                    <h3>Ledger report</h3>
                    <span className="list-muted">
                      {adminLedgerReport
                        ? `${adminLedgerReport.recent_transactions.length} tx`
                        : "n/a"}
                    </span>
                  </div>
                  {adminLedgerReport ? (
                    <div className="admin-list">
                      <article className="admin-list-card">
                        <div className="list-row">
                          <span className="list-muted">Transazioni recenti</span>
                          <span className="list-strong">
                            {adminLedgerReport.summary.recent_transaction_count}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Bilanciate</span>
                          <span className="list-strong">
                            {adminLedgerReport.summary.balanced_transaction_count}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Wallet monitorati</span>
                          <span className="list-strong">
                            {adminLedgerReport.summary.wallet_count}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Wallet con drift</span>
                          <span
                            className={
                              adminLedgerReport.summary.wallets_with_drift_count === 0
                                ? "status-inline success"
                                : "status-inline error"
                            }
                          >
                            {adminLedgerReport.summary.wallets_with_drift_count}
                          </span>
                        </div>
                      </article>

                      {adminLedgerReport.recent_transactions
                        .slice(0, 6)
                        .map((transaction) => (
                          <article className="admin-list-card" key={transaction.id}>
                            <div className="list-row">
                              <span className="list-strong">
                                {transaction.transaction_type}
                              </span>
                              <span className="mono">{shortId(transaction.id)}</span>
                            </div>
                            <p className="helper">
                              {transaction.user_email ?? "system"} ·{" "}
                              {formatDateTime(transaction.created_at)}
                            </p>
                            <p className="helper">
                              debit {transaction.total_debit} / credit{" "}
                              {transaction.total_credit}
                            </p>
                            <div className="actions">
                              <button
                                className={
                                  selectedTransactionDetail?.id === transaction.id
                                    ? "button"
                                    : "button-secondary"
                                }
                                type="button"
                                disabled={!accessToken || busyAction !== null}
                                onClick={() =>
                                  void handleLoadTransactionDetail(transaction.id)
                                }
                              >
                                {busyAction === `ledger-detail-${transaction.id}`
                                  ? "Carico..."
                                  : selectedTransactionDetail?.id === transaction.id
                                    ? "Selezionata"
                                    : "Dettaglio"}
                              </button>
                            </div>
                          </article>
                        ))}

                      <div className="admin-reconciliation">
                        <h4>Riconciliazione wallet</h4>
                        {adminLedgerReport.wallet_reconciliation
                          .slice(0, 8)
                          .map((row) => (
                            <div className="list-row" key={row.wallet_account_id}>
                              <span className="list-muted">
                                {row.user_email} · {row.wallet_type}
                              </span>
                              <span
                                className={
                                  row.drift === "0.000000"
                                    ? "status-inline success"
                                    : "status-inline error"
                                }
                              >
                                drift {row.drift}
                              </span>
                            </div>
                          ))}
                      </div>

                      <article className="admin-list-card">
                        <h4>Dettaglio transaction selezionata</h4>
                        {selectedTransactionDetail ? (
                          <>
                            <div className="list-row">
                              <span className="list-muted">Tipo</span>
                              <span className="list-strong">
                                {selectedTransactionDetail.transaction_type}
                              </span>
                            </div>
                            <div className="list-row">
                              <span className="list-muted">Transaction</span>
                              <span className="mono">
                                {shortId(selectedTransactionDetail.id)}
                              </span>
                            </div>
                            <div className="list-row">
                              <span className="list-muted">Entry count</span>
                              <span className="list-strong">
                                {selectedTransactionDetail.entries.length}
                              </span>
                            </div>
                            <p className="helper">
                              {formatDateTime(selectedTransactionDetail.created_at)} ·{" "}
                              {selectedTransactionDetail.reference_type ?? "n/a"}{" "}
                              {selectedTransactionDetail.reference_id
                                ? shortId(selectedTransactionDetail.reference_id)
                                : ""}
                            </p>
                            <p className="mono">
                              key:{" "}
                              {truncateValue(
                                selectedTransactionDetail.idempotency_key ?? "n/a",
                                44,
                              )}
                            </p>
                            <div className="admin-list">
                              {selectedTransactionDetail.entries.map((entry) => (
                                <article className="admin-list-card" key={entry.id}>
                                  <div className="list-row">
                                    <span className="mono">
                                      {entry.ledger_account_code}
                                    </span>
                                    <span
                                      className={
                                        entry.entry_side === "credit"
                                          ? "status-inline success"
                                          : "status-inline info"
                                      }
                                    >
                                      {entry.entry_side}
                                    </span>
                                  </div>
                                  <p className="helper">
                                    {entry.amount} CHIP ·{" "}
                                    {formatDateTime(entry.created_at)}
                                  </p>
                                </article>
                              ))}
                            </div>
                          </>
                        ) : (
                          <p className="empty-state">
                            Seleziona una transaction dal report per vedere posting ed
                            entry del ledger.
                          </p>
                        )}
                      </article>
                    </div>
                  ) : (
                    <p className="empty-state">
                      Il report ledger admin comparira' qui dopo il caricamento.
                    </p>
                  )}
                </article>
              </div>
            </div>
            </section>
          ) : null}
        </div>

        {showMinesPanel ? (
        <div className="stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>Mines</h2>
                <p>
                  Launch, reveal, cash out, and recover the current run from a
                  dedicated game route backed by the official runtime config.
                </p>
              </div>
              {currentSession ? (
                <span className={`status-badge ${sessionStatusKind(currentSession.status)}`}>
                  Session {currentSession.status}
                </span>
              ) : (
                <span className="status-badge info">No active session</span>
              )}
            </div>

            <div className="mines-grid">
              <div className="stack">
                <form className="session-actions" onSubmit={handleStartSession}>
                <h3>Launch a new round</h3>
                  <p className="helper">
                    Pick a supported setup, choose the wallet source, and let the
                    backend open a new server-authoritative session.
                  </p>
                  <div className="field-grid two-up">
                    <div className="field">
                      <label htmlFor="grid-size">Grid size</label>
                      <select
                        id="grid-size"
                        value={selectedGridSize}
                        onChange={(event) =>
                          setSelectedGridSize(Number(event.target.value))
                        }
                        disabled={busyAction !== null || !runtimeLoaded}
                      >
                        {gridSizes.map((gridSize) => (
                          <option key={gridSize} value={gridSize}>
                            {gridSize} cells
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="field">
                      <label htmlFor="mine-count">Mine</label>
                      <select
                        id="mine-count"
                        value={selectedMineCount}
                        onChange={(event) =>
                          setSelectedMineCount(Number(event.target.value))
                        }
                        disabled={busyAction !== null || !runtimeLoaded}
                      >
                        {mineOptions.map((mineCount) => (
                          <option key={mineCount} value={mineCount}>
                            {mineCount}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="field">
                      <label htmlFor="bet-amount">Bet amount</label>
                      <input
                        id="bet-amount"
                        value={betAmount}
                        onChange={(event) => setBetAmount(event.target.value)}
                        placeholder="5.000000"
                        inputMode="decimal"
                      />
                      <span className="helper">
                        Use the decimal point, not the comma.
                      </span>
                      <div className="quick-chip-row">
                        {["1.000000", "5.000000", "10.000000", "25.000000"].map(
                          (presetAmount) => (
                            <button
                              key={presetAmount}
                              className={
                                betAmount === presetAmount
                                  ? "quick-chip active"
                                  : "quick-chip"
                              }
                              type="button"
                              onClick={() => setBetAmount(presetAmount)}
                            >
                              {presetAmount.replace(".000000", "")} CHIP
                            </button>
                          ),
                        )}
                      </div>
                    </div>
                    <div className="field">
                      <label htmlFor="wallet-type">Wallet</label>
                      <select
                        id="wallet-type"
                        value={walletType}
                        onChange={(event) => setWalletType(event.target.value)}
                      >
                        <option value="cash">cash</option>
                        <option value="bonus">bonus</option>
                      </select>
                    </div>
                  </div>
                  <div className="actions">
                    <button
                      className="button"
                      type="submit"
                      disabled={!accessToken || busyAction !== null || !runtimeLoaded}
                    >
                      {busyAction === "start-session"
                        ? "Launching..."
                        : "Launch round"}
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={!accessToken || !currentSession || busyAction !== null}
                      onClick={() =>
                        accessToken &&
                        currentSession &&
                        void loadSession(
                          accessToken,
                          currentSession.game_session_id,
                        )
                      }
                    >
                      Reload session
                    </button>
                  </div>
                </form>

                <div className="runtime-grid">
                  <article className="runtime-card">
                    <h3>Selected setup</h3>
                    <div className="list-row">
                      <span className="list-muted">Grid</span>
                      <span className="list-strong">{selectedGridSize}</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Mine</span>
                      <span className="list-strong">{selectedMineCount}</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Wallet</span>
                      <span className="list-strong">{walletType}</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">First cashout step</span>
                      <span className="list-strong">
                        {selectedPayoutLadder[0]
                          ? `${selectedPayoutLadder[0]}x`
                          : "n/a"}
                      </span>
                    </div>
                  </article>
                  <article className="runtime-card">
                    <h3>Runtime</h3>
                    <p className="helper">
                      {runtimeLoaded && runtimeConfig
                        ? `Available layouts: ${gridSizes
                            .map((value) => `${value}`)
                            .join(", ")}.`
                        : "Loading runtime..."}
                    </p>
                    <p className="helper">
                      Supported mine counts on this layout:{" "}
                      {mineOptions.join(", ")}
                    </p>
                    {runtimeConfig ? (
                      <>
                        <p className="helper">
                          Runtime file:
                          <span className="mono">
                            {" "}
                            {runtimeConfig.payout_runtime_file}
                          </span>
                        </p>
                        <p className="helper">
                          Fairness version:
                          <span className="mono">
                            {" "}
                            {runtimeConfig.fairness_version}
                          </span>
                        </p>
                      </>
                    ) : null}
                  </article>
                </div>

                <article className="session-card payout-ladder-card">
                  <div className="list-row">
                    <h3>Payout ladder</h3>
                    <span className="status-inline info">
                      {currentSession ? "Live configuration" : "Selected configuration"}
                    </span>
                  </div>
                  <p className="helper">
                    Official runtime multipliers for each safe reveal on this
                    grid and mine setup.
                  </p>
                  <div className="payout-ladder-list">
                    {(currentSession ? activePayoutLadder : selectedPayoutLadder)
                      .slice(0, 8)
                      .map((multiplier, index) => {
                        const revealNumber = index + 1;
                        const isCurrent =
                          currentSession?.status === "active" &&
                          currentSession.safe_reveals_count === revealNumber;
                        const isNext =
                          currentSession?.status === "active"
                            ? currentSession.safe_reveals_count + 1 === revealNumber
                            : revealNumber === 1;
                        return (
                          <article
                            key={`${activeGridSize}-${activeMineCount}-${revealNumber}`}
                            className={`payout-ladder-row${isCurrent ? " current" : ""}${
                              isNext ? " next" : ""
                            }`}
                          >
                            <span className="list-muted">
                              Safe reveal {String(revealNumber).padStart(2, "0")}
                            </span>
                            <strong>{multiplier}x</strong>
                          </article>
                        );
                      })}
                  </div>
                  {(currentSession ? activePayoutLadder : selectedPayoutLadder).length > 8 ? (
                    <p className="helper">
                      Showing the first 8 ladder steps for readability.
                    </p>
                  ) : null}
                </article>
              </div>

              <div className="stack">
                {currentSession ? (
                  <>
                    <article className="mines-session-banner">
                      <div className="mines-session-banner-copy">
                        <p className="eyebrow">Mines Live Session</p>
                        <h3>
                          {currentSession.status === "active"
                            ? "Round is live and ready for the next reveal"
                            : currentSession.status === "won"
                              ? "Round closed in win by the backend"
                              : "Round closed in loss by the backend"}
                        </h3>
                        <p className="helper">
                          Grid {currentSession.grid_size} · {currentSession.mine_count}{" "}
                          mines · {remainingSafeCells} safe cells still available.
                        </p>
                      </div>
                      <div className="mines-progress-card">
                        <span className="list-muted">Reveal progress</span>
                        <strong>{revealProgressPercent}%</strong>
                        <div className="progress-track" aria-hidden="true">
                          <span
                            className="progress-fill"
                            style={{ width: `${revealProgressPercent}%` }}
                          />
                        </div>
                      </div>
                    </article>

                    <div className="mines-stat-strip">
                      <article className="mines-stat-card">
                        <span className="list-muted">Safe reveals</span>
                        <strong>{currentSession.safe_reveals_count}</strong>
                        <p className="helper">
                          out of {activeSafeCellCount} total safe cells
                        </p>
                      </article>
                      <article className="mines-stat-card">
                        <span className="list-muted">Cashout</span>
                        <strong>{cashoutReady ? "ready" : "locked"}</strong>
                        <p className="helper">
                          {cashoutReady
                            ? "The backend can close the round in win."
                            : "At least one safe reveal is required."}
                        </p>
                      </article>
                      <article className="mines-stat-card">
                        <span className="list-muted">Multiplier</span>
                        <strong>{currentSession.multiplier_current}x</strong>
                        <p className="helper">
                          potential payout {currentSession.potential_payout} CHIP
                        </p>
                      </article>
                      <article className="mines-stat-card">
                        <span className="list-muted">Wallet after launch</span>
                        <strong>{currentSession.wallet_balance_after_start}</strong>
                        <p className="helper">{currentSession.wallet_type} snapshot</p>
                      </article>
                      <article className="mines-stat-card">
                        <span className="list-muted">Next pick odds</span>
                        <strong>
                          {nextSafeChance !== null
                            ? `${nextSafeChance.toFixed(1)}% safe`
                            : "n/a"}
                        </strong>
                        <p className="helper">
                          {nextMineRisk !== null
                            ? `${nextMineRisk.toFixed(1)}% mine risk`
                            : "Available while the round is active."}
                        </p>
                      </article>
                    </div>

                    <div className="session-grid">
                      <article className="session-card">
                        <h3>Session</h3>
                        <div className="list-row">
                          <span className="list-muted">ID</span>
                          <span className="mono">
                            {shortId(currentSession.game_session_id)}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Status</span>
                          <span className="list-strong">{currentSession.status}</span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Safe reveals</span>
                          <span className="list-strong">
                            {currentSession.safe_reveals_count}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Bet</span>
                          <span className="list-strong">
                            {currentSession.bet_amount} CHIP
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Created</span>
                          <span className="list-strong">
                            {formatDateTime(currentSession.created_at)}
                          </span>
                        </div>
                      </article>

                      <article className="session-card">
                        <h3>Live payout</h3>
                        <div className="list-row">
                          <span className="list-muted">Multiplier</span>
                          <span className="list-strong">
                            {currentSession.multiplier_current}x
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Potential payout</span>
                          <span className="list-strong">
                            {currentSession.potential_payout} CHIP
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Current ladder step</span>
                          <span className="list-strong">
                            {currentLadderValue ? `${currentLadderValue}x` : "Base round"}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Next ladder step</span>
                          <span className="list-strong">
                            {nextLadderValue ? `${nextLadderValue}x` : "No next step"}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Board hash</span>
                          <span className="mono">
                            {truncateValue(currentSession.board_hash, 18)}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Closed</span>
                          <span className="list-strong">
                            {currentSession.closed_at
                              ? formatDateTime(currentSession.closed_at)
                              : "No"}
                          </span>
                        </div>
                      </article>

                      <article className="session-card">
                        <h3>Fairness snapshot</h3>
                        {currentSessionFairness ? (
                          <>
                            <div className="list-row">
                              <span className="list-muted">Version</span>
                              <span className="list-strong">
                                {currentSessionFairness.fairness_version}
                              </span>
                            </div>
                            <div className="list-row">
                              <span className="list-muted">Nonce</span>
                              <span className="list-strong">
                                {currentSessionFairness.nonce}
                              </span>
                            </div>
                            <div className="list-row">
                              <span className="list-muted">Seed hash</span>
                              <span className="mono">
                                {truncateValue(
                                  currentSessionFairness.server_seed_hash,
                                  18,
                                )}
                              </span>
                            </div>
                            <div className="list-row">
                              <span className="list-muted">Board hash</span>
                              <span className="mono">
                                {truncateValue(
                                  currentSessionFairness.board_hash,
                                  18,
                                )}
                              </span>
                            </div>
                            <p className="helper">
                              User verifiable:{" "}
                              <span className="mono">
                                {currentSessionFairness.user_verifiable
                                  ? "yes"
                                  : "no"}
                              </span>
                            </p>
                          </>
                        ) : (
                          <p className="empty-state">
                            Fairness metadata is not available yet.
                          </p>
                        )}
                      </article>
                    </div>

                    {currentSession.status !== "active" ? (
                      <article className="round-recap-card">
                        <div>
                          <p className="eyebrow">Round Recap</p>
                          <h3>
                            {currentSession.status === "won"
                              ? "Win recorded by the backend"
                              : "Loss recorded by the backend"}
                          </h3>
                          <p className="helper">
                            {currentSession.status === "won"
                              ? `This run closed with a payout snapshot of ${currentSession.potential_payout} CHIP.`
                              : "This run closed after a mine reveal. No additional win credit was created."}
                          </p>
                        </div>
                        <div className="round-recap-grid">
                          <div className="runtime-card">
                            <h4>Bet</h4>
                            <p className="helper">
                              <span className="mono">
                                {currentSession.bet_amount} CHIP · {currentSession.wallet_type}
                              </span>
                            </p>
                          </div>
                          <div className="runtime-card">
                            <h4>Safe reveals</h4>
                            <p className="helper">
                              <span className="mono">
                                {currentSession.safe_reveals_count} cleared
                              </span>
                            </p>
                          </div>
                          <div className="runtime-card">
                            <h4>Closed at</h4>
                            <p className="helper">
                              <span className="mono">
                                {currentSession.closed_at
                                  ? formatDateTime(currentSession.closed_at)
                                  : "n/a"}
                              </span>
                            </p>
                          </div>
                        </div>
                        <div className="actions">
                          <button
                            className="button"
                            type="button"
                            disabled={busyAction !== null}
                            onClick={prepareReplayFromCurrentSession}
                          >
                            Replay same setup
                          </button>
                          <Link className="button-secondary" href="/account">
                            View account recap
                          </Link>
                        </div>
                      </article>
                    ) : null}

                    <article className="board-shell">
                      <div className="board-shell-header">
                        <div>
                          <h3>Board live</h3>
                          <p className="helper">
                            The client only renders state derived from the backend.
                          </p>
                        </div>
                        <div className="board-legend">
                          <span className="legend-chip">
                            <span className="legend-swatch hidden" />
                            hidden
                          </span>
                          <span className="legend-chip">
                            <span className="legend-swatch safe" />
                            safe
                          </span>
                          <span className="legend-chip">
                            <span className="legend-swatch mine" />
                            mine
                          </span>
                        </div>
                      </div>

                      <div
                        className="mines-board"
                        style={{
                          gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))`,
                        }}
                      >
                        {Array.from(
                          { length: currentSession.grid_size },
                          (_, cellIndex) => {
                            const isRevealed =
                              currentSession.revealed_cells.includes(cellIndex);
                            const isMine = highlightedMineCell === cellIndex;
                            const isClosed = currentSession.status !== "active";

                            let className = "board-cell";
                            if (isMine) {
                              className += " revealed-mine";
                            } else if (isRevealed) {
                              className += " revealed-safe";
                            }
                            if (isClosed) {
                              className += " closed";
                            }

                            return (
                              <button
                                key={cellIndex}
                                className={className}
                                type="button"
                                disabled={
                                  busyAction !== null ||
                                  isClosed ||
                                  isRevealed ||
                                  !accessToken
                                }
                                onClick={() => void handleRevealCell(cellIndex)}
                              >
                                <span className="board-cell-index">
                                  {String(cellIndex + 1).padStart(2, "0")}
                                </span>
                                <span className="board-cell-face">
                                  {isMine ? "MINE" : isRevealed ? "SAFE" : "PICK"}
                                </span>
                              </button>
                            );
                          },
                        )}
                      </div>

                      <p className="board-caption">
                        The board shows only the cells already revealed by the
                        backend. No outcome or payout logic is calculated in the
                        client.
                      </p>
                    </article>

                    <div className="actions">
                      <button
                        className="button"
                        type="button"
                        disabled={
                          !accessToken ||
                          !currentSession ||
                          currentSession.status !== "active" ||
                          currentSession.safe_reveals_count <= 0 ||
                          busyAction !== null
                        }
                        onClick={() => void handleCashout()}
                      >
                        {busyAction === "cashout" ? "Cashing out..." : "Cash out"}
                      </button>
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={!accessToken || !currentSession || busyAction !== null}
                        onClick={() =>
                          accessToken &&
                          currentSession &&
                          void loadSession(
                            accessToken,
                            currentSession.game_session_id,
                          )
                        }
                      >
                        Reload snapshot
                      </button>
                      <button
                        className="button-ghost"
                        type="button"
                        disabled={!currentSession || busyAction !== null}
                        onClick={clearCurrentSessionSnapshot}
                      >
                        Clear snapshot
                      </button>
                    </div>
                  </>
                ) : (
                  <article className="mines-empty-state">
                    <p className="eyebrow">Mines Arena</p>
                    <h3>The table is ready</h3>
                    <p className="empty-state">
                      Sign in to launch a round. The backend will record bet,
                      reveals, and cashout in the official flow.
                    </p>
                    <div className="mines-empty-grid">
                      <span>Official runtime</span>
                      <span>Request / response</span>
                      <span>Ledger first</span>
                    </div>
                  </article>
                )}
              </div>
            </div>
          </section>
        </div>
        ) : null}
      </div>
    </main>
  );
}

function getGridSizes(config: MinesRuntimeConfig | null): number[] {
  if (!config) {
    return [25];
  }
  return [...config.supported_grid_sizes].sort((a, b) => a - b);
}

function getMineOptions(
  config: MinesRuntimeConfig | null,
  gridSize: number,
): number[] {
  if (!config) {
    return [3];
  }

  return [...(config.supported_mine_counts[String(gridSize)] ?? [])].sort(
    (a, b) => a - b,
  );
}

function getPayoutLadder(
  config: MinesRuntimeConfig | null,
  gridSize: number,
  mineCount: number,
): string[] {
  if (!config) {
    return [];
  }

  return [...(config.payout_ladders[String(gridSize)]?.[String(mineCount)] ?? [])];
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
      payload && payload.success === false
        ? payload.error.message
        : "Unexpected API response",
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

function truncateValue(value: string, size: number): string {
  if (value.length <= size) {
    return value;
  }
  return `${value.slice(0, size)}...`;
}

function shortId(value: string): string {
  return value.slice(0, 8);
}

function formatMinePositions(value: number[]): string {
  return value.join(", ");
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function mergeSessionHistory(
  history: SessionHistoryItem[],
  session: SessionSnapshot,
): SessionHistoryItem[] {
  const nextItem: SessionHistoryItem = {
    game_session_id: session.game_session_id,
    status: session.status,
    grid_size: session.grid_size,
    mine_count: session.mine_count,
    bet_amount: session.bet_amount,
    wallet_type: session.wallet_type,
    safe_reveals_count: session.safe_reveals_count,
    revealed_cells_count: session.revealed_cells.length,
    multiplier_current: session.multiplier_current,
    potential_payout: session.potential_payout,
    created_at: session.created_at,
    closed_at: session.closed_at,
  };

  return [nextItem, ...history.filter((entry) => entry.game_session_id !== session.game_session_id)]
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .slice(0, 12);
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

function buildAccountOverview(
  history: SessionHistoryItem[],
  transactions: LedgerTransaction[],
): AccountOverview {
  let wins = 0;
  let losses = 0;
  let activeRounds = 0;
  let totalStaked = 0;
  let totalReturned = 0;

  for (const session of history) {
    if (session.status === "won") {
      wins += 1;
    } else if (session.status === "lost") {
      losses += 1;
    } else if (session.status === "active") {
      activeRounds += 1;
    }

    totalStaked += toNumericAmount(session.bet_amount);
    if (session.status === "won") {
      totalReturned += toNumericAmount(session.potential_payout);
    }
  }

  return {
    totalRounds: history.length,
    wins,
    losses,
    activeRounds,
    totalStaked: formatChipAmount(totalStaked),
    totalReturned: formatChipAmount(totalReturned),
    recentWalletMoves: transactions.length,
    lastRoundAt: history[0]?.created_at ?? null,
  };
}

function describeSessionOutcome(
  session: Pick<SessionSnapshot, "status" | "bet_amount" | "potential_payout">,
): string {
  if (session.status === "won") {
    const net = toNumericAmount(session.potential_payout) - toNumericAmount(session.bet_amount);
    return `Net +${formatChipAmount(net)} CHIP`;
  }
  if (session.status === "lost") {
    return `Net -${session.bet_amount} CHIP`;
  }
  return `Live ${session.potential_payout} CHIP`;
}

function parseLaunchPreset(rawValue: string | null): LaunchPreset | null {
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<LaunchPreset>;
    if (
      typeof parsed.grid_size === "number" &&
      typeof parsed.mine_count === "number" &&
      typeof parsed.bet_amount === "string" &&
      typeof parsed.wallet_type === "string"
    ) {
      return {
        grid_size: parsed.grid_size,
        mine_count: parsed.mine_count,
        bet_amount: parsed.bet_amount,
        wallet_type: parsed.wallet_type,
      };
    }
  } catch {
    return null;
  }

  return null;
}

function toNumericAmount(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatChipAmount(value: number): string {
  return value.toFixed(6);
}

function isValidAmount(value: string): boolean {
  if (!/^\d+(\.\d{1,6})?$/.test(value)) {
    return false;
  }

  return Number(value) > 0;
}

function extractValidationMessage(detail: unknown): string {
  if (Array.isArray(detail) && detail.length > 0) {
    const firstError = detail[0];
    if (
      firstError &&
      typeof firstError === "object" &&
      "msg" in firstError &&
      typeof firstError.msg === "string"
    ) {
      const location =
        "loc" in firstError && Array.isArray(firstError.loc)
          ? firstError.loc
              .filter((item: unknown): item is string | number =>
                typeof item === "string" || typeof item === "number",
              )
              .join(".")
          : null;
      return location ? `${location}: ${firstError.msg}` : firstError.msg;
    }
  }

  if (typeof detail === "string" && detail) {
    return detail;
  }

  return "Request validation failed";
}
