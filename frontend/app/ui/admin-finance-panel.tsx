"use client";

import { Fragment, useState, type CSSProperties } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";
import {
  hasAdminGameReplay,
  readAdminGameReplayEndpoint,
  renderAdminGameReplay,
  type GameReplayPayload,
} from "@/app/ui/game-reporting-registry";

const ADMIN_FINANCE_TABLE_HEADER_STYLE: CSSProperties = {
  textAlign: "left",
  padding: "12px 14px",
  fontSize: "0.8rem",
  color: "#64748b",
  borderBottom: "1px solid rgba(148, 163, 184, 0.24)",
};

const ADMIN_FINANCE_TABLE_CELL_STYLE: CSSProperties = {
  padding: "12px 14px",
  borderBottom: "1px solid rgba(148, 163, 184, 0.18)",
  verticalAlign: "top",
  color: "#1f2937",
};

const ADMIN_FINANCE_PLAYER_BUTTON_STYLE: CSSProperties = {
  display: "inline",
  border: 0,
  background: "transparent",
  color: "#1f2937",
  cursor: "pointer",
  font: "inherit",
  fontWeight: 800,
  lineHeight: 1.35,
  padding: 0,
  textAlign: "left",
  wordBreak: "break-word",
};

type AdminFinancialWalletFilter = "all" | "cash" | "bonus";
type AdminFinancialTransactionTypeFilter = "all" | "bet" | "win" | "void";

type FinancialSessionSummary = {
  session_id: string;
  is_legacy?: boolean;
  user_id: string;
  user_email: string;
  game_code: string;
  title_code: string;
  site_code: string;
  started_at: string;
  ended_at: string;
  status: string;
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
  metadata_completeness?: "complete" | "partial" | "legacy";
  game_enrichment: string;
};

type FinancialSessionDetail = FinancialSessionSummary & {
  events: FinancialSessionEvent[];
};

type AdminGameReplay = GameReplayPayload;

type AdminGameReplayState = {
  replay: AdminGameReplay | null;
  loading: boolean;
  error: string | null;
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
};

type AdminFinancePanelProps = {
  accessToken: string;
  busyAction: string | null;
  adminEmailFilter: string;
  onAdminEmailFilterChange: (value: string) => void;
  adminFinancialWalletFilter: AdminFinancialWalletFilter;
  onAdminFinancialWalletFilterChange: (value: AdminFinancialWalletFilter) => void;
  adminTransactionTypeFilter: AdminFinancialTransactionTypeFilter;
  onAdminTransactionTypeFilterChange: (value: AdminFinancialTransactionTypeFilter) => void;
  adminItemsPerPage: number;
  adminDateFromFilter: string;
  onAdminDateFromFilterChange: (value: string) => void;
  adminDateToFilter: string;
  onAdminDateToFilterChange: (value: string) => void;
  adminMinDeltaFilter: string;
  onAdminMinDeltaFilterChange: (value: string) => void;
  adminMaxDeltaFilter: string;
  onAdminMaxDeltaFilterChange: (value: string) => void;
  adminFinancialSessionsReport: AdminFinancialSessionsReport | null;
  financialSessionDetails: Record<string, FinancialSessionDetail>;
  financialSessions: FinancialSessionSummary[];
  financialSessionsPagination: {
    page: number;
    total_items: number;
    total_pages: number;
  };
  canLoadPreviousFinancialPage: boolean;
  canLoadNextFinancialPage: boolean;
  financialSessionsPageTotals: {
    bank_delta: string;
  };
  expandedFinancialSessionId: string | null;
  onApplyFinancialSessionFilters: () => void;
  onToggleFinancialSessionDetail: (sessionId: string) => void;
  onFinancialPageSizeChange: (nextLimit: number) => void;
  onFinancialPreviousPage: () => void;
  onFinancialNextPage: () => void;
  onOpenPlayerProfile?: (userId: string, email: string) => void;
};

