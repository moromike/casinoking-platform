"use client";

import { Fragment, useEffect, useMemo, useState, type FormEvent } from "react";

import { apiEnvelopeRequest, apiRequest, readErrorMessage } from "../lib/api";
import { sanitizeAuthReturnTo, withAuthReturnTo } from "../lib/auth-return";
import { PLAYER_STORAGE_KEYS, readPlayerAuthSnapshot } from "../lib/player-auth";

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

type Wallet = {
  wallet_type: string;
  balance_snapshot: string;
  currency_code?: string;
};

type StatementCategory = "all" | "deposits_withdrawals" | "game" | "bonus" | "adjustments";
type StatementWalletType = "cash" | "bonus";
type StatementPeriod = "today" | "last_7_days" | "last_30_days" | "current_month" | "previous_month";

type PaginationMeta = {
  next_cursor: string | null;
  limit: number;
};

type StatementMeta = PaginationMeta & {
  category: StatementCategory;
  wallet_type: StatementWalletType;
  period: StatementPeriod;
  date_from: string;
  date_to: string;
  balance_disclaimer: string | null;
};

type StatementMovement = {
  id: string;
  movement_family: "game" | "bonus" | "adjustment" | "deposit" | "withdrawal";
  movement_label: string;
  description: string;
  code: string;
  movement_type: string;
  wallet_type: StatementWalletType;
  currency_code: string;
  started_at: string;
  debit_amount: string;
  credit_amount: string;
  net_amount: string;
  balance_after: string;
  expandable: boolean;
};

type StatementDetailItem = {
  id: string;
  item_type: "game_round" | "transaction";
  timestamp: string;
  round_code?: string;
  game_code?: string;
  title_code?: string;
  result?: string;
  transaction_code?: string;
  transaction_type?: string;
  debit_amount: string;
  credit_amount: string;
  net_amount: string;
  balance_after: string;
  wallet_type: StatementWalletType;
  currency_code: string;
  game_summary?: string;
};

type StatementMovementDetail = {
  movement_id: string;
  movement_family: StatementMovement["movement_family"];
  items: StatementDetailItem[];
};

type StatementDetailState = {
  items: StatementDetailItem[];
  loading: boolean;
  error: string | null;
};

type GameHistoryItem = {
  game_code: string;
  game_session_id: string;
  replay_round_id?: string;
  status: string;
  title_code?: string;
  site_code?: string;
  grid_size?: number;
  mine_count?: number;
  rows?: number;
  difficulty?: string;
  outcome?: string | null;
  bet_amount: string;
  wallet_type: string;
  safe_reveals_count: number;
  revealed_cells_count: number;
  potential_payout: string;
  created_at: string;
  closed_at: string | null;
};

type ReplayState = {
  replay: unknown;
  loading: boolean;
  error: string | null;
};

type AccountTab = "overview" | "profile" | "security" | "wallets" | "gameHistory";

const ACCOUNT_TABS: Array<{ id: AccountTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profilo" },
  { id: "security", label: "Sicurezza" },
  { id: "wallets", label: "Cassa" },
  { id: "gameHistory", label: "Storico gioco" },
];

