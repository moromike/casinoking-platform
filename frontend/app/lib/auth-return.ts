export function sanitizeAuthReturnTo(value: string | null): string | null {
  if (!value) {
    return null;
  }

  try {
    if (value.startsWith("/") && !value.startsWith("//")) {
      return value;
    }

    const url = new URL(value);
    return allowedAuthReturnOrigins().has(url.origin) ? url.toString() : null;
  } catch {
    return null;
  }
}

export function withAuthReturnTo(href: string, returnTo: string | null): string {
  if (!returnTo) {
    return href;
  }

  const separator = href.includes("?") ? "&" : "?";
  return `${href}${separator}return_to=${encodeURIComponent(returnTo)}`;
}

function allowedAuthReturnOrigins(): Set<string> {
  const origins = new Set<string>();
  if (typeof window !== "undefined") {
    origins.add(window.location.origin);
  }

  [
    process.env.NEXT_PUBLIC_SITE_V3_BASE_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
  ].forEach((origin) => {
    if (!origin) {
      return;
    }
    try {
      origins.add(new URL(origin).origin);
    } catch {
      // Ignore invalid local development configuration.
    }
  });

  return origins;
}
