"use client";

import { useEffect, useMemo, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasStoredPlayerAccessToken,
} from "@/app/lib/auth-storage";
import { API_BASE_URL, ApiRequestError, apiRequest } from "@/app/lib/api";
import { Button } from "@/app/ui/components/button";

type GameLibraryTitle = {
  title_code: string;
  engine_code: string;
  engine_display_name: string;
  display_name: string;
  catalog_display_name: string;
  description: string | null;
  demo_enabled: boolean;
  real_enabled: boolean;
  featured: boolean;
  position: number;
};

type GameLibraryResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: GameLibraryTitle[];
};

type SiteHomeTargetType = "none" | "title_demo" | "title_real";

type SiteHomeSlot = {
  id: string;
  site_code: string;
  slot_key: string;
  title: string;
  subtitle: string | null;
  cta_label: string | null;
  cta_target_type: SiteHomeTargetType;
  cta_target_ref: string | null;
  media_asset_id: string | null;
  media_asset: SiteHomeAsset | null;
  sort_order: number;
};

type SiteHomeAsset = {
  id: string;
  site_code: string;
  asset_kind: "homepage_banner";
  public_url: string;
  mime: string;
  byte_size: number;
  checksum_sha256: string;
  created_at: string;
  status: "active" | "deleted";
};

type SiteHomeResponse = {
  site: GameLibraryResponse["site"] & {
    created_at?: string;
    updated_at?: string;
  };
  slots: SiteHomeSlot[];
};

type LibraryStatus = "loading" | "idle" | "error";

const LOBBY_CARD_DESCRIPTION_MAX_LENGTH = 92;
const FALLBACK_GAME_DESCRIPTION = "A published CasinoKing game variant.";

