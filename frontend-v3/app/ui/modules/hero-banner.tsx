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
  const ctaLabel = readString(config.cta_label, fallbackSlot?.cta_label ?? (ctaHref ? "Play now" : ""));
  const headline = readString(config.headline, fallbackSlot?.title ?? "CasinoKing");
  const body = readString(config.body, fallbackSlot?.subtitle ?? "");
  const isV1Backed = Boolean(fallbackSlot && !resolveAssetRef(config.media_asset_ref));
  const showCopy = config.show_copy !== false;
  const showCta = config.show_cta !== false;
  const cta = showCta && ctaHref && ctaLabel ? { href: ctaHref, label: ctaLabel } : null;

  return (
    <section className={`site-v3-hero ${isV1Backed ? "is-v1-backed" : ""} ${showCopy ? "" : "is-image-only"}`}>
      {mediaUrl ? <img alt="" src={mediaUrl} /> : <div className="site-v3-hero-media-fallback" />}
      {showCopy ? (
        <div className="site-v3-hero-copy">
          <p className="site-v3-kicker">CasinoKing</p>
          <h1>{headline}</h1>
          {body ? <p>{body}</p> : null}
          {cta ? (
            <a className="site-v3-primary-link" href={cta.href}>
              {cta.label}
            </a>
          ) : null}
        </div>
      ) : null}
      {!showCopy && cta ? (
        <a className="site-v3-primary-link site-v3-hero-cta-only" href={cta.href}>
          {cta.label}
        </a>
      ) : null}
    </section>
  );
}
