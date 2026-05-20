import { ApiRequestError } from "@/app/lib/api";

export type GameErrorKind =
  | "auth_invalid"
  | "validation"
  | "insufficient_balance"
  | "bonus_wallet_empty"
  | "round_closed"
  | "network"
  | "service_unavailable"
  | "reload_required"
  | "generic";

export type GameErrorCopyMap = Partial<Record<GameErrorKind, string>> & {
  generic: string;
};

const AUTH_BACKEND_MESSAGE_PATTERN =
  /\b(bearer token|authenticated user|account is not active)\b/i;

export function classifyGameError(error: unknown): GameErrorKind {
  if (error instanceof ApiRequestError) {
    const code = error.code.toUpperCase();
    if (error.status === 401) {
      return "auth_invalid";
    }
    if (error.status === 403 && AUTH_BACKEND_MESSAGE_PATTERN.test(error.message)) {
      return "auth_invalid";
    }
    if (error.status === 422 || code === "VALIDATION_ERROR") {
      return "validation";
    }
    if (code === "INSUFFICIENT_BALANCE") {
      return "insufficient_balance";
    }
    if (code === "BONUS_WALLET_EMPTY") {
      return "bonus_wallet_empty";
    }
    if (code === "ROUND_ALREADY_CLOSED" || code === "ROUND_CLOSED") {
      return "round_closed";
    }
    if (error.status >= 500) {
      return "service_unavailable";
    }
    return "generic";
  }

  if (isNetworkRequestFailure(error)) {
    return "network";
  }

  return "generic";
}

export function buildGameErrorMessage(
  error: unknown,
  copyMap: GameErrorCopyMap,
): string {
  const kind = classifyGameError(error);
  return copyMap[kind] ?? copyMap.generic;
}

export function isBearerTokenAuthError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.status === 401 &&
    AUTH_BACKEND_MESSAGE_PATTERN.test(error.message)
  );
}

export function isNetworkRequestFailure(error: unknown): boolean {
  if (error instanceof TypeError) {
    return true;
  }
  if (!(error instanceof Error)) {
    return false;
  }
  return /failed to fetch|networkerror|network request|load failed/i.test(error.message);
}
