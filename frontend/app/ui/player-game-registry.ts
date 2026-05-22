export type PlayerGameCode = "mines" | "boxe" | "hi_lo";

type PlayerGameRegistryEntry = {
  displayName: string;
  launchRoute: string;
};

export const PLAYER_GAME_REGISTRY: Record<PlayerGameCode, PlayerGameRegistryEntry> = {
  mines: {
    displayName: "Mines",
    launchRoute: "/mines",
  },
  boxe: {
    displayName: "BOXE",
    launchRoute: "/boxe",
  },
  hi_lo: {
    displayName: "HI-LO",
    launchRoute: "/hi-lo",
  },
};

export function isPlayerGameCode(gameCode: string): gameCode is PlayerGameCode {
  return gameCode in PLAYER_GAME_REGISTRY;
}

export function resolvePlayerGameDisplayName(gameCode: string | null | undefined): string {
  if (!gameCode) {
    return PLAYER_GAME_REGISTRY.mines.displayName;
  }
  if (isPlayerGameCode(gameCode)) {
    return PLAYER_GAME_REGISTRY[gameCode].displayName;
  }
  return gameCode.replace(/_/g, " ").toUpperCase();
}

export function resolvePlayerGameLaunchRoute(engineCode: string): string {
  if (isPlayerGameCode(engineCode)) {
    return PLAYER_GAME_REGISTRY[engineCode].launchRoute;
  }
  return `/${encodeURIComponent(engineCode)}`;
}
