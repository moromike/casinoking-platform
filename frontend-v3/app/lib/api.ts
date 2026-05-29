import type {
  ApiEnvelope,
  GameLibrary,
  GameLibraryTitle,
  SiteHomeResponse,
  SiteV3LoadResult,
  SiteV3Navigation,
  SiteV3PublicPageSnapshot,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000/api/v1";
export const API_FETCH_BASE_URL =
  process.env.SITE_V3_API_INTERNAL_BASE_URL?.replace(/\/+$/, "") ?? API_BASE_URL;

export function normalizeSingleParam(
  value: string | string[] | undefined,
  fallback: string,
): string {
  if (Array.isArray(value)) {
    return value[0] ?? fallback;
  }
  return value ?? fallback;
}

export async function loadSiteV3Page({
  siteCode,
  pageCode,
  locale,
}: {
  siteCode: string;
  pageCode: string;
  locale: string;
}): Promise<SiteV3LoadResult> {
  const [pageResult, navigationResult, libraryResult, homeResult] = await Promise.all([
    apiGet<SiteV3PublicPageSnapshot>(
      `/site-v3/sites/${encodeURIComponent(siteCode)}/pages/${encodeURIComponent(pageCode)}?locale=${encodeURIComponent(locale)}`,
    ),
    apiGet<SiteV3Navigation>(
      `/site-v3/sites/${encodeURIComponent(siteCode)}/navigation?locale=${encodeURIComponent(locale)}`,
    ),
    apiGet<GameLibrary>(`/games/library?site_code=${encodeURIComponent(siteCode)}`),
    apiGet<SiteHomeResponse>(`/site/home?site_code=${encodeURIComponent(siteCode)}`),
  ]);

  return {
    page: pageResult.ok ? pageResult.data : null,
    navigation: navigationResult.ok ? navigationResult.data : null,
    gameLibrary: libraryResult.ok ? libraryResult.data.titles : [],
    homeSlots: homeResult.ok ? homeResult.data.slots : [],
    error: pageResult.ok ? null : pageResult.message,
  };
}

export function resolvePublicAssetUrl(assetUrl: string | null | undefined): string | null {
  if (!assetUrl) {
    return null;
  }
  const normalized = assetUrl.trim();
  if (/^https?:\/\//.test(normalized)) {
    return normalized;
  }
  if (normalized.startsWith("/static/") || normalized.startsWith("/uploads/")) {
    return `${new URL(API_BASE_URL).origin}${normalized}`;
  }
  return null;
}

export function titleMap(titles: GameLibraryTitle[]): Map<string, GameLibraryTitle> {
  return new Map(titles.map((title) => [title.title_code, title]));
}

async function apiGet<T>(
  path: string,
): Promise<{ ok: true; data: T } | { ok: false; message: string }> {
  try {
    const response = await fetch(`${API_FETCH_BASE_URL}${path}`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;
    if (!response.ok || !payload || payload.success !== true) {
      return {
        ok: false,
        message:
          payload && "error" in payload && payload.error?.message
            ? payload.error.message
            : `Public API returned ${response.status}`,
      };
    }
    return { ok: true, data: payload.data };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "Public API unavailable",
    };
  }
}
