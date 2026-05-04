"use client";

import { Fragment, type CSSProperties } from "react";
import { formatChipAmount, formatDateTime, shortId, toNumericAmount } from "@/app/lib/helpers";

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

type AdminFinancialWalletFilter = "all" | "cash" | "bonus";
type AdminFinancialTransactionTypeFilter = "all" | "bet" | "win" | "void";

type FinancialSessionSummary = {
  session_id: string;
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
  bank_delta: string;
  title_code: string;
  site_code: string;
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
  financialSessions: FinancialSessionSummary[];
  expandedFinancialSessionId: string | null;
  selectedFinancialSessionDetail: FinancialSessionDetail | null;
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
  onApplyFinancialSessionFilters: () => void;
  onFinancialPageSizeChange: (nextLimit: number) => void;
  onToggleFinancialSessionDetail: (sessionId: string) => void;
  onFinancialPreviousPage: () => void;
  onFinancialNextPage: () => void;
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
  financialSessions,
  expandedFinancialSessionId,
  selectedFinancialSessionDetail,
  financialSessionsPagination,
  canLoadPreviousFinancialPage,
  canLoadNextFinancialPage,
  financialSessionsPageTotals,
  onApplyFinancialSessionFilters,
  onFinancialPageSizeChange,
  onToggleFinancialSessionDetail,
  onFinancialPreviousPage,
  onFinancialNextPage,
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
              placeholder="email o frammento email"
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
              <option value="all">Tutti</option>
              <option value="cash">Cash</option>
              <option value="bonus">Bonus</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="admin-financial-transaction-type-filter">Tipo transazione</label>
            <select
              id="admin-financial-transaction-type-filter"
              value={adminTransactionTypeFilter}
              onChange={(event) =>
                onAdminTransactionTypeFilterChange(event.target.value as AdminFinancialTransactionTypeFilter)
              }
            >
              <option value="all">Tutte</option>
              <option value="bet">Bet</option>
              <option value="win">Win</option>
              <option value="void">Void</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="admin-financial-page-size">Righe per pagina</label>
            <select
              id="admin-financial-page-size"
              value={adminItemsPerPage}
              onChange={(event) => onFinancialPageSizeChange(Number(event.target.value))}
              disabled={!accessToken || busyAction !== null}
            >
              {[20, 50, 100, 500].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="field-grid finance-field-grid">
          <div className="field">
            <label htmlFor="admin-financial-date-from-filter">Data inizio</label>
            <input
              id="admin-financial-date-from-filter"
              type="date"
              value={adminDateFromFilter}
              onChange={(event) => onAdminDateFromFilterChange(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-date-to-filter">Data fine</label>
            <input
              id="admin-financial-date-to-filter"
              type="date"
              value={adminDateToFilter}
              onChange={(event) => onAdminDateToFilterChange(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-financial-min-delta-filter">Delta banco min</label>
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
            <label htmlFor="admin-financial-max-delta-filter">Delta banco max</label>
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
            {busyAction === "admin-financial-sessions" ? "Filtro in corso..." : "Filtra"}
          </button>
        </div>
      </div>

      <article className="admin-card">
        <h3>Report sessioni banco</h3>
        {adminFinancialSessionsReport ? (
          <div className="stack">
            {financialSessions.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 980 }}>
                  <thead>
                    <tr>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Email</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Data / Ora</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Gioco</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Stato</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Totale Bet</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Totale Payout</th>
                      <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Delta Banco</th>
                    </tr>
                  </thead>
                  <tbody>
                    {financialSessions.map((session) => {
                      const isExpanded = expandedFinancialSessionId === session.session_id;
                      const deltaValue = toNumericAmount(session.bank_delta);
                      const isSelectedDetail = selectedFinancialSessionDetail?.session_id === session.session_id;

                      return (
                        <Fragment key={session.session_id}>
                          <tr
                            onClick={() => onToggleFinancialSessionDetail(session.session_id)}
                            style={{ cursor: "pointer" }}
                          >
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>
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
                            <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{session.status}</td>
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
                              <td colSpan={7} style={{ ...ADMIN_FINANCE_TABLE_CELL_STYLE, padding: 0 }}>
                                <div style={{ padding: 12 }}>
                                  {busyAction === `admin-financial-session-${session.session_id}` && !isSelectedDetail ? (
                                    <p className="empty-state">Caricamento dettaglio sessione...</p>
                                  ) : isSelectedDetail ? (
                                    <div className="stack">
                                      <div className="admin-metric-row">
                                        <span className="list-muted">Title / Site</span>
                                        <span>
                                          {selectedFinancialSessionDetail.title_code} / {selectedFinancialSessionDetail.site_code}
                                        </span>
                                      </div>
                                      <div className="admin-metric-row">
                                        <span className="list-muted">Delta sessione</span>
                                        <span className={`status-inline ${toNumericAmount(selectedFinancialSessionDetail.bank_delta) >= 0 ? "success" : "warning"}`}>
                                          {toNumericAmount(selectedFinancialSessionDetail.bank_delta) >= 0 ? "+" : ""}
                                          {formatChipAmount(toNumericAmount(selectedFinancialSessionDetail.bank_delta))}
                                        </span>
                                      </div>
                                      <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                          <tr>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Quando</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Evento</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Wallet</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Bet</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Payout</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Delta</th>
                                            <th style={ADMIN_FINANCE_TABLE_HEADER_STYLE}>Dettaglio</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {selectedFinancialSessionDetail.events.map((event) => {
                                            const eventDelta = toNumericAmount(event.delta);
                                            return (
                                              <tr key={event.ledger_transaction_id}>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{formatDateTime(event.timestamp)}</td>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.transaction_type}</td>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.wallet_type}</td>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{formatChipAmount(toNumericAmount(event.bank_credit))} CHIP</td>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{formatChipAmount(toNumericAmount(event.bank_debit))} CHIP</td>
                                                <td
                                                  style={{
                                                    ...ADMIN_FINANCE_TABLE_CELL_STYLE,
                                                    color: eventDelta >= 0 ? "#39d98a" : "#ff6b6b",
                                                    fontWeight: 700,
                                                  }}
                                                >
                                                  {eventDelta >= 0 ? "+" : ""}
                                                  {formatChipAmount(eventDelta)} CHIP
                                                </td>
                                                <td style={ADMIN_FINANCE_TABLE_CELL_STYLE}>{event.game_enrichment || "-"}</td>
                                              </tr>
                                            );
                                          })}
                                        </tbody>
                                      </table>
                                    </div>
                                  ) : (
                                    <p className="empty-state">Apri la riga per caricare il dettaglio.</p>
                                  )}
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
            ) : (
              <p className="empty-state">Nessuna sessione trovata con i filtri correnti.</p>
            )}
            <div className="actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <div className="helper">
                {financialSessionsPagination.total_items > 0
                  ? `Pagina ${financialSessionsPagination.page} di ${financialSessionsPagination.total_pages}`
                  : "Pagina 0 di 0"}
              </div>
              <div className="actions">
                <button
                  className="button-secondary"
                  type="button"
                  disabled={!accessToken || busyAction !== null || !canLoadPreviousFinancialPage}
                  onClick={onFinancialPreviousPage}
                >
                  Pagina Precedente
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  disabled={!accessToken || busyAction !== null || !canLoadNextFinancialPage}
                  onClick={onFinancialNextPage}
                >
                  Successiva
                </button>
              </div>
            </div>
            <div className="admin-metric-row">
              <span className="list-muted">Totale Delta Banco Pagina</span>
              <span
                className={`status-inline ${toNumericAmount(financialSessionsPageTotals.bank_delta) >= 0 ? "success" : "warning"}`}
              >
                {toNumericAmount(financialSessionsPageTotals.bank_delta) >= 0 ? "+" : ""}
                {formatChipAmount(toNumericAmount(financialSessionsPageTotals.bank_delta))} CHIP
              </span>
            </div>
          </div>
        ) : (
          <p className="empty-state">Caricamento report sessioni banco...</p>
        )}
      </article>
    </div>
  );
}
