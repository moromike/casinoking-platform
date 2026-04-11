"use client";

import { Fragment, useEffect, useMemo, useState, type FormEvent } from "react";
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
  status: "active" | "won" | "lost";
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

type AccountTab = "profile" | "security" | "wallets" | "statement";

const ACCOUNT_TABS: Array<{ id: AccountTab; label: string }> = [
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
  const [activeTab, setActiveTab] = useState<AccountTab>("profile");
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
      <div className="stack" style={{ gap: 16 }}>
        <article className="panel stack" style={{ gap: 12 }}>
          <div>
            <h3 style={{ marginBottom: 8 }}>Mines access sessions</h3>
          </div>

          {statementGroups.length === 0 ? (
            <p style={{ margin: 0 }}>No sessions loaded.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
                <thead>
                   <tr>
                     <th style={TABLE_HEADER_STYLE}>Avvio sessione</th>
                     <th style={TABLE_HEADER_STYLE}>Chiusura</th>
                     <th style={TABLE_HEADER_STYLE}>Stato</th>
                     <th style={TABLE_HEADER_STYLE}>Round</th>
                     <th style={TABLE_HEADER_STYLE}>Giocato</th>
                     <th style={TABLE_HEADER_STYLE}>Vinto</th>
                     <th style={TABLE_HEADER_STYLE}>Delta</th>
                     <th style={TABLE_HEADER_STYLE}>Dettaglio</th>
                   </tr>
                 </thead>
                 <tbody>
                   {statementGroups.map((group) => {
                     const isExpanded = expandedStatementGroupIds.includes(group.id);
                     const deltaAmount = group.totalWon - group.totalStaked;

                     return (
                       <Fragment key={group.id}>
                         <tr>
                          <td style={TABLE_CELL_STYLE}>
                            <div>{formatDateTime(group.startedAt)}</div>
                            <div style={TABLE_META_STYLE}>
                              {group.accessSessionId ? group.accessSessionId.slice(0, 8) : "direct"}
                            </div>
                          </td>
                          <td style={TABLE_CELL_STYLE}>
                            {group.endedAt ? formatDateTime(group.endedAt) : "-"}
                          </td>
                          <td style={TABLE_CELL_STYLE}>{readAccessSessionStatusLabel(group.status)}</td>
                           <td style={TABLE_CELL_STYLE}>{group.roundsCount}</td>
                           <td style={TABLE_CELL_STYLE}>{formatChipAmount(group.totalStaked)} CHIP</td>
                           <td style={TABLE_CELL_STYLE}>{formatChipAmount(group.totalWon)} CHIP</td>
                           <td style={{ ...TABLE_CELL_STYLE, ...readDeltaCellStyle(deltaAmount) }}>
                             {formatSignedChipAmount(deltaAmount)}
                           </td>
                           <td style={TABLE_CELL_STYLE}>
                              <Button type="button" variant="secondary" onClick={() => toggleStatementGroup(group.id)}>
                                {isExpanded ? "Nascondi" : "Dettaglio"}
                              </Button>
                          </td>
                         </tr>
                         {isExpanded ? (
                           <tr>
                             <td colSpan={8} style={{ ...TABLE_CELL_STYLE, padding: 0 }}>
                               <div style={{ padding: 12 }}>
                                 <table
                                   style={{
                                     width: "100%",
                                     borderCollapse: "collapse",
                                    background: "rgba(255, 255, 255, 0.02)",
                                  }}
                                >
                                  <thead>
                                    <tr>
                                      <th style={TABLE_HEADER_STYLE}>Data round</th>
                                      <th style={TABLE_HEADER_STYLE}>Round</th>
                                      <th style={TABLE_HEADER_STYLE}>Config</th>
                                      <th style={TABLE_HEADER_STYLE}>Puntata</th>
                                      <th style={TABLE_HEADER_STYLE}>Esito</th>
                                      <th style={TABLE_HEADER_STYLE}>Vincita</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {group.rounds.map((round) => (
                                      <tr key={round.game_session_id}>
                                        <td style={TABLE_CELL_STYLE}>{formatDateTime(round.created_at)}</td>
                                        <td style={TABLE_CELL_STYLE}>
                                          <div>{round.game_session_id.slice(0, 8)}</div>
                                          <div style={TABLE_META_STYLE}>{round.wallet_type}</div>
                                        </td>
                                        <td style={TABLE_CELL_STYLE}>
                                          {round.grid_size} celle · {round.mine_count} mine
                                        </td>
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
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <div className="stack">
          <h3 style={{ marginBottom: 0 }}>Recent transactions</h3>
          {transactions.length === 0 ? (
            <p style={{ margin: 0 }}>No transactions loaded.</p>
          ) : (
            transactions.slice(0, 5).map((transaction) => (
              <div key={transaction.id} className="panel">
                <strong>{transaction.transaction_type}</strong>
                <div>{formatDateTime(transaction.created_at)}</div>
                <div>{transaction.reference_type ?? "direct"}</div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Account</h2>
        <p style={{ margin: 0 }}>Player account, profile summary, wallets, and session history.</p>
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
      groups.set(groupId, {
        id: groupId,
        accessSessionId,
        status,
        startedAt,
        endedAt,
        rounds: [session],
        roundsCount: 1,
        totalStaked: toNumericAmount(session.bet_amount),
        totalWon: session.status === "won" ? toNumericAmount(session.potential_payout) : 0,
      });
      continue;
    }

    existingGroup.rounds.push(session);
    existingGroup.roundsCount += 1;
    existingGroup.totalStaked += toNumericAmount(session.bet_amount);
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
  return "Attivo";
}

function readRoundPayoutLabel(session: SessionHistoryItem): string {
  if (session.status === "active") {
    return `${formatChipAmount(toNumericAmount(session.potential_payout))} CHIP`;
  }
  if (session.status === "lost") {
    return "0.00 CHIP";
  }
  return `${formatChipAmount(toNumericAmount(session.potential_payout))} CHIP`;
}

function formatSignedChipAmount(value: number): string {
  const sign = value >= 0 ? "+" : "-";
  return `${sign}${formatChipAmount(Math.abs(value))} CHIP`;
}

function readDeltaCellStyle(value: number): CSSProperties {
  if (value > 0) {
    return {
      color: "#22c55e",
      fontWeight: 700,
    };
  }

  if (value < 0) {
    return {
      color: "#ef4444",
      fontWeight: 700,
    };
  }

  return {
    color: "rgba(255, 255, 255, 0.72)",
    fontWeight: 700,
  };
}
