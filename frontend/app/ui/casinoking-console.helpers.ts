export type LaunchPreset = {
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
};

export type QuickLaunchOption = {
  label: string;
  description: string;
  preset: LaunchPreset;
};

type MinesRuntimeLike = {
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
};

export function getGridSizes(config: MinesRuntimeLike | null): number[] {
  if (!config) {
    return [25];
  }
  return [...config.supported_grid_sizes].sort((a, b) => a - b);
}

export function getMineOptions(
  config: MinesRuntimeLike | null,
  gridSize: number,
): number[] {
  if (!config) {
    return [3];
  }

  return [...(config.supported_mine_counts[String(gridSize)] ?? [])].sort(
    (a, b) => a - b,
  );
}

export function getPayoutLadder(
  config: MinesRuntimeLike | null,
  gridSize: number,
  mineCount: number,
): string[] {
  if (!config) {
    return [];
  }

  return [...(config.payout_ladders[String(gridSize)]?.[String(mineCount)] ?? [])];
}

export function buildQuickLaunchOptions(
  runtimeConfig: MinesRuntimeLike | null,
): QuickLaunchOption[] {
  if (!runtimeConfig) {
    return [];
  }

  const gridSizes = getGridSizes(runtimeConfig);
  if (gridSizes.length === 0) {
    return [];
  }

  const lowGrid = gridSizes[0];
  const midGrid = gridSizes[Math.floor(gridSizes.length / 2)];
  const highGrid = gridSizes[gridSizes.length - 1];
  const lowMineOptions = getMineOptions(runtimeConfig, lowGrid);
  const midMineOptions = getMineOptions(runtimeConfig, midGrid);
  const highMineOptions = getMineOptions(runtimeConfig, highGrid);

  return [
    {
      label: "Quick start",
      description: "Low-friction entry to launch a first round fast.",
      preset: {
        grid_size: lowGrid,
        mine_count: lowMineOptions[0] ?? 1,
        bet_amount: "1.000000",
        wallet_type: "cash",
      },
    },
    {
      label: "Standard table",
      description: "Balanced setup for a normal real-play session.",
      preset: {
        grid_size: midGrid,
        mine_count:
          midMineOptions[Math.floor(midMineOptions.length / 2)] ?? midMineOptions[0] ?? 1,
        bet_amount: "5.000000",
        wallet_type: "cash",
      },
    },
    {
      label: "High volatility",
      description: "Higher risk preset when you want a sharper ladder.",
      preset: {
        grid_size: highGrid,
        mine_count: highMineOptions[highMineOptions.length - 1] ?? highMineOptions[0] ?? 1,
        bet_amount: "10.000000",
        wallet_type: "cash",
      },
    },
  ];
}
