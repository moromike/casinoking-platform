"use client";

import { useId } from "react";

export type GameActionErrorProps = {
  title: string;
  message: string;
  actionLabel?: string;
  actionTestId?: string;
  code?: string;
  dismissLabel?: string;
  onAction?: () => void;
  onDismiss?: () => void;
  requestId?: string;
  supportId?: string;
  testId?: string;
};

export function GameActionError({
  title,
  message,
  actionLabel,
  actionTestId,
  code,
  dismissLabel = "OK",
  onAction,
  onDismiss,
  requestId,
  supportId,
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
        <GameErrorDiagnosticLine
          code={code}
          requestId={requestId}
          supportId={supportId}
        />
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

export function GameErrorDiagnosticLine({
  code,
  requestId,
  supportId,
}: {
  code?: string;
  requestId?: string;
  supportId?: string;
}) {
  if (!code && !requestId && !supportId) {
    return null;
  }
  const supportValue = supportId ?? requestId;
  return (
    <p className="game-error-diagnostic-line" data-testid="game-error-diagnostic-line">
      {code ? <span>Codice: {code}</span> : null}
      {code && supportValue ? <span aria-hidden="true"> · </span> : null}
      {supportValue ? <span>Supporto: {supportValue}</span> : null}
    </p>
  );
}
