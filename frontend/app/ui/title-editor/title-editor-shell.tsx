"use client";

import type {
  FairnessCurrentConfig,
  StatusMessage,
} from "@/app/lib/types";
import type { Dispatch, SetStateAction } from "react";
import {
  resolveEngineDiagnostics,
  resolveEngineEditor,
} from "./engine-editor-registry";

type TitleEditorShellProps = {
  titleCode: string;
  engineCode: string;
  displayName: string;
  isReadOnly?: boolean;
  accessToken: string | null;
  runtimeConfig: unknown | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: Dispatch<SetStateAction<unknown | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
  verifySessionId: string;
  setVerifySessionId: (sessionId: string) => void;
  onRefreshFairnessCurrent: () => void | Promise<void>;
  onVerifyFairness: () => void | Promise<void>;
  showSummaryHeader?: boolean;
};

export function TitleEditorShell({
  titleCode,
  engineCode,
  displayName,
  isReadOnly = false,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
  adminFairnessCurrent,
  verifySessionId,
  setVerifySessionId,
  onRefreshFairnessCurrent,
  onVerifyFairness,
  showSummaryHeader = true,
}: TitleEditorShellProps) {
  const EngineEditor = resolveEngineEditor(engineCode);
  const EngineDiagnostics = resolveEngineDiagnostics(engineCode);

  if (!EngineEditor) {
    return (
      <article className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>{displayName}</h3>
            <p className="mono">{titleCode}</p>
          </div>
          <span className="status-inline warning">{engineCode}</span>
        </div>
        <p className="empty-state">
          This engine does not have a registered backoffice editor yet.
        </p>
      </article>
    );
  }

  if (isReadOnly) {
    return (
      <article className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>{displayName}</h3>
            <p className="mono">{titleCode}</p>
          </div>
          <span className="status-inline warning">locked master</span>
        </div>
        <p className="empty-state">
          This is the engine master: it stays as a stable base for creating variants and is not edited from the backoffice.
        </p>
      </article>
    );
  }

  return (
    <div className="stack" key={`${engineCode}:${titleCode}`}>
      {showSummaryHeader ? (
        <article className="admin-card">
          <div className="admin-card-heading">
            <div>
              <h3>{displayName}</h3>
              <p className="mono">{titleCode}</p>
            </div>
            <span className="status-inline info">{engineCode}</span>
          </div>
        </article>
      ) : null}

      {EngineDiagnostics ? (
        <EngineDiagnostics
          titleCode={titleCode}
          accessToken={accessToken}
          busyAction={busyAction}
          setBusyAction={setBusyAction}
          setStatus={setStatus}
          adminFairnessCurrent={adminFairnessCurrent}
          verifySessionId={verifySessionId}
          setVerifySessionId={setVerifySessionId}
          onRefreshFairnessCurrent={onRefreshFairnessCurrent}
          onVerifyFairness={onVerifyFairness}
        />
      ) : null}

      <EngineEditor
        key={`${engineCode}:${titleCode}`}
        titleCode={titleCode}
        accessToken={accessToken}
        runtimeConfig={runtimeConfig}
        busyAction={busyAction}
        setBusyAction={setBusyAction}
        setStatus={setStatus}
        setRuntimeConfig={setRuntimeConfig}
        adminFairnessCurrent={adminFairnessCurrent}
      />
    </div>
  );
}
