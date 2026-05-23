"use client";

import { useId } from "react";

export type GameActionErrorProps = {
  title: string;
  message: string;
  actionLabel?: string;
  actionTestId?: string;
  dismissLabel?: string;
  onAction?: () => void;
  onDismiss?: () => void;
  testId?: string;
};

export function GameActionError({
  title,
  message,
  actionLabel,
  actionTestId,
  dismissLabel = "OK",
  onAction,
  onDismiss,
  testId = "game-action-error",
}: GameActionErrorProps) {
  const titleId = useId();
  const messageId = useId();
  const primaryHandler = onAction ?? onDismiss;
  const primaryLabel = actionLabel ?? "OK";

  return (
    <div
      className="game-action-error-overlay"
      data-testid={testId}
      role="presentation"
    >
      <article
        aria-describedby={messageId}
        aria-labelledby={titleId}
        aria-modal="true"
        className="game-action-error-dialog"
        role="alertdialog"
      >
        <h2 id={titleId}>{title}</h2>
        <p id={messageId}>{message}</p>
        {primaryHandler ? (
          <button
            className="button"
            data-testid={actionTestId}
            type="button"
            onClick={primaryHandler}
          >
            {primaryLabel}
          </button>
        ) : null}
        {onAction && onDismiss ? (
          <button className="button-secondary" type="button" onClick={onDismiss}>
            {dismissLabel}
          </button>
        ) : null}
      </article>
    </div>
  );
}
