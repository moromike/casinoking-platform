"use client";

import type { MinesRuntimeConfig } from "@/app/lib/types";
import type { EngineEditorProps } from "@/app/ui/title-editor/engine-editor-registry";
import { MinesBackofficeEditor } from "./mines-backoffice-editor";

export type MinesEngineEditorProps = EngineEditorProps<MinesRuntimeConfig>;

export function MinesEngineEditor({
  titleCode,
  accessToken,
  runtimeConfig,
  busyAction,
  setBusyAction,
  setStatus,
  setRuntimeConfig,
  adminFairnessCurrent,
}: MinesEngineEditorProps) {
  return (
    <MinesBackofficeEditor
      titleCode={titleCode}
      accessToken={accessToken}
      runtimeConfig={runtimeConfig}
      busyAction={busyAction}
      setBusyAction={setBusyAction}
      setStatus={setStatus}
      setRuntimeConfig={setRuntimeConfig}
      adminFairnessCurrent={adminFairnessCurrent}
    />
  );
}
