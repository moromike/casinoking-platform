"use client";

export function bootLog(event: string, payload?: Record<string, unknown>) {
  if (process.env.NODE_ENV !== "development" || typeof window === "undefined") {
    return;
  }

  const target = window as typeof window & {
    __casinoKingBootLog?: Array<{ event: string; payload?: Record<string, unknown> }>;
  };
  if (!Array.isArray(target.__casinoKingBootLog)) {
    target.__casinoKingBootLog = [];
  }

  target.__casinoKingBootLog.push(payload === undefined ? { event } : { event, payload });
}
