"use client";

import Link from "next/link";
import { FormEvent, MouseEvent, useEffect, useRef, useState } from "react";
import {
  extractValidationMessage,
  formatChipAmount,
  formatDateTime,
  getDefaultVisibleMineCount,
  getGridSizes,
  getMineOptions,
  getVisibleMineOptions,
  isValidAmount,
  type LaunchPreset,
  shortId,
  toNumericAmount,
  truncateValue,
} from "@/app/lib/helpers";
import { ADMIN_STORAGE_KEYS } from "@/app/lib/admin-storage";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";
import { AdminManagement } from "./admin-management";
import { AdminMySpace } from "./admin-my-space";
import { AdminFinancePanel } from "./admin-finance-panel";
import { AdminShellPanel } from "./admin-shell-panel";
import { MinesBackofficeEditor } from "./mines/mines-backoffice-editor";
import { PlayerAdminPanel } from "./player-admin-panel";
import type {
  ApiEnvelope,
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  SessionFairness,
  SessionSnapshot,
  StatusKind,
  StatusMessage,
  Wallet,
} from "@/app/lib/types";
import { API_BASE_URL, ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";

const MINES_LAUNCH_ROUTE = "/mines";
const MINES_EMBED_ROUTE = "/mines?embed=1";
const MINES_EMBED_CLOSE_MESSAGE = "casinoking:mines-close";
const MINES_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:mines-fullscreen-state";
const MINES_STANDALONE_MEDIA_QUERY = "(max-width: 960px), (pointer: coarse)";

const ACCOUNT_ACTIVITY_WINDOWS: Array<{ value: ActivityWindow; label: string }> = [
  { value: "7d", label: "7D" },
  { value: "30d", label: "30D" },
  { value: "all", label: "All" },
];

const ADMIN_FINANCIAL_PAGE_SIZE_OPTIONS = [20, 50, 100, 500] as const;

type PlayerView = "lobby" | "account" | "login" | "register";
type AdminSection = "menu" | "casino_king" | "players" | "games" | "my_space" | "admins";
type PlayerAdminView = "list" | "detail";
type ActivityWindow = "7d" | "30d" | "all";
type AdminFinancialWalletFilter = "all" | "cash" | "bonus";
type AdminFinancialTransactionTypeFilter = "all" | "bet" | "win" | "void";

type AdminProfile = {
  id: string;
  email: string;
  role: string;
  status: string;
  is_superadmin: boolean;
  areas: string[];
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

type SessionHistoryItem = {
  game_session_id: string;
  status: "active" | "won" | "lost" | "cancelled";
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
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
  fiscal_code?: string | null;
  is_superadmin?: boolean | null;
  areas?: string[] | null;
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

type FinancialSessionSummary = {
  session_id: string;
  is_legacy: boolean;
  user_id: string;
  user_email: string;
  game_code: string;
  started_at: string;
  ended_at: string;
  status: string;
  total_transactions: number;
  bank_total_credit: string;
  bank_total_debit: string;
  bank_delta: string;
};

type FinancialSessionEvent = {
  ledger_transaction_id: string;
  platform_round_id: string;
  timestamp: string;
  transaction_type: string;
  wallet_type: string;
  bank_credit: string;
  bank_debit: string;
  delta: string;
  game_enrichment: string;
};

type FinancialSessionDetail = {
  session_id: string;
  is_legacy: boolean;
  user_id: string;
  user_email: string;
  game_code: string;
  started_at: string;
  ended_at: string;
  status: string;
  bank_total_credit: string;
  bank_total_debit: string;
  bank_delta: string;
  events: FinancialSessionEvent[];
};

type AdminFinancialSessionsReport = {
  sessions: FinancialSessionSummary[];
  pagination: {
    page: number;
    limit: number;
    total_items: number;
    total_pages: number;
  };
  page_totals: {
    bank_delta: string;
  };
  summary: {
    total_bank_delta_period: string;
  };
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

type AdminForceCloseResponse = {
  target_user_id: string;
  game_code: string;
  voided_rounds: Array<{
    round_id: string;
    bet_amount: string;
    ledger_transaction_id: string;
    admin_action_id: string;
    already_existed: boolean;
  }>;
  closed_table_session_ids: string[];
  closed_access_session_ids: string[];
  reason: string;
};

export function CasinoKingConsole({
  area = "player",
  view = "lobby",
}: {
  area?: "player" | "admin";
  view?: PlayerView;
}) {
  const isAdminArea = area === "admin";
  const storageKeys = isAdminArea ? ADMIN_STORAGE_KEYS : PLAYER_STORAGE_KEYS;
  const minesLauncherShellRef = useRef<HTMLDivElement | null>(null);
  const minesLauncherFrameRef = useRef<HTMLIFrameElement | null>(null);
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
  const [betAmount, setBetAmount] = useState("5");
  const [walletType, setWalletType] = useState("cash");
  const [currentSession, setCurrentSession] = useState<SessionSnapshot | null>(
    null,
  );
  const [currentSessionFairness, setCurrentSessionFairness] =
    useState<SessionFairness | null>(null);
  const [runtimeLoaded, setRuntimeLoaded] = useState(false);
  const [adminProfile, setAdminProfile] = useState<AdminProfile | null>(null);
  const [adminEmailFilter, setAdminEmailFilter] = useState("");
  const [adminSection, setAdminSection] =
    useState<AdminSection>("menu");
  const [playerAdminView, setPlayerAdminView] = useState<PlayerAdminView>("list");
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [selectedAdminUserId, setSelectedAdminUserId] = useState("");
  const [adminLedgerReport, setAdminLedgerReport] =
    useState<AdminLedgerReport | null>(null);
  const [adminFinancialSessionsReport, setAdminFinancialSessionsReport] =
    useState<AdminFinancialSessionsReport | null>(null);
  const [selectedFinancialSessionDetail, setSelectedFinancialSessionDetail] =
    useState<FinancialSessionDetail | null>(null);
  const [expandedFinancialSessionId, setExpandedFinancialSessionId] =
    useState<string | null>(null);
  const [adminFinancialWalletFilter, setAdminFinancialWalletFilter] =
    useState<AdminFinancialWalletFilter>("all");
  const [adminTransactionTypeFilter, setAdminTransactionTypeFilter] =
    useState<AdminFinancialTransactionTypeFilter>("all");
  const [adminMinDeltaFilter, setAdminMinDeltaFilter] = useState("");
  const [adminMaxDeltaFilter, setAdminMaxDeltaFilter] = useState("");
  const [adminDateFromFilter, setAdminDateFromFilter] = useState("");
  const [adminDateToFilter, setAdminDateToFilter] = useState("");
  const [adminCurrentPage, setAdminCurrentPage] = useState(1);
  const [adminItemsPerPage, setAdminItemsPerPage] = useState<number>(50);
  const [adminFairnessCurrent, setAdminFairnessCurrent] =
    useState<FairnessCurrentConfig | null>(null);
  const [verifySessionId, setVerifySessionId] = useState("");
  const [fairnessVerifyResult, setFairnessVerifyResult] =
    useState<FairnessVerifyResult | null>(null);
  const [adminSessionSnapshot, setAdminSessionSnapshot] =
    useState<SessionSnapshot | null>(null);
  const [adminPlayerNewPassword, setAdminPlayerNewPassword] = useState("");
  const [bonusAmount, setBonusAmount] = useState("10.000000");
  const [bonusReason, setBonusReason] = useState("manual_bonus");
  const [adjustmentWalletType, setAdjustmentWalletType] = useState("bonus");
  const [adjustmentDirection, setAdjustmentDirection] = useState("credit");
  const [adjustmentAmount, setAdjustmentAmount] = useState("5.000000");
  const [adjustmentReason, setAdjustmentReason] =
    useState("manual_adjustment");
  const [topupThreshold, setTopupThreshold] = useState("5.000000");
  const [topupAmount, setTopupAmount] = useState("10.000000");
  const [forceCloseReason, setForceCloseReason] = useState("");
  const [adminLastAction, setAdminLastAction] = useState<{
    label: string;
    result: AdminActionResponse;
  } | null>(null);
  const [adminReportWindow, setAdminReportWindow] =
    useState<ActivityWindow>("30d");
  const [isMinesLauncherOpen, setIsMinesLauncherOpen] = useState(false);
  const [isMinesLauncherFullscreen, setIsMinesLauncherFullscreen] = useState(false);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(storageKeys.accessToken) ?? "";
    const storedEmail = window.localStorage.getItem(storageKeys.email) ?? "";
    const storedSessionId =
      window.localStorage.getItem(storageKeys.sessionId) ?? "";
    const storedLaunchPreset = parseLaunchPreset(
      window.localStorage.getItem(storageKeys.launchPreset),
    );

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);
    setLoginEmail(storedEmail);
    if (storedLaunchPreset) {
      applyLaunchPreset(storedLaunchPreset);
    }

    void loadRuntimeConfig();

    if (storedToken) {
      if (isAdminArea) {
        void (async () => {
          try {
            const profile = await apiRequest<AdminProfile>(
              "/admin/auth/me",
              {},
              storedToken,
            );
            setAdminProfile(profile);
            setCurrentEmail(profile.email);
          } catch {
            clearAuthState();
            setStatus({
              kind: "info",
              text: "La sessione admin locale non era piu' valida ed e' stata chiusa.",
            });
          }
        })();
      } else {
        void refreshAuthenticatedState({
          token: storedToken,
          sessionId: storedSessionId || null,
        });
      }
    }
  }, [isAdminArea, storageKeys.accessToken, storageKeys.email, storageKeys.launchPreset, storageKeys.sessionId]);

  useEffect(() => {
    function syncMinesLauncherFullscreen() {
      const nextIsFullscreen = document.fullscreenElement === minesLauncherShellRef.current;
      setIsMinesLauncherFullscreen(nextIsFullscreen);
      notifyMinesEmbeddedFullscreenState(nextIsFullscreen);
    }

    document.addEventListener("fullscreenchange", syncMinesLauncherFullscreen);
    return () => {
      document.removeEventListener("fullscreenchange", syncMinesLauncherFullscreen);
    };
  }, []);

  useEffect(() => {
    if (!isMinesLauncherOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isMinesLauncherOpen]);

  useEffect(() => {
    function handleMinesEmbedMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) {
        return;
      }
      if (
        !event.data ||
        typeof event.data !== "object" ||
        !("type" in event.data) ||
        event.data.type !== MINES_EMBED_CLOSE_MESSAGE
      ) {
        return;
      }
      if (isMinesLauncherFullscreen) {
        return;
      }
      void closeMinesLauncher();
      if (accessToken) {
        void refreshAuthenticatedState({
          token: accessToken,
          sessionId: window.localStorage.getItem(storageKeys.sessionId),
        });
      }
    }

    window.addEventListener("message", handleMinesEmbedMessage);
    return () => {
      window.removeEventListener("message", handleMinesEmbedMessage);
    };
  }, [accessToken, isMinesLauncherFullscreen, storageKeys.sessionId]);


  const gridSizes = getGridSizes(runtimeConfig);
  const mineOptions = getVisibleMineOptions(
    runtimeConfig,
    selectedGridSize,
    selectedMineCount,
  );
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
  const selectedAdminUser =
    adminUsers.find((user) => user.id === selectedAdminUserId) ?? null;
  const selectedAdminUserWalletRows =
    adminLedgerReport && selectedAdminUser
      ? adminLedgerReport.wallet_reconciliation.filter(
          (row) => row.user_id === selectedAdminUser.id,
        )
      : [];
  const financialSessions = adminFinancialSessionsReport?.sessions ?? [];
  const financialSessionsPagination = adminFinancialSessionsReport?.pagination ?? {
    page: adminCurrentPage,
    limit: adminItemsPerPage,
    total_items: 0,
    total_pages: 0,
  };
  const financialSessionsPageTotals = adminFinancialSessionsReport?.page_totals ?? {
    bank_delta: "0.000000",
  };
  const canLoadPreviousFinancialPage = financialSessionsPagination.page > 1;
  const canLoadNextFinancialPage =
    financialSessionsPagination.total_pages > 0 &&
    financialSessionsPagination.page < financialSessionsPagination.total_pages;
  const selectedAdminCashWallet =
    selectedAdminUserWalletRows.find((row) => row.wallet_type === "cash") ?? null;
  const selectedAdminBonusWallet =
    selectedAdminUserWalletRows.find((row) => row.wallet_type === "bonus") ?? null;
  const selectedAdminTotalBalance =
    toNumericAmount(selectedAdminCashWallet?.balance_snapshot ?? "0") +
    toNumericAmount(selectedAdminBonusWallet?.balance_snapshot ?? "0");
  const playerView = isAdminArea ? null : view;
  const isPlayerLoginView = !isAdminArea && playerView === "login";
  const isPlayerRegisterView = !isAdminArea && playerView === "register";
  const showPlayerRegistration = isPlayerRegisterView;
  const showPlayerAuthView = isPlayerLoginView || isPlayerRegisterView;
  const showWalletAndLedger = !isAdminArea && playerView === "account";
  const showAdminPanel = isAdminArea;
  const showPlayerLobby = !isAdminArea && playerView === "lobby";
  // Permission helpers derived from adminProfile
  const isSuperadmin = adminProfile?.is_superadmin ?? false;
  const adminAreas = adminProfile?.areas ?? [];
  const canAccessFinance = isSuperadmin || adminAreas.includes("finance");
  const canAccessEndUser = isSuperadmin || adminAreas.includes("end_user");
  const canAccessMines = isSuperadmin || adminAreas.includes("mines");
  const adminSectionLabel =
    adminSection === "menu"
      ? "Menu backoffice"
      : adminSection === "casino_king"
      ? "Finance"
      : adminSection === "players"
        ? "Player admin"
        : adminSection === "my_space"
          ? "My Space"
          : adminSection === "admins"
            ? "Amministratori"
            : "Mines backoffice";

  useEffect(() => {
    if (!runtimeConfig) {
      return;
    }

    const firstGridSize = gridSizes[0];
    if (!gridSizes.includes(selectedGridSize)) {
      setSelectedGridSize(firstGridSize);
      return;
    }

    const supportedMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!supportedMineOptions.includes(selectedMineCount)) {
      setSelectedMineCount(
        getDefaultVisibleMineCount(runtimeConfig, selectedGridSize, selectedMineCount),
      );
    }
  }, [gridSizes, mineOptions, runtimeConfig, selectedGridSize, selectedMineCount]);

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
          window.localStorage.removeItem(storageKeys.sessionId);
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
      window.localStorage.setItem(storageKeys.sessionId, sessionId);
    } else {
      window.localStorage.removeItem(storageKeys.sessionId);
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
    setBetAmount(normalizeWholeChipInput(preset.bet_amount));
    setWalletType("cash");
  }

  function rememberLaunchPreset(
    preset: LaunchPreset,
    sourceLabel: string,
  ) {
    applyLaunchPreset(preset);
    window.localStorage.setItem(storageKeys.launchPreset, JSON.stringify(preset));
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
      const data = await apiRequest<{ access_token: string; token_type: string; role: string }>(
        isAdminArea ? "/admin/auth/login" : "/auth/login",
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
      if (isAdminArea) {
        setAdminSection("menu");
        // Fetch admin profile to get is_superadmin and areas
        try {
          const profile = await apiRequest<AdminProfile>(
            "/admin/auth/me",
            {},
            data.access_token,
          );
          setAdminProfile(profile);
        } catch {
          // If profile fetch fails, treat as superadmin for backward compat
          setAdminProfile(null);
        }
      }
      window.localStorage.setItem(storageKeys.accessToken, data.access_token);
      window.localStorage.setItem(storageKeys.email, normalizedEmail);

      if (!isAdminArea) {
        await refreshAuthenticatedState({
          token: data.access_token,
          sessionId: window.localStorage.getItem(storageKeys.sessionId),
        });
      }

      setStatus({
        kind: "success",
        text: isAdminArea
          ? "Admin sign-in completed. The backoffice session is now active."
          : "Sign-in completed. Wallets, account activity, and the current session were synchronized.",
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
    setAdminSection("players");
    setPlayerAdminView("list");
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

  async function handleLoadLedgerReport(options?: {
    preserveSection?: boolean;
  }) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token valido prima di usare il report ledger admin.",
      });
      return;
    }

    setBusyAction("admin-ledger-report");
    if (!options?.preserveSection) {
      setAdminSection("casino_king");
    }
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

  async function handleLoadFinancialSessions(options?: {
    page?: number;
    limit?: number;
    emailOverride?: string;
    preserveSection?: boolean;
  }) {
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token valido prima di usare il report sessioni finanziarie.",
      });
      return;
    }

    setBusyAction("admin-financial-sessions");
    if (!options?.preserveSection) {
      setAdminSection("casino_king");
    }
    try {
      const requestedPage = options?.page ?? adminCurrentPage;
      const requestedLimit = options?.limit ?? adminItemsPerPage;
      const effectiveEmail = options?.emailOverride ?? adminEmailFilter.trim();
      const queryParams = new URLSearchParams();
      queryParams.set("page", String(requestedPage));
      queryParams.set("limit", String(requestedLimit));
      if (effectiveEmail) {
        queryParams.set("email", effectiveEmail);
      }
      if (adminFinancialWalletFilter !== "all") {
        queryParams.set("wallet_type", adminFinancialWalletFilter);
      }
      if (adminTransactionTypeFilter !== "all") {
        queryParams.set("transaction_type", adminTransactionTypeFilter);
      }
      if (adminMinDeltaFilter.trim()) {
        queryParams.set("min_delta", adminMinDeltaFilter.trim());
      }
      if (adminMaxDeltaFilter.trim()) {
        queryParams.set("max_delta", adminMaxDeltaFilter.trim());
      }
      if (adminDateFromFilter) {
        queryParams.set("date_from", adminDateFromFilter);
      }
      if (adminDateToFilter) {
        queryParams.set("date_to", adminDateToFilter);
      }
      const data = await apiRequest<AdminFinancialSessionsReport>(
        `/admin/reports/financial/sessions?${queryParams.toString()}`,
        {},
        accessToken,
      );
      setAdminFinancialSessionsReport(data);
      setAdminCurrentPage(data.pagination.page);
      setAdminItemsPerPage(data.pagination.limit);
      setSelectedFinancialSessionDetail(null);
      setExpandedFinancialSessionId(null);
      setStatus({
        kind: "info",
        text: `Sessioni finanziarie aggiornate. ${data.sessions.length} sessioni aggregate caricate.`,
      });
    } catch (error) {
      setAdminFinancialSessionsReport(null);
      setSelectedFinancialSessionDetail(null);
      setExpandedFinancialSessionId(null);
      if (error instanceof ApiRequestError && error.status === 401) {
        clearAuthState();
        setStatus({
          kind: "error",
          text: "La sessione admin non e' piu' valida. Effettua di nuovo il login.",
        });
        return;
      }
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento sessioni finanziarie non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleApplyFinancialSessionFilters() {
    setAdminCurrentPage(1);
    void handleLoadFinancialSessions({ page: 1, limit: adminItemsPerPage });
  }

  function handleFinancialPageSizeChange(nextLimit: number) {
    setAdminItemsPerPage(nextLimit);
    setAdminCurrentPage(1);
    void handleLoadFinancialSessions({ page: 1, limit: nextLimit });
  }

  function handleFinancialPreviousPage() {
    if (!canLoadPreviousFinancialPage) {
      return;
    }
    void handleLoadFinancialSessions({
      page: financialSessionsPagination.page - 1,
      limit: financialSessionsPagination.limit,
    });
  }

  function handleFinancialNextPage() {
    if (!canLoadNextFinancialPage) {
      return;
    }
    void handleLoadFinancialSessions({
      page: financialSessionsPagination.page + 1,
      limit: financialSessionsPagination.limit,
    });
  }

  async function handleLoadFinancialSessionDetail(sessionId: string) {
    if (!accessToken) {
      return;
    }

    setBusyAction(`admin-financial-session-${sessionId}`);
    try {
      const data = await apiRequest<FinancialSessionDetail>(
        `/admin/reports/financial/sessions/${encodeURIComponent(sessionId)}`,
        {},
        accessToken,
      );
      setSelectedFinancialSessionDetail(data);
      setStatus({
        kind: "info",
        text: `Dettaglio sessione ${shortId(sessionId)} caricato dal backend finanziario.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Caricamento dettaglio sessione finanziaria non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleToggleFinancialSessionDetail(sessionId: string) {
    if (expandedFinancialSessionId === sessionId) {
      setExpandedFinancialSessionId(null);
      return;
    }

    setExpandedFinancialSessionId(sessionId);
    if (selectedFinancialSessionDetail?.session_id === sessionId) {
      return;
    }

    await handleLoadFinancialSessionDetail(sessionId);
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

  async function handleTopupBelowThreshold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !selectedAdminUserId) return;

    const thresholdNum = toNumericAmount(topupThreshold.trim());
    if (selectedAdminTotalBalance >= thresholdNum) {
      setStatus({
        kind: "error",
        text: `Saldo totale ${formatChipAmount(selectedAdminTotalBalance)} CHIP ≥ soglia ${formatChipAmount(thresholdNum)} CHIP. Top-up non applicato.`,
      });
      return;
    }
    if (!isValidAmount(topupAmount.trim())) {
      setStatus({ kind: "error", text: "Importo top-up non valido." });
      return;
    }

    setBusyAction("admin-topup-threshold");
    try {
      const data = await apiRequest<AdminActionResponse>(
        `/admin/users/${selectedAdminUserId}/bonus-grants`,
        {
          method: "POST",
          headers: { "Idempotency-Key": window.crypto.randomUUID() },
          body: JSON.stringify({
            amount: topupAmount.trim(),
            reason: "topup_below_threshold",
          }),
        },
        accessToken,
      );
      setAdminLastAction({ label: "topup_below_threshold", result: data });
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
        text: `Top-up bonus ${topupAmount.trim()} CHIP accreditato a ${selectedAdminUser?.email ?? shortId(selectedAdminUserId)}. Wallet after: ${data.wallet_balance_after} CHIP.`,
      });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Top-up non riuscito.") });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleForceCloseSessions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      setStatus({
        kind: "error",
        text: "Serve un bearer token admin prima di chiudere le sessioni.",
      });
      return;
    }
    if (!selectedAdminUserId || !selectedAdminUser) {
      setStatus({
        kind: "error",
        text: "Seleziona prima un utente target dal pannello admin.",
      });
      return;
    }
    const normalizedReason = forceCloseReason.trim();
    if (!normalizedReason) {
      setStatus({
        kind: "error",
        text: "Il motivo del force-close e' obbligatorio.",
      });
      return;
    }

    const confirmed = window.confirm(
      `Confermi la chiusura delle sessioni Mines attive per ${selectedAdminUser.email}?`,
    );
    if (!confirmed) {
      return;
    }

    setBusyAction("admin-force-close-sessions");
    try {
      const data = await apiRequest<AdminForceCloseResponse>(
        `/admin/users/${selectedAdminUserId}/sessions/force-close`,
        {
          method: "POST",
          body: JSON.stringify({
            game_code: "mines",
            reason: normalizedReason,
          }),
        },
        accessToken,
      );
      setForceCloseReason("");
      const [reportData] = await Promise.all([
        apiRequest<AdminLedgerReport>("/admin/reports/ledger", {}, accessToken),
        reloadAdminUsers(accessToken),
      ]);
      setAdminLedgerReport(reportData);
      setSelectedTransactionDetail(null);
      setSelectedFinancialSessionDetail(null);
      setExpandedFinancialSessionId(null);
      if (currentEmail && selectedAdminUser.email === currentEmail) {
        await refreshAuthenticatedState({
          token: accessToken,
          sessionId: currentSession?.game_session_id ?? null,
        });
      }
      setStatus({
        kind: "success",
        text: `Force-close completato su ${selectedAdminUser.email}: ${data.voided_rounds.length} round void, ${data.closed_table_session_ids.length} table session chiuse, ${data.closed_access_session_ids.length} access session chiuse.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Force-close sessioni non riuscito."),
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

  async function handleAdminResetPlayerPassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !selectedAdminUserId) {
      setStatus({ kind: "error", text: "Seleziona prima un giocatore." });
      return;
    }
    if (adminPlayerNewPassword.trim().length < 8) {
      setStatus({ kind: "error", text: "La nuova password deve essere di almeno 8 caratteri." });
      return;
    }

    setBusyAction("admin-player-reset-pwd");
    try {
      await apiRequest<{ target_user_id: string; email: string; password_reset: boolean }>(
        `/admin/users/${selectedAdminUserId}/password-reset`,
        {
          method: "POST",
          body: JSON.stringify({ new_password: adminPlayerNewPassword.trim() }),
        },
        accessToken,
      );
      setAdminPlayerNewPassword("");
      setStatus({
        kind: "success",
        text: `Password di ${selectedAdminUser?.email ?? "giocatore"} reimpostata correttamente.`,
      });
    } catch (error) {
      setStatus({ kind: "error", text: readErrorMessage(error, "Reset password non riuscito.") });
    } finally {
      setBusyAction(null);
    }
  }

  function handleLogout() {
    clearAuthState();
    setStatus({
      kind: "info",
      text: "Local session closed. Your data stays on the backend and you can sign in again at any time.",
    });
  }

  function handleOpenFinanceSection() {
    setAdminSection("casino_king");
    if (!accessToken || adminProfile === null || !canAccessFinance) {
      return;
    }
    void handleLoadFinancialSessions();
  }

  function shouldOpenMinesStandalone() {
    return window.matchMedia(MINES_STANDALONE_MEDIA_QUERY).matches;
  }

  function handleMinesLaunch(event: MouseEvent<HTMLAnchorElement>) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }
    if (shouldOpenMinesStandalone()) {
      return;
    }
    event.preventDefault();
    setIsMinesLauncherOpen(true);
  }

  function notifyMinesEmbeddedFullscreenState(active: boolean) {
    const frameWindow = minesLauncherFrameRef.current?.contentWindow;
    if (!frameWindow) {
      return;
    }
    frameWindow.postMessage(
      { type: MINES_EMBED_FULLSCREEN_STATE_MESSAGE, active },
      window.location.origin,
    );
  }

  async function closeMinesLauncher() {
    if (document.fullscreenElement === minesLauncherShellRef.current) {
      return;
    }
    setIsMinesLauncherOpen(false);
  }

  async function enterMinesLauncherFullscreen() {
    const launcherShell = minesLauncherShellRef.current;
    if (!launcherShell || document.fullscreenElement === launcherShell) {
      return;
    }

    try {
      await launcherShell.requestFullscreen();
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Fullscreen mode is not available in this browser."),
      });
    }
  }

  function clearAuthState() {
    setAccessToken("");
    setCurrentEmail("");
    setWallets([]);
    setSelectedWalletDetail(null);
    setTransactions([]);
    setSessionHistory([]);
    setSelectedTransactionDetail(null);
    setAdminSessionSnapshot(null);
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setAdminUsers([]);
    setAdminSection("menu");
    setSelectedAdminUserId("");
    setAdminLedgerReport(null);
    setAdminFinancialSessionsReport(null);
    setSelectedFinancialSessionDetail(null);
    setExpandedFinancialSessionId(null);
    setFairnessVerifyResult(null);
    setAdminLastAction(null);
    setAdminProfile(null);
    window.localStorage.removeItem(storageKeys.accessToken);
    window.localStorage.removeItem(storageKeys.email);
    window.localStorage.removeItem(storageKeys.sessionId);
    window.localStorage.removeItem(storageKeys.launchPreset);
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
                      IL MIO CONTO
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
                className="button-secondary"
                href={MINES_LAUNCH_ROUTE}
                onClick={handleMinesLaunch}
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
              {accessToken ? (
                <>
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

      {!isAdminArea ? (
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
      ) : null}

      <div
        className={
          showAdminPanel
            ? "dashboard-grid dashboard-grid-admin"
            : "dashboard-grid"
        }
      >
        <div className="stack">
          {!showPlayerLobby && !isAdminArea ? (
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
              <article className="session-card">
                <h3>{isPlayerRegisterView ? "Crea account" : "Accedi"}</h3>
                <p className="helper">
                  Usa la pagina dedicata per {isPlayerRegisterView ? "registrarti" : "accedere al tuo account"}.
                </p>
                <div className="actions">
                  <Link className="button" href={isPlayerRegisterView ? "/register" : "/login"}>
                    {isPlayerRegisterView ? "Vai alla registrazione" : "Vai al login"}
                  </Link>
                  {isPlayerRegisterView ? (
                    <Link className="button-secondary" href="/login">Login</Link>
                  ) : (
                    <Link className="button-secondary" href="/register">Register</Link>
                  )}
                </div>
              </article>
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
                  <Link className="button-secondary" href={MINES_LAUNCH_ROUTE} onClick={handleMinesLaunch}>
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
                <Link className="casino-game-card" href={MINES_LAUNCH_ROUTE} onClick={handleMinesLaunch}>
                  <div className="casino-game-thumb">
                    <span className="casino-game-badge">HOT</span>
                    <div className="casino-game-placeholder">
                      <span>M</span>
                    </div>
                  </div>
                  <div className="casino-game-copy">
                    <h3>Mines</h3>
                    <p className="helper">
                      Tavolo standalone del primo gioco proprietario. Entri nel gioco e da li scegli login oppure demo.
                    </p>
                    <div className="lobby-chip-row">
                      <span className="meta-pill">Apri gioco</span>
                      <span className="meta-pill">
                        {runtimeLoaded && runtimeConfig ? runtimeConfig.fairness_version : "Live runtime"}
                      </span>
                    </div>
                  </div>
                </Link>
              </div>
            </section>
          ) : null}

          {showWalletAndLedger ? (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Account</h2>
                  <p>
                    Dati personali del giocatore, wallet, estratto conto e
                    storico di gioco.
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
                  <div className="account-grid account-grid-clean">
                  <article className="session-card account-overview-card">
                    <div className="panel-header compact">
                      <div>
                        <h3>Profilo giocatore</h3>
                        <p>
                          Vista sintetica del tuo conto e dell'attivita' recente.
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
                        <span className="list-muted">Cash</span>
                        <strong>
                          {cashWallet
                            ? `${cashWallet.balance_snapshot} ${cashWallet.currency_code}`
                            : "Locked"}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Bonus</span>
                        <strong>
                          {bonusWallet
                            ? `${bonusWallet.balance_snapshot} ${bonusWallet.currency_code}`
                            : "Locked"}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Vinte / Perse</span>
                        <strong>
                          {accountOverview.wins} / {accountOverview.losses}
                        </strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Attive</span>
                        <strong>{accountOverview.activeRounds}</strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Giocato</span>
                        <strong>{accountOverview.totalStaked} CHIP</strong>
                      </article>
                      <article className="overview-tile">
                        <span className="list-muted">Restituito</span>
                        <strong>{accountOverview.totalReturned} CHIP</strong>
                      </article>
                    </div>

                    <div className="account-recap-strip">
                      <span className="meta-pill">
                        Movimenti wallet {accountOverview.recentWalletMoves}
                      </span>
                      <span className="meta-pill">
                        {accountOverview.lastRoundAt
                          ? `Ultima mano ${formatDateTime(accountOverview.lastRoundAt)}`
                          : "Nessuna mano"}
                      </span>
                      <span className="meta-pill">
                        {currentSession?.status === "active"
                          ? `Sessione attiva ${shortId(currentSession.game_session_id)}`
                          : "Nessuna sessione attiva"}
                      </span>
                    </div>

                    <div className="actions">
                      <button
                        className="button"
                        type="button"
                        onClick={handleRefreshAccount}
                        disabled={!accessToken || busyAction !== null}
                      >
                        {busyAction === "refresh"
                          ? "Aggiornamento..."
                          : "Aggiorna account"}
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

                  <article className="session-card account-statement-card">
                    <div className="panel-header compact">
                      <div>
                        <h3>Estratto conto</h3>
                        <p>
                          Cronologia personale di movimenti wallet e sessioni di
                          gioco.
                        </p>
                      </div>
                      <span className="status-badge info">
                        {accountStatementItems.length} voci
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

                  <div className="transaction-list account-transaction-list">
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

                  <article className="session-card account-current-session-card">
                    <h3>Sessione attiva</h3>
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
                      </>
                    ) : (
                      <p className="empty-state">
                        No active run is stored locally right now.
                      </p>
                    )}
                  </article>

                  <article className="session-card account-session-detail-card">
                    <div className="list-row">
                      <h3>Dettaglio sessione</h3>
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
                            Riprova setup
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

                  <article className="session-card account-history-card">
                    <h3>Storico partite Mines</h3>
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
                                Riprova setup
                              </button>
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

                  <article className="session-card account-wallet-detail-card">
                    <h3>Dettaglio wallet</h3>
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

                  <article className="session-card account-transaction-detail-card">
                    <h3>Dettaglio transazione</h3>
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
            <section className="panel admin-panel-clean">
              {!accessToken ? (
                <>
                  <div className="panel-header">
                    <div>
                      <h2>Login Backoffice</h2>
                      <p>
                        Accedi con un account admin. Qui non ci sono registrazione
                        player, promo, lobby o flussi gioco.
                      </p>
                    </div>
                  </div>
                  <div className="auth-forms admin-login-only">
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
                        <button className="button" type="submit" disabled={busyAction !== null}>
                          {busyAction === "login" ? "Signing in..." : "Sign in"}
                        </button>
                      </div>
                    </form>
                  </div>
                </>
              ) : (
                <AdminShellPanel
                  adminSection={adminSection}
                  adminSectionLabel={adminSectionLabel}
                  canAccessFinance={canAccessFinance}
                  canAccessEndUser={canAccessEndUser}
                  canAccessMines={canAccessMines}
                  isSuperadmin={isSuperadmin}
                  onOpenFinanceSection={handleOpenFinanceSection}
                  onOpenPlayersSection={() => void handleLoadAdminUsers()}
                  onOpenGamesSection={() => setAdminSection("games")}
                  onOpenMySpaceSection={() => setAdminSection("my_space")}
                  onOpenAdminsSection={() => setAdminSection("admins")}
                  onBackToMenu={() => setAdminSection("menu")}
                  onLogout={handleLogout}
                >
                  {adminSection === "casino_king" ? (
                    <AdminFinancePanel
                      accessToken={accessToken}
                      busyAction={busyAction}
                      adminEmailFilter={adminEmailFilter}
                      onAdminEmailFilterChange={setAdminEmailFilter}
                      adminFinancialWalletFilter={adminFinancialWalletFilter}
                      onAdminFinancialWalletFilterChange={setAdminFinancialWalletFilter}
                      adminTransactionTypeFilter={adminTransactionTypeFilter}
                      onAdminTransactionTypeFilterChange={setAdminTransactionTypeFilter}
                      adminItemsPerPage={adminItemsPerPage}
                      adminDateFromFilter={adminDateFromFilter}
                      onAdminDateFromFilterChange={setAdminDateFromFilter}
                      adminDateToFilter={adminDateToFilter}
                      onAdminDateToFilterChange={setAdminDateToFilter}
                      adminMinDeltaFilter={adminMinDeltaFilter}
                      onAdminMinDeltaFilterChange={setAdminMinDeltaFilter}
                      adminMaxDeltaFilter={adminMaxDeltaFilter}
                      onAdminMaxDeltaFilterChange={setAdminMaxDeltaFilter}
                      adminFinancialSessionsReport={adminFinancialSessionsReport}
                      financialSessions={financialSessions}
                      expandedFinancialSessionId={expandedFinancialSessionId}
                      selectedFinancialSessionDetail={selectedFinancialSessionDetail}
                      financialSessionsPagination={financialSessionsPagination}
                      canLoadPreviousFinancialPage={canLoadPreviousFinancialPage}
                      canLoadNextFinancialPage={canLoadNextFinancialPage}
                      financialSessionsPageTotals={financialSessionsPageTotals}
                      onApplyFinancialSessionFilters={handleApplyFinancialSessionFilters}
                      onFinancialPageSizeChange={handleFinancialPageSizeChange}
                      onToggleFinancialSessionDetail={(sessionId) => void handleToggleFinancialSessionDetail(sessionId)}
                      onFinancialPreviousPage={handleFinancialPreviousPage}
                      onFinancialNextPage={handleFinancialNextPage}
                    />
                  ) : null}

                  {adminSection === "players" ? (
                    <PlayerAdminPanel
                      accessToken={accessToken}
                      busyAction={busyAction}
                      playerAdminView={playerAdminView}
                      adminEmailFilter={adminEmailFilter}
                      onAdminEmailFilterChange={setAdminEmailFilter}
                      adminUsers={adminUsers}
                      selectedAdminUser={selectedAdminUser}
                      canAccessFinance={canAccessFinance}
                      adminPlayerNewPassword={adminPlayerNewPassword}
                      onAdminPlayerNewPasswordChange={setAdminPlayerNewPassword}
                      selectedAdminCashWallet={selectedAdminCashWallet}
                      selectedAdminBonusWallet={selectedAdminBonusWallet}
                      selectedAdminTotalBalance={selectedAdminTotalBalance}
                      bonusAmount={bonusAmount}
                      onBonusAmountChange={setBonusAmount}
                      bonusReason={bonusReason}
                      onBonusReasonChange={setBonusReason}
                      adjustmentWalletType={adjustmentWalletType}
                      onAdjustmentWalletTypeChange={setAdjustmentWalletType}
                      adjustmentDirection={adjustmentDirection}
                      onAdjustmentDirectionChange={setAdjustmentDirection}
                      adjustmentAmount={adjustmentAmount}
                      onAdjustmentAmountChange={setAdjustmentAmount}
                      adjustmentReason={adjustmentReason}
                      onAdjustmentReasonChange={setAdjustmentReason}
                      topupThreshold={topupThreshold}
                      onTopupThresholdChange={setTopupThreshold}
                      topupAmount={topupAmount}
                      onTopupAmountChange={setTopupAmount}
                      forceCloseReason={forceCloseReason}
                      onForceCloseReasonChange={setForceCloseReason}
                      onLoadAdminUsers={() => void handleLoadAdminUsers()}
                      onSelectAdminUser={setSelectedAdminUserId}
                      onChangeView={setPlayerAdminView}
                      onSuspendSelectedUser={(userId) => void handleSuspendSelectedUser(userId)}
                      onGoToSessions={(email) => {
                        setAdminEmailFilter(email);
                        setAdminCurrentPage(1);
                        void handleLoadFinancialSessions({
                          page: 1,
                          limit: adminItemsPerPage,
                          emailOverride: email,
                        });
                      }}
                      onAdminResetPlayerPassword={(event) => void handleAdminResetPlayerPassword(event)}
                      onLoadLedgerReport={() => void handleLoadLedgerReport({ preserveSection: true })}
                      onCreateBonusGrant={(event) => void handleCreateBonusGrant(event)}
                      onCreateAdjustment={(event) => void handleCreateAdjustment(event)}
                      onTopupBelowThreshold={(event) => void handleTopupBelowThreshold(event)}
                      onForceCloseSessions={(event) => void handleForceCloseSessions(event)}
                    />
                  ) : null}

                  {adminSection === "games" ? (
                    <div className="stack">
                      <div className="admin-surface admin-surface-section">
                        <div className="field-grid">
                          <div className="field">
                            <label htmlFor="verify-session-id">Sessione da verificare</label>
                            <input
                              id="verify-session-id"
                              value={verifySessionId}
                              onChange={(event) => setVerifySessionId(event.target.value)}
                              placeholder="Incolla qui il game session id per il controllo fairness"
                            />
                          </div>
                        </div>
                        <div className="actions">
                          <button className="button-secondary" type="button" disabled={busyAction !== null} onClick={() => void handleRefreshFairnessCurrent()}>
                            {busyAction === "admin-fairness-current" ? "Ricarico stato live..." : "Fairness live"}
                          </button>
                          <button className="button-ghost" type="button" disabled={!accessToken || busyAction !== null} onClick={() => void handleVerifyFairness()}>
                            {busyAction === "admin-fairness-verify" ? "Verifico..." : "Verifica sessione"}
                          </button>
                        </div>
                      </div>

                      <MinesBackofficeEditor
                        accessToken={accessToken}
                        runtimeConfig={runtimeConfig}
                        busyAction={busyAction}
                        setBusyAction={setBusyAction}
                        setStatus={setStatus}
                        setRuntimeConfig={setRuntimeConfig}
                        adminFairnessCurrent={adminFairnessCurrent}
                      />
                    </div>
                  ) : null}

                  {adminSection === "my_space" ? (
                    <AdminMySpace
                      adminEmail={currentEmail}
                      accessToken={accessToken}
                    />
                  ) : null}

                  {adminSection === "admins" && isSuperadmin ? (
                    <AdminManagement
                      accessToken={accessToken}
                      isSuperadmin={isSuperadmin}
                    />
                  ) : null}
                </AdminShellPanel>
              )}
            </section>
          ) : null}
        </div>
      </div>

      {isMinesLauncherOpen ? (
        <div className="mines-launch-overlay" role="presentation">
          <section
            ref={minesLauncherShellRef}
            className="mines-launch-shell"
            role="dialog"
            aria-modal="true"
            aria-label="Mines desktop launcher"
          >
            <header className="mines-launch-header">
              <div className="mines-launch-heading">
                <p className="eyebrow">CasinoKing</p>
                <h2>Mines</h2>
              </div>
              <div className="mines-launch-header-actions">
                {!isMinesLauncherFullscreen ? (
                  <>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => void enterMinesLauncherFullscreen()}
                    >
                      Fullscreen
                    </button>
                    <button
                      className="button-ghost"
                      type="button"
                      aria-label="Close Mines"
                      onClick={() => void closeMinesLauncher()}
                    >
                      X
                    </button>
                  </>
                ) : null}
              </div>
            </header>
            <div className="mines-launch-frame-shell">
              <iframe
                ref={minesLauncherFrameRef}
                className="mines-launch-frame"
                src={MINES_EMBED_ROUTE}
                title="Mines embedded game"
                allow="fullscreen"
                onLoad={() => notifyMinesEmbeddedFullscreenState(isMinesLauncherFullscreen)}
              />
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
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

    if (session.status !== "cancelled") {
      totalStaked += toNumericAmount(session.bet_amount);
    }
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
  if (session.status === "cancelled") {
    return "Net 0.00 CHIP";
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

function normalizeWholeChipInput(value: string): string {
  const digitsOnly = value.replace(/[^\d]/g, "");
  return digitsOnly.replace(/^0+(?=\d)/, "").slice(0, 6);
}

