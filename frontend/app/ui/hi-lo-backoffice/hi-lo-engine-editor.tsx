"use client";

import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";

export function HiLoEngineEditor({
  titleCode,
}: EngineEditorProps) {
  return (
    <article className="admin-card" data-testid="hi-lo-engine-editor">
      <div className="admin-card-heading">
        <div>
          <h3>HI-LO platform enabled</h3>
          <p className="mono">{titleCode}</p>
        </div>
        <span className="status-inline info">H0</span>
      </div>
      <p className="empty-state">
        HI-LO is registered as a platform game. The full backoffice editor lands in the dedicated HI-LO backoffice wave.
      </p>
    </article>
  );
}
