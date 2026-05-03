"use client";

import { type FormEvent } from "react";
import { formatChipAmount, formatDateTime, shortId, toNumericAmount } from "@/app/lib/helpers";
import { AccessLog } from "./access-log";

type PlayerAdminView = "list" | "detail";

type PlayerAdminUser = {
  id: string;
  email: string;
  status: string;
  created_at: string;
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
};

type PlayerAdminWalletRow = {
  balance_snapshot: string;
};

type PlayerAdminPanelProps = {
  accessToken: string;
  busyAction: string | null;
  playerAdminView: PlayerAdminView;
  adminEmailFilter: string;
  onAdminEmailFilterChange: (value: string) => void;
  adminUsers: PlayerAdminUser[];
  selectedAdminUser: PlayerAdminUser | null;
  canAccessFinance: boolean;
  adminPlayerNewPassword: string;
  onAdminPlayerNewPasswordChange: (value: string) => void;
  selectedAdminCashWallet: PlayerAdminWalletRow | null;
  selectedAdminBonusWallet: PlayerAdminWalletRow | null;
  selectedAdminTotalBalance: number;
  bonusAmount: string;
  onBonusAmountChange: (value: string) => void;
  bonusReason: string;
  onBonusReasonChange: (value: string) => void;
  adjustmentWalletType: string;
  onAdjustmentWalletTypeChange: (value: string) => void;
  adjustmentDirection: string;
  onAdjustmentDirectionChange: (value: string) => void;
  adjustmentAmount: string;
  onAdjustmentAmountChange: (value: string) => void;
  adjustmentReason: string;
  onAdjustmentReasonChange: (value: string) => void;
  topupThreshold: string;
  onTopupThresholdChange: (value: string) => void;
  topupAmount: string;
  onTopupAmountChange: (value: string) => void;
  forceCloseReason: string;
  onForceCloseReasonChange: (value: string) => void;
  onForceCloseSessions: (event: FormEvent<HTMLFormElement>) => void;
  onLoadAdminUsers: () => void;
  onSelectAdminUser: (userId: string) => void;
  onChangeView: (view: PlayerAdminView) => void;
  onSuspendSelectedUser: (userId: string) => void;
  onGoToSessions: (email: string) => void;
  onAdminResetPlayerPassword: (event: FormEvent<HTMLFormElement>) => void;
  onLoadLedgerReport: () => void;
  onCreateBonusGrant: (event: FormEvent<HTMLFormElement>) => void;
  onCreateAdjustment: (event: FormEvent<HTMLFormElement>) => void;
  onTopupBelowThreshold: (event: FormEvent<HTMLFormElement>) => void;
};

