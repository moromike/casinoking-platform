"use client";

import type {
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  StatusMessage,
} from "@/app/lib/types";
import type { Dispatch, SetStateAction } from "react";
import { MinesBackofficeEditor } from "./mines-backoffice-editor";

export type MinesEngineEditorProps = {
  titleCode: string;
  accessToken: string | null;
  runtimeConfig: MinesRuntimeConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: Dispatch<SetStateAction<MinesRuntimeConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

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
