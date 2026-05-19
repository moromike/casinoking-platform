"use client";

import type { TitleEditorStatusModel } from "./types";

type TitleEditorStatusBannerProps = {
  status: TitleEditorStatusModel;
};

export function TitleEditorStatusBanner({ status }: TitleEditorStatusBannerProps) {
  return (
    <article
      className={`admin-card admin-status-banner ${status.toneClass}`}
      aria-live="polite"
      aria-busy={status.isBusy || undefined}
      data-testid={status.testId}
    >
      <span className="admin-status-banner-indicator" aria-hidden="true" />
      <div className="admin-status-banner-copy">
        <span className="meta-pill">{status.eyebrow ?? "Editor status"}</span>
        <h3>Editor Status: {status.label}</h3>
        {status.description ? <p className="helper">{status.description}</p> : null}
      </div>
    </article>
  );
}
