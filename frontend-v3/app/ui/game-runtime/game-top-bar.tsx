"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";

type GameTopBarProps = {
  title: string;
  titleId?: string;
  subtitle?: ReactNode;
  leading?: ReactNode;
  trailing?: ReactNode;
  className?: string;
};

type GameRuntimeToolsProps = {
  locale?: string;
  clockLabel?: string;
  clockTimeZone?: string;
  audio: {
    muted: boolean;
    volume: number;
    hasAnySound?: boolean;
    setMuted: (value: boolean) => void;
    setVolume: (value: number) => void;
  };
  copy: {
    effectsAria: string;
    effectsLabel: string;
    effectsOn: string;
    effectsOff: string;
    volume: string;
  };
  className?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameTopBar({
  title,
  titleId,
  subtitle,
  leading,
  trailing,
  className,
}: GameTopBarProps) {
  const hasSideSlots = Boolean(leading || trailing);

  return (
    <header className={joinClassNames("game-top-bar", className)}>
      {hasSideSlots ? <div className="game-top-bar-side">{leading}</div> : null}
      <div className="game-top-bar-heading">
        <h1 id={titleId}>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {hasSideSlots ? <div className="game-top-bar-side">{trailing}</div> : null}
    </header>
  );
}

export function GameRuntimeTools({
  locale = "it",
  clockLabel = "Rome",
  clockTimeZone = "Europe/Rome",
  audio,
  copy,
  className,
}: GameRuntimeToolsProps) {
  const [clockValue, setClockValue] = useState(() =>
    formatRuntimeClock({ locale, timeZone: clockTimeZone }),
  );
  const [isAudioOpen, setIsAudioOpen] = useState(false);

  useEffect(() => {
    function syncClock() {
      setClockValue(formatRuntimeClock({ locale, timeZone: clockTimeZone }));
    }

    syncClock();
    const now = new Date();
    const delayToNextMinute =
      (60 - now.getSeconds()) * 1000 - now.getMilliseconds();
    let runtimeClockIntervalId: number | null = null;
    const timeoutId = window.setTimeout(() => {
      syncClock();
      runtimeClockIntervalId = window.setInterval(syncClock, 60_000);
    }, delayToNextMinute);

    return () => {
      window.clearTimeout(timeoutId);
      if (runtimeClockIntervalId !== null) {
        window.clearInterval(runtimeClockIntervalId);
      }
    };
  }, [clockTimeZone, locale]);

  const volumePercent = useMemo(
    () => Math.round(audio.volume * 100),
    [audio.volume],
  );

  return (
    <div className={joinClassNames("game-runtime-tools", className)}>
      <span className="game-runtime-clock" aria-label={`${clockLabel} ${clockValue}`}>
        <span>{clockLabel}</span>
        <strong>{clockValue}</strong>
      </span>
      <div className="game-audio-control">
        <button
          className={joinClassNames(
            "button-ghost",
            "game-icon-button",
            "game-audio-trigger",
            audio.muted ? "is-muted" : null,
          )}
          type="button"
          aria-label={copy.effectsAria}
          aria-expanded={isAudioOpen}
          onClick={() => setIsAudioOpen((current) => !current)}
        >
          <SpeakerIcon muted={audio.muted} />
        </button>
        {isAudioOpen ? (
          <div className="game-audio-popover" role="dialog" aria-label={copy.effectsAria}>
            <div className="game-audio-popover-row">
              <span>{copy.effectsLabel}</span>
              <button
                className={joinClassNames(
                  "game-audio-toggle",
                  audio.muted ? "is-muted" : null,
                )}
                type="button"
                aria-pressed={!audio.muted}
                onClick={() => audio.setMuted(!audio.muted)}
              >
                {audio.muted ? copy.effectsOff : copy.effectsOn}
              </button>
            </div>
            <label className="game-audio-volume">
              <span>
                {copy.volume} {volumePercent}
              </span>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={volumePercent}
                onChange={(event) => audio.setVolume(Number(event.target.value) / 100)}
              />
            </label>
            {!audio.hasAnySound ? (
              <span className="game-audio-empty" aria-hidden="true">-</span>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SpeakerIcon({ muted }: { muted: boolean }) {
  return (
    <svg
      className="game-audio-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M4 9.5h3.5L13 5v14l-5.5-4.5H4v-5Z" />
      <path d="M16 8.2a5.1 5.1 0 0 1 0 7.6" />
      <path d="M18.3 5.9a8.4 8.4 0 0 1 0 12.2" />
      {muted ? <path d="m17 10 4 4m0-4-4 4" /> : null}
    </svg>
  );
}

function formatRuntimeClock({
  locale,
  timeZone,
}: {
  locale: string;
  timeZone: string;
}) {
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone,
    }).format(new Date());
  } catch {
    return new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date());
  }
}
