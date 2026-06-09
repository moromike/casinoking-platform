import type { ReactNode } from "react";

type GameSettingsPanelProps = {
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameSettingsPanel({ children, className, ariaLabel }: GameSettingsPanelProps) {
  return (
    <div className={joinClassNames("game-settings-panel", className)} aria-label={ariaLabel}>
      {children}
    </div>
  );
}
