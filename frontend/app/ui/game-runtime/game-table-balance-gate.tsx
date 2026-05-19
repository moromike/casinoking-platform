"use client";

import { useState, type FormEvent, type ReactNode } from "react";

export type GameTableBalanceWalletSource = "cash" | "bonus";

export type GameTableBalanceConfirmParams = {
  tableEntryAmount: string;
  walletSource: GameTableBalanceWalletSource;
};

type GameTableBalanceWalletOption = {
  balanceLabel: string;
  label: string;
  value: GameTableBalanceWalletSource;
};

type GameTableBalanceQuickAmount = {
  label?: string;
  value: string;
};

type GameTableBalanceGateProps = {
  amount: string;
  amountInputId?: string;
  amountLabel: string;
  amountPlaceholder: string;
  availableBalanceLabel: string;
  availableBalanceValue: string;
  busy?: boolean;
  busyLabel: string;
  closeAriaLabel: string;
  confirmLabel: string;
  disabled?: boolean;
  errorDialog?: ReactNode;
  eyebrow: string;
  isReady: boolean;
  lockedWalletSource?: GameTableBalanceWalletSource | null;
  maximumAmount: string;
  maximumAmountLabel: string;
  maximumLabel: string;
  onAmountChange: (value: string) => void;
  onClose: () => void;
  onConfirm: (params: GameTableBalanceConfirmParams) => Promise<void> | void;
  onWalletSourceChange: (walletSource: GameTableBalanceWalletSource) => void;
  preload?: ReactNode;
  quickAmounts: GameTableBalanceQuickAmount[];
  selectedWalletSource: GameTableBalanceWalletSource;
  testId?: string;
  title: string;
  walletGroupAriaLabel: string;
  walletOptions: GameTableBalanceWalletOption[];
};

export function GameTableBalanceGate({
  amount,
  amountInputId = "table-entry-amount",
  amountLabel,
  amountPlaceholder,
  availableBalanceLabel,
  availableBalanceValue,
  busy = false,
  busyLabel,
  closeAriaLabel,
  confirmLabel,
  disabled = false,
  errorDialog = null,
  eyebrow,
  isReady,
  lockedWalletSource = null,
  maximumAmount,
  maximumAmountLabel,
  maximumLabel,
  onAmountChange,
  onClose,
  onConfirm,
  onWalletSourceChange,
  preload = null,
  quickAmounts,
  selectedWalletSource,
  testId,
  title,
  walletGroupAriaLabel,
  walletOptions,
}: GameTableBalanceGateProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isBusy = busy || isSubmitting;
  const numericAmount = parseTableAmount(amount);
  const numericMaximum = parseTableAmount(maximumAmount);
  const isAmountValid = numericAmount > 0 && numericAmount <= numericMaximum;
  const isConfirmDisabled = disabled || isBusy || !isReady || !isAmountValid;
  const lockedWallet = lockedWalletSource
    ? walletOptions.find((option) => option.value === lockedWalletSource)
    : null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isConfirmDisabled) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onConfirm({
        tableEntryAmount: amount,
        walletSource: selectedWalletSource,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel game-table-balance-gate" data-testid={testId}>
      {preload}
      <button
        className="button-ghost game-table-balance-close"
        type="button"
        aria-label={closeAriaLabel}
        onClick={onClose}
      >
        X
      </button>
      {errorDialog}
      <form className="game-table-balance-form" onSubmit={handleSubmit}>
        <div className="game-table-balance-heading">
          <span className="eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
        </div>
        {lockedWallet ? (
          <div className="game-table-balance-source-summary">
            <span>{walletGroupAriaLabel}</span>
            <strong>{lockedWallet.label}</strong>
          </div>
        ) : (
          <div
            className="game-table-balance-wallet-choice"
            role="group"
            aria-label={walletGroupAriaLabel}
          >
            {walletOptions.map((option) => (
              <button
                className={
                  selectedWalletSource === option.value
                    ? "game-table-balance-wallet-choice-button active"
                    : "game-table-balance-wallet-choice-button"
                }
                type="button"
                disabled={disabled || isBusy}
                key={option.value}
                onClick={() => onWalletSourceChange(option.value)}
              >
                <span>{option.label}</span>
                <strong>{option.balanceLabel}</strong>
              </button>
            ))}
          </div>
        )}
        <div className="game-table-balance-metrics">
          <div>
            <span className="list-muted">{availableBalanceLabel}</span>
            <strong>{availableBalanceValue}</strong>
          </div>
          <div>
            <span className="list-muted">{maximumLabel}</span>
            <strong>{maximumAmountLabel}</strong>
          </div>
        </div>
        <div className="field game-table-balance-entry-field">
          <label htmlFor={amountInputId}>{amountLabel}</label>
          <input
            id={amountInputId}
            value={amount}
            onChange={(event) => onAmountChange(event.target.value)}
            inputMode="numeric"
            placeholder={amountPlaceholder}
            disabled={disabled || isBusy}
            autoFocus
          />
        </div>
        {quickAmounts.length > 0 ? (
          <div className="game-table-balance-quick-chip-row">
            {quickAmounts.map((quickAmount) => (
              <button
                key={quickAmount.value}
                className={
                  amount === quickAmount.value
                    ? "game-table-balance-quick-chip active"
                    : "game-table-balance-quick-chip"
                }
                type="button"
                disabled={disabled || isBusy}
                onClick={() => onAmountChange(quickAmount.value)}
              >
                {quickAmount.label ?? quickAmount.value}
              </button>
            ))}
          </div>
        ) : null}
        <button className="button" type="submit" disabled={isConfirmDisabled}>
          {isBusy ? busyLabel : confirmLabel}
        </button>
      </form>
    </section>
  );
}

function parseTableAmount(value: string) {
  const parsed = Number.parseFloat(value || "0");
  return Number.isFinite(parsed) ? parsed : 0;
}
