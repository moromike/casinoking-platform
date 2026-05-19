import type { ReactNode } from "react";
import { GameQuickChips } from "./game-quick-chips";

type GameBetPanelProps = {
  label: string;
  inputId: string;
  value: string;
  onValueChange: (value: string) => void;
  disabled: boolean;
  placeholder?: string;
  inputMode?: "numeric" | "decimal";
  inputTestId?: string;
  quickChipAmounts?: string[];
  actions?: ReactNode;
  className?: string;
  fieldClassName?: string;
  quickChipRowClassName?: string;
  quickChipClassName?: string;
  quickChipActiveClassName?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameBetPanel({
  label,
  inputId,
  value,
  onValueChange,
  disabled,
  placeholder,
  inputMode = "numeric",
  inputTestId,
  quickChipAmounts = [],
  actions,
  className,
  fieldClassName,
  quickChipRowClassName,
  quickChipClassName,
  quickChipActiveClassName,
}: GameBetPanelProps) {
  const field = (
    <div className={joinClassNames("field", "game-bet-field", fieldClassName)}>
      <label htmlFor={inputId}>{label}</label>
      <input
        id={inputId}
        data-testid={inputTestId}
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        inputMode={inputMode}
        placeholder={placeholder}
        disabled={disabled}
      />
      {quickChipAmounts.length > 0 ? (
        <GameQuickChips
          amounts={quickChipAmounts}
          selectedAmount={value}
          disabled={disabled}
          onSelectAmount={onValueChange}
          rowClassName={quickChipRowClassName}
          chipClassName={quickChipClassName}
          activeClassName={quickChipActiveClassName}
        />
      ) : null}
    </div>
  );

  if (!actions && !className) {
    return field;
  }

  return (
    <div className={joinClassNames("game-bet-panel", className)}>
      {field}
      {actions}
    </div>
  );
}