export function PlayerLobbyPage() {
  const [hasAccessToken, setHasAccessToken] = useState(false);
  const [gameLibrary, setGameLibrary] = useState<GameLibraryTitle[]>([]);
  const [homeSlots, setHomeSlots] = useState<SiteHomeSlot[]>([]);
  const [libraryStatus, setLibraryStatus] = useState<LibraryStatus>("loading");

  useEffect(() => {
    function syncAuthState() {
      setHasAccessToken(hasStoredPlayerAccessToken());
    }

    syncAuthState();
    window.addEventListener("storage", syncAuthState);
    window.addEventListener(PLAYER_AUTH_EVENT, syncAuthState);

    return () => {
      window.removeEventListener("storage", syncAuthState);
      window.removeEventListener(PLAYER_AUTH_EVENT, syncAuthState);
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    setLibraryStatus("loading");

    apiRequest<GameLibraryResponse>("/games/library")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setGameLibrary(data.titles);
        setLibraryStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setLibraryStatus("error");
        if (error instanceof ApiRequestError) {
          setGameLibrary([]);
        }
      });

    apiRequest<SiteHomeResponse>("/site/home?site_code=casinoking")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setHomeSlots(data.slots);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setHomeSlots([]);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const librarySummary = useMemo(() => {
    const demoCount = gameLibrary.filter((game) => game.demo_enabled).length;
    const realCount = gameLibrary.filter((game) => game.real_enabled).length;
    return {
      demoCount,
      realCount,
      visibleCount: gameLibrary.length,
    };
  }, [gameLibrary]);
  const highlightedGame = useMemo(
    () => gameLibrary.find((game) => game.featured) ?? gameLibrary[0] ?? null,
    [gameLibrary],
  );
  const homepageSlot = homeSlots[0] ?? null;

  return (
    <main className="player-lobby">
      <section className="player-lobby-head">
        <div className="player-lobby-head-copy">
          {homepageSlot ? (
            <LobbyHomeSlotHero slot={homepageSlot} hasAccessToken={hasAccessToken} />
          ) : (
            <>
              <p className="eyebrow">CasinoKing Lobby</p>
              <h1>Choose your game</h1>
              <p>Play the current CasinoKing titles in demo or real mode.</p>
            </>
          )}
        </div>
        <div className="player-lobby-head-side">
          <div className="player-lobby-stats" aria-label="Catalog summary">
            <StatBlock label="Games" value={librarySummary.visibleCount} />
            <StatBlock label="Demo" value={librarySummary.demoCount} />
            <StatBlock label="Real" value={librarySummary.realCount} />
          </div>
          {highlightedGame ? <LobbySpotlight game={highlightedGame} /> : null}
        </div>
      </section>

      <section className="player-lobby-games" aria-labelledby="player-lobby-games-title">
        <div className="player-lobby-section-head">
          <div>
            <p className="eyebrow">Games</p>
            <h2 id="player-lobby-games-title">Available now</h2>
          </div>
          <span className="player-lobby-status-pill">{formatCatalogStatus(libraryStatus)}</span>
        </div>

        {libraryStatus === "loading" ? <LobbyLoadingState /> : null}

        {libraryStatus === "idle" && gameLibrary.length > 0 ? (
          <div className="player-lobby-grid">
            {gameLibrary.map((game) => (
              <PlayerGameCard
                game={game}
                hasAccessToken={hasAccessToken}
                key={game.title_code}
              />
            ))}
          </div>
        ) : null}

        {libraryStatus === "idle" && gameLibrary.length === 0 ? (
          <LobbyMessageState
            eyebrow="Catalog"
            title="No published games"
            body="Visible game variants will appear here after Site/Lobby publishing."
          />
        ) : null}

        {libraryStatus === "error" ? (
          <LobbyMessageState
            eyebrow="Catalog"
            title="Catalog unavailable"
            body="Try again in a moment."
          />
        ) : null}
      </section>
    </main>
  );
}

function LobbyHomeSlotHero({
  slot,
  hasAccessToken,
}: {
  slot: SiteHomeSlot;
  hasAccessToken: boolean;
}) {
  const ctaHref = resolveHomeSlotHref(slot, hasAccessToken);
  const ctaLabel = slot.cta_label?.trim() || null;
  const mediaUrl = slot.media_asset ? resolveSiteAssetUrl(slot.media_asset.public_url) : null;

  return (
    <div
      className={`player-lobby-home-slot ${mediaUrl ? "has-media" : ""}`}
      style={
        mediaUrl
          ? {
              backgroundImage: `linear-gradient(90deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.58), rgba(15, 23, 42, 0.2)), url("${mediaUrl}")`,
            }
          : undefined
      }
    >
      <div className="player-lobby-home-slot-copy">
        <p className="eyebrow">CasinoKing Lobby</p>
        <h1>{slot.title}</h1>
        {slot.subtitle ? <p className="player-lobby-home-slot-subtitle">{slot.subtitle}</p> : null}
        {ctaHref && ctaLabel ? (
          <div className="player-lobby-home-slot-actions">
            <Button href={ctaHref}>{ctaLabel}</Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function PlayerGameCard({
  game,
  hasAccessToken,
}: {
  game: GameLibraryTitle;
  hasAccessToken: boolean;
}) {
  const encodedTitleCode = encodeURIComponent(game.title_code);
  const demoHref = `/mines?title_code=${encodedTitleCode}&mode=demo`;
  const realHref = hasAccessToken ? `/mines?title_code=${encodedTitleCode}` : "/login";

  return (
    <article className={`player-lobby-card ${game.featured ? "is-featured" : ""}`}>
      <div className="player-lobby-card-art" aria-hidden="true">
        <div className="player-lobby-art-copy">
          <span>{game.engine_display_name}</span>
          <strong>{game.display_name}</strong>
        </div>
        <div className="player-lobby-board">
          {Array.from({ length: 9 }, (_, index) => (
            <span className={index === 4 ? "is-gem" : ""} key={index} />
          ))}
        </div>
      </div>

      <div className="player-lobby-card-body">
        <div className="player-lobby-card-heading">
          <div>
            <p className="eyebrow">{game.engine_display_name}</p>
            <h3>{game.display_name}</h3>
          </div>
          <ModePills game={game} />
        </div>

        <p className="player-lobby-card-description">
          {formatLobbyCardDescription(game.description)}
        </p>

        <div className="player-lobby-card-meta">
          <span>{game.title_code}</span>
          {game.featured ? <strong>Featured</strong> : null}
        </div>

        <div className="player-lobby-card-actions">
          {game.demo_enabled ? <Button href={demoHref}>Demo</Button> : null}
          {game.real_enabled ? (
            <Button href={realHref} variant={game.demo_enabled ? "secondary" : "primary"}>
              {hasAccessToken ? "Play real" : "Log in to play"}
            </Button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function resolveHomeSlotHref(slot: SiteHomeSlot, hasAccessToken: boolean): string | null {
  if (!slot.cta_target_ref) {
    return null;
  }
  const encodedTitleCode = encodeURIComponent(slot.cta_target_ref);
  if (slot.cta_target_type === "title_demo") {
    return `/mines?title_code=${encodedTitleCode}&mode=demo`;
  }
  if (slot.cta_target_type === "title_real") {
    return hasAccessToken ? `/mines?title_code=${encodedTitleCode}` : "/login";
  }
  return null;
}

function resolveSiteAssetUrl(assetUrl: string): string {
  if (!assetUrl.startsWith("/static/sites/")) {
    return assetUrl;
  }
  const apiBase = new URL(API_BASE_URL);
  return `${apiBase.origin}${assetUrl}`;
}

function LobbyLoadingState() {
  return (
    <div className="player-lobby-grid" aria-busy="true" aria-label="Loading games">
      {[0, 1, 2].map((item) => (
        <div className="player-lobby-card player-lobby-card-skeleton" key={item}>
          <div className="player-lobby-card-art" />
          <div className="player-lobby-card-body">
            <span />
            <span />
            <span />
          </div>
        </div>
      ))}
    </div>
  );
}

function LobbySpotlight({ game }: { game: GameLibraryTitle }) {
  return (
    <div className="player-lobby-spotlight" aria-label="Highlighted game">
      <div>
        <span>{game.featured ? "Featured" : "Ready to play"}</span>
        <strong>{game.display_name}</strong>
      </div>
      <ModePills game={game} compact />
    </div>
  );
}

function ModePills({
  game,
  compact = false,
}: {
  game: Pick<GameLibraryTitle, "demo_enabled" | "real_enabled">;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "player-lobby-mode-row is-compact" : "player-lobby-mode-row"}>
      {game.demo_enabled ? <span className="player-lobby-mode">Demo</span> : null}
      {game.real_enabled ? <span className="player-lobby-mode is-real">Real</span> : null}
    </div>
  );
}

function LobbyMessageState({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="player-lobby-empty-state">
      <div className="player-lobby-empty-art" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h3>{title}</h3>
        <p>{body}</p>
      </div>
    </div>
  );
}

function StatBlock({ label, value }: { label: string; value: number }) {
  return (
    <div className="player-lobby-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function formatCatalogStatus(status: LibraryStatus): string {
  if (status === "loading") {
    return "Loading";
  }
  if (status === "error") {
    return "Unavailable";
  }
  return "Live catalog";
}

function formatLobbyCardDescription(description: string | null): string {
  const value = (description?.trim() || FALLBACK_GAME_DESCRIPTION).trim();
  if (value.length <= LOBBY_CARD_DESCRIPTION_MAX_LENGTH) {
    return value;
  }
  return `${value.slice(0, LOBBY_CARD_DESCRIPTION_MAX_LENGTH - 3).trimEnd()}...`;
}
