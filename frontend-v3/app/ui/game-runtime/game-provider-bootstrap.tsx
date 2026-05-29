"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export const PROVIDER_INTRO_BASE = "/brand/moromike-lab";

const DEFAULT_PROVIDER_INTRO_VIDEO_SRC = `${PROVIDER_INTRO_BASE}/moromike-lab-intro.v1.ca8edf14.mp4`;
const DEFAULT_PROVIDER_INTRO_POSTER_SRC = `${PROVIDER_INTRO_BASE}/moromike-lab-poster.v1.46bc88d9.png`;
const DEFAULT_PROVIDER_INTRO_MIN_DURATION_MS = 8_000;

type GameProviderBootstrapProps = {
  ready: boolean;
  skipLabel?: string;
  onComplete: () => void;
  minDurationMs?: number;
  posterSrc?: string;
  videoSrc?: string;
};

export function GameProviderBootstrap({
  ready,
  skipLabel = "Salta",
  onComplete,
  minDurationMs = DEFAULT_PROVIDER_INTRO_MIN_DURATION_MS,
  posterSrc = DEFAULT_PROVIDER_INTRO_POSTER_SRC,
  videoSrc = DEFAULT_PROVIDER_INTRO_VIDEO_SRC,
}: GameProviderBootstrapProps) {
  const [progress, setProgress] = useState(0);
  const [videoFailed, setVideoFailed] = useState(false);
  const [isMediaReady, setIsMediaReady] = useState(false);
  const startAtRef = useRef<number | null>(null);
  const completedRef = useRef(false);
  const canSkip = ready && isMediaReady;

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setIsMediaReady(true);
    }
  }, []);

  const complete = useCallback(() => {
    if (completedRef.current) {
      return;
    }
    completedRef.current = true;
    setProgress(100);
    onComplete();
  }, [onComplete]);

  useEffect(() => {
    let animationFrame = 0;

    const tick = (now: number) => {
      if (!isMediaReady) {
        setProgress(0);
        animationFrame = window.requestAnimationFrame(tick);
        return;
      }

      if (startAtRef.current === null) {
        startAtRef.current = now;
      }

      const elapsedMs = now - startAtRef.current;
      const elapsedRatio = Math.min(elapsedMs / minDurationMs, 1);
      const nextProgress = ready ? elapsedRatio * 100 : Math.min(elapsedRatio * 85, 85);

      setProgress(nextProgress);

      if (ready && elapsedMs >= minDurationMs) {
        complete();
        return;
      }

      animationFrame = window.requestAnimationFrame(tick);
    };

    animationFrame = window.requestAnimationFrame(tick);

    return () => {
      window.cancelAnimationFrame(animationFrame);
    };
  }, [complete, isMediaReady, minDurationMs, ready]);

  return (
    <div
      className="game-provider-bootstrap"
      role="dialog"
      aria-modal="true"
      aria-busy="true"
      aria-label="moromike lab"
    >
      <img
        className="game-provider-bootstrap-poster"
        src={posterSrc}
        alt=""
        aria-hidden="true"
      />
      {videoFailed ? null : (
        <video
          className="game-provider-bootstrap-video"
          src={videoSrc}
          poster={posterSrc}
          muted
          playsInline
          autoPlay
          preload="auto"
          aria-hidden="true"
          onError={() => {
            setVideoFailed(true);
            setIsMediaReady(true);
          }}
          onLoadedData={() => setIsMediaReady(true)}
        />
      )}
      <div className="game-provider-bootstrap-progress" aria-hidden="true">
        <span style={{ transform: `scaleX(${Math.max(0, Math.min(progress, 100)) / 100})` }} />
      </div>
      {canSkip ? (
        <button
          className="game-provider-bootstrap-skip"
          type="button"
          onClick={complete}
        >
          {skipLabel}
        </button>
      ) : null}
    </div>
  );
}

export function GameProviderBootstrapPreload({
  posterSrc = DEFAULT_PROVIDER_INTRO_POSTER_SRC,
  videoSrc = DEFAULT_PROVIDER_INTRO_VIDEO_SRC,
}: {
  posterSrc?: string;
  videoSrc?: string;
}) {
  useEffect(() => {
    const poster = new Image();
    poster.src = posterSrc;

    const video = document.createElement("video");
    video.preload = "auto";
    video.muted = true;
    video.playsInline = true;
    video.src = videoSrc;
    video.load();

    return () => {
      video.removeAttribute("src");
      video.load();
    };
  }, [posterSrc, videoSrc]);

  return null;
}
