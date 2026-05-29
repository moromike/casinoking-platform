import { resolvePublicAssetUrl } from "../lib/api";
import type {
  GameLibraryTitle,
  SiteHomeSlot,
  SiteV3ModuleCode,
  SiteV3PublicModule,
} from "../lib/types";

export const V1_BASE_URL =
  process.env.NEXT_PUBLIC_V1_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";
export const SITE_V3_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

const SLOT_ORDER = new Map<string, number>([
  ["header", 0],
  ["hero", 10],
  ["main", 20],
  ["content", 30],
  ["feature", 40],
  ["games", 50],
  ["promo", 60],
  ["footer", 90],
]);

export function sortedModules(modules: SiteV3PublicModule[]): SiteV3PublicModule[] {
  return [...modules].sort((left, right) => {
    const leftPinned = pinnedSlotOrder(left.slot_key);
    const rightPinned = pinnedSlotOrder(right.slot_key);
    if (leftPinned !== rightPinned) {
      return leftPinned - rightPinned;
    }
    if (left.sort_order !== right.sort_order) {
      return left.sort_order - right.sort_order;
    }
    return left.slot_key.localeCompare(right.slot_key);
  });
}

function pinnedSlotOrder(slotKey: string): number {
  if (slotKey === "header") {
    return 0;
  }
  if (slotKey === "footer") {
    return 100;
  }
  return 50;
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

export function readBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

export function readNavItems(value: unknown): Array<{ label: string; url?: string; title_code?: string }> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      label: readString(item.label, ""),
      url:
        typeof item.url === "string"
          ? item.url
          : typeof item.href === "string"
            ? item.href
            : undefined,
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

export function resolveCtaHref(
  value: unknown,
  mode: "demo" | "real" | undefined,
  returnTo = SITE_V3_BASE_URL,
): string | null {
  const titleCode = readString(value, "");
  if (!titleCode) {
    return null;
  }
  const params = new URLSearchParams({
    title_code: titleCode,
    mode: mode ?? "demo",
  });
  appendReturnToParam(params, returnTo);
  return `${V1_BASE_URL}/${routeForTitleCode(titleCode)}?${params.toString()}`;
}

export type GameLaunchMode = "demo" | "real" | "bonus";

export function resolveGameHref(
  title: GameLibraryTitle,
  mode: GameLaunchMode,
  returnTo = SITE_V3_BASE_URL,
): string {
  const params = new URLSearchParams({ title_code: title.title_code });
  if (mode === "demo") {
    params.set("mode", "demo");
  }
  if (mode === "real") {
    if (title.engine_code === "boxe") {
      params.set("mode", "real_cash");
    }
    params.set("wallet_source", "real");
  }
  if (mode === "bonus") {
    if (title.engine_code === "boxe") {
      params.set("mode", "real_bonus");
    }
    params.set("wallet_source", "bonus");
  }
  appendReturnToParam(params, returnTo);
  return `${V1_BASE_URL}/${routeForEngine(title.engine_code)}?${params.toString()}`;
}

export function resolvePlayerReturnHref(path: "/login" | "/register" | "/account", returnTo = SITE_V3_BASE_URL): string {
  const params = new URLSearchParams({ return_to: returnTo });
  return `${path}?${params.toString()}`;
}

export function resolveLink(rawHref: string, returnTo = SITE_V3_BASE_URL): string {
  if (rawHref.startsWith("#")) {
    return rawHref;
  }
  if (/^(https?:\/\/|mailto:)/.test(rawHref)) {
    return rawHref;
  }
  if (isPlayerShellPath(rawHref)) {
    const url = new URL(rawHref, SITE_V3_BASE_URL);
    if (url.searchParams.has("return_to")) {
      return `${url.pathname}?${url.searchParams.toString()}`;
    }
    return resolvePlayerReturnHref(url.pathname as "/login" | "/register" | "/account", returnTo);
  }
  if (rawHref.startsWith("/")) {
    return `${V1_BASE_URL}${rawHref}`;
  }
  const params = new URLSearchParams({ title_code: rawHref, mode: "demo" });
  appendReturnToParam(params, returnTo);
  return `${V1_BASE_URL}/${routeForTitleCode(rawHref)}?${params.toString()}`;
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

function appendReturnToParam(params: URLSearchParams, returnTo: string): void {
  if (returnTo.trim().length === 0) {
    return;
  }
  params.set("return_to", returnTo);
}

function isPlayerShellPath(rawHref: string): boolean {
  if (
    rawHref === "/login" ||
    rawHref.startsWith("/login?") ||
    rawHref === "/register" ||
    rawHref.startsWith("/register?") ||
    rawHref === "/account" ||
    rawHref.startsWith("/account?")
  ) {
    return true;
  }
  try {
    const url = new URL(rawHref, SITE_V3_BASE_URL);
    return url.origin === new URL(SITE_V3_BASE_URL).origin
      && (url.pathname === "/login" || url.pathname === "/register" || url.pathname === "/account");
  } catch {
    return false;
  }
}
