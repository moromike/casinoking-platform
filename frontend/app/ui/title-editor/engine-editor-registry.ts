"use client";

import type { ComponentType, Dispatch, SetStateAction } from "react";

import type {
  FairnessCurrentConfig,
  MinesRuntimeConfig,
  StatusMessage,
} from "@/app/lib/types";
import { MinesEngineEditor } from "@/app/ui/mines/mines-engine-editor";

export type EngineEditorProps = {
  titleCode: string;
  accessToken: string | null;
  runtimeConfig: MinesRuntimeConfig | null;
  busyAction: string | null;
  setBusyAction: (action: string | null) => void;
  setStatus: (status: StatusMessage | null) => void;
  setRuntimeConfig: Dispatch<SetStateAction<MinesRuntimeConfig | null>>;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

const ENGINE_EDITOR_REGISTRY: Record<string, ComponentType<EngineEditorProps>> = {
  mines: MinesEngineEditor,
};

export function resolveEngineEditor(engineCode: string) {
  return ENGINE_EDITOR_REGISTRY[engineCode] ?? null;
}
