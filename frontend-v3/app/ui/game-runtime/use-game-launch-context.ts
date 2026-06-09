"use client";

import { useCallback, useEffect, useState } from "react";
import {
  readGameBootRequestFromLocation,
  type GameBootRequest,
} from "./game-boot-request";
import {
  clearLegacyGameStorage,
  readGameStorageSnapshot,
} from "./game-storage";

type GameStorageSnapshot = ReturnType<typeof readGameStorageSnapshot>;

export type GameLaunchContext = {
  request: GameBootRequest;
  storageSnapshot: GameStorageSnapshot;
};

export type GameBootFatalReason = "missing_title" | "runtime";

export type GameBootStatus =
  | { kind: "boot" }
  | ({ kind: "launch_ready" } & GameLaunchContext)
  | ({ kind: "runtime_ready" } & GameLaunchContext)
  | ({ kind: "fatal"; reason: GameBootFatalReason } & Partial<GameLaunchContext>);

type UseGameLaunchContextOptions = {
  storageNamespace: string;
  missingTitleRedirectTo?: string;
};

export function useGameLaunchContext({
  storageNamespace,
  missingTitleRedirectTo,
}: UseGameLaunchContextOptions) {
  const [status, setStatus] = useState<GameBootStatus>({ kind: "boot" });

  useEffect(() => {
    const request = readGameBootRequestFromLocation(window.location);
    if (!request) {
      setStatus({ kind: "fatal", reason: "missing_title" });
      if (missingTitleRedirectTo) {
        window.location.replace(missingTitleRedirectTo);
      }
      return;
    }

    const storageSnapshot = readGameStorageSnapshot(window.localStorage, storageNamespace);
    clearLegacyGameStorage(window.localStorage, storageNamespace);
    setStatus({ kind: "launch_ready", request, storageSnapshot });
  }, [missingTitleRedirectTo, storageNamespace]);

  const markRuntimeReady = useCallback(() => {
    setStatus((currentStatus) => {
      if (currentStatus.kind !== "launch_ready") {
        return currentStatus;
      }
      return {
        kind: "runtime_ready",
        request: currentStatus.request,
        storageSnapshot: currentStatus.storageSnapshot,
      };
    });
  }, []);

  const markFatal = useCallback((reason: GameBootFatalReason) => {
    setStatus((currentStatus) => {
      if (currentStatus.kind === "boot") {
        return { kind: "fatal", reason };
      }
      if (currentStatus.kind === "launch_ready") {
        return {
          kind: "fatal",
          reason,
          request: currentStatus.request,
          storageSnapshot: currentStatus.storageSnapshot,
        };
      }
      return currentStatus;
    });
  }, []);

  return { status, markRuntimeReady, markFatal };
}
