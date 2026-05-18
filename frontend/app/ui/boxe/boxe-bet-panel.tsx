"use client";

import type { BoxeCopyKey } from "./boxe-i18n/boxe-copy-defaults";
import type { BoxeWalletSource } from "./use-boxe-runtime";

type BoxeCopy = (key: BoxeCopyKey, placeholders?: Record<string, string>) => string;

export function BoxeBetPanel({
  betAmount,
  balanceAmount,
  walletSource,
  collectAmount,
  canBet,
  canCollect,
  busy,
  insufficientBalance,
  activeRound,
  terminalRound,
  copy,
  onBetAmountChange,
  onBet,
  onCollect,
}: {
  betAmount: string;
  balanceAmount: string;
  walletSource: BoxeWalletSource;
  collectAmount: string;
  canBet: boolean;
  canCollect: boolean;
  busy: boolean;
  insufficientBalance: boolean;
  activeRound: boolean;
  terminalRound: boolean;
  copy: BoxeCopy;
  onBetAmountChange: (value: string) => void;
  onBet: () => void;
  onCollect: () => void;
}) {
  const balanceLabel = walletSource === "demo" ? copy("balance.demo") : copy("balance.label");
  const primaryLabel = activeRound
    ? copy("actions.collect_with_amount", { amount: collectAmount || "0" })
    : copy("actions.bet");
  const primaryDisabled = activeRound ? !canCollect || busy : !canBet || busy;

  return (
    <aside className="boxe-bet-panel" aria-label="BOXE bet panel">
      <label className="boxe-bet-input">
        <span>{copy("settings.bet_amount")}</span>
        <input
          data-testid="boxe-bet-input"
          disabled={activeRound || busy}
          inputMode="decimal"
          onChange={(event) => onBetAmountChange(event.target.value)}
          value={betAmount}
        />
      </label>

      <div className="boxe-balance-strip">
        <span>{balanceLabel}</span>
        <strong>{balanceAmount} CHIP</strong>
        <em>{walletSource.toUpperCase()}</em>
      </div>

      {insufficientBalance ? (
        <p className="boxe-inline-warning">{copy("balance.insufficient")}</p>
      ) : null}

      <button
        className="button boxe-primary-action boxe-wager-action"
        data-testid="boxe-primary-action"
        disabled={primaryDisabled}
        onClick={activeRound ? onCollect : onBet}
        type="button"
      >
        {busy ? "..." : primaryLabel}
      </button>

      {terminalRound ? (
        <p className="boxe-terminal-hint">{copy("actions.reset")}</p>
      ) : null}
    </aside>
  );
}
