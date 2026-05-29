import { redirect } from "next/navigation";

type RedirectSearchParams = Record<string, string | string[] | undefined>;

const DEFAULT_SITE_V3_BASE_URL = "http://localhost:3000";

export function redirectToSiteV3(
  path: "/login" | "/register" | "/account",
  searchParams: RedirectSearchParams = {},
): never {
  const target = new URL(path, readSiteV3BaseUrl());
  appendSearchParams(target.searchParams, searchParams);
  redirect(target.toString());
}

function readSiteV3BaseUrl(): string {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.trim();
  if (!configuredBaseUrl) {
    return DEFAULT_SITE_V3_BASE_URL;
  }

  try {
    return new URL(configuredBaseUrl).toString();
  } catch {
    return DEFAULT_SITE_V3_BASE_URL;
  }
}

function appendSearchParams(target: URLSearchParams, source: RedirectSearchParams): void {
  Object.entries(source).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => target.append(key, item));
      return;
    }
    if (typeof value === "string") {
      target.append(key, value);
    }
  });
}
