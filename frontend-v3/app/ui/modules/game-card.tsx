"use client";

import { resolvePublicAssetUrl } from "../../lib/api";
import {
  PLAYER_AUTH_EVENT,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
  type PlayerAuthSnapshot,
} from "../../lib/player-auth";
import type { GameLibraryTitle } from "../../lib/types";
import { resolveGameHref, type GameLaunchMode } from "../site-v3-render-helpers";
import { useEffect, useState } from "react";

export function GameCard({ title }: { title: GameLibraryTitle }) {
  const [cashierOpen, setCashierOpen] = useState(false);
  const [authSnapshot, setAuthSnapshot] = useState<PlayerAuthSnapshot>({
    accessToken: "",
    email: "",
  });
  const isAuthenticated = hasPlayerAuthSnapshot(authSnapshot);

  useEffect(() => {
    function refreshSnapshot() {
      setAuthSnapshot(readPlayerAuthSnapshot());
    }

    refreshSnapshot();
    window.addEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
    window.addEventListener("storage", refreshSnapshot);
    return () => {
      window.removeEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
      window.removeEventListener("storage", refreshSnapshot);
    };
  }, []);

  return (
    <>
      <button
        aria-label={`Open launch cashier for ${title.display_name}`}
        className="site-v3-game-card"
        onClick={() => setCashierOpen(true)}
        type="button"
      >
        <GameArtwork title={title} />
        <span className="site-v3-game-card-overlay">
          <small>{title.engine_display_name}</small>
          <strong>{title.display_name}</strong>
        </span>
      </button>
      {cashierOpen ? (
        <LaunchCashier
          isAuthenticated={isAuthenticated}
          title={title}
          onClose={() => setCashierOpen(false)}
        />
      ) : null}
    </>
  );
}

export function GameArtwork({ title }: { title: GameLibraryTitle }) {
  const assetUrl = resolvePublicAssetUrl(title.game_card_asset?.public_url);
  if (assetUrl) {
    return <img alt="" className="site-v3-game-art" src={assetUrl} />;
  }
  return (
    <div className="site-v3-game-art site-v3-game-art-fallback">
      <span>{fallbackGlyph(title)}</span>
      <strong>{title.display_name}</strong>
    </div>
  );
}

function LaunchCashier({
  isAuthenticated,
  onClose,
  title,
}: {
  isAuthenticated: boolean;
  onClose: () => void;
  title: GameLibraryTitle;
}) {
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
        className="site-v3-launch-cashier"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <header className="site-v3-launch-head">
          <div>
            <p className="site-v3-kicker">Launch cashier</p>
            <h2 id="site-v3-launch-title">{title.display_name}</h2>
          </div>
          <button aria-label="Close launch cashier" onClick={onClose} type="button">
            Close
          </button>
        </header>
        <div className="site-v3-launch-options">
          <LaunchOption
            disabled={!title.real_enabled || !isAuthenticated}
            disabledReason={!title.real_enabled ? "Real money is not enabled for this title." : "Log in before using real balance."}
            href={resolveGameHref(title, "real")}
            label="Real money"
            mode="real"
            value="Cash balance"
          />
          <LaunchOption
            disabled={!title.real_enabled || !isAuthenticated}
            disabledReason={!title.real_enabled ? "Bonus is not enabled for this title." : "Log in before using bonus balance."}
            href={resolveGameHref(title, "bonus")}
            label="Bonus"
            mode="bonus"
            value="Bonus balance"
          />
          <LaunchOption
            disabled={!title.demo_enabled}
            href={resolveGameHref(title, "demo")}
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
      <button className="site-v3-launch-option" disabled type="button">
        <span>
          <strong>{label}</strong>
          <small>{disabledReason ?? `${label} is not enabled for this title.`}</small>
        </span>
        <em>-</em>
      </button>
    );
  }

  return (
    <a className={`site-v3-launch-option is-${mode}`} href={href}>
      <span>
        <strong>{label}</strong>
        <small>{value}</small>
      </span>
      <em>{mode === "demo" ? "Play demo" : "Enter game"}</em>
    </a>
  );
}

function fallbackGlyph(title: GameLibraryTitle): string {
  if (title.engine_code === "hi_lo") {
    return "A";
  }
  if (title.engine_code === "boxe") {
    return "BX";
  }
  return "M";
}
