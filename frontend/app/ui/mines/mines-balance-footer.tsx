/**
 * MinesBalanceFooter — Balance and win display for Mines.
 *
 * Extracted from mines-standalone.tsx (P1-WP5).
 * Follows the stateless props pattern established by mines-board.tsx.
 */

import { formatWholeChipDisplay } from "@/app/lib/helpers";

type MinesBalanceFooterProps = {
  isDemoPlayer: boolean;
  visibleBalance: string;
  potentialPayout: string | null;
  copy: {
    demoBalance: string;
    defaultBalance: string;
    walletBalance: (walletType: "cash" | "bonus") => string;
    win: string;
    zeroChips: string;
    chipSuffix: string;
  };
  balanceLabel?: string;
  walletType?: "cash" | "bonus";
};

export function MinesBalanceFooter({
  isDemoPlayer,
  visibleBalance,
  potentialPayout,
  copy,
  balanceLabel: customBalanceLabel,
  walletType,
}: MinesBalanceFooterProps) {
  const balanceLabel = customBalanceLabel ?? (isDemoPlayer
    ? copy.demoBalance
    : walletType
      ? copy.walletBalance(walletType)
      : copy.defaultBalance);

  return (
    <div className="mines-balance-footer">
      <div>
        <span className="list-muted">{balanceLabel}</span>
        <strong>{formatWholeChipDisplay(visibleBalance, copy.chipSuffix)}</strong>
      </div>
      <div>
        <span className="list-muted">{copy.win}</span>
        <strong>
          {potentialPayout !== null
            ? formatWholeChipDisplay(potentialPayout, copy.chipSuffix)
            : copy.zeroChips}
        </strong>
      </div>
    </div>
  );
}
