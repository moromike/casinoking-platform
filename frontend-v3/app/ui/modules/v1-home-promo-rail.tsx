import type { SiteHomeSlot } from "../../lib/types";
import {
  resolveHomeSlotHref,
  resolveHomeSlotMedia,
} from "../site-v3-render-helpers";

export function V1HomePromoRail({ homeSlots }: { homeSlots: SiteHomeSlot[] }) {
  const promoSlots = homeSlots.filter((slot) => Boolean(slot.media_asset?.public_url)).slice(1, 5);
  if (promoSlots.length === 0) {
    return null;
  }

  return (
    <section className="site-v3-home-promo-rail" id="promos" aria-label="Promotions">
      {promoSlots.map((slot) => {
        const mediaUrl = resolveHomeSlotMedia(slot);
        const href = resolveHomeSlotHref(slot) ?? "#";
        return (
          <a className="site-v3-home-promo-tile" href={href} key={slot.id}>
            {mediaUrl ? <img alt="" src={mediaUrl} /> : null}
            <span>{slot.title}</span>
          </a>
        );
      })}
    </section>
  );
}
