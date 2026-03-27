"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import {
  buildQuickLaunchOptions,
  extractValidationMessage,
  formatChipAmount,
  formatDateTime,
  formatMinePositions,
  getGridSizes,
  getMineOptions,
  getPayoutLadder,
  isValidAmount,
  type LaunchPreset,
  type QuickLaunchOption,
  shortId,
  toNumericAmount,
  truncateValue,
} from "./casinoking-console.helpers";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const STORAGE_KEYS = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.current_session_id",
  launchPreset: "casinoking.launch_preset",
} as const;

const ACCOUNT_ACTIVITY_WINDOWS: Array<{ value: ActivityWindow; label: string }> = [
  { value: "7d", label: "7D" },
  { value: "30d", label: "30D" },
  { value: "all", label: "All" },
];

type StatusKind = "success" | "error" | "info";

type StatusMessage = {
  kind: StatusKind;
  text: string;
};

type PlayerView = "lobby" | "account" | "mines" | "login" | "register";
type AdminSection = "casino_king" | "players" | "games";
type ActivityWindow = "7d" | "30d" | "all";

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

type ActivityStatementItem = {
  id: string;
  kind: "round" | "transaction";
  created_at: string;
  title: string;
  subtitle: string;
  amountLabel: string;
  statusTone: StatusKind;
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

type DemoAuthResponse = {
  user_id: string;
  email: string;
  wallets: Array<{
    wallet_type: string;
    currency_code: string;
    balance_snapshot: string;
  }>;
  bootstrap_transaction_id: string;
  access_token: string;
  token_type: string;
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
  const [accountActivityWindow, setAccountActivityWindow] =
    useState<ActivityWindow>("30d");
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
  const [adminSection, setAdminSection] =
    useState<AdminSection>("players");
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
  const [adminReportWindow, setAdminReportWindow] =
    useState<ActivityWindow>("30d");
  const [showLobbyMinesGate, setShowLobbyMinesGate] = useState(false);

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
  const minesQuickPresets = buildQuickLaunchOptions(runtimeConfig);
  const recommendedQuickPreset = minesQuickPresets[0] ?? null;
  const activePayoutLadder = getPayoutLadder(
    runtimeConfig,
    activeGridSize,
    activeMineCount,
  );
  const visiblePayoutPreview = (
    currentSession ? activePayoutLadder : selectedPayoutLadder
  ).slice(0, 5);
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
  const recentMinesHistory = sessionHistory.slice(0, 5);
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
  const filteredSessionHistory = sessionHistory.filter((entry) =>
    isWithinActivityWindow(entry.created_at, accountActivityWindow),
  );
  const filteredTransactions = transactions.filter((entry) =>
    isWithinActivityWindow(entry.created_at, accountActivityWindow),
  );
  const accountOverview = buildAccountOverview(
    filteredSessionHistory,
    filteredTransactions,
  );
  const accountStatementItems = buildActivityStatement(
    filteredSessionHistory,
    filteredTransactions,
  );
  const filteredAdminReportTransactions = adminLedgerReport
    ? adminLedgerReport.recent_transactions.filter((entry) =>
        isWithinActivityWindow(entry.created_at, adminReportWindow),
      )
    : [];
  const adminReportPlayerCount = new Set(
    filteredAdminReportTransactions
      .map((entry) => entry.user_id)
      .filter((entry): entry is string => Boolean(entry)),
  ).size;
  const adminReportGameTransactionCount = filteredAdminReportTransactions.filter(
    (entry) => entry.reference_type === "game_session",
  ).length;
  const adminReportSystemCount = filteredAdminReportTransactions.filter(
    (entry) => entry.user_id === null,
  ).length;
  const selectedAdminUser =
    adminUsers.find((user) => user.id === selectedAdminUserId) ?? null;
  const selectedAdminUserWalletRows =
    adminLedgerReport && selectedAdminUser
      ? adminLedgerReport.wallet_reconciliation.filter(
          (row) => row.user_id === selectedAdminUser.id,
        )
      : [];
  const selectedAdminUserTransactions =
    selectedAdminUser && filteredAdminReportTransactions.length > 0
      ? filteredAdminReportTransactions
          .filter((row) => row.user_id === selectedAdminUser.id)
          .slice(0, 6)
      : [];
  const selectedAdminUserGameTransactions = selectedAdminUserTransactions.filter(
    (row) => row.reference_type === "game_session" && row.reference_id,
  );
  const selectedAdminUserDriftCount = selectedAdminUserWalletRows.filter(
    (row) => row.drift !== "0.000000",
  ).length;
  const selectedAdminUserLatestTransaction = selectedAdminUserTransactions[0] ?? null;
  const selectedAdminUserLatestGameTransaction =
    selectedAdminUserGameTransactions[0] ?? null;
  const isDemoPlayer = currentEmail.endsWith("@casinoking.local");
  const visibleFairnessVersion =
    currentSessionFairness?.fairness_version ?? runtimeConfig?.fairness_version ?? "n/a";
  const isAdminArea = area === "admin";
  const playerView = isAdminArea ? null : view;
  const isPlayerLoginView = !isAdminArea && playerView === "login";
  const isPlayerRegisterView = !isAdminArea && playerView === "register";
  const showPlayerRegistration = isPlayerRegisterView;
  const showPlayerAuthView = isPlayerLoginView || isPlayerRegisterView;
  const showWalletAndLedger = !isAdminArea && playerView === "account";
  const showAdminPanel = isAdminArea;
  const showMinesPanel = !isAdminArea && playerView === "mines";
  const showPlayerLobby = !isAdminArea && playerView === "lobby";
  const adminSectionLabel =
    adminSection === "casino_king"
      ? "Casino King"
      : adminSection === "players"
        ? "Players"
        : "Games";

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

  async function startMinesRoundWithPreset(
    token: string,
    preset: LaunchPreset,
    successPrefix: string,
  ) {
    if (!runtimeConfig) {
      throw new Error("The official Mines runtime is still loading.");
    }

    const supportedGridSizes = getGridSizes(runtimeConfig);
    if (!supportedGridSizes.includes(preset.grid_size)) {
      throw new Error("The selected grid size is not supported by the official runtime.");
    }

    const supportedMineOptions = getMineOptions(runtimeConfig, preset.grid_size);
    if (!supportedMineOptions.includes(preset.mine_count)) {
      throw new Error("The selected mine count is not supported for this grid.");
    }

    const normalizedBetAmount = preset.bet_amount.trim();
    if (!isValidAmount(normalizedBetAmount)) {
      throw new Error(
        "Invalid bet amount. Use a positive number with a decimal point, for example 5.000000.",
      );
    }

    applyLaunchPreset(preset);
    const startData = await apiRequest<StartSessionResponse>(
      "/games/mines/start",
      {
        method: "POST",
        headers: {
          "Idempotency-Key": window.crypto.randomUUID(),
        },
        body: JSON.stringify({
          grid_size: preset.grid_size,
          mine_count: preset.mine_count,
          bet_amount: normalizedBetAmount,
          wallet_type: preset.wallet_type,
        }),
      },
      token,
    );

    setHighlightedMineCell(null);
    await refreshAuthenticatedState({
      token,
      sessionId: startData.game_session_id,
    });
    setStatus({
      kind: "success",
      text: `${successPrefix} Session ${shortId(startData.game_session_id)} is active and the bet was recorded in the ledger.`,
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

  async function handleStartDemoMode() {
    setShowLobbyMinesGate(false);
    if (accessToken) {
      setStatus({
        kind: "info",
        text: "A player session is already active. You can enter Mines directly.",
      });
      return;
    }

    setBusyAction("demo-mode");
    try {
      const demoData = await apiRequest<DemoAuthResponse>("/auth/demo", {
        method: "POST",
      });

      setAccessToken(demoData.access_token);
      setCurrentEmail(demoData.email);
      setLoginEmail(demoData.email);
      setLoginPassword("");
      window.localStorage.setItem(STORAGE_KEYS.accessToken, demoData.access_token);
      window.localStorage.setItem(STORAGE_KEYS.email, demoData.email);

      if (recommendedQuickPreset) {
        await startMinesRoundWithPreset(
          demoData.access_token,
          recommendedQuickPreset.preset,
          "Demo mode is ready and the recommended table is already live.",
        );
      } else {
        await refreshAuthenticatedState({
          token: demoData.access_token,
          sessionId: window.localStorage.getItem(STORAGE_KEYS.sessionId),
        });

        setStatus({
          kind: "success",
          text: "Demo mode is ready. A temporary player account was provisioned by the backend and you can launch a real Mines round now.",
        });
      }
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(
          error,
          "Demo mode could not start from the backend.",
        ),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleLobbyMinesEntry() {
    if (accessToken) {
      window.location.assign("/mines");
      return;
    }

    setShowLobbyMinesGate(true);
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
    setAdminSection("players");
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
    setAdminSection("casino_king");
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
    setAdminSection("casino_king");
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
    setAdminSection("games");
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
    setAdminSection("games");
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
    setAdminSection("games");
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

  async function handleLoadAdminSessionSnapshot(sessionId?: string) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin per caricare una sessione Mines.",
      });
      return;
    }
    const effectiveSessionId = sessionId?.trim() || verifySessionId.trim();
    if (!effectiveSessionId) {
      setStatus({
        kind: "error",
        text: "Inserisci un game session id prima di caricare la sessione.",
      });
      return;
    }

    setBusyAction("admin-session-snapshot");
    try {
      setVerifySessionId(effectiveSessionId);
      const data = await apiRequest<SessionSnapshot>(
        `/games/mines/session/${encodeURIComponent(effectiveSessionId)}`,
        {},
        accessToken,
      );
      setAdminSessionSnapshot(data);
      setAdminSection("games");
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

    setBusyAction("start-session");

    try {
      await startMinesRoundWithPreset(
        accessToken,
        {
          grid_size: selectedGridSize,
          mine_count: selectedMineCount,
          bet_amount: betAmount.trim(),
          wallet_type: walletType,
        },
        "Round launched.",
      );
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Round launch failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleQuickPlayPreset(preset: LaunchPreset, sourceLabel: string) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "You need to sign in before launching a round.",
      });
      return;
    }

    setBusyAction("start-session");
    try {
      await startMinesRoundWithPreset(accessToken, preset, sourceLabel);
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Quick play launch failed."),
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
        showPlayerLobby ? (
          <section className="casino-site-shell">
            <div className="casino-warning-bar">
              Il gioco e' vietato ai minori e puo' causare dipendenza patologica.
            </div>
            <header className="casino-site-header">
              <div className="casino-brand-row">
                <Link className="casino-logo" href="/">
                  <span className="casino-logo-wordmark">CASINOKING</span>
                  <span className="casino-logo-badge">BET</span>
                </Link>
                <span className="casino-promo-link">29 Promozioni</span>
              </div>
              <div className="casino-auth-actions">
                {accessToken ? (
                  <>
                    <Link className="casino-login-button" href="/account">
                      ACCOUNT
                    </Link>
                    <button
                      className="casino-register-button"
                      type="button"
                      onClick={handleLogout}
                    >
                      ESCI
                    </button>
                  </>
                ) : (
                  <>
                    <Link className="casino-login-button" href="/login">
                      ACCEDI
                    </Link>
                    <Link className="casino-register-button" href="/register">
                      REGISTRATI
                    </Link>
                  </>
                )}
              </div>
            </header>

            <nav className="casino-category-bar">
              <button className="casino-category-chip active" type="button">
                Casino
              </button>
            </nav>
          </section>
        ) : (
          <section className="product-topbar">
            <div>
              <p className="eyebrow">CasinoKing</p>
              <h2>Embedded Casino Demo</h2>
            </div>
            <div className="product-topbar-nav">
              <Link
                className={playerView === "lobby" ? "button" : "button-secondary"}
                href="/"
              >
                Casino
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
              {accessToken ? (
                <>
                  <Link className="button-secondary" href="/account">
                    My account
                  </Link>
                  <span className="status-badge success">
                    {currentEmail || "Player signed in"}
                  </span>
                  <button className="button-ghost" type="button" onClick={handleLogout}>
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <Link className="button-secondary" href="/login">
                    Login
                  </Link>
                  <Link className="button" href="/register">
                    Register
                  </Link>
                </>
              )}
            </div>
          </section>
        )
      ) : null}

      <section
        className={`hero ${!isAdminArea ? "player-hero" : ""}${
          showPlayerLobby ? " casino-lobby-hero" : ""
        }`}
      >
        <div className="hero-grid">
          <div>
            <p className="eyebrow">CasinoKing</p>
            <h1>
              {isAdminArea
                ? "Local admin backoffice"
                : playerView === "login"
                  ? "Sign in and return to the casino floor"
                  : playerView === "register"
                    ? "Create your player account"
                : playerView === "mines"
                  ? "Mines, presented like a real game surface"
                  : playerView === "account"
                    ? "Player account, wallets, and session history"
                    : "CasinoKing, the king of casino fun"}
            </h1>
            <p className="lead">
              {isAdminArea
                ? "This area is dedicated to admin operations, user controls, ledger reporting, and internal fairness tools."
                : playerView === "login"
                  ? "Use a dedicated login page, then move into the casino lobby, your account area, or an active Mines session."
                  : playerView === "register"
                    ? "Register from a dedicated page, unlock private access, and start from a player-first casino shell."
                : playerView === "mines"
                  ? "Launch a round from a dedicated game route, track the live state, and cash out from a server-authoritative Mines surface."
                  : playerView === "account"
                    ? "Review balances, recent wallet movements, and your current game state from a dedicated player account area."
                    : "Banner promozionale centrale con placeholder temporaneo. Poi sotto la zona Casino e l'ingresso diretto a Mines, come in un sito gambling first-party."}
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
            ) : showPlayerAuthView ? (
              <div className="route-switch">
                <Link className="button-secondary" href="/">
                  Back to casino
                </Link>
                <Link
                  className={isPlayerLoginView ? "button" : "button-secondary"}
                  href="/login"
                >
                  Login
                </Link>
                <Link
                  className={isPlayerRegisterView ? "button" : "button-secondary"}
                  href="/register"
                >
                  Register
                </Link>
              </div>
            ) : null}
          </div>
          <aside className={showPlayerLobby ? "casino-hero-banner" : "hero-note"}>
            {showPlayerLobby ? (
              <div className="casino-hero-banner-inner">
                <p className="eyebrow">Promo banner</p>
                <h3>Placeholder promozionale</h3>
                <p>
                  Qui inseriremo il banner definitivo che mi passerai. Intanto la
                  struttura replica il feeling del sito di riferimento: hero largo,
                  CTA evidenti, accesso al casino e gioco in primo piano.
                </p>
                <div className="casino-hero-dots" aria-hidden="true">
                  <span className="active" />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            ) : (
              <p>
                {isAdminArea
                  ? "Admin actions remain server-side and require an authenticated admin account. Financial logic never runs in the client."
                  : showPlayerAuthView
                    ? "Authentication now lives on dedicated player pages. The casino, account, and game routes stay focused on gameplay and account usage."
                  : playerView === "lobby"
                    ? "The player path is now split into lobby, game, and account. Admin is kept outside the primary player journey."
                    : playerView === "mines"
                      ? "The frontend never decides outcome, board, or payout. Sensitive game state still comes from the backend session snapshot."
                      : "Wallet balances are snapshots derived from the ledger, and the account area stays owner-only through the backend APIs."}
              </p>
            )}
          </aside>
        </div>

        {status && !showPlayerLobby ? (
          <div className="status-line">
            <span className={`status-badge ${status.kind}`}>{status.text}</span>
          </div>
        ) : null}
      </section>

      <div className="dashboard-grid">
        <div className="stack">
          {!showMinesPanel && !showPlayerLobby ? (
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>
                  {isAdminArea
                    ? "Accesso admin"
                    : isPlayerLoginView
                      ? "Player login"
                      : isPlayerRegisterView
                        ? "Create player account"
                        : "Player access"}
                </h2>
                <p>
                  {isAdminArea
                    ? "Login dedicato al backoffice admin. Nessuna registrazione player o flusso Mines e' esposto qui."
                    : showPlayerAuthView
                      ? "Use dedicated authentication pages while keeping the casino lobby, account, and game routes focused on product flows."
                      : "The main player routes stay focused on casino navigation, gameplay, and account usage. Authentication entry points now live on dedicated pages."}
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

            {isAdminArea ? (
              <div className="auth-forms">
                <form className="form-card" onSubmit={handleLogin}>
                  <h3>Login admin</h3>
                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="login-email">Email</label>
                      <input
                        id="login-email"
                        type="email"
                        autoComplete="email"
                        value={loginEmail}
                        onChange={(event) => setLoginEmail(event.target.value)}
                        placeholder="admin@example.com"
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
                </form>
              </div>
            ) : showPlayerAuthView ? (
              <div className="auth-forms auth-forms-player">
                {isPlayerRegisterView ? (
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
                          This private demo still uses a site-wide access password
                          before a new player account can be created.
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
                    <p className="helper">
                      Already registered? Continue on the dedicated{" "}
                      <Link href="/login">login page</Link>.
                    </p>
                  </form>
                ) : (
                  <form className="form-card" onSubmit={handleLogin}>
                    <h3>Login</h3>
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
                    </div>
                    <p className="helper">
                      Need a new account? Use the dedicated{" "}
                      <Link href="/register">registration page</Link>.
                    </p>
                  </form>
                )}

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
              </div>
            ) : accessToken ? (
              <article className="session-card">
                <h3>Player session ready</h3>
                <div className="list-row">
                  <span className="list-muted">Signed in as</span>
                  <span className="list-strong">{currentEmail}</span>
                </div>
                <div className="list-row">
                  <span className="list-muted">Casino area</span>
                  <span className="list-strong">Active</span>
                </div>
                <div className="actions">
                  <Link className="button" href="/account">
                    Open account
                  </Link>
                  <Link className="button-secondary" href="/mines">
                    Open Mines
                  </Link>
                </div>
              </article>
            ) : (
              <article className="session-card">
                <h3>Guest access</h3>
                <p className="helper">
                  Explore the player shell from the casino landing page, then use
                  dedicated authentication pages to sign in or create a new account.
                </p>
                <div className="actions">
                  <Link className="button" href="/login">
                    Login
                  </Link>
                  <Link className="button-secondary" href="/register">
                    Register
                  </Link>
                </div>
              </article>
            )}
          </section>
          ) : null}

          {showPlayerLobby ? (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Casino Online</h2>
                  <p>
                    Prima fascia prodotto della lobby: categoria Casino attiva e
                    card del gioco Mines pronta a ricevere la tua icona definitiva.
                  </p>
                </div>
                <span className="status-badge info">Vedi tutti</span>
              </div>

              <div className="casino-games-grid casino-games-grid-focus">
                {accessToken ? (
                  <Link className="casino-game-card" href="/mines">
                    <div className="casino-game-thumb">
                      <span className="casino-game-badge">HOT</span>
                      <div className="casino-game-placeholder">
                        <span>M</span>
                      </div>
                    </div>
                    <div className="casino-game-copy">
                      <h3>Mines</h3>
                      <p className="helper">
                        Primo gioco proprietario live. Icona definitiva in arrivo.
                      </p>
                      <div className="lobby-chip-row">
                        <span className="meta-pill">
                          {currentSession?.status === "active"
                            ? "Partita attiva"
                            : "Gioca ora"}
                        </span>
                        <span className="meta-pill">
                          {runtimeLoaded && runtimeConfig
                            ? runtimeConfig.fairness_version
                            : "Runtime loading"}
                        </span>
                      </div>
                    </div>
                  </Link>
                ) : (
                  <button
                    className="casino-game-card casino-game-card-button"
                    type="button"
                    onClick={handleLobbyMinesEntry}
                  >
                    <div className="casino-game-thumb">
                      <span className="casino-game-badge">HOT</span>
                      <div className="casino-game-placeholder">
                        <span>M</span>
                      </div>
                    </div>
                    <div className="casino-game-copy">
                      <h3>Mines</h3>
                      <p className="helper">
                        Clicca la card e scegli se accedere o aprire subito la demo.
                      </p>
                      <div className="lobby-chip-row">
                        <span className="meta-pill">Login o Demo</span>
                        <span className="meta-pill">
                          {runtimeLoaded && runtimeConfig
                            ? runtimeConfig.fairness_version
                            : "Runtime loading"}
                        </span>
                      </div>
                    </div>
                  </button>
                )}
              </div>
              {showLobbyMinesGate ? (
                <article className="lobby-card lobby-gate-card">
                  <p className="eyebrow">Ingresso Mines</p>
                  <h3>Scegli come entrare</h3>
                  <p className="helper">
                    Accedi con il tuo account oppure apri subito la modalita' demo.
                  </p>
                  <div className="actions">
                    <Link className="button" href="/login">
                      Login
                    </Link>
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={busyAction !== null}
                      onClick={() => void handleStartDemoMode()}
                    >
                      {busyAction === "demo-mode" ? "Preparing demo..." : "Apri demo"}
                    </button>
                    <button
                      className="button-ghost"
                      type="button"
                      onClick={() => setShowLobbyMinesGate(false)}
                    >
                      Chiudi
                    </button>
                  </div>
                </article>
              ) : null}
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
                    <div className="inline-actions">
                      {ACCOUNT_ACTIVITY_WINDOWS.map((window) => (
                        <button
                          key={window.value}
                          className={
                            accountActivityWindow === window.value
                              ? "button-secondary"
                              : "button-ghost"
                          }
                          type="button"
                          disabled={busyAction !== null}
                          onClick={() => setAccountActivityWindow(window.value)}
                        >
                          {window.label}
                        </button>
                      ))}
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

                  <article className="session-card">
                    <div className="panel-header compact">
                      <div>
                        <h3>Account statement</h3>
                        <p>
                          Wallet movements and Mines rounds combined in one
                          player-facing timeline.
                        </p>
                      </div>
                      <span className="status-badge info">
                        {accountStatementItems.length} entries
                      </span>
                    </div>
                    {accountStatementItems.length > 0 ? (
                      <div className="history-list">
                        {accountStatementItems.slice(0, 8).map((entry) => (
                          <article className="history-card" key={entry.id}>
                            <div className="list-row">
                              <span className="list-strong">{entry.title}</span>
                              <span className={`status-inline ${entry.statusTone}`}>
                                {entry.amountLabel}
                              </span>
                            </div>
                            <p className="helper">{entry.subtitle}</p>
                            <p className="helper">
                              {formatDateTime(entry.created_at)} · {entry.kind}
                            </p>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-state">
                        No wallet movements or Mines rounds fall inside the selected
                        account window yet.
                      </p>
                    )}
                  </article>

                  <div className="transaction-list">
                    {filteredTransactions.slice(0, 8).map((transaction) => (
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
                    {filteredTransactions.length === 0 ? (
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
                    {filteredSessionHistory.length > 0 ? (
                      <div className="history-list">
                        {filteredSessionHistory.slice(0, 6).map((entry) => (
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
                        No Mines rounds have been recorded in the selected account
                        window yet.
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

            <div className="admin-shell-layout">
              <aside className="admin-shell-nav">
                <p className="eyebrow">Admin shell</p>
                <h3>Operator workspace</h3>
                <p className="helper">
                  Move through Casino King, Players, and Games with dedicated
                  backoffice surfaces instead of one mixed operational screen.
                </p>
                <div className="admin-shell-nav-actions">
                  <button
                    className={
                      adminSection === "casino_king" ? "button" : "button-secondary"
                    }
                    type="button"
                    onClick={() => setAdminSection("casino_king")}
                  >
                    Casino King
                  </button>
                  <button
                    className={
                      adminSection === "players" ? "button" : "button-secondary"
                    }
                    type="button"
                    onClick={() => setAdminSection("players")}
                  >
                    Players
                  </button>
                  <button
                    className={
                      adminSection === "games" ? "button" : "button-secondary"
                    }
                    type="button"
                    onClick={() => setAdminSection("games")}
                  >
                    Games
                  </button>
                </div>
                <div className="admin-shell-subnav">
                  {adminSection === "casino_king" ? (
                    <span className="meta-pill">Finance &amp; sessions</span>
                  ) : null}
                  {adminSection === "players" ? (
                    <>
                      <span className="meta-pill">Directory &amp; controls</span>
                      <span className="meta-pill">Email &amp; password workflow</span>
                    </>
                  ) : null}
                  {adminSection === "games" ? (
                    <>
                      <span className="meta-pill">Casino</span>
                      <span className="meta-pill">Mines audit</span>
                    </>
                  ) : null}
                </div>
                <div className="admin-shell-kpis">
                  <span className="meta-pill">{adminUsers.length} users loaded</span>
                  <span className="meta-pill">
                    {adminLedgerReport
                      ? `${filteredAdminReportTransactions.length} tx in report`
                      : "Ledger report pending"}
                  </span>
                  <span className="meta-pill">{adminSectionLabel}</span>
                  <span className="meta-pill">
                    {selectedAdminUser
                      ? `Selected ${selectedAdminUser.email}`
                      : "No user selected"}
                  </span>
                </div>
              </aside>

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

              {adminSection === "players" ? (
                <div className="admin-grid">
                  <article className="admin-card">
                    <div className="list-row">
                      <h3>Players directory</h3>
                      <span className="list-muted">{adminUsers.length}</span>
                    </div>
                    <p className="helper">
                      Search and open a player workspace. Reporting data in the
                      workspace follows the current{" "}
                      {adminReportWindow.toUpperCase()} window.
                    </p>
                    <div className="admin-list">
                      {adminUsers.length > 0 ? (
                        adminUsers.slice(0, 10).map((user) => (
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
                                  ? "Selected"
                                  : "Open workspace"}
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
                                  ? "Already suspended"
                                  : busyAction === "admin-suspend" &&
                                      user.id === selectedAdminUserId
                                    ? "Suspending..."
                                    : "Suspend"}
                              </button>
                            </div>
                          </article>
                        ))
                      ) : (
                        <p className="empty-state">
                          Load users to start the admin workspace flow.
                        </p>
                      )}
                    </div>
                  </article>

                  <article className="admin-card">
                    <div className="list-row">
                      <h3>Selected user workspace</h3>
                      {selectedAdminUser ? (
                        <span
                          className={`status-inline ${
                            selectedAdminUser.status === "suspended"
                              ? "error"
                              : "success"
                          }`}
                        >
                          {selectedAdminUser.status}
                        </span>
                      ) : null}
                    </div>
                    {selectedAdminUser ? (
                      <>
                        <div className="history-detail-grid">
                          <div className="list-row">
                            <span className="list-muted">Email</span>
                            <span className="list-strong">
                              {selectedAdminUser.email}
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Role</span>
                            <span className="mono">{selectedAdminUser.role}</span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Created</span>
                            <span className="list-strong">
                              {formatDateTime(selectedAdminUser.created_at)}
                            </span>
                          </div>
                          <div className="list-row">
                            <span className="list-muted">Wallet rows</span>
                            <span className="list-strong">
                              {selectedAdminUserWalletRows.length}
                            </span>
                          </div>
                        </div>

                        <div className="account-overview-grid">
                          <article className="overview-tile">
                            <span className="list-muted">Transactions in window</span>
                            <strong>{selectedAdminUserTransactions.length}</strong>
                          </article>
                          <article className="overview-tile">
                            <span className="list-muted">Mines-linked tx</span>
                            <strong>{selectedAdminUserGameTransactions.length}</strong>
                          </article>
                          <article className="overview-tile">
                            <span className="list-muted">Wallet drift alerts</span>
                            <strong>{selectedAdminUserDriftCount}</strong>
                          </article>
                          <article className="overview-tile">
                            <span className="list-muted">Report window</span>
                            <strong>
                              {ACCOUNT_ACTIVITY_WINDOWS.find(
                                (window) => window.value === adminReportWindow,
                              )?.label ?? "n/a"}
                            </strong>
                          </article>
                        </div>

                        <div className="actions">
                          <button
                            className="button-secondary"
                            type="button"
                            disabled={!accessToken || busyAction !== null}
                            onClick={() => void handleLoadLedgerReport()}
                          >
                            {busyAction === "admin-ledger-report"
                              ? "Refreshing report..."
                              : "Refresh user report"}
                          </button>
                          {selectedAdminUserLatestTransaction ? (
                            <button
                              className="button-ghost"
                              type="button"
                              disabled={!accessToken || busyAction !== null}
                              onClick={() =>
                                void handleLoadTransactionDetail(
                                  selectedAdminUserLatestTransaction.id,
                                )
                              }
                            >
                              {busyAction ===
                              `ledger-detail-${selectedAdminUserLatestTransaction.id}`
                                ? "Opening tx..."
                                : "Open latest tx"}
                            </button>
                          ) : null}
                          {selectedAdminUserLatestGameTransaction?.reference_id ? (
                            <button
                              className="button-ghost"
                              type="button"
                              disabled={!accessToken || busyAction !== null}
                              onClick={() =>
                                void handleLoadAdminSessionSnapshot(
                                  selectedAdminUserLatestGameTransaction.reference_id ??
                                    undefined,
                                )
                              }
                            >
                              {busyAction === "admin-session-snapshot"
                                ? "Opening session..."
                                : "Open latest Mines round"}
                            </button>
                          ) : null}
                        </div>

                        {selectedAdminUserWalletRows.length > 0 ? (
                          <div className="admin-reconciliation">
                            <h4>Wallet snapshot</h4>
                            {selectedAdminUserWalletRows.map((walletRow) => (
                              <div
                                className="list-row"
                                key={walletRow.wallet_account_id}
                              >
                                <span className="list-muted">
                                  {walletRow.wallet_type} · snapshot{" "}
                                  {walletRow.balance_snapshot}
                                </span>
                                <span
                                  className={
                                    walletRow.drift === "0.000000"
                                      ? "status-inline success"
                                      : "status-inline error"
                                  }
                                >
                                  drift {walletRow.drift}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="helper">
                            Load the ledger report to populate wallet and reconciliation
                            context for the selected user.
                          </p>
                        )}

                        <div className="admin-reconciliation">
                          <h4>Mines drilldown</h4>
                          {selectedAdminUserGameTransactions.length > 0 ? (
                            <div className="admin-list">
                              {selectedAdminUserGameTransactions.map((transaction) => (
                                <article className="admin-list-card" key={transaction.id}>
                                  <div className="list-row">
                                    <span className="list-strong">
                                      {transaction.transaction_type}
                                    </span>
                                    <span className="mono">
                                      {transaction.reference_id
                                        ? shortId(transaction.reference_id)
                                        : shortId(transaction.id)}
                                    </span>
                                  </div>
                                  <p className="helper">
                                    {formatDateTime(transaction.created_at)} · debit{" "}
                                    {transaction.total_debit} / credit{" "}
                                    {transaction.total_credit}
                                  </p>
                                  <div className="actions">
                                    {transaction.reference_id ? (
                                      <button
                                        className="button-secondary"
                                        type="button"
                                        disabled={!accessToken || busyAction !== null}
                                        onClick={() =>
                                          void handleLoadAdminSessionSnapshot(
                                            transaction.reference_id ?? undefined,
                                          )
                                        }
                                      >
                                        {busyAction === "admin-session-snapshot"
                                          ? "Opening..."
                                          : "Open session"}
                                      </button>
                                    ) : null}
                                    <button
                                      className="button-ghost"
                                      type="button"
                                      disabled={!accessToken || busyAction !== null}
                                      onClick={() =>
                                        void handleLoadTransactionDetail(
                                          transaction.id,
                                        )
                                      }
                                    >
                                      {busyAction === `ledger-detail-${transaction.id}`
                                        ? "Opening tx..."
                                        : "Open ledger tx"}
                                    </button>
                                  </div>
                                </article>
                              ))}
                            </div>
                          ) : (
                            <p className="empty-state">
                              No Mines-linked transactions are visible for this user in
                              the selected report window yet.
                            </p>
                          )}
                        </div>

                        <div className="admin-reconciliation">
                          <h4>Recent user transactions</h4>
                          {selectedAdminUserTransactions.length > 0 ? (
                            <div className="admin-list">
                              {selectedAdminUserTransactions.map((transaction) => (
                                <article className="admin-list-card" key={transaction.id}>
                                  <div className="list-row">
                                    <span className="list-strong">
                                      {transaction.transaction_type}
                                    </span>
                                    <span className="mono">
                                      {shortId(transaction.id)}
                                    </span>
                                  </div>
                                  <p className="helper">
                                    {formatDateTime(transaction.created_at)} ·{" "}
                                    {transaction.reference_type ?? "n/a"}
                                  </p>
                                  <p className="helper">
                                    debit {transaction.total_debit} / credit{" "}
                                    {transaction.total_credit}
                                  </p>
                                  <div className="actions">
                                    <button
                                      className="button-secondary"
                                      type="button"
                                      disabled={!accessToken || busyAction !== null}
                                      onClick={() =>
                                        void handleLoadTransactionDetail(
                                          transaction.id,
                                        )
                                      }
                                    >
                                      {busyAction === `ledger-detail-${transaction.id}`
                                        ? "Loading..."
                                        : "Open transaction"}
                                    </button>
                                    {transaction.reference_type === "game_session" &&
                                    transaction.reference_id ? (
                                      <button
                                        className="button-ghost"
                                        type="button"
                                        disabled={!accessToken || busyAction !== null}
                                        onClick={() =>
                                          void handleLoadAdminSessionSnapshot(
                                            transaction.reference_id ?? undefined,
                                          )
                                        }
                                      >
                                        Open session
                                      </button>
                                    ) : null}
                                  </div>
                                </article>
                              ))}
                            </div>
                          ) : (
                            <p className="empty-state">
                              Load the ledger report to inspect recent user activity
                              from this workspace.
                            </p>
                          )}
                        </div>
                      </>
                    ) : (
                      <p className="empty-state">
                        Pick a user from the list to open a dedicated operational
                        workspace.
                      </p>
                    )}
                  </article>
                </div>
              ) : null}

              {adminSection === "games" ? (
                <>
              <div className="admin-grid">
                <article className="admin-card">
                  <h3>Games &gt; Casino</h3>
                  <p className="helper">
                    Current operational surface for Casino games, with Mines
                    fairness, session drilldown, and runtime inspection.
                  </p>
                  <div className="admin-reconciliation">
                    <h4>Current game module</h4>
                    <div className="list-row">
                      <span className="list-muted">Product area</span>
                      <span className="list-strong">Casino</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Active game</span>
                      <span className="list-strong">Mines</span>
                    </div>
                  </div>
                </article>
                <article className="admin-card">
                  <h3>Games &gt; Casino &gt; Mines</h3>
                  <p className="helper">
                    Product-facing publishing surface for the Mines entry point.
                    Player bet, grid, and in-round controls still belong to the
                    game frontend and remain server-authoritative.
                  </p>
                  <div className="admin-reconciliation">
                    <h4>Launch configuration</h4>
                    <div className="list-row">
                      <span className="list-muted">Launch key</span>
                      <span className="mono">mines</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Player route</span>
                      <span className="mono">/mines</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Lobby card</span>
                      <span className="list-strong">Placeholder thumbnail active</span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Fairness model</span>
                      <span className="list-strong">
                        {runtimeConfig?.fairness_version ?? "loading"}
                      </span>
                    </div>
                  </div>
                </article>
                <article className="admin-card">
                  <h3>Mines fairness current</h3>
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
                </>
              ) : null}

              {adminSection === "players" ? (
              <div className="admin-grid">
                <article className="admin-card">
                  <h3>Player controls</h3>
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
                      <div className="admin-reconciliation">
                        <h4>Identity workflow</h4>
                        <div className="list-row">
                          <span className="list-muted">Email on file</span>
                          <span className="list-strong">{selectedAdminUser.email}</span>
                        </div>
                        <p className="helper">
                          Admin email override and forced password reset are not
                          wired to dedicated BO endpoints yet. This section now
                          groups the player identity workflow so we can connect
                          those actions next without mixing them into finance or
                          game audit views.
                        </p>
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
              ) : null}

              {adminSection === "casino_king" ? (
              <div className="admin-grid">
                <article className="admin-card">
                  <div className="list-row">
                    <h3>Casino King ledger</h3>
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
                    <h3>Player sessions and users</h3>
                    <span className="list-muted">{adminUsers.length}</span>
                  </div>
                  <p className="helper">
                    Financial and session-facing BO area for Casino King:
                    player-linked transactions, user pointers, and game-session
                    drilldown.
                  </p>
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
                        ? `${filteredAdminReportTransactions.length} tx`
                        : "n/a"}
                    </span>
                  </div>
                  {adminLedgerReport ? (
                    <div className="admin-list">
                      <div className="inline-actions">
                        {ACCOUNT_ACTIVITY_WINDOWS.map((window) => (
                          <button
                            key={window.value}
                            className={
                              adminReportWindow === window.value
                                ? "button-secondary"
                                : "button-ghost"
                            }
                            type="button"
                            disabled={busyAction !== null}
                            onClick={() => setAdminReportWindow(window.value)}
                          >
                            {window.label}
                          </button>
                        ))}
                      </div>
                      <article className="admin-list-card">
                        <div className="list-row">
                          <span className="list-muted">Transazioni recenti</span>
                          <span className="list-strong">
                            {filteredAdminReportTransactions.length}
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
                          <span className="list-muted">Player toccati</span>
                          <span className="list-strong">{adminReportPlayerCount}</span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Game session tx</span>
                          <span className="list-strong">
                            {adminReportGameTransactionCount}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">System tx</span>
                          <span className="list-strong">{adminReportSystemCount}</span>
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

                      {filteredAdminReportTransactions
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
              ) : null}
            </div>
            </div>
            </section>
          ) : null}
        </div>

        {showMinesPanel ? (
        <div className="stack">
          <section className="panel mines-product-shell">
            <div className="panel-header">
              <div>
                <h2>Mines</h2>
                <p>
                  Enter a focused game table, launch a round, and play a
                  server-authoritative Mines session from a dedicated site route.
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
                {!accessToken ? (
                  <article className="mines-entry-card">
                    <p className="eyebrow">Play Mines</p>
                    <h3>Demo or login, then enter the table</h3>
                    <p className="helper">
                      Create a player account or sign in, then launch a real Mines
                      round backed by the backend session, ledger, and runtime rules.
                    </p>
                    <div className="mines-entry-highlights">
                      <span>Server-authoritative</span>
                      <span>Cash + bonus wallets</span>
                      <span>Round recap</span>
                    </div>
                    <div className="actions">
                      <Link className="button" href="/login">
                        Login to play
                      </Link>
                      <Link className="button-secondary" href="/register">
                        Register
                      </Link>
                      <button
                        className="button-ghost"
                        type="button"
                        disabled={busyAction !== null}
                        onClick={() => void handleStartDemoMode()}
                      >
                        {busyAction === "demo-mode"
                          ? "Preparing demo..."
                          : "Try demo mode"}
                      </button>
                    </div>
                  </article>
                ) : null}

                <form className="session-actions mines-control-rail" onSubmit={handleStartSession}>
                <h3>{currentSession?.status === "active" ? "Live game controls" : "Launch a new round"}</h3>
                  <p className="helper">
                    Pick a supported setup, choose a wallet, and keep the play
                    flow focused on the next real action at the table.
                  </p>
                  {recommendedQuickPreset ? (
                    <article className="history-card">
                      <div className="list-row">
                        <span className="list-strong">Recommended table</span>
                        <span className="status-inline success">
                          {recommendedQuickPreset.preset.grid_size} cells ·{" "}
                          {recommendedQuickPreset.preset.mine_count} mines
                        </span>
                      </div>
                      <p className="helper">{recommendedQuickPreset.description}</p>
                      <div className="history-meta">
                        <span>Bet {recommendedQuickPreset.preset.bet_amount} CHIP</span>
                        <span>{recommendedQuickPreset.preset.wallet_type} wallet</span>
                      </div>
                      <div className="actions">
                        <button
                          className="button"
                          type="button"
                          disabled={!accessToken || busyAction !== null}
                          onClick={() =>
                            void handleQuickPlayPreset(
                              recommendedQuickPreset.preset,
                              "Recommended table launched.",
                            )
                          }
                        >
                          {busyAction === "start-session"
                            ? "Launching..."
                            : "Play recommended table"}
                        </button>
                        <button
                          className="button-ghost"
                          type="button"
                          disabled={busyAction !== null}
                          onClick={() =>
                            rememberLaunchPreset(
                              recommendedQuickPreset.preset,
                              recommendedQuickPreset.label,
                            )
                          }
                        >
                          Customize this setup
                        </button>
                      </div>
                    </article>
                  ) : null}
                  {isDemoPlayer ? (
                    <div className="account-recap-strip">
                      <span className="meta-pill">Demo account active</span>
                      <span className="meta-pill">
                        Temporary player {currentEmail}
                      </span>
                    </div>
                  ) : null}
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
                  {minesQuickPresets.length > 0 ? (
                    <div className="admin-reconciliation">
                      <h4>Quick launch presets</h4>
                      <div className="history-list">
                        {minesQuickPresets.map((option) => (
                          <article className="history-card" key={option.label}>
                            <div className="list-row">
                              <span className="list-strong">{option.label}</span>
                              <span className="status-inline info">
                                {option.preset.grid_size} cells · {option.preset.mine_count} mines
                              </span>
                            </div>
                            <p className="helper">{option.description}</p>
                            <div className="actions">
                              <button
                                className="button-secondary"
                                type="button"
                                disabled={busyAction !== null}
                                onClick={() =>
                                  rememberLaunchPreset(option.preset, option.label)
                                }
                              >
                                Load preset
                              </button>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}
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

                <div className="runtime-grid mines-compact-runtime">
                  <article className="runtime-card">
                    <h3>Table setup</h3>
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
                    <h3>Table rules</h3>
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
                      <p className="helper">
                        Fairness model {runtimeConfig.fairness_version}. Round
                        outcomes stay server-side and the player only sees state
                        returned by the backend.
                      </p>
                    ) : null}
                  </article>
                  <article className="runtime-card">
                    <h3>Fairness & hand report</h3>
                    <p className="helper">
                      Every round keeps a fairness version, nonce, and backend-side
                      session record. You can review the hand again from this route
                      and from the account area.
                    </p>
                    <div className="account-recap-strip">
                      <span className="meta-pill">
                        {runtimeConfig?.fairness_version ?? "Fairness loading"}
                      </span>
                      <span className="meta-pill">
                        {sessionHistory.length > 0
                          ? `${sessionHistory.length} hands tracked`
                          : "No hands yet"}
                      </span>
                      <span className="meta-pill">
                        {currentSessionFairness?.user_verifiable
                          ? "Player-facing metadata"
                          : "Admin audit available"}
                      </span>
                    </div>
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
                <article className="mines-stage-card">
                  <div className="mines-stage-topbar">
                    <div className="mines-stage-heading">
                      <p className="eyebrow">Casino &gt; Mines</p>
                      <h3 className="mines-wordmark">MINES</h3>
                    </div>
                    <div className="mines-payout-preview">
                      {visiblePayoutPreview.length > 0 ? (
                        visiblePayoutPreview.map((multiplier, index) => (
                          <span
                            className={`mines-preview-chip${
                              index === 0 ? " active" : ""
                            }`}
                            key={`${activeGridSize}-${activeMineCount}-preview-${index + 1}`}
                          >
                            {multiplier}x
                          </span>
                        ))
                      ) : (
                        <span className="mines-preview-chip active">Loading</span>
                      )}
                    </div>
                  </div>
                  <div className="mines-stage-stats">
                    <span className="meta-pill">
                      Cash {cashWallet ? `${cashWallet.balance_snapshot} CHIP` : "Locked"}
                    </span>
                    <span className="meta-pill">
                      Bonus {bonusWallet ? `${bonusWallet.balance_snapshot} CHIP` : "Locked"}
                    </span>
                    <span className="meta-pill">
                      {currentSession ? currentSession.bet_amount : betAmount} CHIP bet
                    </span>
                    <span className="meta-pill">
                      {currentSession ? currentSession.mine_count : selectedMineCount} mines
                    </span>
                  </div>
                </article>
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

                    <div className="session-grid mines-session-grid">
                      <article className="session-card">
                        <h3>Round status</h3>
                        <div className="list-row">
                          <span className="list-muted">Round</span>
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
                          <span className="list-muted">Started</span>
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
                          <span className="list-muted">Closed</span>
                          <span className="list-strong">
                            {currentSession.closed_at
                              ? formatDateTime(currentSession.closed_at)
                              : "No"}
                          </span>
                        </div>
                      </article>

                      <article className="session-card">
                        <h3>Fairness summary</h3>
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
                              <span className="list-muted">Verification</span>
                              <span className="list-strong">
                                {currentSessionFairness.user_verifiable
                                  ? "player ready"
                                  : "admin audit available"}
                              </span>
                            </div>
                            <p className="helper">
                              The session is tracked with fairness metadata and can be
                              reconciled later from account history and admin audit tools.
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

                    <article className="board-shell mines-stage-board">
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

                    <div className="actions mines-action-bar">
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

                    <article className="session-card">
                      <div className="panel-header compact">
                        <div>
                          <h3>Recent hands</h3>
                          <p>
                            Review the latest Mines rounds, reopen a hand, or replay
                            the same setup directly from the table.
                          </p>
                        </div>
                        <span className="status-badge info">
                          {sessionHistory.length} tracked
                        </span>
                      </div>
                      {sessionHistory.length > 0 ? (
                        <div className="history-list">
                          {sessionHistory.slice(0, 4).map((entry) => (
                            <article className="history-card" key={entry.game_session_id}>
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
                              </div>
                              <div className="actions">
                                <button
                                  className="button-secondary"
                                  type="button"
                                  disabled={!accessToken || busyAction !== null}
                                  onClick={() =>
                                    void handleOpenHistorySession(entry.game_session_id)
                                  }
                                >
                                  {busyAction === `history-session-${entry.game_session_id}`
                                    ? "Opening..."
                                    : "Open hand"}
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
                              </div>
                            </article>
                          ))}
                        </div>
                      ) : (
                        <p className="empty-state">
                          Your hand report will start filling here as soon as you
                          launch rounds on this table.
                        </p>
                      )}
                    </article>

                    <article className="session-card mines-info-card">
                      <div className="panel-header compact">
                        <div>
                          <h3>Game info - Mines</h3>
                          <p>
                            Player-facing guidance inspired by the original dark
                            template, while keeping only rules and claims that are
                            supported by the current backend runtime.
                          </p>
                        </div>
                        <span className="status-inline success">Runtime-backed</span>
                      </div>
                      <div className="mines-info-sections">
                        <section>
                          <h4>Ways to win</h4>
                          <p>
                            Pick at least one safe cell and collect the potential
                            win before a mine is revealed. Every safe pick moves the
                            round forward on the official payout ladder.
                          </p>
                        </section>
                        <section>
                          <h4>Payout display</h4>
                          <p>
                            The multipliers above the board preview the current
                            configuration. Live current and next payout steps are
                            derived from the backend session snapshot.
                          </p>
                        </section>
                        <section>
                          <h4>Settings menu</h4>
                          <p>
                            Grid size, number of mines, stake, and wallet are chosen
                            from the left rail. Outcome, board, and cashout logic stay
                            server-side.
                          </p>
                        </section>
                        <section>
                          <h4>History and return to player</h4>
                          <p>
                            Completed rounds stay visible in the hand report and in
                            the account area, together with round recap and fairness
                            metadata for later audit.
                          </p>
                        </section>
                      </div>
                    </article>
                  </>
                ) : (
                  <article className="mines-empty-state">
                    <p className="eyebrow">Mines Arena</p>
                    <h3>{accessToken ? "The table is ready" : "Sign in to take a seat"}</h3>
                    <p className="empty-state">
                      {accessToken
                        ? "Choose your setup on the left and launch a real round. The backend records bet, reveals, and cashout in the official flow."
                        : "Use your player account to enter Mines. Real play stays authenticated so wallet, ledger, and round state remain coherent."}
                    </p>
                    <div className="mines-empty-grid">
                      <span>Official runtime</span>
                      <span>Request / response</span>
                      <span>Ledger first</span>
                    </div>
                    <article className="runtime-card">
                      <h3>What you will see when you play</h3>
                      <div className="history-list">
                        <article className="history-card">
                          <div className="list-row">
                            <span className="list-strong">Board-first table</span>
                            <span className="status-inline info">Live</span>
                          </div>
                          <p className="helper">
                            Focus on the board, the next action, and the payout ladder,
                            without admin or debug noise.
                          </p>
                        </article>
                        <article className="history-card">
                          <div className="list-row">
                            <span className="list-strong">Hand report</span>
                            <span className="status-inline info">Tracked</span>
                          </div>
                          <p className="helper">
                            Each round can be reopened later with stake, outcome,
                            payout, and fairness metadata.
                          </p>
                        </article>
                        <article className="history-card">
                          <div className="list-row">
                            <span className="list-strong">Fairness</span>
                            <span className="status-inline info">Readable</span>
                          </div>
                          <p className="helper">
                            The game exposes only claims that are really supported by
                            the backend metadata.
                          </p>
                        </article>
                      </div>
                    </article>
                    <article className="session-card mines-info-card">
                      <div className="panel-header compact">
                        <div>
                          <h3>Game info - Mines</h3>
                          <p>
                            The table follows the original dark help-screen vibe
                            while staying consistent with the current backend model.
                          </p>
                        </div>
                        <span className="status-inline success">Guide</span>
                      </div>
                      <div className="mines-info-sections">
                        <section>
                          <h4>Ways to win</h4>
                          <p>Reveal safe cells, grow the multiplier, then cash out before a mine is hit.</p>
                        </section>
                        <section>
                          <h4>Settings menu</h4>
                          <p>The left rail controls grid, mines, wallet, and stake before a round starts.</p>
                        </section>
                      </div>
                    </article>
                    {!accessToken ? (
                      <div className="actions">
                        <Link className="button" href="/login">
                          Login
                        </Link>
                        <Link className="button-secondary" href="/register">
                          Register
                        </Link>
                        <button
                          className="button-ghost"
                          type="button"
                          disabled={busyAction !== null}
                          onClick={() => void handleStartDemoMode()}
                        >
                          {busyAction === "demo-mode"
                            ? "Preparing demo..."
                            : "Try demo mode"}
                        </button>
                      </div>
                    ) : null}
                  </article>
                )}

                <article className="session-card">
                  <div className="list-row">
                    <h3>Game integrity</h3>
                    <span className="status-inline info">{visibleFairnessVersion}</span>
                  </div>
                  <p className="helper">
                    Mines outcomes stay server-side. The player sees only round state
                    returned by the backend, while hashes and nonce make each round
                    auditable later.
                  </p>
                  <div className="history-detail-grid">
                    <div className="list-row">
                      <span className="list-muted">Runtime</span>
                      <span className="list-strong">
                        {runtimeConfig?.payout_runtime_file ?? "Loading"}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Verification</span>
                      <span className="list-strong">
                        {currentSessionFairness?.user_verifiable
                          ? "round metadata visible"
                          : "audit available"}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Current nonce</span>
                      <span className="list-strong">
                        {currentSessionFairness ? currentSessionFairness.nonce : "n/a"}
                      </span>
                    </div>
                    <div className="list-row">
                      <span className="list-muted">Round report</span>
                      <span className="list-strong">
                        {recentMinesHistory.length > 0 ? "ready" : "pending"}
                      </span>
                    </div>
                  </div>
                  <p className="helper">
                    You can replay setups from this table, inspect round history, and
                    use account history as the player-facing hand report.
                  </p>
                </article>

                <article className="session-card">
                  <div className="list-row">
                    <h3>Recent table history</h3>
                    <span className="status-inline info">
                      {recentMinesHistory.length} rounds
                    </span>
                  </div>
                  {recentMinesHistory.length > 0 ? (
                    <div className="history-list">
                      {recentMinesHistory.map((entry) => (
                        <article className="history-card" key={entry.game_session_id}>
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
                            {entry.grid_size} cells · {entry.mine_count} mines · bet{" "}
                            {entry.bet_amount} CHIP
                          </p>
                          <p className="helper">
                            {formatDateTime(entry.created_at)} · payout{" "}
                            {entry.potential_payout} CHIP
                          </p>
                          <div className="actions">
                            <button
                              className="button-secondary"
                              type="button"
                              disabled={!accessToken || busyAction !== null}
                              onClick={() =>
                                void handleOpenHistorySession(entry.game_session_id)
                              }
                            >
                              {busyAction === `history-session-${entry.game_session_id}`
                                ? "Loading..."
                                : "Open round"}
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
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-state">
                      No rounds have been recorded for this player yet. Launch one
                      from the table to start the hand report.
                    </p>
                  )}
                </article>
              </div>
            </div>
          </section>
        </div>
        ) : null}
      </div>
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

function isWithinActivityWindow(timestamp: string, window: ActivityWindow): boolean {
  if (window === "all") {
    return true;
  }

  const days = window === "7d" ? 7 : 30;
  const eventTime = Date.parse(timestamp);
  if (Number.isNaN(eventTime)) {
    return false;
  }

  return Date.now() - eventTime <= days * 24 * 60 * 60 * 1000;
}

function buildActivityStatement(
  history: SessionHistoryItem[],
  transactions: LedgerTransaction[],
): ActivityStatementItem[] {
  const roundItems: ActivityStatementItem[] = history.map((session) => ({
    id: `round-${session.game_session_id}`,
    kind: "round",
    created_at: session.created_at,
    title: `Mines ${session.status}`,
    subtitle: `${session.grid_size} cells · ${session.mine_count} mines · ${session.wallet_type} wallet`,
    amountLabel: describeSessionOutcome(session),
    statusTone: sessionStatusKind(session.status),
  }));

  const transactionItems: ActivityStatementItem[] = transactions.map((transaction) => ({
    id: `tx-${transaction.id}`,
    kind: "transaction",
    created_at: transaction.created_at,
    title: transaction.transaction_type,
    subtitle: `${transaction.reference_type ?? "wallet movement"} · ${
      transaction.reference_id ? shortId(transaction.reference_id) : "no reference"
    }`,
    amountLabel: shortId(transaction.id),
    statusTone: "info",
  }));

  return [...roundItems, ...transactionItems].sort((left, right) =>
    right.created_at.localeCompare(left.created_at),
  );
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

