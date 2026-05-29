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

export class ApiRequestError extends Error {
  code: string;
  details?: unknown;
  requestId?: string;
  retryable?: boolean;
  status: number;
  supportId?: string;

  constructor(
    message: string,
    code: string,
    status: number,
    options: {
      details?: unknown;
      requestId?: string;
      retryable?: boolean;
      supportId?: string;
    } = {},
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.details = options.details;
    this.requestId = options.requestId;
    this.retryable = options.retryable;
    this.status = status;
    this.supportId = options.supportId;
  }
}

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

export async function loadGameLibraryTitles(siteCode: string): Promise<GameLibraryTitle[]> {
  const libraryResult = await apiGet<GameLibrary>(
    `/games/library?site_code=${encodeURIComponent(siteCode)}`,
  );
  return libraryResult.ok ? libraryResult.data.titles : [];
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

export function resolveBackendAssetUrl(publicUrl: string): string {
  const normalized = publicUrl.trim();
  if (!normalized.startsWith("/static/games/")) {
    return normalized;
  }
  return `${new URL(API_BASE_URL).origin}${normalized}`;
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

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const payload = await apiEnvelopeRequest<T>(path, init, token);
  return payload.data;
}

export async function apiEnvelopeRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<Extract<ApiEnvelope<T>, { success: true }>> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;
  if (!response.ok || !payload || payload.success !== true) {
    throw buildApiRequestError(payload, response);
  }

  return payload;
}

export async function apiFormRequest<T>(
  path: string,
  formData: FormData,
  token?: string,
): Promise<T> {
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
    headers,
    cache: "no-store",
  });

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;
  if (!response.ok || !payload || payload.success !== true) {
    throw buildApiRequestError(payload, response);
  }

  return payload.data;
}

export function readErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    return `${fallback} ${error.message}`;
  }
  if (error instanceof Error) {
    return `${fallback} ${error.message}`;
  }
  return fallback;
}

function buildApiRequestError<T>(
  payload: ApiEnvelope<T> | null,
  response: Response,
): ApiRequestError {
  const requestId = response.headers.get("X-Request-ID") ?? undefined;
  const platformError = readPlatformError(payload);
  if (platformError) {
    return new ApiRequestError(platformError.message, platformError.code, response.status, {
      details: platformError.details,
      requestId: platformError.requestId ?? requestId,
      retryable: platformError.retryable,
      supportId: platformError.supportId,
    });
  }

  if (payload && typeof payload === "object" && "detail" in payload) {
    return new ApiRequestError(extractValidationMessage(payload.detail), "VALIDATION_ERROR", response.status, {
      requestId,
    });
  }

  return new ApiRequestError("Unexpected API response", "API_ERROR", response.status, {
    requestId,
  });
}

function readPlatformError<T>(payload: ApiEnvelope<T> | null): {
  code: string;
  details?: unknown;
  message: string;
  requestId?: string;
  retryable?: boolean;
  supportId?: string;
} | null {
  if (!payload || typeof payload !== "object" || payload.success !== false || !payload.error) {
    return null;
  }
  if (typeof payload.error.code !== "string" || typeof payload.error.message !== "string") {
    return null;
  }
  return {
    code: payload.error.code,
    details: payload.error.details,
    message: payload.error.message,
    requestId: payload.error.request_id,
    retryable: payload.error.retryable,
    supportId: payload.error.support_id,
  };
}

function extractValidationMessage(detail: unknown): string {
  if (Array.isArray(detail) && detail.length > 0) {
    const firstError = detail[0];
    if (
      firstError &&
      typeof firstError === "object" &&
      "msg" in firstError &&
      typeof firstError.msg === "string"
    ) {
      const location =
        "loc" in firstError && Array.isArray(firstError.loc)
          ? firstError.loc
              .filter((item: unknown): item is string | number =>
                typeof item === "string" || typeof item === "number",
              )
              .join(".")
          : null;
      return location ? `${location}: ${firstError.msg}` : firstError.msg;
    }
  }

  if (typeof detail === "string" && detail) {
    return detail;
  }

  return "Request validation failed";
}
