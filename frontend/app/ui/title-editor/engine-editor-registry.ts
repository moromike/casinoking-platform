"use client";

import dynamic from "next/dynamic";
import type { ComponentType, Dispatch, SetStateAction } from "react";

import type {
  FairnessCurrentConfig,
  StatusMessage,
} from "@/app/lib/types";

export type EngineEditorProps<TConfig = unknown> = {
  titleCode: string;
  accessToken: string | null;
  runtimeConfig: TConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: Dispatch<SetStateAction<TConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

export type EngineDiagnosticsProps = {
  titleCode: string;
  accessToken: string | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  adminFairnessCurrent: FairnessCurrentConfig | null;
  verifySessionId: string;
  setVerifySessionId: (sessionId: string) => void;
  onRefreshFairnessCurrent: () => void | Promise<void>;
  onVerifyFairness: () => void | Promise<void>;
};

export const REGISTERED_ENGINE_EDITORS = {
  mines: dynamic<EngineEditorProps<unknown>>(() =>
    import("@/app/ui/mines/mines-engine-editor").then(
      (module) =>
        module.MinesEngineEditor as unknown as ComponentType<EngineEditorProps<unknown>>,
    ),
  ),
  boxe: dynamic<EngineEditorProps<unknown>>(() =>
    import("@/app/ui/boxe-backoffice/boxe-engine-editor").then(
      (module) =>
        module.BoxeEngineEditor as unknown as ComponentType<EngineEditorProps<unknown>>,
    ),
  ),
} as const;

export const REGISTERED_ENGINE_DIAGNOSTICS = {
  mines: dynamic(() =>
    import("@/app/ui/mines/mines-engine-diagnostics").then(
      (module) => module.MinesEngineDiagnostics,
    ),
  ) as ComponentType<EngineDiagnosticsProps>,
  boxe: dynamic(() =>
    import("@/app/ui/boxe-backoffice/boxe-engine-diagnostics").then(
      (module) => module.BoxeEngineDiagnostics,
    ),
  ) as ComponentType<EngineDiagnosticsProps>,
} as const;

export type RegisteredEngineCode = keyof typeof REGISTERED_ENGINE_EDITORS;

export function isRegisteredEngineCode(engineCode: string): engineCode is RegisteredEngineCode {
  return engineCode in REGISTERED_ENGINE_EDITORS;
}

export function resolveEngineEditor(engineCode: string) {
  if (!isRegisteredEngineCode(engineCode)) {
    return null;
  }
  return REGISTERED_ENGINE_EDITORS[engineCode];
}

export function resolveEngineDiagnostics(engineCode: string) {
  if (!(engineCode in REGISTERED_ENGINE_DIAGNOSTICS)) {
    return null;
  }
  return REGISTERED_ENGINE_DIAGNOSTICS[
    engineCode as keyof typeof REGISTERED_ENGINE_DIAGNOSTICS
  ];
}