export function PlayerAdminPanel({
  accessToken,
  busyAction,
  playerAdminView,
  adminEmailFilter,
  onAdminEmailFilterChange,
  adminUsers,
  selectedAdminUser,
  canAccessFinance,
  adminPlayerNewPassword,
  onAdminPlayerNewPasswordChange,
  selectedAdminCashWallet,
  selectedAdminBonusWallet,
  selectedAdminTotalBalance,
  bonusAmount,
  onBonusAmountChange,
  bonusReason,
  onBonusReasonChange,
  adjustmentWalletType,
  onAdjustmentWalletTypeChange,
  adjustmentDirection,
  onAdjustmentDirectionChange,
  adjustmentAmount,
  onAdjustmentAmountChange,
  adjustmentReason,
  onAdjustmentReasonChange,
  topupThreshold,
  onTopupThresholdChange,
  topupAmount,
  onTopupAmountChange,
  forceCloseReason,
  onForceCloseReasonChange,
  onForceCloseSessions,
  onLoadAdminUsers,
  onSelectAdminUser,
  onChangeView,
  onSuspendSelectedUser,
  onGoToSessions,
  onAdminResetPlayerPassword,
  onLoadLedgerReport,
  onCreateBonusGrant,
  onCreateAdjustment,
  onTopupBelowThreshold,
}: PlayerAdminPanelProps) {
  return (
    <div className="stack">
      {playerAdminView === "list" ? (
        <>
          <div className="admin-surface admin-surface-section">
            <div className="field-grid">
              <div className="field">
                <label htmlFor="admin-email-filter">Filtra per email</label>
                <input
                  id="admin-email-filter"
                  value={adminEmailFilter}
                  onChange={(event) => onAdminEmailFilterChange(event.target.value)}
                  placeholder="email o frammento email"
                />
              </div>
            </div>
            <div className="actions">
              <button
                className="button-secondary"
                type="button"
                disabled={!accessToken || busyAction !== null}
                onClick={onLoadAdminUsers}
              >
                {busyAction === "admin-users" ? "Carico..." : "Aggiorna lista"}
              </button>
            </div>
          </div>
          {adminUsers.length > 0 ? (
            <div className="admin-list admin-list-static">
              {[...adminUsers]
                .sort((a, b) => b.created_at.localeCompare(a.created_at))
                .map((user) => (
                  <article className="admin-list-card" key={user.id}>
                    <div className="list-row">
                      <span className="list-strong">{user.email}</span>
                      <span className={`status-inline ${user.status === "active" ? "success" : "warning"}`}>
                        {user.status}
                      </span>
                    </div>
                    <div className="admin-metric-row">
                      <span className="list-muted">Registrato il</span>
                      <span>{formatDateTime(user.created_at)}</span>
                    </div>
                    <div className="actions">
                      <button
                        className="button-secondary"
                        type="button"
                        onClick={() => {
                          onSelectAdminUser(user.id);
                          onChangeView("detail");
                        }}
                      >
                        Apri scheda
                      </button>
                    </div>
                  </article>
                ))}
            </div>
          ) : busyAction === "admin-users" ? null : (
            <p className="empty-state">Nessun giocatore caricato.</p>
          )}
        </>
      ) : (
        <div className="stack">
          <div className="actions">
            <button
              className="button-secondary"
              type="button"
              onClick={() => onChangeView("list")}
            >
              ← Lista giocatori
            </button>
          </div>

          {selectedAdminUser ? (
            <>
              <article className="admin-card">
                <h3>{selectedAdminUser.email}</h3>
                <div className="admin-metric-row">
                  <span className="list-muted">User ID</span>
                  <span className="mono">{shortId(selectedAdminUser.id)}</span>
                </div>
                {selectedAdminUser.first_name || selectedAdminUser.last_name ? (
                  <div className="admin-metric-row">
                    <span className="list-muted">Nome</span>
                    <span>{[selectedAdminUser.first_name, selectedAdminUser.last_name].filter(Boolean).join(" ")}</span>
                  </div>
                ) : null}
                {selectedAdminUser.phone_number ? (
                  <div className="admin-metric-row">
                    <span className="list-muted">Telefono</span>
                    <span>{selectedAdminUser.phone_number}</span>
                  </div>
                ) : null}
                <div className="admin-metric-row">
                  <span className="list-muted">Status</span>
                  <span className={`status-inline ${selectedAdminUser.status === "active" ? "success" : "warning"}`}>
                    {selectedAdminUser.status}
                  </span>
                </div>
                <div className="admin-metric-row">
                  <span className="list-muted">Registrato il</span>
                  <span>{formatDateTime(selectedAdminUser.created_at)}</span>
                </div>
                <div className="actions">
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={busyAction !== null || selectedAdminUser.status === "suspended"}
                    onClick={() => onSuspendSelectedUser(selectedAdminUser.id)}
                  >
                    {busyAction === "admin-suspend" ? "Sospendo..." : "Sospendi account"}
                  </button>
                  {canAccessFinance ? (
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => onGoToSessions(selectedAdminUser.email)}
                    >
                      Vai alle sessioni
                    </button>
                  ) : null}
                </div>
                <form className="stack" onSubmit={(event) => void onAdminResetPlayerPassword(event)}>
                  <div className="field">
                    <label htmlFor="admin-player-new-pwd">Reset password</label>
                    <input
                      id="admin-player-new-pwd"
                      type="password"
                      value={adminPlayerNewPassword}
                      onChange={(event) => onAdminPlayerNewPasswordChange(event.target.value)}
                      placeholder="Nuova password (min. 8 caratteri)"
                      autoComplete="new-password"
                    />
                  </div>
                  <div className="actions">
                    <button
                      className="button-ghost"
                      type="submit"
                      disabled={busyAction !== null || adminPlayerNewPassword.trim().length < 8}
                    >
                      {busyAction === "admin-player-reset-pwd" ? "Resetto..." : "Reimposta password"}
                    </button>
                  </div>
                </form>
              </article>

              <article className="admin-card">
                <h3>Wallet</h3>
                {selectedAdminCashWallet || selectedAdminBonusWallet ? (
                  <div className="account-overview-grid">
                    <article className="overview-tile">
                      <span className="list-muted">Cash</span>
                      <strong>
                        {selectedAdminCashWallet
                          ? `${formatChipAmount(toNumericAmount(selectedAdminCashWallet.balance_snapshot))} CHIP`
                          : "n/a"}
                      </strong>
                    </article>
                    <article className="overview-tile">
                      <span className="list-muted">Bonus</span>
                      <strong>
                        {selectedAdminBonusWallet
                          ? `${formatChipAmount(toNumericAmount(selectedAdminBonusWallet.balance_snapshot))} CHIP`
                          : "n/a"}
                      </strong>
                    </article>
                  </div>
                ) : (
                  <div className="actions">
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={busyAction !== null}
                      onClick={onLoadLedgerReport}
                    >
                      {busyAction === "admin-ledger-report" ? "Carico..." : "Carica dati wallet"}
                    </button>
                  </div>
                )}
              </article>

              {canAccessFinance ? (
                <div className="admin-grid admin-grid-two">
                  <article className="admin-card">
                    <h3>Bonus grant</h3>
                    <form className="stack" onSubmit={(event) => void onCreateBonusGrant(event)}>
                      <div className="field">
                        <label htmlFor="bonus-amount">Importo (CHIP)</label>
                        <input
                          id="bonus-amount"
                          value={bonusAmount}
                          onChange={(event) => onBonusAmountChange(event.target.value)}
                          placeholder="es. 10.000000"
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="bonus-reason">Motivo</label>
                        <input
                          id="bonus-reason"
                          value={bonusReason}
                          onChange={(event) => onBonusReasonChange(event.target.value)}
                          placeholder="es. manual_bonus"
                        />
                      </div>
                      <div className="actions">
                        <button className="button-secondary" type="submit" disabled={busyAction !== null}>
                          {busyAction === "admin-bonus-grant" ? "Registro..." : "Accredita bonus"}
                        </button>
                      </div>
                    </form>
                  </article>

                  <article className="admin-card">
                    <h3>Wallet adjustment</h3>
                    <form className="stack" onSubmit={(event) => void onCreateAdjustment(event)}>
                      <div className="field">
                        <label htmlFor="adj-wallet-type">Wallet</label>
                        <select
                          id="adj-wallet-type"
                          value={adjustmentWalletType}
                          onChange={(event) => onAdjustmentWalletTypeChange(event.target.value)}
                        >
                          <option value="cash">cash</option>
                          <option value="bonus">bonus</option>
                        </select>
                      </div>
                      <div className="field">
                        <label htmlFor="adj-direction">Direzione</label>
                        <select
                          id="adj-direction"
                          value={adjustmentDirection}
                          onChange={(event) => onAdjustmentDirectionChange(event.target.value)}
                        >
                          <option value="credit">credit</option>
                          <option value="debit">debit</option>
                        </select>
                      </div>
                      <div className="field">
                        <label htmlFor="adj-amount">Importo (CHIP)</label>
                        <input
                          id="adj-amount"
                          value={adjustmentAmount}
                          onChange={(event) => onAdjustmentAmountChange(event.target.value)}
                          placeholder="es. 5.000000"
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="adj-reason">Motivo</label>
                        <input
                          id="adj-reason"
                          value={adjustmentReason}
                          onChange={(event) => onAdjustmentReasonChange(event.target.value)}
                          placeholder="es. manual_adjustment"
                        />
                      </div>
                      <div className="actions">
                        <button className="button-secondary" type="submit" disabled={busyAction !== null}>
                          {busyAction === "admin-adjustment" ? "Registro..." : "Applica adjustment"}
                        </button>
                      </div>
                    </form>
                  </article>

                  <article className="admin-card">
                    <h3>Top-up sotto soglia</h3>
                    <form className="stack" onSubmit={(event) => void onTopupBelowThreshold(event)}>
                      <div className="admin-metric-row">
                        <span className="list-muted">Saldo totale</span>
                        <span className={`status-inline ${selectedAdminTotalBalance < toNumericAmount(topupThreshold) ? "warning" : "success"}`}>
                          {formatChipAmount(selectedAdminTotalBalance)} CHIP
                        </span>
                      </div>
                      <div className="field">
                        <label htmlFor="topup-threshold">Soglia (CHIP)</label>
                        <input
                          id="topup-threshold"
                          value={topupThreshold}
                          onChange={(event) => onTopupThresholdChange(event.target.value)}
                          placeholder="es. 5.000000"
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="topup-amount">Importo top-up (CHIP)</label>
                        <input
                          id="topup-amount"
                          value={topupAmount}
                          onChange={(event) => onTopupAmountChange(event.target.value)}
                          placeholder="es. 10.000000"
                        />
                      </div>
                      <div className="actions">
                        <button
                          className="button-secondary"
                          type="submit"
                          disabled={busyAction !== null || selectedAdminTotalBalance >= toNumericAmount(topupThreshold)}
                        >
                          {busyAction === "admin-topup-threshold" ? "Accredito..." : "Top-up bonus"}
                        </button>
                      </div>
                    </form>
                  </article>

                  <article className="admin-card">
                    <h3>Force-close sessioni di gioco</h3>
                    <form
                      className="stack"
                      onSubmit={(event) => void onForceCloseSessions(event)}
                    >
                      <div className="field">
                        <label htmlFor="force-close-reason">Motivo</label>
                        <input
                          id="force-close-reason"
                          value={forceCloseReason}
                          onChange={(event) => onForceCloseReasonChange(event.target.value)}
                          placeholder="es. ticket #1234, anomalia segnalata"
                        />
                      </div>
                      <div className="actions">
                        <button
                          className="button-secondary"
                          type="submit"
                          disabled={busyAction !== null || forceCloseReason.trim().length === 0}
                        >
                          {busyAction === "admin-force-close-sessions"
                            ? "Chiudo..."
                            : "Chiudi sessioni attive"}
                        </button>
                      </div>
                    </form>
                  </article>
                </div>
              ) : null}

              <article className="admin-card">
                <h3>Accessi giocatore</h3>
                <AccessLog
                  accessToken={accessToken}
                  defaultRole="player"
                  defaultEmail={selectedAdminUser.email}
                  showRoleFilter={false}
                />
              </article>
            </>
          ) : (
            <p className="empty-state">Seleziona un giocatore dalla lista.</p>
          )}
        </div>
      )}
    </div>
  );
}
