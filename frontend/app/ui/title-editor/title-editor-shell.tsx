"use client";

import type {
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  StatusMessage,
} from "@/app/lib/types";
import type { Dispatch, SetStateAction } from "react";
import { resolveEngineEditor } from "./engine-editor-registry";

type TitleEditorShellProps = {
  titleCode: string;
  engineCode: string;
  displayName: string;
  accessToken: string | null;
  runtimeConfig: MinesRuntimeConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: Dispatch<SetStateAction<MinesRuntimeConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

export function TitleEditorShell({
  titleCode,
  engineCode,
  displayName,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
  adminFairnessCurrent,
}: TitleEditorShellProps) {
  const EngineEditor = resolveEngineEditor(engineCode);

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
          Questo engine non ha ancora un editor backoffice registrato.
        </p>
      </article>
    );
  }

  return (
    <div className="stack" key={`${engineCode}:${titleCode}`}>
      <article className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>{displayName}</h3>
            <p className="mono">{titleCode}</p>
          </div>
          <span className="status-inline info">{engineCode}</span>
        </div>
      </article>

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
