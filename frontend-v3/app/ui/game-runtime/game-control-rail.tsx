import type { FormEventHandler, ReactNode } from "react";

type GameControlRailProps = {
  headerTools?: ReactNode;
  settings?: ReactNode;
  betPanel?: ReactNode;
  footer?: ReactNode;
  children?: ReactNode;
  className?: string;
  onSubmit?: FormEventHandler<HTMLFormElement>;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameControlRail({
  headerTools,
  settings,
  betPanel,
  footer,
  children,
  className,
  onSubmit,
}: GameControlRailProps) {
  return (
    <form className={joinClassNames("game-control-rail", className)} onSubmit={onSubmit}>
      {headerTools}
      {settings}
      {betPanel}
      {children}
      {footer}
    </form>
  );
}
