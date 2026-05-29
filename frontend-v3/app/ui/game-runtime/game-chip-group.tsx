type GameChipOption<T extends string | number> = {
  label: string;
  value: T;
  testId?: string;
};

type GameChipGroupProps<T extends string | number> = {
  ariaLabel: string;
  options: Array<GameChipOption<T>>;
  selectedValue: T;
  disabled?: boolean;
  className?: string;
  chipClassName?: string;
  activeClassName?: string;
  onChange: (value: T) => void;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameChipGroup<T extends string | number>({
  ariaLabel,
  options,
  selectedValue,
  disabled = false,
  className,
  chipClassName,
  activeClassName,
  onChange,
}: GameChipGroupProps<T>) {
  return (
    <div className={joinClassNames("game-chip-row", className)} role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const isActive = option.value === selectedValue;
        return (
          <button
            aria-pressed={isActive}
            className={joinClassNames(
              "game-chip",
              chipClassName,
              isActive ? "active" : null,
              isActive ? activeClassName : null,
            )}
            data-testid={option.testId}
            disabled={disabled}
            key={String(option.value)}
            onClick={() => onChange(option.value)}
            type="button"
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