export function AdminFinancePanel({
  accessToken,
  busyAction,
  adminEmailFilter,
  onAdminEmailFilterChange,
  adminFinancialWalletFilter,
  onAdminFinancialWalletFilterChange,
  adminTransactionTypeFilter,
  onAdminTransactionTypeFilterChange,
  adminItemsPerPage,
  adminDateFromFilter,
  onAdminDateFromFilterChange,
  adminDateToFilter,
  onAdminDateToFilterChange,
  adminMinDeltaFilter,
  onAdminMinDeltaFilterChange,
  adminMaxDeltaFilter,
  onAdminMaxDeltaFilterChange,
  adminFinancialSessionsReport,
  financialSessionDetails,
  financialSessions,
  financialSessionsPagination,
  expandedFinancialSessionId,
  canLoadPreviousFinancialPage,
  canLoadNextFinancialPage,
  financialSessionsPageTotals,
  onApplyFinancialSessionFilters,
  onToggleFinancialSessionDetail,
  onFinancialPageSizeChange,
  onFinancialPreviousPage,
  onFinancialNextPage,
  onOpenPlayerProfile,
}: AdminFinancePanelProps) {
  return (
    <div className="stack">
      <div className="admin-surface admin-surface-section finance-filter-panel">
        <div className="field-grid finance-field-grid">
          <div className="field">
            <label htmlFor="admin-email-filter">Player</label>
            <input
              id="admin-email-filter"
              value={adminEmailFilter}
              onChange={(event) => onAdminEmailFilterChange(event.target.value)}
              placeholder="email or email fragment"
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-wallet-filter">Wallet</label>
            <select
              id="admin-financial-wallet-filter"
              value={adminFinancialWalletFilter}
              onChange={(event) =>
                onAdminFinancialWalletFilterChange(event.target.value as AdminFinancialWalletFilter)
              }
            >
              <option value="all">All</option>
              <option value="cash">Cash</option>
              <option value="bonus">Bonus</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="admin-financial-transaction-type-filter">Transaction type</label>
            <select
              id="admin-financial-transaction-type-filter"
              value={adminTransactionTypeFilter}
              onChange={(event) =>
                onAdminTransactionTypeFilterChange(event.target.value as AdminFinancialTransactionTypeFilter)
              }
            >
              <option value="all">All</option>
              <option value="bet">Bet</option>
              <option value="win">Win</option>
              <option value="void">Void</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="admin-financial-page-size">Rows per page</label>
            <select
              id="admin-financial-page-size"
              value={adminItemsPerPage}
              onChange={(event) => onFinancialPageSizeChange(Number(event.target.value))}
              disabled={!accessToken || busyAction !== null}
            >
              {[25, 50, 100].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="field-grid finance-field-grid">
          <div className="field">
            <label htmlFor="admin-financial-date-from-filter">Start date</label>
            <input
              id="admin-financial-date-from-filter"
              type="date"
              value={adminDateFromFilter}
              onChange={(event) => onAdminDateFromFilterChange(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-date-to-filter">End date</label>
            <input
              id="admin-financial-date-to-filter"
              type="date"
              value={adminDateToFilter}
              onChange={(event) => onAdminDateToFilterChange(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-min-delta-filter">Min bank delta</label>
            <input
              id="admin-financial-min-delta-filter"
              type="text"
              inputMode="decimal"
              value={adminMinDeltaFilter}
              onChange={(event) => onAdminMinDeltaFilterChange(event.target.value)}
              placeholder="0.000000"
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-max-delta-filter">Max bank delta</label>
            <input
              id="admin-financial-max-delta-filter"
              type="text"
              inputMode="decimal"
              value={adminMaxDeltaFilter}
              onChange={(event) => onAdminMaxDeltaFilterChange(event.target.value)}
              placeholder="0.000000"
            />
          </div>
        </div>
        <div className="actions finance-filter-actions">
          <button
            className="button-secondary"
            type="button"
            disabled={!accessToken || busyAction !== null}
            onClick={onApplyFinancialSessionFilters}
          >
            {busyAction === "admin-financial-sessions" ? "Filtering..." : "Filter"}
          </button>
        </div>
      </div>

      <article className="admin-card">
        <h3>Bank session report</h3>
        {adminFinancialSessionsReport ? (
          <div className="stack">
            {financialSessions.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 980 }}>
                  <thead>
                    <tr>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Email</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Date / Time</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Game</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Status</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Total Bet</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Total Payout</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Bank Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {financialSessions.map((session) => {
                      const deltaValue = toNumericAmount(session.bank_delta);
                      const isExpanded = expandedFinancialSessionId === session.session_id;
                      const detail = financialSessionDetails[session.session_id] ?? null;
                      const isDetailLoading =
                        busyAction === `admin-financial-session-detail:${session.session_id}`;

                      return (
                        <Fragment key={session.session_id}>
                          <tr>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              {onOpenPlayerProfile ? (
                                <button
                                  style={ADMIN_FINANCE_PLAYER_BUTTON_STYLE}
                                  type="button"
                                  onClick={() => onOpenPlayerProfile(session.user_id, session.user_email)}
                                >
                                  {session.user_email}
                                </button>
                              ) : (
                                <div
                                  style={{
                                    color: "#1f2937",
                                    fontWeight: 700,
                                    lineHeight: 1.35,
                                    wordBreak: "break-word",
                                  }}
                                >
                                  {session.user_email}
                                </div>
                              )}
                              <div
                                style={{
                                  color: "#6b7280",
                                  fontSize: 12,
                                  lineHeight: 1.35,
                                  marginTop: 4,
                                  wordBreak: "break-all",
                                }}
                              >
                                {session.user_id}
                              </div>
                            </td>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              <div>{formatDateTime(session.started_at)}</div>
                              <div className="helper">
                                {session.ended_at ? formatDateTime(session.ended_at) : "-"}
                              </div>
                            </td>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              <div>{session.game_code}</div>
                              <div className="helper">{session.title_code}</div>
                              <div className="helper">{session.site_code}</div>
                            </td>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              <div>{session.status}</div>
                              <button
                                className="button-secondary"
                                type="button"
                                disabled={!accessToken || busyAction !== null}
                                aria-expanded={isExpanded}
                                aria-busy={isDetailLoading || undefined}
                                onClick={() => onToggleFinancialSessionDetail(session.session_id)}
                                style={{
                                  marginTop: 8,
                                  minHeight: 30,
                                  padding: "6px 10px",
                                  fontSize: "0.76rem",
                                }}
                              >
                                {isDetailLoading ? "Loading detail..." : "Round detail"}
                              </button>
                            </td>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              {formatChipAmount(toNumericAmount(session.bank_total_credit))} CHIP
                            </td>
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                              {formatChipAmount(toNumericAmount(session.bank_total_debit))} CHIP
                            </td>
                            <td
                              style={{
                                ...ADMIN_FINANCE_TABLE_CELL_STYLE,
                                color: deltaValue >= 0 ? "#39d98a" : "#ff6b6b",
                                fontWeight: 700,
                              }}
                            >
                              {deltaValue >= 0 ? "+" : ""}
                              {formatChipAmount(deltaValue)} CHIP
                            </td>
                          </tr>
                          {isExpanded ? (
                            <tr>
                              <td colSpan={7} style={{ ...ADMIN_FINANCE_TABLE_CELL_STYLE, background: "#f8fafc" }}>
                                {detail ? (
                                  <FinancialSessionDetailRows
                                    accessToken={accessToken}
                                    events={detail.events}
                                    gameCode={detail.game_code}
                                  />
                                ) : (
                                  <p className="empty-state">
                                    {isDetailLoading ? "Loading round detail..." : "Detail not loaded yet."}
                                  </p>
                                )}
                              </td>
                            </tr>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="empty-state">No sessions found with the current filters.</p>
            )}
            <div className="actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <div className="helper">
                {financialSessionsPagination.total_items > 0
                  ? `Page ${financialSessionsPagination.page} of ${financialSessionsPagination.total_pages}`
                  : "Page 0 of 0"}
              </div>
              <div className="actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={!accessToken || busyAction !== null || !canLoadPreviousFinancialPage}
                  onClick={onFinancialPreviousPage}
                >
                  Previous Page
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={!accessToken || busyAction !== null || !canLoadNextFinancialPage}
                  onClick={onFinancialNextPage}
                >
                  Next
                </button>
              </div>
            </div>
            <div className="admin-metric-row">
              <span className="list-muted">Page Bank Delta Total</span>
              <span
                className={`status-inline ${toNumericAmount(financialSessionsPageTotals.bank_delta) >= 0 ? "success" : "warning"}`}
              >
                {toNumericAmount(financialSessionsPageTotals.bank_delta) >= 0 ? "+" : ""}
                {formatChipAmount(toNumericAmount(financialSessionsPageTotals.bank_delta))} CHIP
              </span>
            </div>
          </div>
        ) : (
          <p className="empty-state">Loading bank session report...</p>
        )}
      </article>
    </div>
  );
}

function FinancialSessionDetailRows({
  accessToken,
  events,
  gameCode,
}: {
  accessToken: string;
  events: FinancialSessionEvent[];
  gameCode: string;
}) {
  const [expandedReplayRoundId, setExpandedReplayRoundId] = useState<string | null>(null);
  const [replayStates, setReplayStates] = useState<Record<string, AdminGameReplayState>>({});

  if (events.length === 0) {
    return <p className="empty-state">No ledger events for this session.</p>;
  }

  function toggleReplay(roundId: string) {
    const isExpanded = expandedReplayRoundId === roundId;
    setExpandedReplayRoundId(isExpanded ? null : roundId);
    if (!isExpanded && !replayStates[roundId]?.replay) {
      void loadReplay(roundId);
    }
  }

  async function loadReplay(roundId: string) {
    const endpoint = readAdminGameReplayEndpoint(gameCode, roundId);
    if (!endpoint) {
      setReplayStates((current) => ({
        ...current,
        [roundId]: {
          replay: current[roundId]?.replay ?? null,
          loading: false,
          error: `Replay unavailable for ${gameCode}.`,
        },
      }));
      return;
    }

    setReplayStates((current) => ({
      ...current,
      [roundId]: {
        replay: current[roundId]?.replay ?? null,
        loading: true,
        error: null,
      },
    }));
    try {
      const replay = await apiRequest<AdminGameReplay>(
        endpoint,
        {},
        accessToken,
      );
      setReplayStates((current) => ({
        ...current,
        [roundId]: {
          replay,
          loading: false,
          error: null,
        },
      }));
    } catch (error) {
      setReplayStates((current) => ({
        ...current,
        [roundId]: {
          replay: current[roundId]?.replay ?? null,
          loading: false,
          error: readErrorMessage(error, "Replay loading failed."),
        },
      }));
    }
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 1040 }}>
        <thead>
          <tr>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Time</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Type</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Wallet</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Round / Spin</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Ledger TX</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Bank +</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Bank -</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Delta</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Metadata</th>
            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Note</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => {
            const deltaValue = toNumericAmount(event.delta);
            const replayExpanded = expandedReplayRoundId === event.platform_round_id;
            const replayState = replayStates[event.platform_round_id];
            const replayAvailable = hasAdminGameReplay(gameCode);

            return (
              <Fragment key={`${event.ledger_transaction_id}:${event.platform_round_id}`}>
                <tr>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{formatDateTime(event.timestamp)}</td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.transaction_type}</td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.wallet_type}</td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                    <div style={{ fontWeight: 800 }}>
                      RND-{event.platform_round_id.slice(0, 8).toUpperCase()}
                    </div>
                    <div className="helper" style={{ wordBreak: "break-all" }}>
                      {event.platform_round_id}
                    </div>
                    {replayAvailable ? (
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={!accessToken}
                        aria-expanded={replayExpanded}
                        onClick={() => toggleReplay(event.platform_round_id)}
                        style={{
                          marginTop: 8,
                          minHeight: 30,
                          padding: "6px 10px",
                          fontSize: "0.76rem",
                        }}
                      >
                        {replayExpanded ? "Close replay" : "Replay"}
                      </button>
                    ) : (
                      <div className="helper" style={{ marginTop: 8 }}>
                        Replay unavailable for {gameCode}.
                      </div>
                    )}
                  </td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                    <div className="helper" style={{ wordBreak: "break-all" }}>
                      {event.ledger_transaction_id}
                    </div>
                  </td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                    {formatChipAmount(toNumericAmount(event.bank_credit))} CHIP
                  </td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                    {formatChipAmount(toNumericAmount(event.bank_debit))} CHIP
                  </td>
                  <td
                    style={{
                      ...ADMIN_FINANCE_TABLE_CELL_STYLE,
                      color: deltaValue >= 0 ? "#166534" : "#b91c1c",
                      fontWeight: 800,
                    }}
                  >
                    {deltaValue >= 0 ? "+" : ""}
                    {formatChipAmount(deltaValue)} CHIP
                  </td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
                    <span className="status-line">{event.metadata_completeness ?? "legacy"}</span>
                  </td>
                  <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.game_enrichment || "-"}</td>
                </tr>
                {replayExpanded ? (
                  <tr>
                    <td colSpan={10} style={{ ...ADMIN_FINANCE_TABLE_CELL_STYLE, background: "#0f172a" }}>
                      {replayState?.loading ? <p className="empty-state">Loading replay...</p> : null}
                      {replayState?.error ? <p className="empty-state">{replayState.error}</p> : null}
                      {replayState?.replay ? renderAdminGameReplay(gameCode, replayState.replay) : null}
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

