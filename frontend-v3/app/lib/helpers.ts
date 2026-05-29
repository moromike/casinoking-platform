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

export function formatWholeChipDisplay(
  value: string | number | null | undefined,
  chipSuffix = "CHIP",
): string {
  const numericValue =
    typeof value === "number" ? value : value ? Number.parseFloat(value) : 0;
  const safeValue = Number.isFinite(numericValue) ? numericValue : 0;
  return `${Math.max(0, safeValue).toFixed(2)} ${chipSuffix}`;
}
