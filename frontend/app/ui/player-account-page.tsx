"use client";

import { Fragment, useEffect, useMemo, useState, type FormEvent } from "react";
import type { CSSProperties } from "react";

import { apiEnvelopeRequest, apiRequest, readErrorMessage } from "@/app/lib/api";
import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";
import type { Wallet } from "@/app/lib/types";
import { Button } from "@/app/ui/components/button";
import {
  GAME_ACCOUNT_HISTORY_DESCRIPTORS,
  readGameReplayStateKey,
  readGameReportingDescriptor,
  readPlayerGameReplayEndpoint,
  renderPlayerGameReplay,
  type GameAccountHistoryItem,
  type GameReplayPayload,
} from "@/app/ui/game-reporting-registry";
import { resolvePlayerGameDisplayName } from "@/app/ui/player-game-registry";

type PlayerProfile = {
  id: string;
  email: string;
  role: string;
  status: string;
  first_name: string | null;
  last_name: string | null;
  fiscal_code: string | null;
  phone_number: string | null;
  created_at: string;
};

type StatementCategory = "all" | "deposits_withdrawals" | "game" | "bonus" | "adjustments";
type StatementWalletType = "cash" | "bonus";
type StatementPeriod = "today" | "last_7_days" | "last_30_days" | "current_month" | "previous_month" | "custom";

type StatementMovement = {
  id: string;
  movement_family: "game" | "bonus" | "adjustment" | "deposit" | "withdrawal";
  movement_label: string;
  description: string;
  code: string;
  causale: string;
  movement_type: string;
  wallet_type: StatementWalletType;
  currency_code: string;
  started_at: string;
  competency_at: string;
  show_competency_at: boolean;
  detail_count: number;
  show_detail_count: boolean;
  debit_amount: string;
  credit_amount: string;
  net_amount: string;
  balance_after: string;
  expandable: boolean;
  contains_adjustments: boolean;
};

type StatementMeta = PaginationMeta & {
  category: StatementCategory;
  wallet_type: StatementWalletType;
  period: StatementPeriod;
  date_from: string;
  date_to: string;
  balance_disclaimer: string | null;
};

type StatementDetailItem = {
  id: string;
  item_type: "game_round" | "transaction";
  timestamp: string;
  competency_at?: string;
  round_code?: string;
  platform_round_id?: string;
  game_code?: string;
  title_code?: string;
  site_code?: string;
  result?: string;
  grid_size?: number;
  mine_count?: number;
  safe_reveals_count?: number;
  bet_amount?: string;
  win_amount?: string;
  transaction_code?: string;
  transaction_type?: string;
  debit_amount: string;
  credit_amount: string;
  net_amount: string;
  balance_after: string;
  wallet_type: StatementWalletType;
  currency_code: string;
  contains_adjustments?: boolean;
  game_summary?: string;
};

type StatementMovementDetail = {
  movement_id: string;
  movement_family: StatementMovement["movement_family"];
  items: StatementDetailItem[];
};

type StatementDetailState = {
  items: StatementDetailItem[];
  nextCursor: string | null;
  loading: boolean;
  error: string | null;
};

type SessionHistoryItem = GameAccountHistoryItem;

type AccessSessionStatementGroup = {
  id: string;
  accessSessionId: string | null;
  status: "active" | "closed" | "timed_out" | "no_access_session";
  startedAt: string;
  endedAt: string | null;
  rounds: SessionHistoryItem[];
  roundsCount: number;
  totalStaked: number;
  totalWon: number;
};

type GameRoundReplay = GameReplayPayload;

type ReplayState = {
  replay: GameRoundReplay | null;
  loading: boolean;
  error: string | null;
};

type PaginationMeta = {
  next_cursor: string | null;
  limit: number;
};

type AccountTab = "overview" | "profile" | "security" | "wallets" | "gameHistory";

type StatementCategoryOption = { id: StatementCategory; label: string };

const ACCOUNT_TABS: Array<{ id: AccountTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profilo" },
  { id: "security", label: "Sicurezza" },
  { id: "wallets", label: "Cassa" },
  { id: "gameHistory", label: "Storico gioco" },
];

const STATEMENT_CATEGORY_OPTIONS: StatementCategoryOption[] = [
  { id: "all", label: "Tutte le causali" },
  { id: "deposits_withdrawals", label: "Depositi e prelievi" },
  { id: "game", label: "Gioco" },
  { id: "bonus", label: "Bonus" },
  { id: "adjustments", label: "Rettifiche" },
];

const STATEMENT_WALLET_OPTIONS: Array<{ id: StatementWalletType; label: string }> = [
  { id: "cash", label: "Saldo reale" },
  { id: "bonus", label: "Bonus" },
];

const STATEMENT_PERIOD_OPTIONS: Array<{ id: StatementPeriod; label: string }> = [
  { id: "today", label: "Oggi" },
  { id: "last_7_days", label: "Ultimi 7 giorni" },
  { id: "last_30_days", label: "Ultimi 30 giorni" },
  { id: "current_month", label: "Mese corrente" },
  { id: "previous_month", label: "Mese precedente" },
];

function readStoredProfileValue(key: (typeof PLAYER_STORAGE_KEYS)[keyof typeof PLAYER_STORAGE_KEYS]): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

function readPaginationMeta(meta: unknown): PaginationMeta {
  if (!meta || typeof meta !== "object") {
    return { next_cursor: null, limit: 0 };
  }

  const candidate = meta as Partial<PaginationMeta>;
  return {
    next_cursor: typeof candidate.next_cursor === "string" ? candidate.next_cursor : null,
    limit: typeof candidate.limit === "number" ? candidate.limit : 0,
  };
}

function readStatementMeta(meta: unknown): StatementMeta {
  const pagination = readPaginationMeta(meta);
  if (!meta || typeof meta !== "object") {
    return {
      ...pagination,
      category: "all",
      wallet_type: "cash",
      period: "last_30_days",
      date_from: "",
      date_to: "",
      balance_disclaimer: null,
    };
  }

  const candidate = meta as Partial<StatementMeta>;
  return {
    ...pagination,
    category: readStatementCategory(candidate.category),
    wallet_type: readStatementWalletType(candidate.wallet_type),
    period: readStatementPeriod(candidate.period),
    date_from: typeof candidate.date_from === "string" ? candidate.date_from : "",
    date_to: typeof candidate.date_to === "string" ? candidate.date_to : "",
    balance_disclaimer:
      typeof candidate.balance_disclaimer === "string" ? candidate.balance_disclaimer : null,
  };
}