const STATEMENT_CATEGORY_OPTIONS: Array<{ id: StatementCategory; label: string }> = [
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

const GAME_HISTORY_DESCRIPTORS = [
  {
    gameCode: "mines",
    label: "Mines",
    buildHistoryPath: (limit: number, cursor?: string | null) => buildPagePath("/games/mines/sessions", limit, cursor),
    mapItems: mapMinesHistoryItems,
    buildReplayPath: (round: GameHistoryItem) =>
      `/games/mines/session/${encodeURIComponent(round.game_session_id)}/replay`,
  },
  {
    gameCode: "boxe",
    label: "BOXE",
    buildHistoryPath: (limit: number, cursor?: string | null) => buildPagePath("/games/boxe/sessions", limit, cursor),
    mapItems: mapBoxeHistoryItems,
    buildReplayPath: (round: GameHistoryItem) =>
      `/games/boxe/round/${encodeURIComponent(round.replay_round_id ?? round.game_session_id)}/replay`,
  },
  {
    gameCode: "hi_lo",
    label: "HI-LO",
    buildHistoryPath: (limit: number, cursor?: string | null) => buildPagePath("/games/hi-lo/sessions", limit, cursor),
    mapItems: mapHiLoHistoryItems,
    buildReplayPath: (round: GameHistoryItem) =>
      `/games/hi-lo/round/${encodeURIComponent(round.replay_round_id ?? round.game_session_id)}/replay`,
  },
] as const;

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
  const [gameHistory, setGameHistory] = useState<GameHistoryItem[]>([]);
  const [gameHistoryNextCursors, setGameHistoryNextCursors] = useState<Record<string, string | null>>({});
  const [expandedReplayIds, setExpandedReplayIds] = useState<string[]>([]);
  const [replayStates, setReplayStates] = useState<Record<string, ReplayState>>({});
  const [loading, setLoading] = useState(false);
  const [loadingStatement, setLoadingStatement] = useState(false);
  const [loadingMoreStatement, setLoadingMoreStatement] = useState(false);
  const [loadingMoreHistory, setLoadingMoreHistory] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordStatus, setPasswordStatus] = useState<string | null>(null);
  const [returnTo, setReturnTo] = useState<string | null>(null);

  useEffect(() => {
    setReturnTo(sanitizeAuthReturnTo(new URLSearchParams(window.location.search).get("return_to")));
    const snapshot = readPlayerAuthSnapshot();
    setAccessToken(snapshot.accessToken);
    setCurrentEmail(snapshot.email);
    if (snapshot.accessToken) {
      void loadAccountState(snapshot.accessToken);
    }
  }, []);

  const cashWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "cash") ?? null,
    [wallets],
  );
  const bonusWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null,
    [wallets],
  );
  const primaryWallet = cashWallet ?? wallets[0] ?? null;
  const latestMovement = statementMovements[0] ?? null;
  const latestRound = gameHistory[0] ?? null;

  async function loadAccountState(token: string) {
    setLoading(true);
    setStatus(null);

    try {
      const [profileData, walletData, statementPage, ...historyPages] = await Promise.all([
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
        ...GAME_HISTORY_DESCRIPTORS.map((descriptor) =>
          apiEnvelopeRequest<unknown[]>(descriptor.buildHistoryPath(10), {}, token),
        ),
      ]);

      setProfile(profileData);
      setWallets(walletData);
      setStatementMovements(statementPage.data);
      setStatementMeta(readStatementMeta(statementPage.meta));
      setStatementNextCursor(readPaginationMeta(statementPage.meta).next_cursor);
      setExpandedStatementMovementIds([]);
      setStatementMovementDetails({});
      setGameHistory(mergeGameHistory(
        [],
        historyPages.flatMap((page, index) => GAME_HISTORY_DESCRIPTORS[index].mapItems(page.data)),
      ));
      setGameHistoryNextCursors(Object.fromEntries(
        historyPages.map((page, index) => [
          GAME_HISTORY_DESCRIPTORS[index].gameCode,
          readPaginationMeta(page.meta).next_cursor,
        ]),
      ));
      setExpandedReplayIds([]);
      setReplayStates({});
    } catch (error) {
      setStatus(readErrorMessage(error, "Account loading failed."));
    } finally {
      setLoading(false);
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

  async function loadStatementMovementDetail(movement: StatementMovement) {
    if (!accessToken || statementMovementDetails[movement.id]?.loading) {
      return;
    }

    setStatementMovementDetails((current) => ({
      ...current,
      [movement.id]: { items: current[movement.id]?.items ?? [], loading: true, error: null },
    }));

    try {
      const query = new URLSearchParams({ wallet_type: movement.wallet_type, limit: "50" });
      const page = await apiEnvelopeRequest<StatementMovementDetail>(
        `/account/statement-movements/${encodeURIComponent(movement.id)}?${query.toString()}`,
        {},
        accessToken,
      );
      setStatementMovementDetails((current) => ({
        ...current,
        [movement.id]: { items: page.data.items, loading: false, error: null },
      }));
    } catch (error) {
      setStatementMovementDetails((current) => ({
        ...current,
        [movement.id]: {
          items: current[movement.id]?.items ?? [],
          loading: false,
          error: readErrorMessage(error, "Caricamento dettaglio fallito."),
        },
      }));
    }
  }

  async function loadMoreGameHistory() {
    if (!accessToken || !GAME_HISTORY_DESCRIPTORS.some((descriptor) => gameHistoryNextCursors[descriptor.gameCode])) {
      return;
    }

    setLoadingMoreHistory(true);
    setStatus(null);

    try {
      const pages = await Promise.all(
        GAME_HISTORY_DESCRIPTORS.map(async (descriptor) => {
          const cursor = gameHistoryNextCursors[descriptor.gameCode];
          if (!cursor) {
            return null;
          }
          const page = await apiEnvelopeRequest<unknown[]>(descriptor.buildHistoryPath(10, cursor), {}, accessToken);
          return { descriptor, page };
        }),
      );

      const loadedPages = pages.filter((page): page is NonNullable<typeof page> => page !== null);
      setGameHistory((current) => mergeGameHistory(
        current,
        loadedPages.flatMap(({ descriptor, page }) => descriptor.mapItems(page.data)),
      ));
      setGameHistoryNextCursors((current) => ({
        ...current,
        ...Object.fromEntries(
          loadedPages.map(({ descriptor, page }) => [
            descriptor.gameCode,
            readPaginationMeta(page.meta).next_cursor,
          ]),
        ),
      }));
    } catch (error) {
      setStatus(readErrorMessage(error, "Caricamento storico gioco fallito."));
    } finally {
      setLoadingMoreHistory(false);
    }
  }

  async function toggleReplay(round: GameHistoryItem) {
    const replayKey = readReplayStateKey(round);
    const isExpanded = expandedReplayIds.includes(replayKey);
    setExpandedReplayIds((current) =>
      current.includes(replayKey) ? current.filter((entry) => entry !== replayKey) : [...current, replayKey],
    );

    if (isExpanded || replayStates[replayKey]?.replay) {
      return;
    }

    const descriptor = GAME_HISTORY_DESCRIPTORS.find((entry) => entry.gameCode === round.game_code);
    if (!descriptor || !accessToken) {
      setReplayStates((current) => ({
        ...current,
        [replayKey]: { replay: null, loading: false, error: `Replay unavailable for ${round.game_code}.` },
      }));
      return;
    }

    setReplayStates((current) => ({
      ...current,
      [replayKey]: { replay: current[replayKey]?.replay ?? null, loading: true, error: null },
    }));

    try {
      const replay = await apiRequest<unknown>(descriptor.buildReplayPath(round), {}, accessToken);
      setReplayStates((current) => ({
        ...current,
        [replayKey]: { replay, loading: false, error: null },
      }));
    } catch (error) {
      setReplayStates((current) => ({
        ...current,
        [replayKey]: {
          replay: current[replayKey]?.replay ?? null,
          loading: false,
          error: readErrorMessage(error, "Caricamento replay fallito."),
        },
      }));
    }
  }

  async function handleChangePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setPasswordBusy(true);
    setPasswordStatus(null);

    try {
      await apiRequest<{ password_changed: boolean }>("/auth/password/change", {
        method: "POST",
        body: JSON.stringify({ old_password: currentPassword, new_password: newPassword }),
      }, accessToken);
      setCurrentPassword("");
      setNewPassword("");
      setPasswordStatus("Password aggiornata.");
    } catch (error) {
      setPasswordStatus(readErrorMessage(error, "Aggiornamento password fallito."));
    } finally {
      setPasswordBusy(false);
    }
  }

  function toggleStatementMovement(movement: StatementMovement) {
    if (!movement.expandable) {
      return;
    }
    const isExpanded = expandedStatementMovementIds.includes(movement.id);
    setExpandedStatementMovementIds((current) =>
      current.includes(movement.id) ? current.filter((entry) => entry !== movement.id) : [...current, movement.id],
    );
    if (!isExpanded && !statementMovementDetails[movement.id]) {
      void loadStatementMovementDetail(movement);
    }
  }

  function renderActiveTab() {
    if (activeTab === "profile") {
      return (
        <article className="site-v3-account-card">
          <h2>Profilo</h2>
          <div className="site-v3-account-detail-grid">
            <Detail label="Email" value={profile?.email || currentEmail || "-"} />
            <Detail label="Stato" value={profile?.status ?? "-"} />
            <Detail label="Nome" value={(profile?.first_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.firstName)) || "-"} />
            <Detail label="Cognome" value={(profile?.last_name ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.lastName)) || "-"} />
            <Detail label="Codice fiscale" value={(profile?.fiscal_code ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.fiscalCode)) || "-"} />
            <Detail label="Telefono" value={(profile?.phone_number ?? readStoredProfileValue(PLAYER_STORAGE_KEYS.phoneNumber)) || "-"} />
          </div>
        </article>
      );
    }

    if (activeTab === "security") {
      return (
        <article className="site-v3-account-card">
          <h2>Sicurezza</h2>
          {passwordStatus ? <div className="site-v3-player-status">{passwordStatus}</div> : null}
          <form className="site-v3-player-form" onSubmit={(event) => void handleChangePassword(event)}>
            <div className="site-v3-player-field-grid">
              <label>
                Password attuale
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  autoComplete="current-password"
                />
              </label>
              <label>
                Nuova password
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                />
              </label>
            </div>
            <div className="site-v3-player-form-actions">
              <button className="site-v3-button" type="submit" disabled={passwordBusy || !currentPassword || !newPassword}>
                {passwordBusy ? "Aggiornamento..." : "Aggiorna password"}
              </button>
            </div>
          </form>
        </article>
      );
    }

    if (activeTab === "wallets") {
      return renderWalletsTab();
    }

    if (activeTab === "gameHistory") {
      return renderGameHistoryTab();
    }

    return (
      <div className="site-v3-account-overview">
        <article className="site-v3-account-summary-card">
          <span>Saldo reale</span>
          <strong>{formatChipAmount(cashWallet?.balance_snapshot)} CHIP</strong>
          <small>{cashWallet?.currency_code ?? "CHIP"}</small>
        </article>
        <article className="site-v3-account-summary-card">
          <span>Bonus</span>
          <strong>{formatChipAmount(bonusWallet?.balance_snapshot)} CHIP</strong>
          <small>{bonusWallet?.currency_code ?? "CHIP"}</small>
        </article>
        <article className="site-v3-account-summary-card">
          <span>Ultimo movimento</span>
          <strong>{latestMovement ? latestMovement.movement_label : "-"}</strong>
          <small>{latestMovement ? formatDateTime(latestMovement.started_at) : "Nessun movimento"}</small>
        </article>
        <article className="site-v3-account-summary-card">
          <span>Ultimo round</span>
          <strong>{latestRound ? readGameLabel(latestRound.game_code) : "-"}</strong>
          <small>{latestRound ? formatDateTime(latestRound.created_at) : "Nessun round"}</small>
        </article>

        <article className="site-v3-account-card">
          <h2>Dettagli account</h2>
          <div className="site-v3-account-detail-grid">
            <Detail label="Player" value={profile?.email || currentEmail || "-"} />
            <Detail label="Saldo principale" value={`${formatChipAmount(primaryWallet?.balance_snapshot)} CHIP`} />
            <Detail label="Creato il" value={profile?.created_at ? formatDateTime(profile.created_at) : "-"} />
          </div>
        </article>
      </div>
    );
  }

  function renderWalletsTab() {
    return (
      <article className="site-v3-account-card">
        <div className="site-v3-account-card-head">
          <div>
            <h2>Cassa</h2>
            <p>Saldo, movimenti e dettaglio contabile player.</p>
          </div>
          <button
            className="site-v3-button is-secondary"
            type="button"
            onClick={() => void refreshStatementMovements()}
            disabled={loadingStatement}
          >
            {loadingStatement ? "Aggiorno..." : "Aggiorna"}
          </button>
        </div>

        <div className="site-v3-account-wallet-strip">
          <Detail label="Saldo reale" value={`${formatChipAmount(cashWallet?.balance_snapshot)} CHIP`} />
          <Detail label="Bonus" value={`${formatChipAmount(bonusWallet?.balance_snapshot)} CHIP`} />
        </div>

        <div className="site-v3-account-filter-row">
          <select
            aria-label="Wallet"
            value={statementWalletType}
            onChange={(event) => {
              const nextWalletType = event.target.value as StatementWalletType;
              const nextCategory = isStatementCategoryAvailableForWallet(statementCategory, nextWalletType)
                ? statementCategory
                : "all";
              setStatementWalletType(nextWalletType);
              setStatementCategory(nextCategory);
              void refreshStatementMovements(nextCategory, nextWalletType, statementPeriod);
            }}
          >
            {STATEMENT_WALLET_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
          <select
            aria-label="Category"
            value={statementCategory}
            onChange={(event) => {
              const nextCategory = event.target.value as StatementCategory;
              if (!isStatementCategoryAvailableForWallet(nextCategory, statementWalletType)) {
                return;
              }
              setStatementCategory(nextCategory);
              void refreshStatementMovements(nextCategory, statementWalletType, statementPeriod);
            }}
          >
            {STATEMENT_CATEGORY_OPTIONS.filter((option) =>
              isStatementCategoryAvailableForWallet(option.id, statementWalletType),
            ).map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
          <select
            aria-label="Period"
            value={statementPeriod}
            onChange={(event) => {
              const nextPeriod = event.target.value as StatementPeriod;
              setStatementPeriod(nextPeriod);
              void refreshStatementMovements(statementCategory, statementWalletType, nextPeriod);
            }}
          >
            {STATEMENT_PERIOD_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
        </div>

        {statementMeta?.balance_disclaimer ? (
          <div className="site-v3-player-status">{statementMeta.balance_disclaimer}</div>
        ) : null}

        <div className="site-v3-account-list">
          {statementMovements.length === 0 ? (
            <div className="site-v3-account-empty">Nessun movimento.</div>
          ) : (
            statementMovements.map((movement) => {
              const isExpanded = expandedStatementMovementIds.includes(movement.id);
              return (
                <article className="site-v3-account-row" key={movement.id}>
                  <button
                    className="site-v3-account-row-button"
                    type="button"
                    disabled={!movement.expandable}
                    aria-expanded={isExpanded}
                    onClick={() => toggleStatementMovement(movement)}
                  >
                    <span>
                      <strong>{movement.movement_label}</strong>
                      <small>{movement.description || movement.code}</small>
                    </span>
                    <span>
                      <strong className={amountClassName(movement.net_amount)}>{formatSignedChipAmount(movement.net_amount)}</strong>
                      <small>{formatDateTime(movement.started_at)}</small>
                    </span>
                  </button>
                  {isExpanded ? renderStatementDetail(movement) : null}
                </article>
              );
            })
          )}
        </div>

        {statementNextCursor ? (
          <button
            className="site-v3-button is-secondary"
            type="button"
            onClick={() => void loadMoreStatementMovements()}
            disabled={loadingMoreStatement}
          >
            {loadingMoreStatement ? "Carico..." : "Carica altri movimenti"}
          </button>
        ) : null}
      </article>
    );
  }

  function renderStatementDetail(movement: StatementMovement) {
    const detail = statementMovementDetails[movement.id];
    if (!detail || detail.loading) {
      return <div className="site-v3-player-status">Caricamento dettaglio...</div>;
    }
    if (detail.error) {
      return <div className="site-v3-player-status">{detail.error}</div>;
    }
    return (
      <div className="site-v3-account-detail-list">
        {detail.items.map((item) => (
          <div className="site-v3-account-detail-row" key={item.id}>
            <span>
              <strong>{readStatementDetailTitle(item)}</strong>
              <small>{readStatementDetailMeta(item)}</small>
            </span>
            <span>
              <strong className={amountClassName(item.net_amount)}>{formatSignedChipAmount(item.net_amount)}</strong>
              <small>Saldo {formatChipAmount(item.balance_after)} CHIP</small>
            </span>
          </div>
        ))}
      </div>
    );
  }

  function renderGameHistoryTab() {
    return (
      <article className="site-v3-account-card">
        <h2>Storico gioco</h2>
        <div className="site-v3-account-list">
          {gameHistory.length === 0 ? (
            <div className="site-v3-account-empty">Nessun round gioco.</div>
          ) : (
            gameHistory.map((round) => {
              const replayKey = readReplayStateKey(round);
              const isExpanded = expandedReplayIds.includes(replayKey);
              const replayState = replayStates[replayKey];
              return (
                <article className="site-v3-account-row" key={replayKey}>
                  <div className="site-v3-account-round-card">
                    <div>
                      <strong>{readGameLabel(round.game_code)} - {readRoundStatusLabel(round.status)}</strong>
                      <small>{formatDateTime(round.created_at)} - {readRoundConfigLabel(round)}</small>
                    </div>
                    <div>
                      <strong>{formatChipAmount(round.bet_amount)} CHIP</strong>
                      <small>Payout {formatChipAmount(round.potential_payout)} CHIP</small>
                    </div>
                    <button
                      className="site-v3-button is-secondary"
                      type="button"
                      aria-expanded={isExpanded}
                      onClick={() => void toggleReplay(round)}
                    >
                      {isExpanded ? "Chiudi replay" : "Rivedi mano"}
                    </button>
                  </div>
                  {isExpanded ? (
                    <div className="site-v3-replay-summary">
                      {replayState?.loading ? <div className="site-v3-player-status">Caricamento replay...</div> : null}
                      {replayState?.error ? <div className="site-v3-player-status">{replayState.error}</div> : null}
                      {replayState?.replay ? <ReplaySummary replay={replayState.replay} /> : null}
                    </div>
                  ) : null}
                </article>
              );
            })
          )}
        </div>

        {GAME_HISTORY_DESCRIPTORS.some((descriptor) => gameHistoryNextCursors[descriptor.gameCode]) ? (
          <button
            className="site-v3-button is-secondary"
            type="button"
            onClick={() => void loadMoreGameHistory()}
            disabled={loadingMoreHistory}
          >
            {loadingMoreHistory ? "Carico..." : "Carica altre sessioni"}
          </button>
        ) : null}
      </article>
    );
  }

  return (
    <section className="site-v3-player-panel site-v3-account-page">
      <div>
        <p className="site-v3-player-eyebrow">Player</p>
        <h1>Account</h1>
        <p>Saldo, attivita' recente e dettagli account.</p>
      </div>

      {!accessToken ? (
        <div className="site-v3-player-stack">
          <div className="site-v3-player-status">Guest access</div>
          <div className="site-v3-player-form-actions">
            <a className="site-v3-button" href={withAuthReturnTo("/login", returnTo)}>
              Sign in
            </a>
            <a className="site-v3-button is-secondary" href={withAuthReturnTo("/register", returnTo)}>
              Register
            </a>
          </div>
        </div>
      ) : (
        <>
          <div className="site-v3-account-session-row">
            <div className="site-v3-player-status">{profile?.email || currentEmail || "Player session"}</div>
            <button
              className="site-v3-button is-secondary"
              type="button"
              onClick={() => void loadAccountState(accessToken)}
              disabled={loading}
            >
              {loading ? "Refresh..." : "Refresh"}
            </button>
          </div>

          {status ? <div className="site-v3-player-status">{status}</div> : null}

          <div className="site-v3-account-tabs" aria-label="Account sections" role="tablist">
            {ACCOUNT_TABS.map((tab) => (
              <button
                key={tab.id}
                aria-selected={activeTab === tab.id}
                className={activeTab === tab.id ? "is-active" : ""}
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

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReplaySummary({ replay }: { replay: unknown }) {
  const record = replay && typeof replay === "object" ? replay as Record<string, unknown> : {};
  const fairness = record.fairness && typeof record.fairness === "object"
    ? record.fairness as Record<string, unknown>
    : record;
  const entries = [
    ["Round", readFirstString(record, ["round_id", "game_session_id", "session_id"])],
    ["Status", readFirstString(record, ["status", "outcome"])],
    ["Bet", formatChipAmount(readFirstString(record, ["bet_amount"]))],
    ["Payout", formatChipAmount(readFirstString(record, ["payout_amount", "final_payout_amount"]))],
    ["Started", readFirstString(record, ["created_at"])],
    ["Closed", readFirstString(record, ["closed_at"])],
    ["Server seed hash", readFirstString(fairness, ["server_seed_hash"])],
    ["Verification", readFirstString(fairness, ["outcome_verification", "round_path_hash", "draw_sequence_hash", "board_hash"])],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]));

  return (
    <div className="site-v3-replay-panel">
      <ReplayVisual replay={replay} />
      <dl className="site-v3-replay-meta">
        {entries.map(([label, value]) => (
          <Fragment key={label}>
            <dt>{label}</dt>
            <dd>{label === "Started" || label === "Closed" ? formatDateTime(value) : shortenHash(value)}</dd>
          </Fragment>
        ))}
      </dl>
    </div>
  );
}

function ReplayVisual({ replay }: { replay: unknown }) {
  const record = replay && typeof replay === "object" ? replay as Record<string, unknown> : {};
  if (typeof record.grid_size === "number") {
    return <MinesReplayVisual replay={record} />;
  }
  if (typeof record.rows === "number" && Array.isArray(record.picks)) {
    return <BoxeReplayVisual replay={record} />;
  }
  if (Array.isArray(record.actions)) {
    return <HiLoReplayVisual replay={record} />;
  }
  return null;
}

function MinesReplayVisual({ replay }: { replay: Record<string, unknown> }) {
  const gridSize = Number(replay.grid_size);
  const boardSide = Math.sqrt(gridSize);
  if (!Number.isInteger(boardSide) || gridSize <= 0) {
    return null;
  }
  const revealedCells = readNumberArray(replay.final_revealed_cells).length > 0
    ? readNumberArray(replay.final_revealed_cells)
    : readNumberArray(replay.revealed_cells);
  const minePositions = Boolean(replay.board_reveal_available) ? readNumberArray(replay.mine_positions) : [];
  const revealedSet = new Set(revealedCells);
  const mineSet = new Set(minePositions);

  return (
    <div
      className="site-v3-replay-mines-grid"
      aria-label="Mines replay board"
      style={{ gridTemplateColumns: `repeat(${boardSide}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: gridSize }, (_item, index) => {
        const state = mineSet.has(index) ? "mine" : revealedSet.has(index) ? "safe" : "covered";
        return <span className={`site-v3-replay-cell is-${state}`} key={index}>{state === "mine" ? "M" : state === "safe" ? "D" : ""}</span>;
      })}
    </div>
  );
}

function BoxeReplayVisual({ replay }: { replay: Record<string, unknown> }) {
  const rows = Number(replay.rows);
  if (!Number.isInteger(rows) || rows <= 0) {
    return null;
  }
  const picks = Array.isArray(replay.picks) ? replay.picks : [];
  const fullReveal = readBoxeFullReveal(replay.pyramid_full_reveal);
  const visualRows = Array.from({ length: rows }, (_item, index) => rows - index - 1);

  return (
    <div className="site-v3-replay-boxe-pyramid" aria-label="BOXE replay pyramid">
      {visualRows.map((row) => {
        const cellCount = rows - row + 1;
        return (
          <div
            className="site-v3-replay-boxe-row"
            key={row}
            style={{ gridTemplateColumns: `repeat(${cellCount}, minmax(0, 1fr))` }}
          >
            {Array.from({ length: cellCount }, (_item, position) => {
              const state = readBoxeCellState({ picks, fullReveal, row, position });
              return <span className={`site-v3-replay-cell is-${state}`} key={position}>{state === "mine" ? "M" : state === "safe" ? "D" : ""}</span>;
            })}
          </div>
        );
      })}
    </div>
  );
}

function HiLoReplayVisual({ replay }: { replay: Record<string, unknown> }) {
  const actions = Array.isArray(replay.actions)
    ? [...replay.actions].filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    : [];
  const orderedActions = actions.sort((left, right) => Number(left.action_index ?? 0) - Number(right.action_index ?? 0));
  const currentAction = orderedActions.at(-1) ?? null;
  const currentCard = currentAction && typeof currentAction.drawn_card === "object" && currentAction.drawn_card
    ? currentAction.drawn_card as Record<string, unknown>
    : null;

  return (
    <div className="site-v3-replay-hilo" aria-label="HI-LO replay">
      <div className="site-v3-replay-hilo-card">
        <strong>{readFirstString(currentCard ?? {}, ["rank_label"]) || "?"}</strong>
        <span>{readFirstString(currentCard ?? {}, ["suit"])}</span>
      </div>
      <ol>
        {orderedActions.slice(-6).map((action) => (
          <li key={`${String(action.action_index)}:${String(action.created_at)}`}>
            <span>{readFirstString(action, ["prediction_action", "action_type"]) || "start"}</span>
            <strong>{readFirstString(action, ["multiplier_after"]) || "1.0000"}x</strong>
          </li>
        ))}
      </ol>
    </div>
  );
}

function readStoredProfileValue(key: string): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(key) ?? "";
}

function buildPagePath(path: string, limit: number, cursor?: string | null): string {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) {
    params.set("cursor", cursor);
  }
  return `${path}?${params.toString()}`;
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
    wallet_type: candidate.wallet_type === "bonus" ? "bonus" : "cash",
    period: readStatementPeriod(candidate.period),
    date_from: typeof candidate.date_from === "string" ? candidate.date_from : "",
    date_to: typeof candidate.date_to === "string" ? candidate.date_to : "",
    balance_disclaimer: typeof candidate.balance_disclaimer === "string" ? candidate.balance_disclaimer : null,
  };
}

function readStatementCategory(value: unknown): StatementCategory {
  return STATEMENT_CATEGORY_OPTIONS.some((option) => option.id === value)
    ? value as StatementCategory
    : "all";
}

function readStatementPeriod(value: unknown): StatementPeriod {
  return STATEMENT_PERIOD_OPTIONS.some((option) => option.id === value)
    ? value as StatementPeriod
    : "last_30_days";
}

function isStatementCategoryAvailableForWallet(category: StatementCategory, walletType: StatementWalletType): boolean {
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

function mapMinesHistoryItems(items: unknown[]): GameHistoryItem[] {
  return (items as Array<Partial<GameHistoryItem>>).map((item) => ({
    game_code: "mines",
    game_session_id: String(item.game_session_id ?? ""),
    replay_round_id: item.replay_round_id,
    status: String(item.status ?? "active"),
    title_code: item.title_code,
    site_code: item.site_code,
    grid_size: Number(item.grid_size ?? 0),
    mine_count: Number(item.mine_count ?? 0),
    bet_amount: String(item.bet_amount ?? "0"),
    wallet_type: String(item.wallet_type ?? "cash"),
    safe_reveals_count: Number(item.safe_reveals_count ?? 0),
    revealed_cells_count: Number(item.revealed_cells_count ?? item.safe_reveals_count ?? 0),
    potential_payout: String(item.potential_payout ?? "0"),
    created_at: String(item.created_at ?? ""),
    closed_at: typeof item.closed_at === "string" ? item.closed_at : null,
  }));
}

function mapBoxeHistoryItems(items: unknown[]): GameHistoryItem[] {
  return (items as Array<Record<string, unknown>>).map((item) => ({
    game_code: "boxe",
    game_session_id: String(item.last_round_id ?? item.session_id ?? ""),
    replay_round_id: String(item.last_round_id ?? ""),
    status: readBoxeStatus(item),
    title_code: typeof item.title_code === "string" ? item.title_code : undefined,
    site_code: typeof item.site_code === "string" ? item.site_code : undefined,
    rows: Number(item.rows ?? 0),
    difficulty: typeof item.difficulty === "string" ? item.difficulty : undefined,
    outcome: typeof item.outcome === "string" ? item.outcome : null,
    bet_amount: String(item.bet_amount ?? "0"),
    wallet_type: String(item.wallet_source ?? "cash"),
    safe_reveals_count: Number(item.safe_picks_count ?? 0),
    revealed_cells_count: Number(item.safe_picks_count ?? 0),
    potential_payout: String(item.payout_amount ?? "0"),
    created_at: String(item.created_at ?? ""),
    closed_at: typeof item.closed_at === "string" ? item.closed_at : null,
  }));
}

function mapHiLoHistoryItems(items: unknown[]): GameHistoryItem[] {
  return (items as Array<Record<string, unknown>>).map((item) => ({
    game_code: "hi_lo",
    game_session_id: String(item.round_id ?? item.session_id ?? ""),
    replay_round_id: String(item.round_id ?? ""),
    status: readHiLoStatus(item),
    title_code: typeof item.title_code === "string" ? item.title_code : undefined,
    site_code: typeof item.site_code === "string" ? item.site_code : undefined,
    outcome: typeof item.outcome === "string" ? item.outcome : null,
    bet_amount: String(item.bet_amount ?? "0"),
    wallet_type: String(item.wallet_source ?? "cash"),
    safe_reveals_count: Number(item.correct_predictions_count ?? 0),
    revealed_cells_count: Number(item.correct_predictions_count ?? 0),
    potential_payout: String(item.final_payout_amount ?? "0"),
    created_at: String(item.created_at ?? ""),
    closed_at: typeof item.closed_at === "string" ? item.closed_at : null,
  }));
}

function readBoxeStatus(item: Record<string, unknown>): string {
  if (item.outcome === "loss" || item.status === "failed_mine") {
    return "lost";
  }
  if (item.outcome === "expired" || item.outcome === "quarantined") {
    return "cancelled";
  }
  return "won";
}

function readHiLoStatus(item: Record<string, unknown>): string {
  if (item.outcome === "loss" || item.status === "failed_prediction") {
    return "lost";
  }
  if (item.outcome === "expired" || item.outcome === "quarantined") {
    return "cancelled";
  }
  if (item.status === "active") {
    return "active";
  }
  return "won";
}

function mergeGameHistory(left: GameHistoryItem[], right: GameHistoryItem[]): GameHistoryItem[] {
  const items = new Map<string, GameHistoryItem>();
  for (const item of [...left, ...right]) {
    items.set(readReplayStateKey(item), item);
  }
  return [...items.values()].sort((leftItem, rightItem) => rightItem.created_at.localeCompare(leftItem.created_at));
}

function readReplayStateKey(round: GameHistoryItem): string {
  return `${round.game_code}:${round.replay_round_id ?? round.game_session_id}`;
}

function readGameLabel(gameCode: string): string {
  if (gameCode === "boxe") {
    return "BOXE";
  }
  if (gameCode === "hi_lo") {
    return "HI-LO";
  }
  if (gameCode === "mines") {
    return "Mines";
  }
  return gameCode.replace(/_/g, " ").toUpperCase();
}

function readRoundStatusLabel(status: string): string {
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

function readRoundConfigLabel(round: GameHistoryItem): string {
  if (round.game_code === "mines") {
    return `${round.grid_size ?? 0} celle - ${round.mine_count ?? 0} mine`;
  }
  if (round.game_code === "boxe") {
    return `${round.rows ?? 0} rows - ${round.difficulty ?? "-"}`;
  }
  if (round.game_code === "hi_lo") {
    return `${round.safe_reveals_count} previsioni corrette`;
  }
  return "-";
}

function readStatementDetailTitle(item: StatementDetailItem): string {
  if (item.item_type === "game_round") {
    return item.round_code ? `Round ${item.round_code}` : "Round gioco";
  }
  return item.transaction_type ? item.transaction_type.replace(/_/g, " ") : item.transaction_code ?? "Movimento";
}

function readStatementDetailMeta(item: StatementDetailItem): string {
  const timestamp = formatDateTime(item.timestamp);
  if (item.item_type === "game_round") {
    return `${timestamp} - ${item.game_summary ?? item.result ?? "Round"}`;
  }
  return `${timestamp} - ${item.transaction_code ?? "Dettaglio movimento"}`;
}

function amountClassName(value: string): string {
  const amount = Number.parseFloat(value);
  if (amount > 0) {
    return "is-positive";
  }
  if (amount < 0) {
    return "is-negative";
  }
  return "is-neutral";
}

function formatSignedChipAmount(value: string): string {
  const amount = Number.parseFloat(value);
  if (!Number.isFinite(amount) || amount === 0) {
    return "0.00 CHIP";
  }
  const sign = amount >= 0 ? "+" : "-";
  return `${sign}${Math.abs(amount).toFixed(2)} CHIP`;
}

function formatChipAmount(value: string | number | null | undefined): string {
  const numericValue = typeof value === "number" ? value : value ? Number.parseFloat(value) : 0;
  return Number.isFinite(numericValue) ? numericValue.toFixed(2) : "0.00";
}

function formatDateTime(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return "-";
  }
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function readFirstString(record: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
    if (typeof value === "number" && Number.isFinite(value)) {
      return String(value);
    }
  }
  return "";
}

function readNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => Number(item))
    .filter((item) => Number.isInteger(item));
}

function readBoxeFullReveal(value: unknown): Array<{ row: number; position: number; state: "safe" | "mine" }> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((rowEntry) => {
    if (!rowEntry || typeof rowEntry !== "object") {
      return [];
    }
    const rowRecord = rowEntry as Record<string, unknown>;
    const row = Number(rowRecord.row);
    const cells = Array.isArray(rowRecord.cells) ? rowRecord.cells : [];
    if (!Number.isInteger(row)) {
      return [];
    }
    return cells
      .map((cell) => {
        if (!cell || typeof cell !== "object") {
          return null;
        }
        const cellRecord = cell as Record<string, unknown>;
        const position = Number(cellRecord.position);
        const state = cellRecord.state;
        if (!Number.isInteger(position) || (state !== "safe" && state !== "mine")) {
          return null;
        }
        return { row, position, state };
      })
      .filter((cell): cell is { row: number; position: number; state: "safe" | "mine" } => cell !== null);
  });
}

function readBoxeCellState({
  fullReveal,
  picks,
  position,
  row,
}: {
  fullReveal: Array<{ row: number; position: number; state: "safe" | "mine" }>;
  picks: unknown[];
  position: number;
  row: number;
}): "covered" | "safe" | "mine" {
  const pick = picks.find((item) => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const record = item as Record<string, unknown>;
    return Number(record.row) === row && Number(record.position) === position;
  }) as Record<string, unknown> | undefined;
  if (pick) {
    return pick.safe === false ? "mine" : "safe";
  }
  return fullReveal.find((cell) => cell.row === row && cell.position === position)?.state ?? "covered";
}

function shortenHash(value: string): string {
  if (value.length <= 24) {
    return value;
  }
  return `${value.slice(0, 12)}...${value.slice(-8)}`;
}
