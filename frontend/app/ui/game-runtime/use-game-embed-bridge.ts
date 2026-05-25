"use client";

import { useCallback, useEffect, useState } from "react";

export const GAME_EMBED_CLOSE_MESSAGE = "casinoking:game-close";
export const GAME_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:game-fullscreen-state";

type GameEmbedBridgeOptions = {
  gameCode: string;
  enabled: boolean;
};

type GameEmbedMessageKind = "close" | "fullscreen-state";

export function buildGameEmbedLegacyMessageType(
  gameCode: string,
  kind: GameEmbedMessageKind,
): string {
  return `casinoking:${gameCode.replace(/_/g, "-")}-${kind}`;
}

export function useGameEmbedBridge({ gameCode, enabled }: GameEmbedBridgeOptions) {
  const [hostOrigin, setHostOrigin] = useState<string | null>(null);
  const [isHostFullscreen, setIsHostFullscreen] = useState(false);

  useEffect(() => {
    setHostOrigin(readEmbedHostOrigin());
  }, []);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") {
      return;
    }

    function handleHostMessage(event: MessageEvent) {
      const acceptedOrigin = hostOrigin ?? readEmbedHostOrigin() ?? window.location.origin;
      if (event.origin !== acceptedOrigin) {
        return;
      }
      if (!event.data || typeof event.data !== "object" || !("type" in event.data)) {
        return;
      }

      const data = event.data as { type?: unknown; gameCode?: unknown; active?: unknown };
      const legacyFullscreenMessage = buildGameEmbedLegacyMessageType(
        gameCode,
        "fullscreen-state",
      );
      const isGenericFullscreenMessage =
        data.type === GAME_EMBED_FULLSCREEN_STATE_MESSAGE &&
        (typeof data.gameCode !== "string" || data.gameCode === gameCode);

      if (data.type !== legacyFullscreenMessage && !isGenericFullscreenMessage) {
        return;
      }

      setIsHostFullscreen(Boolean(data.active));
    }

    window.addEventListener("message", handleHostMessage);
    return () => {
      window.removeEventListener("message", handleHostMessage);
    };
  }, [enabled, gameCode, hostOrigin]);

  const requestClose = useCallback(() => {
    if (
      !enabled ||
      typeof window === "undefined" ||
      window.parent === window
    ) {
      return false;
    }

    const targetOrigin = hostOrigin ?? readEmbedHostOrigin() ?? window.location.origin;
    window.parent.postMessage(
      { type: GAME_EMBED_CLOSE_MESSAGE, gameCode },
      targetOrigin,
    );
    window.parent.postMessage(
      { type: buildGameEmbedLegacyMessageType(gameCode, "close") },
      targetOrigin,
    );
    return true;
  }, [enabled, gameCode, hostOrigin]);

  return { isHostFullscreen, requestClose };
}

function readEmbedHostOrigin(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawOrigin = new URLSearchParams(window.location.search).get("embed_origin");
  if (!rawOrigin) {
    return null;
  }

  try {
    const origin = new URL(rawOrigin).origin;
    if (origin === "null") {
      return null;
    }
    return origin;
  } catch {
    return null;
  }
}
