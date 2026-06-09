export function GameShortViewportGate({
  title = "Rotate device to play",
  description = "This screen is too short for gameplay in landscape.",
  className,
}: {
  title?: string;
  description?: string;
  className?: string;
}) {
  const classes = ["game-short-viewport-gate", className].filter(Boolean).join(" ");

  return (
    <aside className={classes} role="status" aria-live="polite" aria-label={title}>
      <div className="game-short-viewport-gate__panel">
        <span className="game-short-viewport-gate__icon" aria-hidden="true">
          <span />
        </span>
        <span className="game-short-viewport-gate__copy">
          <strong>{title}</strong>
          <span>{description}</span>
        </span>
      </div>
    </aside>
  );
}
