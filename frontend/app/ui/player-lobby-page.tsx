"use client";

import { useEffect, useMemo, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasStoredPlayerAccessToken,
  readStoredString,
} from "@/app/lib/auth-storage";
import { API_BASE_URL, ApiRequestError, apiRequest, resolveBackendAssetUrl } from "@/app/lib/api";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";
import type { MinesPresentationConfig, MinesRuntimeConfig, Wallet } from "@/app/lib/types";
import { Button } from "@/app/ui/components/button";
import { createMinesCopyResolver } from "@/app/ui/mines/i18n/mines-copy-resolver";

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
  game_card_asset: GameCardAsset | null;
};

type GameCardAsset = {
  id: string;
  asset_kind: "game_card";
  public_url: string;
  mime: string;
  byte_size: number;
  created_at: string;
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
type WalletLoadStatus = "idle" | "loading" | "error";
type LaunchMode = "demo" | "real" | "bonus";
type LaunchCashierCopy = ReturnType<typeof createMinesCopyResolver>["t"];
type CashierRuntimeConfig = MinesRuntimeConfig | null;

const ENGLISH_CASHIER_PRESENTATION: MinesPresentationConfig = {
  rules_sections: {},
  published_grid_sizes: [],
  published_mine_counts: {},
  default_mine_counts: {},
  ui_labels: {},
  i18n: {
    published_locale: "en",
    resolved_locale: "en",
    default_locale: "en",
    fallback_locale: "en",
    copy: {},
  },
};

const DEFAULT_LAUNCH_CASHIER_COPY: Record<string, string> = {
  "launch_cashier.eyebrow": "Launch cashier",
  "launch_cashier.close_aria": "Close launch cashier",
  "launch_cashier.close": "Close",
  "launch_cashier.real_money": "Real money",
  "launch_cashier.cash_balance": "Cash balance",
  "launch_cashier.bonus": "Bonus",
  "launch_cashier.bonus_balance": "Bonus balance",
  "launch_cashier.demo": "Demo",
  "launch_cashier.demo_balance": "Demo balance",
  "launch_cashier.demo_balance_value": "100.00 CHIP",
  "launch_cashier.balance_unavailable_error": "Balance is unavailable right now.",
  "launch_cashier.real_disabled": "Real play is not enabled for this title.",
  "launch_cashier.real_login_required": "Log in to use real balance.",
  "launch_cashier.loading_balance": "Loading balance...",
  "launch_cashier.balance_unavailable": "Balance unavailable.",
  "launch_cashier.bonus_disabled": "Bonus play is not enabled for this title.",
  "launch_cashier.bonus_login_required": "Log in to use bonus balance.",
  "launch_cashier.no_bonus_balance": "No bonus balance available.",
  "launch_cashier.demo_disabled": "Demo play is not enabled for this title.",
};

export function PlayerLobbyPage() {
  const [hasAccessToken, setHasAccessToken] = useState(false);
  const [gameLibrary, setGameLibrary] = useState<GameLibraryTitle[]>([]);
  const [homeSlots, setHomeSlots] = useState<SiteHomeSlot[]>([]);
  const [libraryStatus, setLibraryStatus] = useState<LibraryStatus>("loading");
  const [cashierGame, setCashierGame] = useState<GameLibraryTitle | null>(null);
  const [cashierWallets, setCashierWallets] = useState<Wallet[]>([]);
  const [cashierWalletStatus, setCashierWalletStatus] = useState<WalletLoadStatus>("idle");
  const [cashierRuntimeConfig, setCashierRuntimeConfig] = useState<CashierRuntimeConfig>(null);

  useEffect(() => {
    function syncAuthState() {
      const hasToken = hasStoredPlayerAccessToken();
      setHasAccessToken(hasToken);
      if (!hasToken) {
        setCashierWallets([]);
        setCashierWalletStatus("idle");
      }
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
    if (!cashierGame || !hasAccessToken) {
      return;
    }

    let isMounted = true;
    const token = readStoredString(PLAYER_STORAGE_KEYS.accessToken);
    if (!token) {
      setCashierWallets([]);
      setCashierWalletStatus("idle");
      return;
    }

    setCashierWalletStatus("loading");
    apiRequest<Wallet[]>("/wallets", {}, token)
      .then((wallets) => {
        if (!isMounted) {
          return;
        }
        setCashierWallets(wallets);
        setCashierWalletStatus("idle");
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setCashierWallets([]);
        setCashierWalletStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, [cashierGame, hasAccessToken]);

  useEffect(() => {
    if (!cashierGame) {
      setCashierRuntimeConfig(null);
      return;
    }

    let isMounted = true;
    setCashierRuntimeConfig(null);

    if (cashierGame.engine_code !== "mines") {
      return;
    }

    apiRequest<MinesRuntimeConfig>(
      `/games/mines/config?title_code=${encodeURIComponent(cashierGame.title_code)}`,
    )
      .then((config) => {
        if (!isMounted) {
          return;
        }
        setCashierRuntimeConfig(config);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setCashierRuntimeConfig(null);
      });

    return () => {
      isMounted = false;
    };
  }, [cashierGame]);

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
            <LobbyHomeSlotHero
              gameLibrary={gameLibrary}
              onOpenCashier={setCashierGame}
              slot={homepageSlot}
            />
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
              <PlayerGameCard game={game} key={game.title_code} onOpenCashier={setCashierGame} />
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

      {cashierGame ? (
        <LaunchCashierModal
          game={cashierGame}
          hasAccessToken={hasAccessToken}
          onClose={() => setCashierGame(null)}
          runtimeConfig={cashierRuntimeConfig}
          walletStatus={cashierWalletStatus}
          wallets={cashierWallets}
        />
      ) : null}
    </main>
  );
}

function LobbyHomeSlotHero({
  gameLibrary,
  onOpenCashier,
  slot,
}: {
  gameLibrary: GameLibraryTitle[];
  onOpenCashier: (game: GameLibraryTitle) => void;
  slot: SiteHomeSlot;
}) {
  const ctaGame =
    slot.cta_target_ref && slot.cta_target_type !== "none"
      ? gameLibrary.find((game) => game.title_code === slot.cta_target_ref) ?? null
      : null;
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
        {ctaGame && ctaLabel ? (
          <div className="player-lobby-home-slot-actions">
            <Button onClick={() => onOpenCashier(ctaGame)}>{ctaLabel}</Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function PlayerGameCard({
  game,
  onOpenCashier,
}: {
  game: GameLibraryTitle;
  onOpenCashier: (game: GameLibraryTitle) => void;
}) {
  const cardAssetUrl = game.game_card_asset
    ? resolveBackendAssetUrl(game.game_card_asset.public_url)
    : null;

  return (
    <button
      aria-label={`Open launch cashier for ${game.display_name}`}
      className={`player-lobby-card ${game.featured ? "is-featured" : ""}`}
      onClick={() => onOpenCashier(game)}
      type="button"
    >
      <div
        className={`player-lobby-card-art ${cardAssetUrl ? "has-game-card" : ""}`}
        aria-hidden="true"
        style={cardAssetUrl ? { backgroundImage: `url("${cardAssetUrl}")` } : undefined}
      >
        {!cardAssetUrl ? (
          <>
            <div className="player-lobby-art-copy">
              <span>{game.engine_display_name}</span>
              <strong>{game.display_name}</strong>
            </div>
            <div className="player-lobby-board">
              {Array.from({ length: 9 }, (_, index) => (
                <span className={index === 4 ? "is-gem" : ""} key={index} />
              ))}
            </div>
          </>
        ) : null}
      </div>

      <div className="player-lobby-card-body">
        <div className="player-lobby-card-heading">
          <div>
            <p className="eyebrow">{game.engine_display_name}</p>
            <h3>{game.display_name}</h3>
          </div>
          {game.featured ? <strong className="player-lobby-card-badge">Featured</strong> : null}
        </div>
      </div>
    </button>
  );
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

function LaunchCashierModal({
  game,
  hasAccessToken,
  onClose,
  runtimeConfig,
  walletStatus,
  wallets,
}: {
  game: GameLibraryTitle;
  hasAccessToken: boolean;
  onClose: () => void;
  runtimeConfig: CashierRuntimeConfig;
  walletStatus: WalletLoadStatus;
  wallets: Wallet[];
}) {
  const copy = createLaunchCashierCopy(game.engine_code, runtimeConfig);
  const cashWallet = wallets.find((wallet) => wallet.wallet_type === "cash") ?? null;
  const bonusWallet = wallets.find((wallet) => wallet.wallet_type === "bonus") ?? null;
  const walletReadReady = hasAccessToken && walletStatus === "idle";
  const bonusBalance = parseWalletAmount(bonusWallet);
  const realBalanceLabel = walletReadReady ? formatWalletBalance(cashWallet) : "-";
  const bonusBalanceLabel = walletReadReady ? formatWalletBalance(bonusWallet) : "-";
  const realDisabledReason = getRealLaunchDisabledReason(
    game,
    hasAccessToken,
    walletStatus,
    copy,
  );
  const bonusDisabledReason = getBonusLaunchDisabledReason(
    game,
    hasAccessToken,
    walletStatus,
    bonusBalance,
    copy,
  );
  const demoDisabledReason = game.demo_enabled ? null : copy("launch_cashier.demo_disabled");

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  function launch(mode: LaunchMode) {
    window.location.href = buildLaunchHref(game, mode);
  }

  return (
    <div className="player-lobby-cashier-overlay" onMouseDown={onClose} role="presentation">
      <section
        aria-labelledby="player-lobby-cashier-title"
        aria-modal="true"
        className="player-lobby-cashier"
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="player-lobby-cashier-head">
          <div>
            <p className="eyebrow">{copy("launch_cashier.eyebrow")}</p>
            <h2 id="player-lobby-cashier-title">{game.display_name}</h2>
          </div>
          <Button aria-label={copy("launch_cashier.close_aria")} onClick={onClose} variant="ghost">
            {copy("launch_cashier.close")}
          </Button>
        </div>

        <div className="player-lobby-cashier-options">
          <LaunchCashierOption
            balanceLabel={realBalanceLabel}
            disabledReason={realDisabledReason}
            label={copy("launch_cashier.real_money")}
            onClick={() => launch("real")}
            valueLabel={copy("launch_cashier.cash_balance")}
          />
          <LaunchCashierOption
            balanceLabel={bonusBalanceLabel}
            disabledReason={bonusDisabledReason}
            label={copy("launch_cashier.bonus")}
            onClick={() => launch("bonus")}
            valueLabel={copy("launch_cashier.bonus_balance")}
          />
          <LaunchCashierOption
            balanceLabel={copy("launch_cashier.demo_balance_value")}
            disabledReason={demoDisabledReason}
            label={copy("launch_cashier.demo")}
            onClick={() => launch("demo")}
            valueLabel={copy("launch_cashier.demo_balance")}
          />
        </div>

        {walletStatus === "error" ? (
          <p className="player-lobby-cashier-error">
            {copy("launch_cashier.balance_unavailable_error")}
          </p>
        ) : null}
      </section>
    </div>
  );
}

function LaunchCashierOption({
  balanceLabel,
  disabledReason,
  label,
  onClick,
  valueLabel,
}: {
  balanceLabel: string;
  disabledReason: string | null;
  label: string;
  onClick: () => void;
  valueLabel: string;
}) {
  return (
    <button
      className="player-lobby-cashier-option"
      disabled={Boolean(disabledReason)}
      onClick={onClick}
      type="button"
    >
      <span>
        <strong>{label}</strong>
        <small>{disabledReason ?? valueLabel}</small>
      </span>
      <em>{balanceLabel}</em>
    </button>
  );
}

function buildLaunchHref(game: GameLibraryTitle, mode: LaunchMode): string {
  const params = new URLSearchParams({ title_code: game.title_code });
  if (mode === "demo") {
    params.set("mode", "demo");
  }
  if (mode === "real") {
    if (game.engine_code === "boxe") {
      params.set("mode", "real_cash");
    }
    params.set("wallet_source", "real");
  }
  if (mode === "bonus") {
    if (game.engine_code === "boxe") {
      params.set("mode", "real_bonus");
    }
    params.set("wallet_source", "bonus");
  }
  return `${resolveLaunchRoute(game.engine_code)}?${params.toString()}`;
}

function resolveLaunchRoute(engineCode: string): string {
  if (engineCode === "boxe") {
    return "/boxe";
  }
  if (engineCode === "mines") {
    return "/mines";
  }
  return `/${encodeURIComponent(engineCode)}`;
}

function createLaunchCashierCopy(
  engineCode: string,
  runtimeConfig: CashierRuntimeConfig,
): LaunchCashierCopy {
  if (engineCode === "mines") {
    return createMinesCopyResolver(
      runtimeConfig?.presentation_config ?? ENGLISH_CASHIER_PRESENTATION,
      "real",
    ).t;
  }

  return (key: string) => DEFAULT_LAUNCH_CASHIER_COPY[key] ?? key;
}

function getRealLaunchDisabledReason(
  game: Pick<GameLibraryTitle, "real_enabled">,
  hasAccessToken: boolean,
  walletStatus: WalletLoadStatus,
  copy: LaunchCashierCopy,
): string | null {
  if (!game.real_enabled) {
    return copy("launch_cashier.real_disabled");
  }
  if (!hasAccessToken) {
    return copy("launch_cashier.real_login_required");
  }
  if (walletStatus === "loading") {
    return copy("launch_cashier.loading_balance");
  }
  if (walletStatus === "error") {
    return copy("launch_cashier.balance_unavailable");
  }
  return null;
}

function getBonusLaunchDisabledReason(
  game: Pick<GameLibraryTitle, "real_enabled">,
  hasAccessToken: boolean,
  walletStatus: WalletLoadStatus,
  bonusBalance: number,
  copy: LaunchCashierCopy,
): string | null {
  if (!game.real_enabled) {
    return copy("launch_cashier.bonus_disabled");
  }
  if (!hasAccessToken) {
    return copy("launch_cashier.bonus_login_required");
  }
  if (walletStatus === "loading") {
    return copy("launch_cashier.loading_balance");
  }
  if (walletStatus === "error") {
    return copy("launch_cashier.balance_unavailable");
  }
  if (bonusBalance <= 0) {
    return copy("launch_cashier.no_bonus_balance");
  }
  return null;
}

function parseWalletAmount(wallet: Wallet | null): number {
  if (!wallet) {
    return 0;
  }
  const amount = Number.parseFloat(wallet.balance_snapshot);
  return Number.isFinite(amount) ? amount : 0;
}

function formatWalletBalance(wallet: Wallet | null): string {
  if (!wallet) {
    return "0.00";
  }
  const amount = parseWalletAmount(wallet);
  const currency = wallet.currency_code ?? "EUR";
  try {
    return new Intl.NumberFormat("en-US", {
      currency,
      style: "currency",
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
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
