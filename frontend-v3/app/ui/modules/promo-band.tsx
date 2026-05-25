import type { SiteV3PublicModule } from "../../lib/types";
import { readString, resolveAssetRef, resolveLink } from "../site-v3-render-helpers";

export function PromoBand({ module }: { module: SiteV3PublicModule }) {
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
