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
};

export function MinesBalanceFooter({
  isDemoPlayer,
  visibleBalance,
  potentialPayout,
}: MinesBalanceFooterProps) {
  return (
    <div className="mines-balance-footer">
      <div>
        <span className="list-muted">{isDemoPlayer ? "Demo balance" : "Balance"}</span>
        <strong>{formatWholeChipDisplay(visibleBalance)}</strong>
      </div>
      <div>
        <span className="list-muted">Win</span>
        <strong>
          {potentialPayout !== null
            ? formatWholeChipDisplay(potentialPayout)
            : "0 CHIP"}
        </strong>
      </div>
    </div>
  );
}
