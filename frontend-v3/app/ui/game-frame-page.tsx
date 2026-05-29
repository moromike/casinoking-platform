"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { sanitizeAuthReturnTo, withAuthReturnTo } from "../lib/auth-return";
import type { GameLibraryTitle } from "../lib/types";

type GameFrameConfig = {
  displayName: string;
  engineCode: string;
  gameCode: "mines" | "boxe" | "hi_lo";
  routePath: "mines" | "boxe" | "hi-lo";
  runtimePath?: "/runtime/boxe" | "/runtime/hi-lo";
};

type GameFramePageProps = {
  config: GameFrameConfig;
  searchParams: Record<string, string | string[] | undefined>;
  titles: GameLibraryTitle[];
};

const FORWARDED_GAME_PARAMS = ["mode", "wallet_source", "preview", "preview_token", "return_to"];
const GAME_EMBED_CLOSE_MESSAGE = "casinoking:game-close";
const GAME_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:game-fullscreen-state";

export function GameFramePage({ config, searchParams, titles }: GameFramePageProps) {
  const shellRef = useRef<HTMLElement | null>(null);
  const frameRef = useRef<HTMLIFrameElement | null>(null);
  const [origin, setOrigin] = useState("");
  const [currentHref, setCurrentHref] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const gameTitles = useMemo(
    () => titles.filter((title) => normalizeEngineCode(title.engine_code) === config.engineCode),
    [config.engineCode, titles],
  );
  const defaultTitleCode = useMemo(
    () => resolveInitialTitleCode(gameTitles, readSingleParam(searchParams.title_code)),
    [gameTitles, searchParams.title_code],
  );
  const [selectedTitleCode, setSelectedTitleCode] = useState(defaultTitleCode);
  const selectedTitle = gameTitles.find((title) => title.title_code === selectedTitleCode) ?? gameTitles[0] ?? null;
  const returnTo = sanitizeAuthReturnTo(readSingleParam(searchParams.return_to)) ?? "/";
  const accountHref = withAuthReturnTo("/account", currentHref);
  const frameSrc = useMemo(() => {
    if (!origin || !selectedTitle) {
      return "";
    }
    const params = new URLSearchParams();
    for (const key of FORWARDED_GAME_PARAMS) {
      const value = readSingleParam(searchParams[key]);
      if (value) {
        params.set(key, value);
      }
    }
    params.set("title_code", selectedTitle.title_code);
    if (!params.has("mode")) {
      params.set("mode", "demo");
    }
    if (!params.has("return_to")) {
      params.set("return_to", origin);
    }
    params.set("embed", "1");
    params.set("embed_origin", origin);
    const framePath = config.runtimePath ?? `/legacy-games/${config.routePath}`;
    return `${framePath}?${params.toString()}`;
  }, [config.routePath, config.runtimePath, origin, searchParams, selectedTitle]);

  useEffect(() => {
    setOrigin(window.location.origin);
    setCurrentHref(window.location.href);
  }, []);

  useEffect(() => {
    setSelectedTitleCode(defaultTitleCode);
  }, [defaultTitleCode]);

  useEffect(() => {
    function handleFullscreenChange() {
      const active = document.fullscreenElement === shellRef.current;
      setIsFullscreen(active);
      notifyEmbeddedFullscreenState(active);
    }

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  useEffect(() => {
    function handleEmbedMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) {
        return;
      }
      if (!event.data || typeof event.data !== "object" || !("type" in event.data)) {
        return;
      }
      const data = event.data as { type?: unknown; gameCode?: unknown };
      const legacyCloseMessage = buildLegacyMessageType(config.gameCode, "close");
      const isGenericClose =
        data.type === GAME_EMBED_CLOSE_MESSAGE &&
        (typeof data.gameCode !== "string" || data.gameCode === config.gameCode);
      if (data.type !== legacyCloseMessage && !isGenericClose) {
        return;
      }
      void closeToReturnTarget();
    }

    window.addEventListener("message", handleEmbedMessage);
    return () => window.removeEventListener("message", handleEmbedMessage);
  }, [config.gameCode, returnTo]);

  async function enterFullscreen() {
    if (!shellRef.current || document.fullscreenElement === shellRef.current) {
      return;
    }
    await shellRef.current.requestFullscreen().catch(() => undefined);
  }

  async function closeToReturnTarget() {
    if (document.fullscreenElement) {
      await document.exitFullscreen().catch(() => undefined);
    }
    window.location.assign(returnTo);
  }

  function notifyEmbeddedFullscreenState(active: boolean) {
    const frameWindow = frameRef.current?.contentWindow;
    if (!frameWindow || typeof window === "undefined") {
      return;
    }
    frameWindow.postMessage(
      { type: buildLegacyMessageType(config.gameCode, "fullscreen-state"), active },
      window.location.origin,
    );
    frameWindow.postMessage(
      { type: GAME_EMBED_FULLSCREEN_STATE_MESSAGE, gameCode: config.gameCode, active },
      window.location.origin,
    );
  }

  return (
    <main className="site-v3-game-shell">
      <section
        aria-label={`${config.displayName} game host`}
        className="site-v3-game-host"
        ref={shellRef}
      >
        <header className="site-v3-game-host-topbar">
          <a className="site-v3-game-host-brand" href="/">
            CasinoKing
          </a>
          <div className="site-v3-game-host-title">
            <p className="site-v3-kicker">Game</p>
            <h1>{selectedTitle?.display_name ?? config.displayName}</h1>
          </div>
          <div className="site-v3-game-host-actions">
            {gameTitles.length > 1 ? (
              <label className="site-v3-game-host-select">
                <span>Title</span>
                <select
                  value={selectedTitleCode}
                  onChange={(event) => setSelectedTitleCode(event.target.value)}
                >
                  {gameTitles.map((title) => (
                    <option key={title.title_code} value={title.title_code}>
                      {title.display_name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <a className="site-v3-game-host-link" href={accountHref}>
              Account
            </a>
            {!isFullscreen ? (
              <button className="site-v3-game-host-link" type="button" onClick={() => void enterFullscreen()}>
                Fullscreen
              </button>
            ) : null}
            <button className="site-v3-game-host-link" type="button" onClick={() => void closeToReturnTarget()}>
              Close
            </button>
          </div>
        </header>

        <div className="site-v3-game-frame-wrap">
          {frameSrc ? (
            <iframe
              allow="fullscreen"
              className="site-v3-game-frame"
              ref={frameRef}
              src={frameSrc}
              title={`${config.displayName} embedded runtime`}
              onLoad={() => notifyEmbeddedFullscreenState(isFullscreen)}
            />
          ) : (
            <div className="site-v3-game-unavailable">
              <h2>{config.displayName}</h2>
              <p>No published title is available for this game.</p>
              <a className="site-v3-button" href="/">
                Lobby
              </a>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function readSingleParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }
  return value ?? null;
}

function resolveInitialTitleCode(titles: GameLibraryTitle[], requestedTitleCode: string | null): string {
  if (requestedTitleCode && titles.some((title) => title.title_code === requestedTitleCode)) {
    return requestedTitleCode;
  }
  return titles[0]?.title_code ?? "";
}

function normalizeEngineCode(engineCode: string): string {
  return engineCode === "hi-lo" ? "hi_lo" : engineCode;
}

function buildLegacyMessageType(gameCode: string, kind: "close" | "fullscreen-state"): string {
  return `casinoking:${gameCode.replace(/_/g, "-")}-${kind}`;
}
