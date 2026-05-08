"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import type { CSSProperties } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";
import type { Wallet } from "@/app/lib/types";
import { Button } from "@/app/ui/components/button";

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

type LedgerTransaction = {
  id: string;
  transaction_type: string;
  created_at: string;
  reference_type: string | null;
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
  access_session_id: string | null;
  access_session: {
    id: string;
    game_code: string;
    status: "active" | "closed" | "timed_out";
    started_at: string;
    last_activity_at: string;
    ended_at: string | null;
  } | null;
  created_at: string;
  closed_at: string | null;
};

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

type AccountTab = "overview" | "profile" | "security" | "wallets" | "statement";

const ACCOUNT_TABS: Array<{ id: AccountTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profilo" },
  { id: "security", label: "Sicurezza" },
  { id: "wallets", label: "Cassa" },
  { id: "statement", label: "Estratto Conto" },
];

function readStoredProfileValue(key: (typeof PLAYER_STORAGE_KEYS)[keyof typeof PLAYER_STORAGE_KEYS]): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

export function PlayerAccountPage() {
  const [accessToken, setAccessToken] = useState("");
  const [currentEmail, setCurrentEmail] = useState("");
  const [activeTab, setActiveTab] = useState<AccountTab>("overview");
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [expandedStatementGroupIds, setExpandedStatementGroupIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordStatus, setPasswordStatus] = useState<string | null>(null);

  async function loadAccountState(token: string) {
    setLoading(true);
    setStatus(null);

    try {
      const [profileData, walletData, transactionData, sessionData] = await Promise.all([
        apiRequest<PlayerProfile>("/auth/me", {}, token),
        apiRequest<Wallet[]>("/wallets", {}, token),
        apiRequest<LedgerTransaction[]>("/ledger/transactions", {}, token),
        apiRequest<SessionHistoryItem[]>("/games/mines/sessions", {}, token),
      ]);

      setProfile(profileData);
      setWallets(walletData);
      setTransactions(transactionData);
      setSessions(sessionData);
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
  const recentTransactions = useMemo(
    () => [...transactions].sort((left, right) => right.created_at.localeCompare(left.created_at)),
    [transactions],
  );
  const primaryWallet = useMemo(
    () => wallets.find((wallet) => wallet.wallet_type === "cash") ?? wallets[0] ?? null,
    [wallets],
  );
  const latestStatementGroup = statementGroups[0] ?? null;
  const latestTransaction = recentTransactions[0] ?? null;

  function toggleStatementGroup(groupId: string) {
    setExpandedStatementGroupIds((current) =>
      current.includes(groupId)
        ? current.filter((entry) => entry !== groupId)
        : [...current, groupId],
    );
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
              <span className="player-account-summary-label">Ultima sessione Mines</span>
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
              <strong className="player-account-summary-value">{recentTransactions.length}</strong>
              <span className="player-account-summary-meta">
                {recentTransactions.length === 1 ? "movimento caricato" : "movimenti caricati"}
              </span>
              {latestTransaction ? (
                <span className="player-account-summary-detail">
                  Ultimo: {readLedgerTransactionTypeLabel(latestTransaction.transaction_type)} -{" "}
                  {formatDateTime(latestTransaction.created_at)}
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
              <Button type="button" variant="secondary" onClick={() => setActiveTab("statement")}>
                Estratto conto
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
        <div className="stack">
          <h3 style={{ marginBottom: 0 }}>Wallets</h3>
          {wallets.length === 0 ? (
            <p style={{ margin: 0 }}>No wallets loaded.</p>
          ) : (
            wallets.map((wallet) => (
              <div key={wallet.wallet_type} className="panel">
                <strong>{wallet.wallet_type}</strong>
                <div>{formatChipAmount(toNumericAmount(wallet.balance_snapshot))}</div>
              </div>
            ))
          )}
        </div>
      );
    }

    return (
      <div className="player-account-statement stack">
        <article className="panel stack player-account-statement-panel">
          <div className="player-account-statement-head">
            <h3>Estratto conto Mines</h3>
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
                        <h4>Mines - {formatDateTime(group.startedAt)}</h4>
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
                                <th style={TABLE_HEADER_STYLE}>Celle safe</th>
                                <th style={TABLE_HEADER_STYLE}>Puntata</th>
                                <th style={TABLE_HEADER_STYLE}>Esito</th>
                                <th style={TABLE_HEADER_STYLE}>Payout</th>
                              </tr>
                            </thead>
                            <tbody>
                              {group.rounds.map((round) => (
                                <tr key={round.game_session_id}>
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
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        <div className="player-account-round-card-list">
                          {group.rounds.map((round) => (
                            <article key={round.game_session_id} className="player-account-round-card">
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
                                  <span>Celle safe</span>
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
                            </article>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          )}
        </article>

        <div className="stack player-account-transactions">
          <h3>Movimenti recenti</h3>
          {transactions.length === 0 ? (
            <p className="player-account-empty">Nessun movimento caricato.</p>
          ) : (
            <div className="player-account-transaction-list">
              {recentTransactions.slice(0, 5).map((transaction) => (
                <div key={transaction.id} className="panel player-account-transaction-card">
                  <strong>{readLedgerTransactionTypeLabel(transaction.transaction_type)}</strong>
                  <div>{formatDateTime(transaction.created_at)}</div>
                  <div>Riferimento: {transaction.reference_type ?? "diretto"}</div>
                </div>
              ))}
            </div>
          )}
        </div>
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
  return `${session.grid_size} celle - ${session.mine_count} mine`;
}

function readRoundRevealLabel(session: SessionHistoryItem): string {
  return `${session.safe_reveals_count} safe / ${session.revealed_cells_count} scoperte`;
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
