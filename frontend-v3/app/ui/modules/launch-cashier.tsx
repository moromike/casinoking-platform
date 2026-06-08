"use client";

import { useEffect, useState } from "react";
import {
  PLAYER_AUTH_EVENT,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
  type PlayerAuthSnapshot,
} from "../../lib/player-auth";
import type { GameLibraryTitle } from "../../lib/types";
import { resolveGameHref, SITE_V3_BASE_URL, type GameLaunchMode } from "../site-v3-render-helpers";

export function LaunchCashier({
  onClose,
  title,
}: {
  onClose: () => void;
  title: GameLibraryTitle;
}) {
  const [authSnapshot, setAuthSnapshot] = useState<PlayerAuthSnapshot>({
    accessToken: "",
    email: "",
  });
  const [returnTo, setReturnTo] = useState(SITE_V3_BASE_URL);
  const isAuthenticated = hasPlayerAuthSnapshot(authSnapshot);

  useEffect(() => {
    function refreshSnapshot() {
      setAuthSnapshot(readPlayerAuthSnapshot());
    }

    refreshSnapshot();
    setReturnTo(window.location.href);
    window.addEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
    window.addEventListener("storage", refreshSnapshot);
    return () => {
      window.removeEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
      window.removeEventListener("storage", refreshSnapshot);
    };
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="site-v3-launch-overlay" onMouseDown={onClose} role="presentation">
      <section
        aria-labelledby="site-v3-launch-title"
        aria-modal="true"
        className="site-v3-launch-cashier player-lobby-cashier"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <header className="site-v3-launch-head">
          <div>
            <p className="site-v3-kicker">Launch cashier</p>
            <h2 id="site-v3-launch-title">{title.display_name}</h2>
          </div>
          <button aria-label="Close launch cashier" className="button-ghost" onClick={onClose} type="button">
            Close
          </button>
        </header>
        <div className="site-v3-launch-options">
          <LaunchOption
            disabled={!title.real_enabled || !isAuthenticated}
            disabledReason={
              !title.real_enabled
                ? "Real money is not enabled for this title."
                : "Log in before using real balance."
            }
            href={resolveGameHref(title, "real", returnTo)}
            label="Real money"
            mode="real"
            value="Cash balance"
          />
          <LaunchOption
            disabled={!title.real_enabled || !isAuthenticated}
            disabledReason={
              !title.real_enabled
                ? "Bonus is not enabled for this title."
                : "Log in before using bonus balance."
            }
            href={resolveGameHref(title, "bonus", returnTo)}
            label="Bonus"
            mode="bonus"
            value="Bonus balance"
          />
          <LaunchOption
            disabled={!title.demo_enabled}
            href={resolveGameHref(title, "demo", returnTo)}
            label="Demo"
            mode="demo"
            value="100.00 CHIP"
          />
        </div>
      </section>
    </div>
  );
}

function LaunchOption({
  disabled,
  disabledReason,
  href,
  label,
  mode,
  value,
}: {
  disabled: boolean;
  disabledReason?: string;
  href: string;
  label: string;
  mode: GameLaunchMode;
  value: string;
}) {
  if (disabled) {
    return (
      <button className="site-v3-launch-option player-lobby-cashier-option" disabled type="button">
        <span>
          <strong>{label}</strong>
          <small>{disabledReason ?? `${label} is not enabled for this title.`}</small>
        </span>
        <em>-</em>
      </button>
    );
  }

  return (
    <a className={`site-v3-launch-option player-lobby-cashier-option is-${mode}`} href={href}>
      <span>
        <strong>{label}</strong>
        <small>{value}</small>
      </span>
      <em>{mode === "demo" ? "Play demo" : "Enter game"}</em>
    </a>
  );
}
