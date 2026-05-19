import { formatWholeChipDisplay } from "@/app/lib/helpers";

type GameBalanceFooterProps = {
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
  className?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameBalanceFooter({
  isDemoPlayer,
  visibleBalance,
  potentialPayout,
  copy,
  balanceLabel: customBalanceLabel,
  walletType,
  className,
}: GameBalanceFooterProps) {
  const balanceLabel =
    customBalanceLabel ??
    (isDemoPlayer
      ? copy.demoBalance
      : walletType
        ? copy.walletBalance(walletType)
        : copy.defaultBalance);

  return (
    <div className={joinClassNames("game-balance-footer", className)}>
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
