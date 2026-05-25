/**
 * Shared API client for CasinoKing platform.
 *
 * Shared by admin, player, and game runtime modules. Keep request error
 * handling centralized here so UI surfaces get consistent validation messages.
 */

import type { ApiEnvelope } from "@/app/lib/types";
import { extractValidationMessage } from "@/app/lib/helpers";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

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

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    payload = null;
  }

  if (!response.ok || !payload || payload.success === false) {
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

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    payload = null;
  }

  if (!response.ok || !payload || payload.success === false) {
    throw buildApiRequestError(payload, response);
  }

  return payload.data;
}

export async function apiDeleteRequest<T>(
  path: string,
  token?: string,
): Promise<T> {
  return apiRequest<T>(path, { method: "DELETE" }, token);
}

export function resolveBackendAssetUrl(assetUrl: string): string {
  if (!assetUrl.startsWith("/static/games/")) {
    return assetUrl;
  }
  const apiBase = new URL(API_BASE_URL);
  return `${apiBase.origin}${assetUrl}`;
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
    return new ApiRequestError(
      platformError.message,
      platformError.code,
      response.status,
      {
        details: platformError.details,
        requestId: platformError.requestId ?? requestId,
        retryable: platformError.retryable,
        supportId: platformError.supportId,
      },
    );
  }

  if (payload && typeof payload === "object" && "detail" in payload) {
    return new ApiRequestError(
      extractValidationMessage(payload.detail),
      "VALIDATION_ERROR",
      response.status,
      { requestId },
    );
  }

  return new ApiRequestError(
    "Unexpected API response",
    "API_ERROR",
    response.status,
    { requestId },
  );
}

function readPlatformError<T>(payload: ApiEnvelope<T> | null): {
  code: string;
  details?: unknown;
  message: string;
  requestId?: string;
  retryable?: boolean;
  supportId?: string;
} | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  if (payload.success === false) {
    return normalizeApiError(payload.error);
  }
  if ("detail" in payload && isNestedErrorEnvelope(payload.detail)) {
    return normalizeApiError(payload.detail.error);
  }
  return null;
}

function normalizeApiError(error: unknown): {
  code: string;
  details?: unknown;
  message: string;
  requestId?: string;
  retryable?: boolean;
  supportId?: string;
} | null {
  if (!error || typeof error !== "object") {
    return null;
  }
  const record = error as Record<string, unknown>;
  if (typeof record.code !== "string" || typeof record.message !== "string") {
    return null;
  }
  return {
    code: record.code,
    details: record.details,
    message: record.message,
    requestId: typeof record.request_id === "string" ? record.request_id : undefined,
    retryable: typeof record.retryable === "boolean" ? record.retryable : undefined,
    supportId: typeof record.support_id === "string" ? record.support_id : undefined,
  };
}

function isNestedErrorEnvelope(value: unknown): value is {
  success: false;
  error: unknown;
} {
  return (
    value !== null &&
    typeof value === "object" &&
    (value as { success?: unknown }).success === false &&
    "error" in value
  );
}
