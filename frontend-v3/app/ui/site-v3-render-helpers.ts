import { resolvePublicAssetUrl } from "../lib/api";
import type {
  GameLibraryTitle,
  SiteHomeSlot,
  SiteV3ModuleCode,
  SiteV3PublicModule,
} from "../lib/types";

export const V1_BASE_URL =
  process.env.NEXT_PUBLIC_V1_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export function sortedModules(modules: SiteV3PublicModule[]): SiteV3PublicModule[] {
  return [...modules].sort((left, right) => {
    const slotCompare = left.slot_key.localeCompare(right.slot_key);
    if (slotCompare !== 0) {
      return slotCompare;
    }
    return left.sort_order - right.sort_order;
  });
}

export function findFirstModule(
  modules: SiteV3PublicModule[],
  moduleCode: SiteV3ModuleCode,
): SiteV3PublicModule | null {
  return modules.find((module) => module.module_code === moduleCode) ?? null;
}

export function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

export function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

export function readNavItems(value: unknown): Array<{ label: string; url?: string; title_code?: string }> {
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

export function resolveAssetRef(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const asset = value as Record<string, unknown>;
  return resolvePublicAssetUrl(typeof asset.public_url === "string" ? asset.public_url : null);
}

export function firstHomeSlotWithMedia(homeSlots: SiteHomeSlot[]): SiteHomeSlot | null {
  return homeSlots.find((slot) => Boolean(slot.media_asset?.public_url)) ?? null;
}

export function resolveHomeSlotMedia(slot: SiteHomeSlot | null): string | null {
  return resolvePublicAssetUrl(slot?.media_asset?.public_url);
}

export function resolveHomeSlotHref(slot: SiteHomeSlot | null): string | null {
  if (!slot?.cta_target_ref) {
    return null;
  }
  if (slot.cta_target_type === "title_real") {
    return resolveCtaHref(slot.cta_target_ref, "real");
  }
  if (slot.cta_target_type === "title_demo") {
    return resolveCtaHref(slot.cta_target_ref, "demo");
  }
  return null;
}

export function resolveCtaHref(value: unknown, mode: "demo" | "real" | undefined): string | null {
  const titleCode = readString(value, "");
  if (!titleCode) {
    return null;
  }
  return `${V1_BASE_URL}/${routeForTitleCode(titleCode)}?title_code=${encodeURIComponent(titleCode)}&mode=${mode ?? "demo"}`;
}

export function resolveGameHref(title: GameLibraryTitle, mode: "demo" | "real"): string {
  return `${V1_BASE_URL}/${routeForEngine(title.engine_code)}?title_code=${encodeURIComponent(title.title_code)}&mode=${mode}`;
}

export function resolveLink(rawHref: string): string {
  if (rawHref.startsWith("#")) {
    return rawHref;
  }
  if (/^https?:\/\//.test(rawHref)) {
    return rawHref;
  }
  if (rawHref.startsWith("/")) {
    return `${V1_BASE_URL}${rawHref}`;
  }
  return `${V1_BASE_URL}/${routeForTitleCode(rawHref)}?title_code=${encodeURIComponent(rawHref)}&mode=demo`;
}

export function routeForTitleCode(titleCode: string): string {
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
