import {
  loadSiteV3Page,
  normalizeSingleParam,
  resolvePublicAssetUrl,
  titleMap,
} from "../lib/api";
import type {
  GameLibraryTitle,
  SiteV3ModuleCode,
  SiteV3PublicModule,
  SiteV3PublicPageSnapshot,
} from "../lib/types";

const V1_BASE_URL =
  process.env.NEXT_PUBLIC_V1_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export async function SiteV3PublicPage({
  pageCode,
  searchParams,
}: {
  pageCode: string;
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const siteCode = normalizeSingleParam(searchParams.site_code, "casinoking");
  const locale = normalizeSingleParam(searchParams.locale, "it");
  const result = await loadSiteV3Page({ siteCode, pageCode, locale });

  if (!result.page) {
    return (
      <main className="site-v3-page site-v3-page-fallback">
        <section className="site-v3-fallback-panel">
          <p className="site-v3-kicker">Site V3</p>
          <h1>Pagina non pubblicata</h1>
          <p>
            Questa pagina non ha ancora uno snapshot live. Pubblicala dal
            builder admin prima di aprirla sul sito pubblico.
          </p>
          <small>{result.error ?? "Published page unavailable"}</small>
        </section>
      </main>
    );
  }

  const page = result.page;
  const modules = sortedModules(page.modules);
  const header =
    findFirstModule(modules, "global_header") ?? result.navigation?.header ?? null;
  const footer =
    findFirstModule(modules, "global_footer") ?? result.navigation?.footer ?? null;
  const bodyModules = modules.filter(
    (module) => module.module_code !== "global_header" && module.module_code !== "global_footer",
  );
  const games = titleMap(result.gameLibrary);

  return (
    <main className="site-v3-page">
      <SiteHeader module={header} />
      <div className="site-v3-main" data-page-code={page.page_code}>
        {bodyModules.length > 0 ? (
          bodyModules.map((module) => (
            <ModuleRenderer
              gameLibrary={result.gameLibrary}
              games={games}
              key={module.id}
              module={module}
              page={page}
            />
          ))
        ) : (
          <section className="site-v3-empty-section">
            <p>La pagina pubblicata non contiene ancora moduli visuali.</p>
          </section>
        )}
      </div>
      <SiteFooter module={footer} />
    </main>
  );
}

function SiteHeader({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const brand = readString(config.brand_label, "CasinoKing");
  const navItems = readNavItems(config.nav_items);

  return (
    <header className="site-v3-header">
      <a className="site-v3-brand" href="/">
        {brand}
      </a>
      <nav aria-label="Site V3 navigation">
        {navItems.slice(0, 6).map((item) => (
          <a href={resolveLink(item.url ?? item.title_code ?? "/")} key={`${item.label}:${item.url ?? item.title_code}`}>
            {item.label}
          </a>
        ))}
      </nav>
      <div className="site-v3-header-actions">
        <a href={`${V1_BASE_URL}/login`}>{readString(config.login_label, "Login")}</a>
        <a className="is-strong" href={`${V1_BASE_URL}/account`}>
          {readString(config.account_label, "Account")}
        </a>
      </div>
    </header>
  );
}

function SiteFooter({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const links = readNavItems(config.links);
  return (
    <footer className="site-v3-footer">
      <p>{readString(config.legal_text, "CasinoKing - gioco responsabile.")}</p>
      {links.length > 0 ? (
        <nav aria-label="Footer links">
          {links.slice(0, 8).map((item) => (
            <a href={resolveLink(item.url ?? item.title_code ?? "/")} key={`${item.label}:${item.url ?? item.title_code}`}>
              {item.label}
            </a>
          ))}
        </nav>
      ) : null}
    </footer>
  );
}

function ModuleRenderer({
  module,
  page,
  gameLibrary,
  games,
}: {
  module: SiteV3PublicModule;
  page: SiteV3PublicPageSnapshot;
  gameLibrary: GameLibraryTitle[];
  games: Map<string, GameLibraryTitle>;
}) {
  switch (module.module_code as SiteV3ModuleCode) {
    case "hero_banner":
      return <HeroBanner module={module} />;
    case "game_grid":
      return <GameGrid module={module} titles={gameLibrary} games={games} />;
    case "featured_game":
      return <FeaturedGame module={module} games={games} />;
    case "promo_band":
      return <PromoBand module={module} />;
    case "rich_text_safe":
      return <RichTextSafe module={module} />;
    case "global_header":
    case "global_footer":
      return null;
    default:
      if (process.env.NODE_ENV === "development") {
        console.warn(`Unknown Site V3 module on ${page.page_code}: ${module.module_code}`);
      }
      return null;
  }
}

function HeroBanner({ module }: { module: SiteV3PublicModule }) {
  const config = module.config_json;
  const mediaUrl = resolveAssetRef(config.media_asset_ref);
  const ctaHref = resolveCtaHref(config.cta_title_code, undefined);
  const ctaLabel = readString(config.cta_label, ctaHref ? "Gioca ora" : "");

  return (
    <section className="site-v3-hero">
      {mediaUrl ? <img alt="" src={mediaUrl} /> : <div className="site-v3-hero-media-fallback" />}
      <div className="site-v3-hero-copy">
        <p className="site-v3-kicker">CasinoKing</p>
        <h1>{readString(config.headline, "CasinoKing")}</h1>
        {readString(config.body, "") ? <p>{readString(config.body, "")}</p> : null}
        {ctaHref && ctaLabel ? (
          <a className="site-v3-primary-link" href={ctaHref}>
            {ctaLabel}
          </a>
        ) : null}
      </div>
    </section>
  );
}

function GameGrid({
  module,
  titles,
  games,
}: {
  module: SiteV3PublicModule;
  titles: GameLibraryTitle[];
  games: Map<string, GameLibraryTitle>;
}) {
  const requestedCodes = readStringArray(module.config_json.title_codes);
  const selectedTitles =
    requestedCodes.length > 0
      ? requestedCodes.map((code) => games.get(code)).filter((title): title is GameLibraryTitle => Boolean(title))
      : titles;

  return (
    <section className="site-v3-section">
      <div className="site-v3-section-heading">
        <p className="site-v3-kicker">Giochi</p>
        <h2>{readString(module.config_json.heading, "Scegli il tuo gioco")}</h2>
      </div>
      {selectedTitles.length > 0 ? (
        <div className="site-v3-game-grid">
          {selectedTitles.map((title) => (
            <GameCard key={title.title_code} title={title} />
          ))}
        </div>
      ) : (
        <p className="site-v3-empty-section">Nessun gioco pubblicato disponibile per questa sezione.</p>
      )}
    </section>
  );
}

function FeaturedGame({
  module,
  games,
}: {
  module: SiteV3PublicModule;
  games: Map<string, GameLibraryTitle>;
}) {
  const titleCode = readString(module.config_json.title_code, "");
  const game = titleCode ? games.get(titleCode) : undefined;
  if (!game) {
    return null;
  }

  return (
    <section className="site-v3-featured">
      <GameArtwork title={game} />
      <div>
        <p className="site-v3-kicker">{game.engine_display_name}</p>
        <h2>{readString(module.config_json.headline, game.display_name)}</h2>
        <p>{readString(module.config_json.body, game.description ?? "Apri il gioco dalla lobby CasinoKing.")}</p>
        <a className="site-v3-primary-link" href={resolveGameHref(game, "demo")}>
          {readString(module.config_json.cta_label, "Prova in demo")}
        </a>
      </div>
    </section>
  );
}

function PromoBand({ module }: { module: SiteV3PublicModule }) {
  const config = module.config_json;
  const href = readString(config.cta_url, "");
  const mediaUrl = resolveAssetRef(config.media_asset_ref);
  return (
    <section className="site-v3-promo">
      {mediaUrl ? <img alt="" src={mediaUrl} /> : null}
      <div>
        <p className="site-v3-kicker">Promo</p>
        <h2>{readString(config.headline, "Promozione")}</h2>
        {readString(config.body, "") ? <p>{readString(config.body, "")}</p> : null}
      </div>
      {href ? (
        <a className="site-v3-secondary-link" href={resolveLink(href)}>
          {readString(config.cta_label, "Scopri")}
        </a>
      ) : null}
    </section>
  );
}

function RichTextSafe({ module }: { module: SiteV3PublicModule }) {
  const html = readString(module.config_json.html, "");
  if (!html) {
    return null;
  }
  return (
    <section
      className="site-v3-rich-text"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function GameCard({ title }: { title: GameLibraryTitle }) {
  return (
    <article className="site-v3-game-card">
      <GameArtwork title={title} />
      <div className="site-v3-game-card-body">
        <p>{title.engine_display_name}</p>
        <h3>{title.display_name}</h3>
        {title.description ? <span>{title.description}</span> : null}
        <div className="site-v3-mode-row">
          {title.demo_enabled ? <a href={resolveGameHref(title, "demo")}>Demo</a> : null}
          {title.real_enabled ? <a href={resolveGameHref(title, "real")}>Real</a> : null}
        </div>
      </div>
    </article>
  );
}

function GameArtwork({ title }: { title: GameLibraryTitle }) {
  const assetUrl = resolvePublicAssetUrl(title.game_card_asset?.public_url);
  if (assetUrl) {
    return <img alt="" className="site-v3-game-art" src={assetUrl} />;
  }
  return (
    <div className="site-v3-game-art site-v3-game-art-fallback">
      <span>{title.display_name.slice(0, 2).toUpperCase()}</span>
    </div>
  );
}

function sortedModules(modules: SiteV3PublicModule[]): SiteV3PublicModule[] {
  return [...modules].sort((left, right) => {
    const slotCompare = left.slot_key.localeCompare(right.slot_key);
    if (slotCompare !== 0) {
      return slotCompare;
    }
    return left.sort_order - right.sort_order;
  });
}

function findFirstModule(
  modules: SiteV3PublicModule[],
  moduleCode: SiteV3ModuleCode,
): SiteV3PublicModule | null {
  return modules.find((module) => module.module_code === moduleCode) ?? null;
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function readNavItems(value: unknown): Array<{ label: string; url?: string; title_code?: string }> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      label: readString(item.label, ""),
      url: typeof item.url === "string" ? item.url : undefined,
      title_code: typeof item.title_code === "string" ? item.title_code : undefined,
    }))
    .filter((item) => item.label);
}

function resolveAssetRef(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const asset = value as Record<string, unknown>;
  return resolvePublicAssetUrl(typeof asset.public_url === "string" ? asset.public_url : null);
}

function resolveCtaHref(value: unknown, mode: "demo" | "real" | undefined): string | null {
  const titleCode = readString(value, "");
  if (!titleCode) {
    return null;
  }
  return `${V1_BASE_URL}/${routeForTitleCode(titleCode)}?title_code=${encodeURIComponent(titleCode)}&mode=${mode ?? "demo"}`;
}

function resolveGameHref(title: GameLibraryTitle, mode: "demo" | "real"): string {
  return `${V1_BASE_URL}/${routeForEngine(title.engine_code)}?title_code=${encodeURIComponent(title.title_code)}&mode=${mode}`;
}

function resolveLink(rawHref: string): string {
  if (/^https?:\/\//.test(rawHref)) {
    return rawHref;
  }
  if (rawHref.startsWith("/")) {
    return rawHref;
  }
  return `${V1_BASE_URL}/${routeForTitleCode(rawHref)}?title_code=${encodeURIComponent(rawHref)}&mode=demo`;
}

function routeForTitleCode(titleCode: string): string {
  if (titleCode.startsWith("boxe")) {
    return "boxe";
  }
  if (titleCode.startsWith("hilo") || titleCode.startsWith("hi-lo")) {
    return "hi-lo";
  }
  return "mines";
}

function routeForEngine(engineCode: string): string {
  if (engineCode === "boxe") {
    return "boxe";
  }
  if (engineCode === "hi_lo" || engineCode === "hi-lo") {
    return "hi-lo";
  }
  return "mines";
}
