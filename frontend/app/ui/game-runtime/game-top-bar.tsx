import type { ReactNode } from "react";

type GameTopBarProps = {
  title: string;
  titleId?: string;
  subtitle?: ReactNode;
  leading?: ReactNode;
  trailing?: ReactNode;
  className?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameTopBar({
  title,
  titleId,
  subtitle,
  leading,
  trailing,
  className,
}: GameTopBarProps) {
  return (
    <header className={joinClassNames("game-top-bar", className)}>
      {leading ? <div className="game-top-bar-side">{leading}</div> : null}
      <div className="game-top-bar-heading">
        <h1 id={titleId}>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {trailing ? <div className="game-top-bar-side">{trailing}</div> : null}
    </header>
  );
}
