type GameQuickChipsProps = {
  amounts: string[];
  selectedAmount: string;
  disabled: boolean;
  onSelectAmount: (amount: string) => void;
  rowClassName?: string;
  chipClassName?: string;
  activeClassName?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameQuickChips({
  amounts,
  selectedAmount,
  disabled,
  onSelectAmount,
  rowClassName,
  chipClassName,
  activeClassName,
}: GameQuickChipsProps) {
  return (
    <div className={joinClassNames("game-quick-chip-row", rowClassName)}>
      {amounts.map((amount) => {
        const isActive = selectedAmount === amount;
        return (
          <button
            key={amount}
            className={joinClassNames(
              "game-quick-chip",
              chipClassName,
              isActive ? "active" : null,
              isActive ? activeClassName : null,
            )}
            type="button"
            disabled={disabled}
            onClick={() => onSelectAmount(amount)}
          >
            {amount}
          </button>
        );
      })}
    </div>
  );
}
