import type { SiteV3PublicModule } from "../../lib/types";
import { readNavItems, readString, resolveLink, resolveV1ReturnHref } from "../site-v3-render-helpers";

export function SiteHeader({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const brand = readString(config.brand_label, "CasinoKing");
  const navItems = readNavItems(config.nav_items);
  const resolvedNavItems =
    navItems.length > 0
      ? navItems
      : [
          { label: "Games", url: "#games" },
          { label: "Promotions", url: "#promos" },
        ];

  return (
    <header className="site-v3-header">
      <a className="site-v3-brand" href="/" aria-label="CasinoKing home">
        {brand}
      </a>
      <nav aria-label="Site V3 navigation">
        {resolvedNavItems.slice(0, 6).map((item) => (
          <a href={resolveLink(item.url ?? item.title_code ?? "/")} key={`${item.label}:${item.url ?? item.title_code}`}>
            {item.label}
          </a>
        ))}
      </nav>
      <div className="site-v3-header-actions">
        <a className="is-login" href={resolveV1ReturnHref("/login")}>
          {readString(config.login_label, "Login")}
        </a>
        <a className="is-account" href={resolveV1ReturnHref("/account")}>
          {readString(config.account_label, "Account")}
        </a>
      </div>
    </header>
  );
}
