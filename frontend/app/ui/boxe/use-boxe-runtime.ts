"use client";

import { apiRequest } from "@/app/lib/api";
import type { Wallet } from "@/app/lib/types";

export type BoxeRuntimeConfig = {
  game_code: "boxe";
  title_code: string;
  default_rows: number;
  rows_enabled: number[];
  default_difficulty: string;
  difficulty_enabled: string[];
  rtp_label: string;
  multiplier_paths: Record<string, Record<string, string[]>>;
  copy_refs: Record<string, string>;
  presentation_config?: {
    default_locale: string;
    copy: Record<string, Record<string, string>>;
    rules_html: Record<string, Record<string, string>>;
  };
};

export type BoxeStartRoundResponse = {
  session_id: string;
  round_id: string;
  multipliers: string[];
  status: BoxeRoundStatus;
  server_seed_hash: string;
};

export type BoxeRevealOutcome = "safe" | "mine" | "top_row";

export type BoxeStepOption = {
  row: number;
  position: number;
};

export type BoxeRevealResponse = {
  round_id: string;
  outcome: BoxeRevealOutcome;
  multiplier: string;
  payout: string;
  next_step_options: BoxeStepOption[];
  status: BoxeRoundStatus;
};

export type BoxeCashoutResponse = {
  round_id: string;
  payout: string;
  status: "completed_cashout";
  platform_round_id?: string;
  ledger_transaction_id?: string;
};

export type BoxeReplayPick = {
  step: number;
  row: number;
  position: number;
  safe: boolean;
  multiplier_after: string;
  payout_after: string;
};

export type BoxeRoundReplay = {
  session_id: string;
  round_id: string;
  platform_round_id: string | null;
  title_code: string;
  rows: number;
  difficulty: string;
  picks: BoxeReplayPick[];
  revealed_current_row: BoxeReplayPick | null;
  safe_path: BoxeReplayPick[];
  outcome: "cashout" | "top_row" | "loss" | "expired" | "quarantined";
  multiplier_final: string;
  payout_amount: string;
  fairness: {
    server_seed_hash: string;
    client_seed: string;
    nonce: number;
    round_path_hash: string;
  };
};

export type BoxeRoundStatus =
  | "created"
  | "active"
  | "row_revealed"
  | "cashout_pending"
  | "completed_cashout"
  | "completed_top_row"
  | "failed_mine"
  | "expired"
  | "quarantined";

export type BoxeWalletSource = "cash" | "bonus" | "demo";

export type BoxeDemoPlayerAuth = {
  user_id: string;
  email: string;
  access_token: string;
  token_type: "bearer";
};

export async function loadBoxeRuntimeConfig(titleCode: string): Promise<BoxeRuntimeConfig> {
  const params = new URLSearchParams({ title_code: titleCode });
  return apiRequest<BoxeRuntimeConfig>(`/games/boxe/config?${params.toString()}`);
}

export async function provisionBoxeDemoPlayer(): Promise<BoxeDemoPlayerAuth> {
  return apiRequest<BoxeDemoPlayerAuth>("/auth/demo", { method: "POST" });
}

export async function loadBoxeWallets(token: string): Promise<Wallet[]> {
  return apiRequest<Wallet[]>("/wallets", {}, token);
}

export async function startBoxeRound(
  input: {
    titleCode: string;
    rows: number;
    difficulty: string;
    betAmount: string;
    walletSource: BoxeWalletSource;
    token: string;
    idempotencyKey: string;
  },
): Promise<BoxeStartRoundResponse> {
  return apiRequest<BoxeStartRoundResponse>(
    "/games/boxe/start",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({
        title_code: input.titleCode,
        rows: input.rows,
        difficulty: input.difficulty,
        bet_amount: input.betAmount,
        wallet_source: input.walletSource,
        client_seed: `boxe-ui:${input.idempotencyKey}`,
      }),
    },
    input.token,
  );
}

export async function revealBoxePick(
  input: {
    roundId: string;
    row: number;
    position: number;
    token: string;
    idempotencyKey: string;
  },
): Promise<BoxeRevealResponse> {
  return apiRequest<BoxeRevealResponse>(
    "/games/boxe/reveal",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({
        round_id: input.roundId,
        row: input.row,
        position: input.position,
      }),
    },
    input.token,
  );
}

export async function cashoutBoxeRound(
  input: {
    roundId: string;
    token: string;
    idempotencyKey: string;
  },
): Promise<BoxeCashoutResponse> {
  return apiRequest<BoxeCashoutResponse>(
    "/games/boxe/cashout",
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({ round_id: input.roundId }),
    },
    input.token,
  );
}

export async function getBoxeReplay(
  input: {
    roundId: string;
    token: string;
  },
): Promise<BoxeRoundReplay> {
  return apiRequest<BoxeRoundReplay>(
    `/games/boxe/round/${encodeURIComponent(input.roundId)}/replay`,
    {},
    input.token,
  );
}
