"use client";

import type { EngineDiagnosticsProps } from "@/app/ui/title-editor/engine-editor-registry";

export function MinesEngineDiagnostics({
  accessToken,
  busyAction,
  verifySessionId,
  setVerifySessionId,
  onRefreshFairnessCurrent,
  onVerifyFairness,
}: EngineDiagnosticsProps) {
  return (
    <details className="admin-diagnostic-panel">
      <summary>Fairness diagnostics</summary>
      <div className="admin-diagnostic-content">
        <div className="field">
          <label htmlFor="verify-session-id">Session to verify</label>
          <input
            id="verify-session-id"
            value={verifySessionId}
            onChange={(event) => setVerifySessionId(event.target.value)}
            placeholder="Paste the game session id for fairness verification"
          />
        </div>
        <div className="actions">
          <button
            className="button-secondary"
            type="button"
            disabled={busyAction !== null}
            onClick={() => void onRefreshFairnessCurrent()}
          >
            {busyAction === "admin-fairness-current" ? "Loading live state..." : "Fairness live"}
          </button>
          <button
            className="button-ghost"
            type="button"
            disabled={!accessToken || busyAction !== null}
            onClick={() => void onVerifyFairness()}
          >
            {busyAction === "admin-fairness-verify" ? "Verifying..." : "Verify session"}
          </button>
        </div>
      </div>
    </details>
  );
}
