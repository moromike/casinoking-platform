"use client";

import type { BoxeRuntimeConfig } from "@/app/ui/boxe/use-boxe-runtime";
import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";

export type BoxeEngineEditorProps = EngineEditorProps<BoxeRuntimeConfig>;

export function BoxeEngineEditor({
  titleCode,
  runtimeConfig,
}: BoxeEngineEditorProps) {
  return (
    <article className="admin-card" data-testid="boxe-engine-editor-placeholder">
      <div className="admin-card-heading">
        <div>
          <h3>BOXE engine editor - placeholder</h3>
          <p className="mono">{titleCode}</p>
        </div>
        <span className="status-inline info">Fase 4A in arrivo</span>
      </div>
      <p className="empty-state">
        BOXE config, copy and rules editing will be implemented in WP-BOXE-4A.
      </p>
      {runtimeConfig ? (
        <div className="admin-metric-grid">
          <div className="admin-metric-row">
            <span className="list-muted">Rows</span>
            <span className="list-strong">{runtimeConfig.rows_enabled.join(", ")}</span>
          </div>
          <div className="admin-metric-row">
            <span className="list-muted">Difficulty</span>
            <span className="list-strong">{runtimeConfig.difficulty_enabled.join(", ")}</span>
          </div>
        </div>
      ) : null}
    </article>
  );
}
