import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";

export const PLAYER_AUTH_EVENT = "player-auth-changed";

export function readStoredString(key: string): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

export function hasStoredPlayerAccessToken(): boolean {
  return readStoredString(PLAYER_STORAGE_KEYS.accessToken).length > 0;
}

export function storePlayerAuthSession({
  accessToken,
  email,
  firstName,
  lastName,
  fiscalCode,
  phoneNumber,
}: {
  accessToken: string;
  email: string;
  firstName?: string;
  lastName?: string;
  fiscalCode?: string;
  phoneNumber?: string;
}) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(PLAYER_STORAGE_KEYS.accessToken, accessToken);
  window.localStorage.setItem(PLAYER_STORAGE_KEYS.email, email);

  const optionalValues = [
    [PLAYER_STORAGE_KEYS.firstName, firstName],
    [PLAYER_STORAGE_KEYS.lastName, lastName],
    [PLAYER_STORAGE_KEYS.fiscalCode, fiscalCode],
    [PLAYER_STORAGE_KEYS.phoneNumber, phoneNumber],
  ] as const;

  optionalValues.forEach(([key, value]) => {
    if (value && value.trim().length > 0) {
      window.localStorage.setItem(key, value);
      return;
    }

    window.localStorage.removeItem(key);
  });
}

export function clearPlayerAuthStorage() {
  if (typeof window === "undefined") {
    return;
  }

  Object.values(PLAYER_STORAGE_KEYS).forEach((key) => {
    window.localStorage.removeItem(key);
  });
}

export function dispatchPlayerAuthChanged() {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(PLAYER_AUTH_EVENT));
}

export function readStoredPlayerAuthSnapshot() {
  return {
    accessToken: readStoredString(PLAYER_STORAGE_KEYS.accessToken),
    email: readStoredString(PLAYER_STORAGE_KEYS.email),
    firstName: readStoredString(PLAYER_STORAGE_KEYS.firstName),
  };
}
