import type { SiteV3PublicModule } from "../../lib/types";
import { readString } from "../site-v3-render-helpers";
import { SiteHeaderAuthActions } from "./site-header-auth-actions";

export function SiteHeader({ module }: { module: SiteV3PublicModule | null }) {
  const config = module?.config_json ?? {};
  const brand = readString(config.brand_label, "CasinoKing");

  return (
    <header className="site-v3-header">
      <a className="site-v3-brand" href="/" aria-label="CasinoKing home">
        {brand}
      </a>
      <div className="site-v3-header-actions">
        <SiteHeaderAuthActions
          accountLabel={readString(config.account_label, "Account")}
          loginLabel={readString(config.login_label, "Login")}
        />
      </div>
    </header>
  );
}
