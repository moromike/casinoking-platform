import type {
  ApiEnvelope,
  GameLibrary,
  SiteHomeResponse,
  SiteV3LoadResult,
  SiteV3Navigation,
  SiteV3PublicPageSnapshot,
} from "./types";
import { API_FETCH_BASE_URL } from "./api";

type DraftPreviewClaims = {
  typ?: string;
  site_code?: string;
  page_code?: string;
  locale?: string;
};

export async function loadSiteV3Preview(token: string): Promise<SiteV3LoadResult> {
  const claims = decodeDraftPreviewClaims(token);
  if (!claims.site_code || !claims.page_code || !claims.locale) {
    return {
      page: null,
      navigation: null,
      gameLibrary: [],
      homeSlots: [],
      error: "Preview token is invalid or expired",
    };
  }

  const [pageResult, navigationResult, libraryResult, homeResult] = await Promise.all([
    apiGet<SiteV3PublicPageSnapshot>(
      `/site-v3/sites/${encodeURIComponent(claims.site_code)}/pages/${encodeURIComponent(
        claims.page_code,
      )}/preview-draft?locale=${encodeURIComponent(claims.locale)}`,
      { "X-Draft-Preview-Token": token },
    ),
    apiGet<SiteV3Navigation>(
      `/site-v3/sites/${encodeURIComponent(claims.site_code)}/navigation?locale=${encodeURIComponent(claims.locale)}`,
    ),
    apiGet<GameLibrary>(`/games/library?site_code=${encodeURIComponent(claims.site_code)}`),
    apiGet<SiteHomeResponse>(`/site/home?site_code=${encodeURIComponent(claims.site_code)}`),
  ]);

  return {
    page: pageResult.ok ? pageResult.data : null,
    navigation: navigationResult.ok ? navigationResult.data : null,
    gameLibrary: libraryResult.ok ? libraryResult.data.titles : [],
    homeSlots: homeResult.ok ? homeResult.data.slots : [],
    error: pageResult.ok ? null : pageResult.message,
  };
}

function decodeDraftPreviewClaims(token: string): DraftPreviewClaims {
  try {
    const [, payload] = token.split(".");
    if (!payload) {
      return {};
    }
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const decoded = JSON.parse(Buffer.from(padded, "base64").toString("utf-8")) as DraftPreviewClaims;
    if (decoded.typ !== "site_v3_draft_preview") {
      return {};
    }
    return decoded;
  } catch {
    return {};
  }
}

async function apiGet<T>(
  path: string,
  headers: Record<string, string> = {},
): Promise<{ ok: true; data: T } | { ok: false; message: string }> {
  try {
    const response = await fetch(`${API_FETCH_BASE_URL}${path}`, {
      cache: "no-store",
      headers: { Accept: "application/json", ...headers },
    });
    const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;
    if (!response.ok || !payload || payload.success !== true) {
      return {
        ok: false,
        message:
          payload && "error" in payload && payload.error?.message
            ? payload.error.message
            : `Preview API returned ${response.status}`,
      };
    }
    return { ok: true, data: payload.data };
  } catch (error) {
    return {
      ok: false,
      message: error instanceof Error ? error.message : "Preview API unavailable",
    };
  }
}
