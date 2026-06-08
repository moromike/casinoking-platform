"use client";

import { useState } from "react";
import type { GameLibraryTitle, SiteHomeSlot, SiteV3PublicModule } from "../../lib/types";
import {
  firstHomeSlotWithMedia,
  readString,
  resolveAssetRef,
  resolveCtaHref,
  resolveHomeSlotHref,
  resolveHomeSlotMedia,
} from "../site-v3-render-helpers";
import { LaunchCashier } from "./launch-cashier";

export function HeroBanner({
  games,
  homeSlots,
  module,
}: {
  games: Map<string, GameLibraryTitle>;
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

  const ctaTitleCode = readString(config.cta_title_code, fallbackSlot?.cta_target_ref ?? "");
  const ctaTitle = ctaTitleCode ? games.get(ctaTitleCode) : undefined;
  const [cashierOpen, setCashierOpen] = useState(false);

  const hasCta = showCta && (ctaTitle || ctaHref) && ctaLabel;

  return (
    <section className={`site-v3-hero ${isV1Backed ? "is-v1-backed" : ""} ${showCopy ? "" : "is-image-only"}`}>
      {mediaUrl ? <img alt="" src={mediaUrl} /> : <div className="site-v3-hero-media-fallback" />}
      {showCopy ? (
        <div className="site-v3-hero-copy">
          <p className="site-v3-kicker">CasinoKing</p>
          <h1>{headline}</h1>
          {body ? <p>{body}</p> : null}
          {hasCta ? (
            <CtaButton
              ctaHref={ctaHref}
              ctaLabel={ctaLabel}
              ctaTitle={ctaTitle}
              cashierOpen={cashierOpen}
              onToggleCashier={() => setCashierOpen((open) => !open)}
            />
          ) : null}
        </div>
      ) : null}
      {!showCopy && hasCta ? (
        <CtaButton
          className="site-v3-hero-cta-only"
          ctaHref={ctaHref}
          ctaLabel={ctaLabel}
          ctaTitle={ctaTitle}
          cashierOpen={cashierOpen}
          onToggleCashier={() => setCashierOpen((open) => !open)}
        />
      ) : null}
    </section>
  );
}

function CtaButton({
  className = "",
  ctaHref,
  ctaLabel,
  ctaTitle,
  cashierOpen,
  onToggleCashier,
}: {
  className?: string;
  ctaHref: string | null;
  ctaLabel: string;
  ctaTitle: GameLibraryTitle | undefined;
  cashierOpen: boolean;
  onToggleCashier: () => void;
}) {
  if (ctaTitle) {
    return (
      <>
        <button
          className={`site-v3-primary-link ${className}`.trim()}
          onClick={onToggleCashier}
          type="button"
        >
          {ctaLabel}
        </button>
        {cashierOpen ? <LaunchCashier title={ctaTitle} onClose={onToggleCashier} /> : null}
      </>
    );
  }

  if (ctaHref) {
    return (
      <a className={`site-v3-primary-link ${className}`.trim()} href={ctaHref}>
        {ctaLabel}
      </a>
    );
  }

  return null;
}
