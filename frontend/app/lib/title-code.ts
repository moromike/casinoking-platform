export const TITLE_CODE_HELPER_TEXT =
  "3-64 caratteri: a-z, 0-9, underscore. Spazi e trattini diventano underscore.";

export const TITLE_CODE_PATTERN = /^[a-z0-9_]{3,64}$/;

export function normalizeTitleCodeInput(rawValue: string): string {
  return rawValue
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/_+/g, "_")
    .slice(0, 64);
}

export function isTitleCodeValid(value: string): boolean {
  return TITLE_CODE_PATTERN.test(value);
}
