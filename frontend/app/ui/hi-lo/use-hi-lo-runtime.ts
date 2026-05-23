"use client";

import { apiRequest } from "@/app/lib/api";
import type { Wallet } from "@/app/lib/types";

export type HiLoRuntimeConfig = {
  game_code: "hi_lo";
  title_code: string;
  rtp_label: string;
  active_skip_limit: number;
  actions: HiLoPredictionAction[];
  fairness_version: string;
  copy_refs: Record<string, string>;
  presentation_config?: {
    default_locale?: string;
    rules_html?: Record<string, Partial<Record<string, string | { body_html?: string }>>>;
  };
};

export type HiLoPredictionAction = "black" | "red" | "down" | "up";
export type HiLoWalletSource = "cash" | "bonus" | "demo";
export type HiLoRoundStatus =
  | "created"
  | "active"
  | "cashout_pending"
  | "completed_cashout"
  | "failed_prediction"
  | "expired"
  | "quarantined";

export type HiLoCard = {
  rank: number;
  rank_label: string;
  suit: "clubs" | "spades" | "hearts" | "diamonds";
  color: "black" | "red";
};

export type HiLoQuote = {
  action: HiLoPredictionAction;
  label: string;
  probability: string;
  probability_percent: string;
  multiplier: string;
  cumulative_success_probability_after_success: string;
};

export type HiLoRoundResponse = {
  game_code: "hi_lo";
  session_id: string;
  round_id: string;
  title_code: string;
  site_code: string;
  event: "start" | "prediction" | "active_skip" | "cashout";
  status: HiLoRoundStatus;
  wallet_source: HiLoWalletSource;
  bet_amount: string;
  current_card: HiLoCard;
  previous_card: HiLoCard | null;
  drawn_card: HiLoCard | null;
  quotes: HiLoQuote[];
  correct_predictions_count: number;
  active_skip_count: number;
  active_skip_limit: number;
  cumulative_success_probability: string;
  multiplier_current: string;
  payout_current: string;
  final_payout_amount: string | null;
  outcome: "cashout" | "loss" | "expired" | "quarantined" | null;
  terminal: boolean;
  prediction: {
    action: HiLoPredictionAction;
    label: string;
    success: boolean;
    probability: string;
  } | null;
  settlement: {
    wallet_balance_after?: string;
    ledger_transaction_id?: string | null;
    already_exists?: boolean;
  } | null;
  server_seed_hash: string;
  fairness_version: string;
  table_session_id?: string | null;
  table_session?: HiLoTableSession | null;
  wallet_balance_after_start?: string | null;
};

export type HiLoTableSessionLimits = {
  wallet_balance_available: string;
  table_session_max_chips: string;
  default_table_amount: string;
  max_table_amount: string;
};

export type HiLoAccessSession = {
  id: string;
  user_id: string;
  game_code: string;
  title_code: string;
  site_code: string;
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  status: "active" | "closed" | "timed_out";
};

export type HiLoTableSession = {
  id: string;
  access_session_id: string | null;
  game_code: string;
  title_code: string;
  site_code: string;
  wallet_type: "cash" | "bonus";
  table_budget_amount: string;
  table_balance_amount: string;
  loss_limit_amount: string;
  loss_reserved_amount: string;
  loss_consumed_amount: string;
  loss_remaining_amount: string;
  status: "active" | "closed" | "timed_out";
};

export type HiLoDemoPlayerAuth = {
  user_id: string;
  email: string;
  access_token: string;
  token_type: "bearer";
};

export async function loadHiLoRuntimeConfig(titleCode: string): Promise<HiLoRuntimeConfig> {
  const params = new URLSearchParams({ title_code: titleCode });
  return apiRequest<HiLoRuntimeConfig>(`/games/hi-lo/config?${params.toString()}`);
}

export async function provisionHiLoDemoPlayer(): Promise<HiLoDemoPlayerAuth> {
  return apiRequest<HiLoDemoPlayerAuth>("/auth/demo", { method: "POST" });
}

export async function loadHiLoWallets(token: string): Promise<Wallet[]> {
  return apiRequest<Wallet[]>("/wallets", {}, token);
}

export async function loadHiLoTableSessionLimits(
  token: string,
  walletType: "cash" | "bonus",
): Promise<HiLoTableSessionLimits> {
  return apiRequest<HiLoTableSessionLimits>(
    `/table-sessions/limits?wallet_type=${walletType}&game_code=hi_lo`,
    {},
    token,
  );
}

export async function createHiLoAccessSession(input: {
  titleCode: string;
  token: string;
}): Promise<HiLoAccessSession> {
  return apiRequest<HiLoAccessSession>(
    "/access-sessions",
    {
      method: "POST",
      body: JSON.stringify({
        game_code: "hi_lo",
        title_code: input.titleCode,
        site_code: "casinoking",
      }),
    },
    input.token,
  );
}

export async function createHiLoTableSession(input: {
  titleCode: string;
  walletType: "cash" | "bonus";
  tableBudgetAmount: string;
  accessSessionId: string;
  token: string;
}): Promise<HiLoTableSession> {
  return apiRequest<HiLoTableSession>(
    "/table-sessions",
    {
      method: "POST",
      body: JSON.stringify({
        game_code: "hi_lo",
        title_code: input.titleCode,
        site_code: "casinoking",
        wallet_type: input.walletType,
        table_budget_amount: input.tableBudgetAmount,
        access_session_id: input.accessSessionId,
      }),
    },
    input.token,
  );
}

export async function startHiLoRound(input: {
  titleCode: string;
  betAmount: string;
  walletSource: HiLoWalletSource;
  token: string;
  idempotencyKey: string;
  tableSessionId?: string | null;
  accessSessionId?: string | null;
}): Promise<HiLoRoundResponse> {
  return apiRequest<HiLoRoundResponse>(
    "/games/hi-lo/start",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({
        title_code: input.titleCode,
        bet_amount: input.betAmount,
        wallet_source: input.walletSource,
        client_seed: `hi-lo-ui:${input.idempotencyKey}`,
        table_session_id: input.tableSessionId ?? null,
        access_session_id: input.accessSessionId ?? null,
      }),
    },
    input.token,
  );
}

export async function predictHiLoRound(input: {
  roundId: string;
  action: HiLoPredictionAction;
  token: string;
  idempotencyKey: string;
}): Promise<HiLoRoundResponse> {
  return apiRequest<HiLoRoundResponse>(
    "/games/hi-lo/predict",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({
        round_id: input.roundId,
        action: input.action,
      }),
    },
    input.token,
  );
}

export async function skipHiLoRound(input: {
  roundId: string;
  token: string;
  idempotencyKey: string;
}): Promise<HiLoRoundResponse> {
  return apiRequest<HiLoRoundResponse>(
    "/games/hi-lo/skip",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({ round_id: input.roundId }),
    },
    input.token,
  );
}

export async function cashoutHiLoRound(input: {
  roundId: string;
  token: string;
  idempotencyKey: string;
}): Promise<HiLoRoundResponse> {
  return apiRequest<HiLoRoundResponse>(
    "/games/hi-lo/cashout",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({ round_id: input.roundId }),
    },
    input.token,
  );
}
