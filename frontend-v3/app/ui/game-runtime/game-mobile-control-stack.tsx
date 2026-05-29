import type { ReactNode } from "react";

type GameMobileControlStackProps = {
  balance?: ReactNode;
  betPanel?: ReactNode;
  actions?: ReactNode;
  settingsSummary?: ReactNode;
  children?: ReactNode;
  className?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameMobileControlStack({
  balance,
  betPanel,
  actions,
  settingsSummary,
  children,
  className,
}: GameMobileControlStackProps) {
  return (
    <section className={joinClassNames("game-mobile-control-stack", className)}>
      {balance}
      {betPanel}
      {actions}
      {settingsSummary}
      {children}
    </section>
  );
}
