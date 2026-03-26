"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

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

type SessionFairness = {
  game_session_id: string;
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  user_verifiable: boolean;
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
}: {
  area?: "player" | "admin";
}) {
  const [status, setStatus] = useState<StatusMessage | null>({
    kind: "info",
    text: "Bootstrap frontend allineato al backend locale. Puoi registrarti, fare login e giocare una sessione Mines MVP.",
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

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);
    setLoginEmail(storedEmail);

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
  const selectedAdminUser =
    adminUsers.find((user) => user.id === selectedAdminUserId) ?? null;
  const isAdminArea = area === "admin";
  const showPlayerRegistration = !isAdminArea;
  const showWalletAndLedger = !isAdminArea;
  const showAdminPanel = isAdminArea;
  const showMinesPanel = !isAdminArea;

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
        text: readErrorMessage(error, "Impossibile caricare il runtime ufficiale di Mines."),
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
      const [walletData, transactionData] = await Promise.all([
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<LedgerTransaction[]>("/ledger/transactions", {}, token),
      ]);

      setWallets(walletData);
      setTransactions(transactionData);
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
          "La sessione locale non e' piu' valida. Esegui di nuovo il login.",
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
    window.localStorage.setItem(STORAGE_KEYS.sessionId, sessionId);
    if (announce) {
      setStatus({
        kind: "info",
        text: `Sessione ${shortId(sessionId)} riallineata dal backend.`,
      });
    }
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
        text: `Registrazione completata. User ${shortId(data.user_id)} creato, credito iniziale registrato e login pronto.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Registrazione non riuscita."),
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
        text: "Login riuscito. Wallet, ledger e sessione corrente sono stati sincronizzati.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Login non riuscito."),
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
        text: "Password di accesso sito valida. Ora puoi completare la registrazione del player.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Password di accesso sito non valida."),
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
        text: "Snapshot wallet, ledger e sessione riallineati dal backend.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Refresh account non riuscito."),
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
        text: "Inserisci prima l'email dell'account da riallineare.",
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
          ? "Reset token generato dal backend locale. Ora puoi impostare una nuova password."
          : "Richiesta reset accettata. Nessun token esposto per questo account o ambiente.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Richiesta reset password non riuscita."),
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
        text: "Inserisci prima il reset token restituito dal backend.",
      });
      return;
    }
    if (resetNewPassword.trim().length < 8) {
      setStatus({
        kind: "error",
        text: "La nuova password deve avere almeno 8 caratteri.",
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
        text: "Password aggiornata. Puoi usare subito il login con le nuove credenziali.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Reset password non riuscito."),
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
        text: "Devi fare login prima di avviare una partita.",
      });
      return;
    }
    if (!runtimeConfig) {
      setStatus({
        kind: "error",
        text: "Il runtime ufficiale di Mines non e' ancora stato caricato. Aspetta un attimo e riprova.",
      });
      return;
    }

    const supportedGridSizes = getGridSizes(runtimeConfig);
    if (!supportedGridSizes.includes(selectedGridSize)) {
      setStatus({
        kind: "error",
        text: "La griglia selezionata non e' supportata dal runtime ufficiale.",
      });
      return;
    }

    const supportedMineOptions = getMineOptions(runtimeConfig, selectedGridSize);
    if (!supportedMineOptions.includes(selectedMineCount)) {
      setStatus({
        kind: "error",
        text: "Il numero di mine selezionato non e' supportato per la griglia corrente.",
      });
      return;
    }

    const normalizedBetAmount = betAmount.trim();
    if (!isValidAmount(normalizedBetAmount)) {
      setStatus({
        kind: "error",
        text: "Bet amount non valido. Usa un numero positivo con punto decimale, ad esempio 5.000000.",
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
        text: `Partita avviata. Sessione ${shortId(startData.game_session_id)} attiva e bet registrata a ledger.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Avvio partita non riuscito."),
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
            ? `Reveal sicuro completato. Payout potenziale aggiornato a ${revealData.potential_payout ?? currentSession.potential_payout} CHIP.`
            : "Hai trovato una mina. La sessione e' stata chiusa in loss dal backend.",
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Reveal non riuscito."),
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
        text: `Cashout completato. Payout ${cashoutData.payout_amount} CHIP registrato e wallet aggiornato.`,
      });
    } catch (error) {
      setStatus({
        kind: "error",
        text: readErrorMessage(error, "Cashout non riuscito."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleLogout() {
    clearAuthState();
    setStatus({
      kind: "info",
      text: "Sessione locale chiusa. I dati restano sul backend e puoi rientrare quando vuoi.",
    });
  }

  function clearCurrentSessionSnapshot() {
    setCurrentSession(null);
    setCurrentSessionFairness(null);
    setHighlightedMineCell(null);
    window.localStorage.removeItem(STORAGE_KEYS.sessionId);
    setStatus({
      kind: "info",
      text: "Snapshot locale della sessione rimosso. Puoi avviare o ricaricare una nuova partita.",
    });
  }

  function clearAuthState() {
    setAccessToken("");
    setCurrentEmail("");
    setWallets([]);
    setSelectedWalletDetail(null);
    setTransactions([]);
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
      <section className="hero">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">CasinoKing</p>
            <h1>Frontend base integrato con backend locale</h1>
            <p className="lead">
              {isAdminArea
                ? "Questa area e' dedicata alle operazioni admin: login, utenti, reporting contabile minimo e fairness interna."
                : "Questa UI resta volutamente semplice: auth player, lettura wallet, ledger essenziale e Mines MVP server-authoritative con flusso request/response."}
            </p>
            <div className="hero-meta">
              <span className="meta-pill">FastAPI + Next.js</span>
              <span className="meta-pill">
                {isAdminArea ? "Backoffice Admin" : "Mines via runtime ufficiale"}
              </span>
              <span className="meta-pill">API base: {API_BASE_URL}</span>
            </div>
            <div className="route-switch">
              <Link
                className={isAdminArea ? "button-secondary" : "button"}
                href="/"
              >
                Area Player
              </Link>
              <Link
                className={isAdminArea ? "button" : "button-secondary"}
                href="/admin"
              >
                Area Admin
              </Link>
            </div>
          </div>
          <aside className="hero-note">
            <p>
              {isAdminArea
                ? "Le azioni admin restano server-side e richiedono un account con ruolo admin. Nessuna logica finanziaria viene calcolata nel client."
                : "Il frontend non decide mai esito, board o payout. Ogni azione sensibile passa dal backend e il recupero stato usa"}
              {!isAdminArea ? (
                <span className="mono"> GET /games/mines/session/{`{id}`}</span>
              ) : null}
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
                <h2>{isAdminArea ? "Accesso admin" : "Accesso e account"}</h2>
                <p>
                  {isAdminArea
                    ? "Login dedicato al backoffice admin. Nessuna registrazione player o flusso Mines e' esposto qui."
                    : "Registrazione con password sito, login player e reset password locale agganciati al backend."}
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
                  <h3>Registrazione</h3>
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
                        placeholder="almeno 8 caratteri"
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="site-access-password">
                        Password accesso sito
                      </label>
                      <input
                        id="site-access-password"
                        type="password"
                        value={siteAccessPassword}
                        onChange={(event) =>
                          setSiteAccessPassword(event.target.value)
                        }
                        placeholder="richiesta per il bootstrap"
                      />
                      <span className="helper">
                        Per il bootstrap locale e' configurata in
                        <span className="mono"> infra/docker/.env</span>. Se non
                        l&apos;hai cambiata, il valore predefinito e'
                        <span className="mono"> change-me</span>.
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
                        ? "Registrazione in corso..."
                        : "Crea player"}
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={busyAction !== null || !siteAccessPassword}
                      onClick={handleVerifySiteAccess}
                    >
                      {busyAction === "site-access"
                        ? "Verifica..."
                        : "Verifica accesso sito"}
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
                    {busyAction === "login" ? "Login..." : "Entra"}
                  </button>
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={!accessToken}
                    onClick={handleLogout}
                  >
                    Esci
                  </button>
                </div>
                {currentEmail ? (
                  <p className="helper">Account locale attivo: {currentEmail}</p>
                ) : null}
              </form>

              {showPlayerRegistration ? (
                <form className="form-card" onSubmit={handleCompletePasswordReset}>
                  <h3>Reset password</h3>
                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="reset-email">Email account</label>
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
                        placeholder="token locale restituito dal backend"
                      />
                      <span className="helper">
                        In ambiente locale il backend espone il token direttamente
                        nella risposta del forgot password.
                      </span>
                    </div>
                    <div className="field">
                      <label htmlFor="reset-new-password">Nuova password</label>
                      <input
                        id="reset-new-password"
                        type="password"
                        autoComplete="new-password"
                        value={resetNewPassword}
                        onChange={(event) => setResetNewPassword(event.target.value)}
                        placeholder="almeno 8 caratteri"
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
                        ? "Richiesta..."
                        : "Richiedi reset token"}
                    </button>
                    <button
                      className="button"
                      type="submit"
                      disabled={busyAction !== null}
                    >
                      {busyAction === "password-reset"
                        ? "Reset in corso..."
                        : "Aggiorna password"}
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          </section>

          {showWalletAndLedger ? (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Wallet e ledger</h2>
                  <p>
                    Snapshot wallet materializzato e ultime transazioni owner-only
                    lette dal backend.
                  </p>
                </div>
                <div className="inline-actions">
                  <button
                    className="button-secondary"
                    type="button"
                    onClick={handleRefreshAccount}
                    disabled={!accessToken || busyAction !== null}
                  >
                    {busyAction === "refresh" ? "Refresh..." : "Aggiorna dati"}
                  </button>
                </div>
              </div>

              {accessToken ? (
                <div className="account-grid">
                  <div className="wallet-grid">
                    {wallets.map((wallet) => (
                      <article className="wallet-card" key={wallet.wallet_type}>
                        <h3>{wallet.wallet_type.toUpperCase()}</h3>
                        <div className="list-row">
                          <span className="list-muted">Saldo</span>
                          <span className="list-strong">
                            {wallet.balance_snapshot} {wallet.currency_code}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Stato</span>
                          <span className="list-strong">{wallet.status}</span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Ledger account</span>
                          <span className="mono">{wallet.ledger_account_code}</span>
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
                          ref{" "}
                          <span className="mono">
                            {transaction.reference_id
                              ? shortId(transaction.reference_id)
                              : "n/a"}
                          </span>
                        </p>
                        <p className="mono">
                          key: {truncateValue(transaction.idempotency_key, 44)}
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
                    {transactions.length === 0 ? (
                      <p className="empty-state">Nessuna transazione disponibile.</p>
                    ) : null}
                  </div>

                  <article className="session-card">
                    <h3>Dettaglio wallet</h3>
                    {selectedWalletDetail ? (
                      <>
                        <div className="list-row">
                          <span className="list-muted">Tipo</span>
                          <span className="list-strong">
                            {selectedWalletDetail.wallet_type}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Saldo</span>
                          <span className="list-strong">
                            {selectedWalletDetail.balance_snapshot}{" "}
                            {selectedWalletDetail.currency_code}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Stato</span>
                          <span className="list-strong">
                            {selectedWalletDetail.status}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Ledger account</span>
                          <span className="mono">
                            {selectedWalletDetail.ledger_account_code}
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
                              ? "Carico..."
                              : "Ricarica dettaglio"}
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <p className="empty-state">
                          Seleziona un wallet per vedere il dettaglio read-only.
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
                                ? `Carico ${wallet.wallet_type}...`
                                : `Dettaglio ${wallet.wallet_type}`}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </article>

                  <article className="session-card">
                    <h3>Dettaglio transaction</h3>
                    {selectedTransactionDetail ? (
                      <>
                        <div className="list-row">
                          <span className="list-muted">Tipo</span>
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
                                {entry.amount} CHIP Â·{" "}
                                {formatDateTime(entry.created_at)}
                              </p>
                            </article>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="empty-state">
                        Seleziona una transaction per vedere posting ed entry del
                        ledger.
                      </p>
                    )}
                  </article>
                </div>
              ) : (
                <p className="empty-state">
                  Dopo il login qui compariranno wallet cash/bonus e lo storico
                  transazioni del player.
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
                <h2>Mines MVP</h2>
                <p>
                  Start, reveal, cashout e recover state. Il client usa solo
                  configurazioni presenti nel runtime ufficiale.
                </p>
              </div>
              {currentSession ? (
                <span className={`status-badge ${sessionStatusKind(currentSession.status)}`}>
                  Sessione {currentSession.status}
                </span>
              ) : (
                <span className="status-badge info">Nessuna sessione attiva</span>
              )}
            </div>

            <div className="mines-grid">
              <div className="stack">
                <form className="session-actions" onSubmit={handleStartSession}>
                <h3>Nuova partita</h3>
                  <p className="helper">
                    Seleziona una configurazione supportata dal runtime ufficiale
                    e avvia una nuova sessione server-authoritative.
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
                            {gridSize} celle
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
                        Usa il punto decimale, non la virgola.
                      </span>
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
                        ? "Avvio..."
                        : "Avvia sessione"}
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
                      Recupera stato
                    </button>
                  </div>
                </form>

                <div className="runtime-grid">
                  <article className="runtime-card">
                    <h3>Configurazione selezionata</h3>
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
                  </article>
                  <article className="runtime-card">
                    <h3>Runtime</h3>
                    <p className="helper">
                      {runtimeLoaded && runtimeConfig
                        ? `Configurazioni disponibili: ${gridSizes
                            .map((value) => `${value}`)
                            .join(", ")}.`
                        : "Caricamento runtime in corso..."}
                    </p>
                    <p className="helper">
                      Mine supportate sulla griglia selezionata:{" "}
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
              </div>

              <div className="stack">
                {currentSession ? (
                  <>
                    <div className="session-grid">
                      <article className="session-card">
                        <h3>Sessione</h3>
                        <div className="list-row">
                          <span className="list-muted">ID</span>
                          <span className="mono">
                            {shortId(currentSession.game_session_id)}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Stato</span>
                          <span className="list-strong">{currentSession.status}</span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Reveal sicuri</span>
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
                          <span className="list-muted">Creata</span>
                          <span className="list-strong">
                            {formatDateTime(currentSession.created_at)}
                          </span>
                        </div>
                      </article>

                      <article className="session-card">
                        <h3>Payout live</h3>
                        <div className="list-row">
                          <span className="list-muted">Moltiplicatore</span>
                          <span className="list-strong">
                            {currentSession.multiplier_current}x
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Payout potenziale</span>
                          <span className="list-strong">
                            {currentSession.potential_payout} CHIP
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Board hash</span>
                          <span className="mono">
                            {truncateValue(currentSession.board_hash, 18)}
                          </span>
                        </div>
                        <div className="list-row">
                          <span className="list-muted">Chiusa</span>
                          <span className="list-strong">
                            {currentSession.closed_at
                              ? formatDateTime(currentSession.closed_at)
                              : "No"}
                          </span>
                        </div>
                      </article>

                      <article className="session-card">
                        <h3>Fairness sessione</h3>
                        {currentSessionFairness ? (
                          <>
                            <div className="list-row">
                              <span className="list-muted">Versione</span>
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
                            Metadati fairness non ancora disponibili.
                          </p>
                        )}
                      </article>
                    </div>

                    <div
                      className="mines-board"
                      style={{
                        gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))`,
                      }}
                    >
                      {Array.from({ length: currentSession.grid_size }, (_, cellIndex) => {
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
                            {isMine ? "M" : isRevealed ? "S" : cellIndex + 1}
                          </button>
                        );
                      })}
                    </div>

                    <p className="board-caption">
                      La board mostra solo le celle gia' rivelate dal backend.
                      Nessuna logica di outcome o payout e' calcolata nel client.
                    </p>

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
                        {busyAction === "cashout" ? "Cashout..." : "Cashout"}
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
                        Ricarica snapshot
                      </button>
                      <button
                        className="button-ghost"
                        type="button"
                        disabled={!currentSession || busyAction !== null}
                        onClick={clearCurrentSessionSnapshot}
                      >
                        Chiudi snapshot
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="empty-state">
                    Dopo il login puoi avviare una sessione Mines e il backend
                    registrera' bet, reveal e cashout nel flusso ufficiale.
                  </p>
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

function sessionStatusKind(status: SessionSnapshot["status"]): StatusKind {
  if (status === "won") {
    return "success";
  }
  if (status === "lost") {
    return "error";
  }
  return "info";
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
