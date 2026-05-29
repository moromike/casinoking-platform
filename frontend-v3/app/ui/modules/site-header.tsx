import type { SiteV3PublicModule } from "../../lib/types";
import { readNavItems, readString, resolveLink } from "../site-v3-render-helpers";
import { SiteHeaderAuthActions } from "./site-header-auth-actions";

export function SiteHeader({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const brand = readString(config.brand_label, "CasinoKing");
  const navItems = readNavItems(config.nav_items);
  const resolvedNavItems =
    navItems.length > 0
      ? navItems
      : [
          { label: "Games", url: "#games" },
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
        <SiteHeaderAuthActions
          accountLabel={readString(config.account_label, "Account")}
          loginLabel={readString(config.login_label, "Login")}
        />
      </div>
    </header>
  );
}
