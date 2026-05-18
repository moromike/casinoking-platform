export const ALLOWED_GAME_NAMESPACES = ["mines", "boxe"] as const;
export type GameStorageNamespace = (typeof ALLOWED_GAME_NAMESPACES)[number];

export const MINES_GAME_STORAGE_NAMESPACE: GameStorageNamespace = "mines";
export const BOXE_GAME_STORAGE_NAMESPACE: GameStorageNamespace = "boxe";

type GameStorageKeys = {
  accessToken: string;
  email: string;
  sessionId: string;
  gameLaunchToken: string;
  gameLaunchTokenExpiresAt: string;
  gameLaunchTitleCode: string;
  demoAnonToken: string;
  demoGameLaunchToken: string;
  demoGameLaunchTokenExpiresAt: string;
  demoGameLaunchTitleCode: string;
  demoChipBalance: string;
  legacyTableSessionId: string;
};

const MINES_STORAGE_KEYS: GameStorageKeys = {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.current_session_id",
  gameLaunchToken: "casinoking.mines_launch_token",
  gameLaunchTokenExpiresAt: "casinoking.mines_launch_token_expires_at",
  gameLaunchTitleCode: "casinoking.mines_launch_title_code",
  demoAnonToken: "ck_demo_anon_token",
  demoGameLaunchToken: "ck_demo_game_launch_token",
  demoGameLaunchTokenExpiresAt: "ck_demo_game_launch_token_expires_at",
  demoGameLaunchTitleCode: "ck_demo_game_launch_title_code",
  demoChipBalance: "ck_demo_chip_balance",
  legacyTableSessionId: "casinoking.mines_table_session_id",
} as const;

const GAME_STORAGE_KEYS: Record<GameStorageNamespace, GameStorageKeys> = {
  mines: MINES_STORAGE_KEYS,
  boxe: {
    accessToken: "casinoking.access_token",
    email: "casinoking.email",
    sessionId: "casinoking.boxe_current_session_id",
    gameLaunchToken: "casinoking.boxe_launch_token",
    gameLaunchTokenExpiresAt: "casinoking.boxe_launch_token_expires_at",
    gameLaunchTitleCode: "casinoking.boxe_launch_title_code",
    demoAnonToken: "ck_boxe_demo_anon_token",
    demoGameLaunchToken: "ck_boxe_demo_game_launch_token",
    demoGameLaunchTokenExpiresAt: "ck_boxe_demo_game_launch_token_expires_at",
    demoGameLaunchTitleCode: "ck_boxe_demo_game_launch_title_code",
    demoChipBalance: "ck_boxe_demo_chip_balance",
    legacyTableSessionId: "casinoking.boxe_table_session_id",
  },
};

export function isAllowedGameStorageNamespace(
  namespace: string,
): namespace is GameStorageNamespace {
  return (ALLOWED_GAME_NAMESPACES as readonly string[]).includes(namespace);
}

export function getGameStorageKeys(namespace: string): GameStorageKeys {
  if (!isAllowedGameStorageNamespace(namespace)) {
    throw new Error(`Unsupported game storage namespace: ${namespace}`);
  }
  return GAME_STORAGE_KEYS[namespace];
}

export function readGameStorageSnapshot(storage: Storage, namespace: string) {
  const keys = getGameStorageKeys(namespace);
  return {
    accessToken: storage.getItem(keys.accessToken) ?? "",
    email: storage.getItem(keys.email) ?? "",
    sessionId: storage.getItem(keys.sessionId),
    gameLaunchToken: storage.getItem(keys.gameLaunchToken) ?? "",
    gameLaunchTokenExpiresAt: storage.getItem(keys.gameLaunchTokenExpiresAt) ?? "",
    gameLaunchTitleCode: storage.getItem(keys.gameLaunchTitleCode) ?? "",
    demoAnonToken: storage.getItem(keys.demoAnonToken) ?? "",
    demoGameLaunchToken: storage.getItem(keys.demoGameLaunchToken) ?? "",
    demoGameLaunchTokenExpiresAt: storage.getItem(keys.demoGameLaunchTokenExpiresAt) ?? "",
    demoGameLaunchTitleCode: storage.getItem(keys.demoGameLaunchTitleCode) ?? "",
    demoChipBalance: storage.getItem(keys.demoChipBalance) ?? "",
  };
}

export function clearLegacyGameStorage(storage: Storage, namespace: string) {
  storage.removeItem(getGameStorageKeys(namespace).legacyTableSessionId);
}

export function clearStoredRealLaunchToken(storage: Storage, namespace: string) {
  const keys = getGameStorageKeys(namespace);
  storage.removeItem(keys.gameLaunchToken);
  storage.removeItem(keys.gameLaunchTokenExpiresAt);
  storage.removeItem(keys.gameLaunchTitleCode);
}

export function writeStoredRealLaunchToken(
  storage: Storage,
  namespace: string,
  token: string,
  expiresAt: string,
  titleCode: string,
) {
  const keys = getGameStorageKeys(namespace);
  storage.setItem(keys.gameLaunchToken, token);
  storage.setItem(keys.gameLaunchTokenExpiresAt, expiresAt);
  storage.setItem(keys.gameLaunchTitleCode, titleCode);
}

export function clearStoredDemoLaunchToken(storage: Storage, namespace: string) {
  const keys = getGameStorageKeys(namespace);
  storage.removeItem(keys.demoGameLaunchToken);
  storage.removeItem(keys.demoGameLaunchTokenExpiresAt);
  storage.removeItem(keys.demoGameLaunchTitleCode);
}

export function writeStoredDemoLaunchToken(
  storage: Storage,
  namespace: string,
  token: string,
  expiresAt: string,
  titleCode: string,
) {
  const keys = getGameStorageKeys(namespace);
  storage.setItem(keys.demoGameLaunchToken, token);
  storage.setItem(keys.demoGameLaunchTokenExpiresAt, expiresAt);
  storage.setItem(keys.demoGameLaunchTitleCode, titleCode);
}

export function writeStoredDemoAnonToken(storage: Storage, namespace: string, token: string) {
  storage.setItem(getGameStorageKeys(namespace).demoAnonToken, token);
}

export function clearStoredDemoChipBalance(storage: Storage, namespace: string) {
  storage.removeItem(getGameStorageKeys(namespace).demoChipBalance);
}

export function writeStoredDemoChipBalance(storage: Storage, namespace: string, balance: string) {
  storage.setItem(getGameStorageKeys(namespace).demoChipBalance, balance);
}

export function clearStoredSessionId(storage: Storage, namespace: string) {
  storage.removeItem(getGameStorageKeys(namespace).sessionId);
}

export function writeStoredSessionId(storage: Storage, namespace: string, sessionId: string) {
  storage.setItem(getGameStorageKeys(namespace).sessionId, sessionId);
}

export function clearStoredAuthState(storage: Storage, namespace: string) {
  const keys = getGameStorageKeys(namespace);
  storage.removeItem(keys.accessToken);
  storage.removeItem(keys.gameLaunchToken);
  storage.removeItem(keys.gameLaunchTokenExpiresAt);
  storage.removeItem(keys.email);
  storage.removeItem(keys.sessionId);
}
