import type { SiteHomeSlot, SiteV3PublicModule } from "../../lib/types";
import {
  firstHomeSlotWithMedia,
  readString,
  resolveAssetRef,
  resolveCtaHref,
  resolveHomeSlotHref,
  resolveHomeSlotMedia,
} from "../site-v3-render-helpers";

export function HeroBanner({
  homeSlots,
  module,
}: {
  homeSlots: SiteHomeSlot[];
  module: SiteV3PublicModule;
}) {
  const config = module.config_json;
  const fallbackSlot = firstHomeSlotWithMedia(homeSlots);
  const mediaUrl = resolveAssetRef(config.media_asset_ref) ?? resolveHomeSlotMedia(fallbackSlot);
  const ctaHref = resolveCtaHref(config.cta_title_code, undefined) ?? resolveHomeSlotHref(fallbackSlot);
  const ctaLabel = readString(config.cta_label, fallbackSlot?.cta_label ?? (ctaHref ? "Gioca ora" : ""));
  const headline = readString(config.headline, fallbackSlot?.title ?? "CasinoKing");
  const body = readString(config.body, fallbackSlot?.subtitle ?? "");
  const isV1Backed = Boolean(fallbackSlot && !resolveAssetRef(config.media_asset_ref));

  return (
    <section className={`site-v3-hero ${isV1Backed ? "is-v1-backed" : ""}`}>
      {mediaUrl ? <img alt="" src={mediaUrl} /> : <div className="site-v3-hero-media-fallback" />}
      <div className="site-v3-hero-copy">
        <p className="site-v3-kicker">CasinoKing</p>
        <h1>{headline}</h1>
        {body ? <p>{body}</p> : null}
        {ctaHref && ctaLabel ? (
          <a className="site-v3-primary-link" href={ctaHref}>
            {ctaLabel}
          </a>
        ) : null}
      </div>
    </section>
  );
}
