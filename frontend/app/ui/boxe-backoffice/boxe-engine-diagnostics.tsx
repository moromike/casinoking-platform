"use client";

import type { EngineDiagnosticsProps } from "@/app/ui/title-editor/engine-editor-registry";

export function BoxeEngineDiagnostics({ titleCode }: EngineDiagnosticsProps) {
  return (
    <details className="admin-diagnostic-panel">
      <summary>BOXE diagnostics</summary>
      <div className="admin-diagnostic-content">
        <div className="admin-card-heading">
          <div>
            <h3>Fairness diagnostics</h3>
            <p className="mono">{titleCode}</p>
          </div>
          <span className="status-inline info">read-only v1</span>
        </div>
        <p className="helper">
          BOXE v1 exposes fairness through the server-authoritative round payload,
          replay verification data and the 98% RTP math contract. Mines-style
          live seed rotation and session verify actions are not shared controls
          for BOXE until dedicated BOXE fairness endpoints exist.
        </p>
      </div>
    </details>
  );
}
