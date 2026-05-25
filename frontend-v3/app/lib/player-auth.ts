"use client";

export const PLAYER_AUTH_EVENT = "player-auth-changed";

const PLAYER_AUTH_HANDOFF_KIND = "casinoking.player_auth_handoff";
const PLAYER_AUTH_HANDOFF_VERSION = 1;
const PLAYER_AUTH_HANDOFF_MAX_AGE_MS = 2 * 60 * 1000;

export const PLAYER_STORAGE_KEYS = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
} as const;

export type PlayerAuthSnapshot = {
  accessToken: string;
  email: string;
};

type PlayerAuthHandoff = {
  kind: typeof PLAYER_AUTH_HANDOFF_KIND;
  version: typeof PLAYER_AUTH_HANDOFF_VERSION;
  target_origin: string;
  issued_at: number;
  session: PlayerAuthSnapshot;
};

export function readPlayerAuthSnapshot(): PlayerAuthSnapshot {
  if (typeof window === "undefined") {
    return { accessToken: "", email: "" };
  }

  return {
    accessToken: window.localStorage.getItem(PLAYER_STORAGE_KEYS.accessToken) ?? "",
    email: window.localStorage.getItem(PLAYER_STORAGE_KEYS.email) ?? "",
  };
}

export function hasPlayerAuthSnapshot(snapshot = readPlayerAuthSnapshot()): boolean {
  return snapshot.accessToken.length > 0;
}

export function consumePlayerAuthHandoff(): PlayerAuthSnapshot | null {
  if (typeof window === "undefined" || !window.name) {
    return null;
  }

  let parsed: PlayerAuthHandoff | null = null;
  try {
    const value = JSON.parse(window.name) as Partial<PlayerAuthHandoff>;
    if (value.kind !== PLAYER_AUTH_HANDOFF_KIND || value.version !== PLAYER_AUTH_HANDOFF_VERSION) {
      return null;
    }
    parsed = value as PlayerAuthHandoff;
  } catch {
    return null;
  }

  window.name = "";

  if (parsed.target_origin !== window.location.origin) {
    return null;
  }
  if (!Number.isFinite(parsed.issued_at) || Date.now() - parsed.issued_at > PLAYER_AUTH_HANDOFF_MAX_AGE_MS) {
    return null;
  }
  if (!parsed.session?.accessToken || !parsed.session?.email) {
    return null;
  }

  window.localStorage.setItem(PLAYER_STORAGE_KEYS.accessToken, parsed.session.accessToken);
  window.localStorage.setItem(PLAYER_STORAGE_KEYS.email, parsed.session.email);
  window.dispatchEvent(new Event(PLAYER_AUTH_EVENT));
  return parsed.session;
}
