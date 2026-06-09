import type { MinesRuntimeLike, SessionSnapshot, StatusKind } from "./types";

export type LaunchPreset = {
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
};

export function getGridSizes(config: MinesRuntimeLike | null): number[] {
  if (!config) {
    return [25];
  }
  const publishedGridSizes = config.presentation_config?.published_grid_sizes ?? [];
  return [...(publishedGridSizes.length > 0 ? publishedGridSizes : config.supported_grid_sizes)].sort(
    (a, b) => a - b,
  );
}

export function getVisibleGridSizes(
  config: MinesRuntimeLike | null,
  preferredGridSize?: number,
): number[] {
  const allOptions = getGridSizes(config);
  if (allOptions.length <= 5) {
    return allOptions;
  }

  const lastIndex = allOptions.length - 1;
  const sampledIndices = new Set<number>();
  for (let index = 0; index < 5; index += 1) {
    sampledIndices.add(Math.round((index * lastIndex) / 4));
  }

  const sampledOptions = [...sampledIndices]
    .sort((a, b) => a - b)
    .map((index) => allOptions[index]);

  if (
    preferredGridSize === undefined ||
    sampledOptions.includes(preferredGridSize) ||
    !allOptions.includes(preferredGridSize)
  ) {
    return sampledOptions;
  }

  const candidateReplaceIndex = sampledOptions.findIndex(
    (option) => option > preferredGridSize,
  );
  const replaceIndex =
    candidateReplaceIndex <= 0 ? sampledOptions.length - 2 : candidateReplaceIndex;
  sampledOptions[replaceIndex] = preferredGridSize;
  return [...new Set(sampledOptions)].sort((a, b) => a - b);
}

export function getMineOptions(
  config: MinesRuntimeLike | null,
  gridSize: number,
): number[] {
  if (!config) {
    return [3];
  }

  const publishedMineCounts = config.presentation_config?.published_mine_counts[String(gridSize)] ?? [];
  return [...(publishedMineCounts.length > 0 ? publishedMineCounts : config.supported_mine_counts[String(gridSize)] ?? [])].sort(
    (a, b) => a - b,
  );
}

export function getVisibleMineOptions(
  config: MinesRuntimeLike | null,
  gridSize: number,
  preferredMineCount?: number,
): number[] {
  const allOptions = getMineOptions(config, gridSize);
  if (allOptions.length <= 5) {
    return allOptions;
  }

  const lastIndex = allOptions.length - 1;
  const sampledIndices = new Set<number>();
  for (let index = 0; index < 5; index += 1) {
    sampledIndices.add(Math.round((index * lastIndex) / 4));
  }

  const sampledOptions = [...sampledIndices]
    .sort((a, b) => a - b)
    .map((index) => allOptions[index]);

  if (
    preferredMineCount === undefined ||
    sampledOptions.includes(preferredMineCount) ||
    !allOptions.includes(preferredMineCount)
  ) {
    return sampledOptions;
  }

  const candidateReplaceIndex = sampledOptions.findIndex(
    (option) => option > preferredMineCount,
  );
  const replaceIndex =
    candidateReplaceIndex <= 0 ? sampledOptions.length - 2 : candidateReplaceIndex;
  sampledOptions[replaceIndex] = preferredMineCount;
  return [...new Set(sampledOptions)].sort((a, b) => a - b);
}

export function getDefaultVisibleMineCount(
  config: MinesRuntimeLike | null,
  gridSize: number,
  preferredMineCount?: number,
): number {
  const publishedDefault = config?.presentation_config?.default_mine_counts[String(gridSize)];
  if (
    publishedDefault !== undefined &&
    getMineOptions(config, gridSize).includes(publishedDefault)
  ) {
    return publishedDefault;
  }

  const visibleOptions = getVisibleMineOptions(config, gridSize, preferredMineCount);
  if (visibleOptions.length === 0) {
    return preferredMineCount ?? 3;
  }

  return visibleOptions[Math.floor(visibleOptions.length / 2)];
}

export function getRulesSections(config: MinesRuntimeLike | null): Record<string, string> {
  const i18nRules = config?.presentation_config?.i18n?.rules_sections;
  if (i18nRules) {
    return Object.fromEntries(
      Object.entries(i18nRules)
        .map(([key, section]) => [key, section?.body_html])
        .filter((entry): entry is [string, string] => typeof entry[1] === "string"),
    );
  }
  return config?.presentation_config?.rules_sections ?? {};
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

export function truncateValue(value: string, size: number): string {
  if (value.length <= size) {
    return value;
  }
  return `${value.slice(0, size)}...`;
}

export function shortId(value: string): string {
  return value.slice(0, 8);
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function toNumericAmount(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatChipAmount(value: number): string {
  return value.toFixed(2);
}

export function isValidAmount(value: string): boolean {
  if (!/^\d+(\.\d{1,6})?$/.test(value)) {
    return false;
  }

  return Number(value) > 0;
}

export function extractValidationMessage(detail: unknown): string {
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

export function normalizeWholeChipInput(value: string): string {
  const digitsOnly = value.replace(/[^\d]/g, "");
  return digitsOnly.replace(/^0+(?=\d)/, "").slice(0, 6);
}

export function formatWholeChipDisplay(
  value: string | number | null | undefined,
  chipSuffix = "CHIP",
): string {
  const numericValue =
    typeof value === "number" ? value : value ? Number.parseFloat(value) : 0;
  const safeValue = Number.isFinite(numericValue) ? numericValue : 0;
  return `${Math.max(0, safeValue).toFixed(2)} ${chipSuffix}`;
}

export function formatGridChoiceLabel(
  gridSize: number,
  formatCells?: (cellCount: number) => string,
): string {
  const side = Math.sqrt(gridSize);
  return Number.isInteger(side) ? `${side}x${side}` : formatCells?.(gridSize) ?? `${gridSize} cells`;
}

export function isExpiredIsoDate(value: string): boolean {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return true;
  }
  return parsed <= Date.now();
}

export function sessionStatusKind(status: SessionSnapshot["status"]): StatusKind {
  if (status === "won") {
    return "success";
  }
  if (status === "lost") {
    return "error";
  }
  return "info";
}