export function PlayerAccountPage() {
  const [accessToken, setAccessToken] = useState("");
  const [currentEmail, setCurrentEmail] = useState("");
  const [activeTab, setActiveTab] = useState<AccountTab>("overview");
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [statementMovements, setStatementMovements] = useState<StatementMovement[]>([]);
  const [statementMeta, setStatementMeta] = useState<StatementMeta | null>(null);
  const [statementNextCursor, setStatementNextCursor] = useState<string | null>(null);
  const [statementCategory, setStatementCategory] = useState<StatementCategory>("all");
  const [statementWalletType, setStatementWalletType] = useState<StatementWalletType>("cash");
  const [statementPeriod, setStatementPeriod] = useState<StatementPeriod>("last_30_days");
  const [expandedStatementMovementIds, setExpandedStatementMovementIds] = useState<string[]>([]);
  const [statementMovementDetails, setStatementMovementDetails] = useState<Record<string, StatementDetailState>>({});
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [gameHistoryNextCursors, setGameHistoryNextCursors] = useState<Record<string, string | null>>({});
  const [expandedStatementGroupIds, setExpandedStatementGroupIds] = useState<string[]>([]);
  const [expandedReplayRoundIds, setExpandedReplayRoundIds] = useState<string[]>([]);
  const [roundReplayStates, setRoundReplayStates] = useState<Record<string, ReplayState>>({});
  const [loading, setLoading] = useState(false);
  const [loadingStatement, setLoadingStatement] = useState(false);
  const [loadingMoreStatement, setLoadingMoreStatement] = useState(false);
  const [loadingMoreSessions, setLoadingMoreSessions] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordStatus, setPasswordStatus] = useState<string | null>(null);

  async function loadAccountState(token: string) {
    setLoading(true);
    setStatus(null);

    try {
      const [profileData, walletData, statementPage, ...gameHistoryPages] = await Promise.all([
        apiRequest<PlayerProfile>("/auth/me", {}, token),
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiEnvelopeRequest<StatementMovement[]>(
          buildStatementMovementsPath({
            category: statementCategory,
            walletType: statementWalletType,
            period: statementPeriod,
            limit: 10,
          }),
          {},
          token,
        ),
        ...GAME_ACCOUNT_HISTORY_DESCRIPTORS.map((descriptor) =>
          apiEnvelopeRequest<unknown[]>(
            descriptor.buildPlayerHistoryPath({ limit: 10 }),
            {},
            token,
          ),
        ),
      ]);

      setProfile(profileData);
      setWallets(walletData);
      setStatementMovements(statementPage.data);
      setStatementMeta(readStatementMeta(statementPage.meta));
      setStatementNextCursor(readPaginationMeta(statementPage.meta).next_cursor);
      setExpandedStatementMovementIds([]);
      setStatementMovementDetails({});
      setSessions(mergeGameHistory(
        [],
        gameHistoryPages.flatMap((page, index) =>
          GAME_ACCOUNT_HISTORY_DESCRIPTORS[index].mapPlayerHistoryItems(page.data),
        ),
      ));
      setGameHistoryNextCursors(Object.fromEntries(
        gameHistoryPages.map((page, index) => [
          GAME_ACCOUNT_HISTORY_DESCRIPTORS[index].gameCode,
          readPaginationMeta(page.meta).next_cursor,
        ]),
      ));
      setExpandedReplayRoundIds([]);
      setRoundReplayStates({});
    } catch (error) {
      setStatus(readErrorMessage(error, "Account loading failed."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const storedToken = readStoredProfileValue(PLAYER_STORAGE_KEYS.accessToken);
    const storedEmail = readStoredProfileValue(PLAYER_STORAGE_KEYS.email);

    setAccessToken(storedToken);
    setCurrentEmail(storedEmail);

    if (storedToken) {
      void loadAccountState(storedToken);
    }
  }, []);

  const firstName = profile?.first_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.firstName);
  const lastName = profile?.last_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.lastName);
  const fiscalCode = profile?.fiscal_code ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.fiscalCode);
  const phoneNumber = profile?.phone_number ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.phoneNumber);
  const statementGroups = useMemo(() => buildAccessSessionStatementGroups(sessions), [sessions]);
  const primaryWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "cash") ?? wallets[0] ?? null,
    [wallets],
  );
  const cashWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "cash") ?? null,
    [wallets],
  );
  const bonusWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null,
    [wallets],
  );
  const latestStatementGroup = statementGroups[0] ?? null;
  const latestStatementMovement = statementMovements[0] ?? null;
  const availableStatementCategoryOptions = useMemo(
    () => readAvailableStatementCategoryOptions(statementWalletType),
    [statementWalletType],
  );

  function toggleStatementGroup(groupId: string) {
    setExpandedStatementGroupIds((current) =>
      current.includes(groupId)
        ? current.filter((entry) => entry !== groupId)
        : [...current, groupId],
    );
  }

  function toggleRoundReplay(round: SessionHistoryItem) {
    const roundId = readGameReplayStateKey(round);
    const isExpanded = expandedReplayRoundIds.includes(roundId);
    setExpandedReplayRoundIds((current) =>
      current.includes(roundId)
        ? current.filter((entry) => entry !== roundId)
        : [...current, roundId],
    );

    if (!isExpanded && !roundReplayStates[roundId]?.replay) {
      void loadRoundReplay(round);
    }
  }

  async function loadRoundReplay(round: SessionHistoryItem) {
    if (!accessToken) {
      return;
    }
    const replayStateKey = readGameReplayStateKey(round);
    const endpoint = readPlayerGameReplayEndpoint(round);
    if (!endpoint) {
      setRoundReplayStates((current) => ({
        ...current,
        [replayStateKey]: {
          replay: current[replayStateKey]?.replay ?? null,
          loading: false,
          error: `Replay unavailable for ${round.game_code}.`,
        },
      }));
      return;
    }

    setRoundReplayStates((current) => ({
      ...current,
      [replayStateKey]: {
        replay: current[replayStateKey]?.replay ?? null,
        loading: true,
        error: null,
      },
    }));

    try {
      const replay = await apiRequest<GameRoundReplay>(
        endpoint,
        {},
        accessToken,
      );
      setRoundReplayStates((current) => ({
        ...current,
        [replayStateKey]: {
          replay,
          loading: false,
          error: null,
        },
      }));
    } catch (error) {
      setRoundReplayStates((current) => ({
        ...current,
        [replayStateKey]: {
          replay: current[replayStateKey]?.replay ?? null,
          loading: false,
          error: readErrorMessage(error, "Caricamento replay fallito."),
        },
      }));
    }
  }

  async function refreshStatementMovements(
    nextCategory: StatementCategory = statementCategory,
    nextWalletType: StatementWalletType = statementWalletType,
    nextPeriod: StatementPeriod = statementPeriod,
  ) {
    if (!accessToken) {
      return;
    }

    setLoadingStatement(true);
    setStatus(null);

    try {
      const page = await apiEnvelopeRequest<StatementMovement[]>(
        buildStatementMovementsPath({
          category: nextCategory,
          walletType: nextWalletType,
          period: nextPeriod,
          limit: 10,
        }),
        {},
        accessToken,
      );
      setStatementMovements(page.data);
      setStatementMeta(readStatementMeta(page.meta));
      setStatementNextCursor(readPaginationMeta(page.meta).next_cursor);
      setExpandedStatementMovementIds([]);
      setStatementMovementDetails({});
    } catch (error) {
      setStatus(readErrorMessage(error, "Caricamento movimenti fallito."));
    } finally {
      setLoadingStatement(false);
    }
  }

  async function loadMoreStatementMovements() {
    if (!accessToken || !statementNextCursor) {
      return;
    }

    setLoadingMoreStatement(true);
    setStatus(null);

    try {
      const page = await apiEnvelopeRequest<StatementMovement[]>(
        buildStatementMovementsPath({
          category: statementCategory,
          walletType: statementWalletType,
          period: statementPeriod,
          limit: 10,
          cursor: statementNextCursor,
        }),
        {},
        accessToken,
      );
      setStatementMovements((current) => [...current, ...page.data]);
      setStatementMeta(readStatementMeta(page.meta));
      setStatementNextCursor(readPaginationMeta(page.meta).next_cursor);
    } catch (error) {
      setStatus(readErrorMessage(error, "Caricamento movimenti fallito."));
    } finally {
      setLoadingMoreStatement(false);
    }
  }

  function handleStatementCategoryChange(nextCategory: StatementCategory) {
    if (!isStatementCategoryAvailableForWallet(nextCategory, statementWalletType)) {
      return;
    }

    setStatementCategory(nextCategory);
    void refreshStatementMovements(nextCategory, statementWalletType, statementPeriod);
  }

  function handleStatementWalletTypeChange(nextWalletType: StatementWalletType) {
    const nextCategory = isStatementCategoryAvailableForWallet(statementCategory, nextWalletType)
      ? statementCategory
      : "all";

    setStatementWalletType(nextWalletType);
    setStatementCategory(nextCategory);
    void refreshStatementMovements(nextCategory, nextWalletType, statementPeriod);
  }

  function handleStatementPeriodChange(nextPeriod: StatementPeriod) {
    setStatementPeriod(nextPeriod);
    void refreshStatementMovements(statementCategory, statementWalletType, nextPeriod);
  }

  function toggleStatementMovement(movement: StatementMovement) {
    if (!movement.expandable) {
      return;
    }

    const isExpanded = expandedStatementMovementIds.includes(movement.id);
    setExpandedStatementMovementIds((current) =>
      current.includes(movement.id)
        ? current.filter((entry) => entry !== movement.id)
        : [...current, movement.id],
    );

    if (!isExpanded && !statementMovementDetails[movement.id]) {
      void loadStatementMovementDetail(movement);
    }
  }

  async function loadStatementMovementDetail(movement: StatementMovement, cursor?: string) {
    if (!accessToken) {
      return;
    }

    setStatementMovementDetails((current) => ({
      ...current,
      [movement.id]: {
        items: cursor ? (current[movement.id]?.items ?? []) : [],
        nextCursor: current[movement.id]?.nextCursor ?? null,
        loading: true,
        error: null,
      },
    }));

    try {
      const query = new URLSearchParams({
        wallet_type: movement.wallet_type,
        limit: "50",
      });
      if (cursor) {
        query.set("cursor", cursor);
      }

      const page = await apiEnvelopeRequest<StatementMovementDetail>(
        `/account/statement-movements/${encodeURIComponent(movement.id)}?${query.toString()}`,
        {},
        accessToken,
      );
      const nextCursor = readPaginationMeta(page.meta).next_cursor;
      setStatementMovementDetails((current) => ({
        ...current,
        [movement.id]: {
          items: cursor
            ? [...(current[movement.id]?.items ?? []), ...page.data.items]
            : page.data.items,
          nextCursor,
          loading: false,
          error: null,
        },
      }));
    } catch (error) {
      setStatementMovementDetails((current) => ({
        ...current,
        [movement.id]: {
          items: current[movement.id]?.items ?? [],
          nextCursor: current[movement.id]?.nextCursor ?? null,
          loading: false,
          error: readErrorMessage(error, "Caricamento dettaglio fallito."),
        },
      }));
    }
  }

  async function loadMoreSessions() {
    const hasNextPage = GAME_ACCOUNT_HISTORY_DESCRIPTORS.some(
      (descriptor) => gameHistoryNextCursors[descriptor.gameCode],
    );
    if (!accessToken || !hasNextPage) {
      return;
    }

    setLoadingMoreSessions(true);
    setStatus(null);

    try {
      const pageResults = await Promise.all(
        GAME_ACCOUNT_HISTORY_DESCRIPTORS.map(async (descriptor) => {
          const cursor = gameHistoryNextCursors[descriptor.gameCode];
          if (!cursor) {
            return null;
          }
          const page = await apiEnvelopeRequest<unknown[]>(
            descriptor.buildPlayerHistoryPath({ limit: 10, cursor }),
            {},
            accessToken,
          );
          return { descriptor, page };
        }),
      );
      setSessions((current) =>
        mergeGameHistory(
          current,
          pageResults.flatMap((result) =>
            result ? result.descriptor.mapPlayerHistoryItems(result.page.data) : [],
          ),
        ),
      );
      setGameHistoryNextCursors((current) => ({
        ...current,
        ...Object.fromEntries(
          pageResults
            .filter((result): result is NonNullable<typeof result> => result !== null)
            .map((result) => [
              result.descriptor.gameCode,
              readPaginationMeta(result.page.meta).next_cursor,
            ]),
        ),
      }));
    } catch (error) {
      setStatus(readErrorMessage(error, "Caricamento storico gioco fallito."));
    } finally {
      setLoadingMoreSessions(false);
    }
  }

  async function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!accessToken) {
      setPasswordStatus("Sessione player non disponibile.");
      return;
    }

    setPasswordBusy(true);
    setPasswordStatus(null);

    try {
      await apiRequest<{ password_changed: boolean }>(
        "/auth/password/change",
        {
          method: "POST",
          body: JSON.stringify({
            old_password: currentPassword,
            new_password: newPassword,
          }),
        },
        accessToken,
      );
      setCurrentPassword("");
      setNewPassword("");
      setPasswordStatus("Password aggiornata correttamente.");
    } catch (error) {
      setPasswordStatus(readErrorMessage(error, "Cambio password fallito."));
    } finally {
      setPasswordBusy(false);
    }
  }

  function renderRoundReplay(round: SessionHistoryItem) {
    const replayState = roundReplayStates[readGameReplayStateKey(round)];

    if (replayState?.loading && !replayState.replay) {
      return <div className="status-line">Caricamento replay mano...</div>;
    }
    if (replayState?.error) {
      return <div className="status-line">{replayState.error}</div>;
    }
    if (!replayState?.replay) {
      return null;
    }

    return renderPlayerGameReplay(round.game_code, replayState.replay);
  }

  function renderActiveTab() {
    if (activeTab === "overview") {
      return (
        <div className="player-account-overview stack">
          {loading && !profile ? <div className="status-line">Caricamento account...</div> : null}

          <div className="player-account-summary-grid">
            <article className="player-account-summary-card">
              <span className="player-account-summary-label">Saldo disponibile</span>
              {primaryWallet ? (
                <>
                  <strong className="player-account-summary-value">
                    {formatChipAmount(toNumericAmount(primaryWallet.balance_snapshot))} CHIP
                  </strong>
                  <span className="player-account-summary-meta">
                    {readWalletTypeLabel(primaryWallet.wallet_type)}
                  </span>
                </>
              ) : (
                <>
                  <strong className="player-account-summary-value">-</strong>
                  <span className="player-account-summary-meta">Nessun wallet caricato</span>
                </>
              )}
              {wallets.length > 0 ? (
                <div className="player-account-wallet-strip" aria-label="Saldi wallet caricati">
                  {wallets.map((wallet) => (
                    <span key={wallet.wallet_type}>
                      {readWalletTypeLabel(wallet.wallet_type)} -{" "}
                      {formatChipAmount(toNumericAmount(wallet.balance_snapshot))} CHIP
                    </span>
                  ))}
                </div>
              ) : null}
            </article>

            <article className="player-account-summary-card">
              <span className="player-account-summary-label">Ultima sessione gioco</span>
              {latestStatementGroup ? (
                <>
                  <strong
                    className={`player-account-summary-value ${readStatementGroupResultClassName(
                      latestStatementGroup,
                    )}`}
                  >
                    {readStatementGroupResultLabel(latestStatementGroup)}
                  </strong>
                  <span className="player-account-summary-meta">
                    {latestStatementGroup.roundsCount} round - {formatDateTime(latestStatementGroup.startedAt)}
                  </span>
                  <span className="player-account-summary-detail">
                    Giocato {formatChipAmount(latestStatementGroup.totalStaked)} CHIP - Vinto{" "}
                    {formatChipAmount(latestStatementGroup.totalWon)} CHIP
                  </span>
                </>
              ) : (
                <>
                  <strong className="player-account-summary-value">-</strong>
                  <span className="player-account-summary-meta">Nessuna sessione caricata</span>
                </>
              )}
            </article>

            <article className="player-account-summary-card">
              <span className="player-account-summary-label">Attivita' recente</span>
              <strong className="player-account-summary-value">{statementMovements.length}</strong>
              <span className="player-account-summary-meta">
                {statementMovements.length === 1 ? "movimento caricato" : "movimenti caricati"}
              </span>
              {latestStatementMovement ? (
                <span className="player-account-summary-detail">
                  Ultimo: {latestStatementMovement.movement_label} -{" "}
                  {formatDateTime(latestStatementMovement.started_at)}
                </span>
              ) : (
                <span className="player-account-summary-detail">Nessun movimento caricato</span>
              )}
            </article>
          </div>

          <article className="player-account-detail-panel">
            <h3>Dettagli account</h3>
            <div className="player-account-detail-actions">
              <Button type="button" variant="secondary" onClick={() => setActiveTab("wallets")}>
                Cassa
              </Button>
              <Button type="button" variant="secondary" onClick={() => setActiveTab("gameHistory")}>
                Storico gioco
              </Button>
              <Button type="button" variant="secondary" onClick={() => setActiveTab("profile")}>
                Profilo
              </Button>
              <Button type="button" variant="secondary" onClick={() => setActiveTab("security")}>
                Sicurezza
              </Button>
            </div>
          </article>
        </div>
      );
    }

    if (activeTab === "profile") {
      return (
        <div className="stack">
          <h3 style={{ marginBottom: 0 }}>Player profile</h3>
          <div className="panel player-profile-grid">
            <div>
              <strong>Name</strong>
              <div>{`${firstName} ${lastName}`.trim() || "-"}</div>
            </div>
            <div>
              <strong>Email</strong>
              <div>{profile?.email || currentEmail || "-"}</div>
            </div>
            <div>
              <strong>Fiscal code</strong>
              <div>{fiscalCode || "-"}</div>
            </div>
            <div>
              <strong>Phone</strong>
              <div>{phoneNumber || "-"}</div>
            </div>
          </div>
        </div>
      );
    }

    if (activeTab === "security") {
      return (
        <div className="stack">
          <h3 style={{ marginBottom: 0 }}>Security</h3>
          <form className="form-card stack" onSubmit={(event) => void handlePasswordChange(event)}>
            <div className="field-grid player-form-fields">
              <label>
                <span>Password attuale</span>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  autoComplete="current-password"
                />
              </label>
              <label>
                <span>Nuova password</span>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                />
              </label>
            </div>
            <div className="player-form-actions">
              <Button type="submit" disabled={passwordBusy} isLoading={passwordBusy}>
                Cambia password
              </Button>
            </div>
            {passwordStatus ? <div className="status-line">{passwordStatus}</div> : null}
          </form>
        </div>
      );
    }

    if (activeTab === "wallets") {
      return (
        <div className="player-account-cashier stack">
          <div className="player-account-cashier-head">
            <h3>Cassa</h3>
            <span className="player-account-summary-meta">
              {statementMeta ? `${statementMeta.date_from} - ${statementMeta.date_to}` : "Movimenti"}
            </span>
          </div>

          <div className="player-account-cashier-wallets" aria-label="Saldi wallet">
            <article className="player-account-cashier-wallet">
              <span>Saldo reale</span>
              <strong>
                {cashWallet ? formatChipAmount(toNumericAmount(cashWallet.balance_snapshot)) : "0.00"} CHIP
              </strong>
            </article>
            <article className="player-account-cashier-wallet">
              <span>Bonus</span>
              <strong>
                {bonusWallet ? formatChipAmount(toNumericAmount(bonusWallet.balance_snapshot)) : "0.00"} CHIP
              </strong>
            </article>
          </div>

          <div className="player-account-cashier-toolbar">
            <div className="player-account-filter-group" aria-label="Causale movimento">
              {availableStatementCategoryOptions.map((option) => (
                <button
                  key={option.id}
                  className={`player-account-filter-button${
                    statementCategory === option.id ? " is-active" : ""
                  }`}
                  type="button"
                  onClick={() => handleStatementCategoryChange(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="player-account-filter-row">
              <div className="player-account-filter-group" aria-label="Wallet movimento">
                {STATEMENT_WALLET_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    className={`player-account-filter-button${
                      statementWalletType === option.id ? " is-active" : ""
                    }`}
                    type="button"
                    onClick={() => handleStatementWalletTypeChange(option.id)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              <label className="player-account-period-field">
                <span>Periodo</span>
                <select
                  value={statementPeriod}
                  onChange={(event) =>
                    handleStatementPeriodChange(readStatementPeriod(event.currentTarget.value))
                  }
                >
                  {STATEMENT_PERIOD_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {statementMeta?.balance_disclaimer ? (
            <div className="player-account-disclaimer">{statementMeta.balance_disclaimer}</div>
          ) : null}

          {loadingStatement ? <div className="status-line">Caricamento movimenti...</div> : null}

          {statementMovements.length === 0 ? (
            <p className="player-account-empty">Nessun movimento nel periodo selezionato.</p>
          ) : (
            <div className="player-account-cashier-list">
              {statementMovements.map((movement) => {
                const isExpanded = expandedStatementMovementIds.includes(movement.id);
                const detail = statementMovementDetails[movement.id];
                const detailId = `cashier-detail-${movement.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
                const isGameMovement = movement.movement_family === "game";
                const amountLabels = readStatementAmountLabels(movement);

                return (
                  <article key={movement.id} className="player-account-cashier-row">
                    <div className="player-account-cashier-row-main">
                      <div className="player-account-cashier-date">
                        {isGameMovement ? (
                          <>
                            <small>Inizio sessione</small>
                            <span>{formatDateTime(movement.started_at)}</span>
                            <small>
                              Fine sessione{" "}
                              {movement.show_competency_at ? formatDateTime(movement.competency_at) : "-"}
                            </small>
                          </>
                        ) : (
                          <>
                            <small>Data movimento</small>
                            <span>{formatDateTime(movement.started_at)}</span>
                          </>
                        )}
                      </div>

                      <div className="player-account-cashier-description">
                        <strong>{movement.movement_label}</strong>
                        <span>
                          {movement.description} - {movement.code}
                        </span>
                        <div className="player-account-cashier-tags">
                          <span>{movement.causale}</span>
                          <span>{readStatementWalletLabel(movement.wallet_type)}</span>
                          {movement.show_detail_count ? <span>{movement.detail_count} dettagli</span> : null}
                          {movement.contains_adjustments ? <span>Rettifiche</span> : null}
                        </div>
                      </div>

                      <div className="player-account-cashier-amounts">
                        <div className="player-account-cashier-amount is-debit">
                          <span>{amountLabels.debit}</span>
                          <strong>{formatDebitCreditAmount(movement.debit_amount)}</strong>
                        </div>
                        <div className="player-account-cashier-amount is-credit">
                          <span>{amountLabels.credit}</span>
                          <strong>{formatDebitCreditAmount(movement.credit_amount)}</strong>
                        </div>
                        <div className={`player-account-cashier-amount is-net ${readStatementNetClassName(
                          movement,
                        )}`}>
                          <span>{amountLabels.net}</span>
                          <strong>{formatStatementNetAmount(movement)}</strong>
                        </div>
                        <div className="player-account-cashier-amount">
                          <span>Saldo finale</span>
                          <strong>{formatChipAmount(toNumericAmount(movement.balance_after))} CHIP</strong>
                        </div>
                      </div>

                      <Button
                        aria-controls={detailId}
                        aria-expanded={isExpanded}
                        type="button"
                        variant="secondary"
                        onClick={() => toggleStatementMovement(movement)}
                        disabled={!movement.expandable}
                      >
                        {isExpanded ? "Chiudi" : "Dettaglio"}
                      </Button>
                    </div>

                    {isExpanded ? (
                      <div id={detailId} className="player-account-cashier-detail">
                        {detail?.error ? <div className="status-line">{detail.error}</div> : null}
                        {detail?.loading && detail.items.length === 0 ? (
                          <div className="status-line">Caricamento dettaglio...</div>
                        ) : null}
                        {detail && detail.items.length > 0 ? (
                          <div className="player-account-cashier-detail-list">
                            {detail.items.map((item) => (
                              <article key={item.id} className="player-account-cashier-detail-row">
                                <div>
                                  <strong>{readStatementDetailTitle(item)}</strong>
                                  <span>{readStatementDetailMeta(item)}</span>
                                </div>
                                <div className="player-account-cashier-detail-amounts">
                                  <span>{formatStatementDetailNetAmount(item.net_amount)}</span>
                                  <span>Saldo {formatChipAmount(toNumericAmount(item.balance_after))} CHIP</span>
                                </div>
                              </article>
                            ))}
                          </div>
                        ) : null}
                        {detail?.nextCursor ? (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => void loadStatementMovementDetail(movement, detail.nextCursor ?? undefined)}
                            disabled={detail.loading}
                            isLoading={detail.loading}
                          >
                            Carica altri dettagli
                          </Button>
                        ) : null}
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          )}

          {statementNextCursor ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => void loadMoreStatementMovements()}
              disabled={loadingMoreStatement}
              isLoading={loadingMoreStatement}
            >
              Carica altri movimenti
            </Button>
          ) : null}
        </div>
      );
    }

    return (
      <div className="player-account-statement stack">
        <article className="panel stack player-account-statement-panel">
          <div className="player-account-statement-head">
            <h3>Storico gioco</h3>
          </div>

          {statementGroups.length === 0 ? (
            <p className="player-account-empty">Nessuna sessione caricata.</p>
          ) : (
            <div className="player-account-statement-list">
              {statementGroups.map((group) => {
                const isExpanded = expandedStatementGroupIds.includes(group.id);
                const resultClassName = readStatementGroupResultClassName(group);
                const detailId = `statement-detail-${group.id}`;

                return (
                  <article key={group.id} className="player-account-statement-card">
                    <div className="player-account-statement-main">
                      <div className="player-account-statement-title">
                        <span className="player-account-summary-label">Sessione</span>
                        <h4>{readGroupGameLabel(group)} - {formatDateTime(group.startedAt)}</h4>
                        <span className="player-account-summary-meta">
                          {group.accessSessionId
                            ? `ID accesso ${group.accessSessionId.slice(0, 8)}`
                            : "Sessione diretta"}
                        </span>
                      </div>
                      <span className="player-account-statement-status">
                        {readAccessSessionStatusLabel(group.status)}
                      </span>
                    </div>

                    <div className="player-account-statement-metrics">
                      <div className="player-account-statement-metric">
                        <span>Round</span>
                        <strong>{group.roundsCount}</strong>
                      </div>
                      <div className="player-account-statement-metric">
                        <span>Giocato</span>
                        <strong>{formatChipAmount(group.totalStaked)} CHIP</strong>
                      </div>
                      <div className="player-account-statement-metric">
                        <span>Vinto</span>
                        <strong>{formatChipAmount(group.totalWon)} CHIP</strong>
                      </div>
                      <div className="player-account-statement-metric">
                        <span>Risultato</span>
                        <strong className={resultClassName}>{readStatementGroupResultLabel(group)}</strong>
                      </div>
                    </div>

                    <div className="player-account-statement-actions">
                      <span className="player-account-summary-meta">
                        Chiusura: {group.endedAt ? formatDateTime(group.endedAt) : "in corso"}
                      </span>
                      <Button
                        aria-controls={detailId}
                        aria-expanded={isExpanded}
                        type="button"
                        variant="secondary"
                        onClick={() => toggleStatementGroup(group.id)}
                      >
                        {isExpanded ? "Nascondi dettaglio" : "Mostra dettaglio"}
                      </Button>
                    </div>
                    {isExpanded ? (
                      <div id={detailId} className="player-account-statement-detail">
                        <div className="player-account-statement-meta-grid">
                          <div>
                            <span>Avvio</span>
                            <strong>{formatDateTime(group.startedAt)}</strong>
                          </div>
                          <div>
                            <span>Chiusura</span>
                            <strong>{group.endedAt ? formatDateTime(group.endedAt) : "In corso"}</strong>
                          </div>
                          <div>
                            <span>ID accesso</span>
                            <strong>{group.accessSessionId ? group.accessSessionId.slice(0, 8) : "Diretta"}</strong>
                          </div>
                        </div>

                        <div className="player-account-round-table-shell">
                          <table className="player-account-round-table">
                            <thead>
                              <tr>
                                <th style={TABLE_HEADER_STYLE}>Data round</th>
                                <th style={TABLE_HEADER_STYLE}>Round</th>
                                <th style={TABLE_HEADER_STYLE}>Config</th>
                                <th style={TABLE_HEADER_STYLE}>Progress</th>
                                <th style={TABLE_HEADER_STYLE}>Puntata</th>
                                <th style={TABLE_HEADER_STYLE}>Esito</th>
                                <th style={TABLE_HEADER_STYLE}>Payout</th>
                                <th style={TABLE_HEADER_STYLE}>Replay</th>
                              </tr>
                            </thead>
                            <tbody>
                              {group.rounds.map((round) => {
                                const replayKey = readGameReplayStateKey(round);
                                const replayExpanded = expandedReplayRoundIds.includes(replayKey);
                                const replayButtonLabel = replayExpanded ? "Chiudi replay" : "Rivedi mano";

                                return (
                                  <Fragment key={replayKey}>
                                    <tr>
                                      <td style={TABLE_CELL_STYLE}>{formatDateTime(round.created_at)}</td>
                                      <td style={TABLE_CELL_STYLE}>
                                        <div>{round.game_session_id.slice(0, 8)}</div>
                                        <div style={TABLE_META_STYLE}>{readWalletTypeLabel(round.wallet_type)}</div>
                                      </td>
                                      <td style={TABLE_CELL_STYLE}>{readRoundConfigLabel(round)}</td>
                                      <td style={TABLE_CELL_STYLE}>{readRoundRevealLabel(round)}</td>
                                      <td style={TABLE_CELL_STYLE}>
                                        {formatChipAmount(toNumericAmount(round.bet_amount))} CHIP
                                      </td>
                                      <td style={TABLE_CELL_STYLE}>{readRoundStatusLabel(round.status)}</td>
                                      <td style={TABLE_CELL_STYLE}>{readRoundPayoutLabel(round)}</td>
                                      <td style={TABLE_CELL_STYLE}>
                                        <Button
                                          aria-expanded={replayExpanded}
                                          type="button"
                                          variant="secondary"
                                          onClick={() => toggleRoundReplay(round)}
                                        >
                                          {replayButtonLabel}
                                        </Button>
                                      </td>
                                    </tr>
                                    {replayExpanded ? (
                                      <tr className="player-account-round-replay-row">
                                        <td colSpan={8}>{renderRoundReplay(round)}</td>
                                      </tr>
                                    ) : null}
                                  </Fragment>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>

                        <div className="player-account-round-card-list">
                          {group.rounds.map((round) => {
                            const replayExpanded = expandedReplayRoundIds.includes(readGameReplayStateKey(round));
                            return (
                              <article key={readGameReplayStateKey(round)} className="player-account-round-card">
                                <div className="player-account-round-card-head">
                                  <strong>Round {round.game_session_id.slice(0, 8)}</strong>
                                  <span>{readRoundStatusLabel(round.status)}</span>
                                </div>
                                <div className="player-account-round-card-grid">
                                  <div>
                                    <span>Data</span>
                                    <strong>{formatDateTime(round.created_at)}</strong>
                                  </div>
                                  <div>
                                    <span>Wallet</span>
                                    <strong>{readWalletTypeLabel(round.wallet_type)}</strong>
                                  </div>
                                  <div>
                                    <span>Config</span>
                                    <strong>{readRoundConfigLabel(round)}</strong>
                                  </div>
                                  <div>
                                    <span>Progress</span>
                                    <strong>{readRoundRevealLabel(round)}</strong>
                                  </div>
                                  <div>
                                    <span>Puntata</span>
                                    <strong>{formatChipAmount(toNumericAmount(round.bet_amount))} CHIP</strong>
                                  </div>
                                  <div>
                                    <span>Payout</span>
                                    <strong>{readRoundPayoutLabel(round)}</strong>
                                  </div>
                                </div>
                                <div className="player-account-round-card-actions">
                                  <Button
                                    aria-expanded={replayExpanded}
                                    type="button"
                                    variant="secondary"
                                    onClick={() => toggleRoundReplay(round)}
                                  >
                                    {replayExpanded ? "Chiudi replay" : "Rivedi mano"}
                                  </Button>
                                </div>
                                {replayExpanded ? renderRoundReplay(round) : null}
                              </article>
                            );
                          })}
                        </div>
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          )}
          {GAME_ACCOUNT_HISTORY_DESCRIPTORS.some((descriptor) => gameHistoryNextCursors[descriptor.gameCode]) ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => void loadMoreSessions()}
              disabled={loadingMoreSessions}
              isLoading={loadingMoreSessions}
            >
              Carica altre sessioni
            </Button>
          ) : null}
        </article>
      </div>
    );
  }

  return (
    <section className="panel stack player-account-page">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Account</h2>
        <p style={{ margin: 0 }}>Saldo, attivita' recente e dettagli account.</p>
      </div>

      {!accessToken ? (
        <div className="stack">
          <div className="status-line">Guest access</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <Button href="/login">Sign in</Button>
            <Button href="/register" variant="secondary">
              Register
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <div className="status-line">{profile?.email || currentEmail || "Player session"}</div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void loadAccountState(accessToken)}
              disabled={loading}
              isLoading={loading}
            >
              Refresh
            </Button>
          </div>

          {status ? <div className="status-line">{status}</div> : null}

          <div className="tab-bar" aria-label="Account sections" role="tablist">
            {ACCOUNT_TABS.map((tab) => (
              <button
                key={tab.id}
                aria-selected={activeTab === tab.id}
                className={`tab-button${activeTab === tab.id ? " is-active" : ""}`}
                role="tab"
                type="button"
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {renderActiveTab()}
        </>
      )}
    </section>
  );
}

const TABLE_HEADER_STYLE: CSSProperties = {
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
  padding: "10px 12px",
  textAlign: "left",
  fontSize: 12,
  letterSpacing: "0.04em",
  textTransform: "uppercase",
};

const TABLE_CELL_STYLE: CSSProperties = {
  borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
  padding: "10px 12px",
  verticalAlign: "top",
};

const TABLE_META_STYLE: CSSProperties = {
  fontSize: 12,
  opacity: 0.7,
  marginTop: 4,
};

function readStatementCategory(value: unknown): StatementCategory {
  return STATEMENT_CATEGORY_OPTIONS.some((option) => option.id === value)
    ? (value as StatementCategory)
    : "all";
}

function readStatementWalletType(value: unknown): StatementWalletType {
  return value === "bonus" ? "bonus" : "cash";
}

function readStatementPeriod(value: unknown): StatementPeriod {
  return STATEMENT_PERIOD_OPTIONS.some((option) => option.id === value)
    ? (value as StatementPeriod)
    : "last_30_days";
}

function readAvailableStatementCategoryOptions(walletType: StatementWalletType): StatementCategoryOption[] {
  return STATEMENT_CATEGORY_OPTIONS.filter((option) =>
    isStatementCategoryAvailableForWallet(option.id, walletType),
  );
}

function isStatementCategoryAvailableForWallet(
  category: StatementCategory,
  walletType: StatementWalletType,
): boolean {
  if (category === "all" || category === "game" || category === "adjustments") {
    return true;
  }
  if (category === "bonus") {
    return walletType === "bonus";
  }
  if (category === "deposits_withdrawals") {
    return walletType === "cash";
  }
  return false;
}

function buildStatementMovementsPath(options: {
  category: StatementCategory;
  walletType: StatementWalletType;
  period: StatementPeriod;
  limit: number;
  cursor?: string;
}): string {
  const params = new URLSearchParams({
    category: options.category,
    wallet_type: options.walletType,
    period: options.period,
    limit: String(options.limit),
  });
  if (options.cursor) {
    params.set("cursor", options.cursor);
  }
  return `/account/statement-movements?${params.toString()}`;
}

function readStatementWalletLabel(walletType: StatementWalletType): string {
  return walletType === "bonus" ? "Bonus" : "Saldo reale";
}

function formatDebitCreditAmount(value: string): string {
  const amount = toNumericAmount(value);
  if (amount === 0) {
    return "-";
  }
  return `${formatChipAmount(amount)} CHIP`;
}

function formatStatementNetAmount(movement: StatementMovement): string {
  if (movement.movement_family !== "game") {
    return "-";
  }

  const amount = toNumericAmount(movement.net_amount);
  if (amount === 0) {
    return "0.00 CHIP";
  }
  return formatSignedChipAmount(amount);
}

function formatStatementDetailNetAmount(value: string): string {
  const amount = toNumericAmount(value);
  if (amount === 0) {
    return "0.00 CHIP";
  }
  return formatSignedChipAmount(amount);
}

function readStatementAmountLabels(
  movement: StatementMovement,
): { debit: string; credit: string; net: string } {
  if (movement.movement_family === "game") {
    return {
      debit: "Giocato",
      credit: "Vinto",
      net: "Delta",
    };
  }

  return {
    debit: "Uscite",
    credit: "Entrate",
    net: "Delta",
  };
}

function readStatementNetClassName(movement: StatementMovement): string {
  if (movement.movement_family !== "game") {
    return "is-neutral";
  }

  const amount = toNumericAmount(movement.net_amount);
  if (amount > 0) {
    return "is-positive";
  }
  if (amount < 0) {
    return "is-negative";
  }
  return "is-neutral";
}

function readStatementDetailTitle(item: StatementDetailItem): string {
  if (item.item_type === "game_round") {
    return item.round_code ? `Round ${item.round_code}` : "Round gioco";
  }
  if (item.transaction_type) {
    return readLedgerTransactionTypeLabel(item.transaction_type);
  }
  return item.transaction_code ?? "Movimento";
}

function readStatementDetailMeta(item: StatementDetailItem): string {
  if (item.item_type === "game_round") {
    const result = item.result ? readRoundStatusLabel(item.result as SessionHistoryItem["status"]) : "Round";
    return `${formatDateTime(item.timestamp)} - ${item.game_summary ?? result}`;
  }
  return `${formatDateTime(item.timestamp)} - ${item.transaction_code ?? "Dettaglio movimento"}`;
}

function mergeGameHistory(
  left: SessionHistoryItem[],
  right: SessionHistoryItem[],
): SessionHistoryItem[] {
  const items = new Map<string, SessionHistoryItem>();
  for (const item of [...left, ...right]) {
    items.set(readGameReplayStateKey(item), item);
  }
  return [...items.values()].sort((leftItem, rightItem) =>
    rightItem.created_at.localeCompare(leftItem.created_at),
  );
}

function readGroupGameLabel(group: AccessSessionStatementGroup): string {
  const gameCode = group.rounds[0]?.game_code;
  return resolvePlayerGameDisplayName(gameCode);
}

function buildAccessSessionStatementGroups(
  sessions: SessionHistoryItem[],
): AccessSessionStatementGroup[] {
  const groups = new Map<string, AccessSessionStatementGroup>();

  for (const session of sessions) {
    const accessSessionId = session.access_session?.id ?? session.access_session_id;
    const groupId = accessSessionId ?? `round-${session.game_session_id}`;
    const startedAt = session.access_session?.started_at ?? session.created_at;
    const endedAt = session.access_session?.ended_at ?? session.closed_at;
    const status = session.access_session?.status ?? "no_access_session";
    const existingGroup = groups.get(groupId);

    if (!existingGroup) {
      const accountingStake =
        session.status === "cancelled" ? 0 : toNumericAmount(session.bet_amount);
      groups.set(groupId, {
        id: groupId,
        accessSessionId,
        status,
        startedAt,
        endedAt,
        rounds: [session],
        roundsCount: 1,
        totalStaked: accountingStake,
        totalWon: session.status === "won" ? toNumericAmount(session.potential_payout) : 0,
      });
      continue;
    }

    existingGroup.rounds.push(session);
    existingGroup.roundsCount += 1;
    if (session.status !== "cancelled") {
      existingGroup.totalStaked += toNumericAmount(session.bet_amount);
    }
    if (session.status === "won") {
      existingGroup.totalWon += toNumericAmount(session.potential_payout);
    }
    if (startedAt < existingGroup.startedAt) {
      existingGroup.startedAt = startedAt;
    }
    if (existingGroup.endedAt === null || (endedAt !== null && endedAt > existingGroup.endedAt)) {
      existingGroup.endedAt = endedAt;
    }
  }

  return [...groups.values()]
    .map((group) => ({
      ...group,
      rounds: [...group.rounds].sort((left, right) => right.created_at.localeCompare(left.created_at)),
    }))
    .sort((left, right) => right.startedAt.localeCompare(left.startedAt));
}

function readAccessSessionStatusLabel(status: AccessSessionStatementGroup["status"]): string {
  if (status === "active") {
    return "Attiva";
  }
  if (status === "closed") {
    return "Chiusa";
  }
  if (status === "timed_out") {
    return "Scaduta";
  }
  return "Diretta";
}

function readRoundStatusLabel(status: SessionHistoryItem["status"]): string {
  if (status === "won") {
    return "Vinto";
  }
  if (status === "lost") {
    return "Perso";
  }
  if (status === "cancelled") {
    return "Annullato";
  }
  return "Attivo";
}

function readRoundPayoutLabel(session: SessionHistoryItem): string {
  if (session.status === "active") {
    return `${formatChipAmount(toNumericAmount(session.potential_payout))} CHIP`;
  }
  if (session.status === "lost") {
    return "0.00 CHIP";
  }
  if (session.status === "cancelled") {
    return "0.00 CHIP";
  }
  return `${formatChipAmount(toNumericAmount(session.potential_payout))} CHIP`;
}

function readRoundConfigLabel(session: SessionHistoryItem): string {
  return readGameReportingDescriptor(session.game_code)?.readConfigLabel(session) ?? session.game_code;
}

function readRoundRevealLabel(session: SessionHistoryItem): string {
  return readGameReportingDescriptor(session.game_code)?.readProgressLabel(session) ?? "-";
}

function readWalletTypeLabel(walletType: string): string {
  const normalizedWalletType = walletType.toLowerCase();
  if (normalizedWalletType === "cash") {
    return "Wallet cash";
  }
  if (normalizedWalletType === "bonus") {
    return "Wallet bonus";
  }
  if (normalizedWalletType === "demo") {
    return "Wallet demo";
  }
  return walletType;
}

function readLedgerTransactionTypeLabel(transactionType: string): string {
  if (transactionType === "signup_credit") {
    return "Credito iniziale";
  }
  if (transactionType === "bet") {
    return "Puntata";
  }
  if (transactionType === "win") {
    return "Vincita";
  }
  if (transactionType === "void") {
    return "Annullamento";
  }
  if (transactionType === "bonus_grant") {
    return "Bonus";
  }
  if (transactionType === "admin_adjustment") {
    return "Rettifica";
  }
  return transactionType.replace(/_/g, " ");
}

function isStatementGroupInProgress(group: AccessSessionStatementGroup): boolean {
  return group.status === "active" || group.rounds.some((round) => round.status === "active");
}

function readStatementGroupResultLabel(group: AccessSessionStatementGroup): string {
  if (isStatementGroupInProgress(group)) {
    return "In corso";
  }
  return formatSignedChipAmount(group.totalWon - group.totalStaked);
}

function readStatementGroupResultClassName(group: AccessSessionStatementGroup): string {
  if (isStatementGroupInProgress(group)) {
    return "is-neutral";
  }

  const deltaAmount = group.totalWon - group.totalStaked;
  if (deltaAmount > 0) {
    return "is-positive";
  }
  if (deltaAmount < 0) {
    return "is-negative";
  }
  return "is-neutral";
}

function formatSignedChipAmount(value: number): string {
  const sign = value >= 0 ? "+" : "-";
  return `${sign}${formatChipAmount(Math.abs(value))} CHIP`;
}
