"use client";

import { apiRequest } from "@/app/lib/api";
import type { Wallet } from "@/app/lib/types";
import type { GameLatestAccessSessionHistory } from "../game-runtime/game-latest-replay-panel";

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
  table_session_id?: string | null;
  table_session?: BoxeTableSession | null;
  wallet_balance_after_start?: string | null;
};

export type BoxeRevealOutcome = "safe" | "mine" | "top_row";

export type BoxeStepOption = {
  row: number;
  position: number;
};

export type BoxePyramidRevealCell = {
  position: number;
  state: "safe" | "mine";
  picked: boolean;
  reveal_scope: "picked_path" | "terminal_full_reveal";
};

export type BoxePyramidRevealRow = {
  row: number;
  cells: BoxePyramidRevealCell[];
};

export type BoxePyramidFullReveal = BoxePyramidRevealRow[];

export type BoxeDemoSettlement = {
  wallet_balance_after: string;
  ledger_transaction_id?: string | null;
  already_exists?: boolean;
};

export type BoxeRevealResponse = {
  round_id: string;
  outcome: BoxeRevealOutcome;
  multiplier: string;
  payout: string;
  next_step_options: BoxeStepOption[];
  status: BoxeRoundStatus;
  pyramid_full_reveal?: BoxePyramidFullReveal | null;
  table_session?: BoxeTableSession | null;
  settlement?: BoxeDemoSettlement | null;
};

export type BoxeCashoutResponse = {
  round_id: string;
  payout: string;
  status: "completed_cashout";
  pyramid_full_reveal: BoxePyramidFullReveal;
  platform_round_id?: string;
  ledger_transaction_id?: string;
  table_session?: BoxeTableSession | null;
  settlement?: BoxeDemoSettlement | null;
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
  game_code: "boxe";
  session_id: string;
  round_id: string;
  platform_round_id: string | null;
  title_code: string;
  site_code: string | null;
  status: BoxeRoundStatus;
  rows: number;
  difficulty: string;
  bet_amount: string;
  currency: string;
  multiplier_ladder: string[];
  picks: BoxeReplayPick[];
  revealed_current_row: BoxeReplayPick | null;
  safe_path: BoxeReplayPick[];
  outcome: "cashout" | "top_row" | "loss" | "expired" | "quarantined" | null;
  terminal_status: BoxeRoundStatus | null;
  multiplier_final: string;
  cashout_multiplier: string | null;
  payout_amount: string;
  created_at: string;
  closed_at: string | null;
  pyramid_full_reveal: BoxePyramidFullReveal | null;
  pyramid_full_reveal_available: boolean;
  replay_version: string;
  fairness: {
    fairness_version: string;
    server_seed_hash: string;
    client_seed: string;
    nonce: number;
    round_path_hash: string;
    outcome_verification: string;
    user_verifiable: boolean;
  };
  admin_context?: {
    user_id: string;
    user_email: string | null;
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

export type BoxeTableSessionLimits = {
  wallet_balance_available: string;
  table_session_max_chips: string;
  default_table_amount: string;
  max_table_amount: string;
};

export type BoxeAccessSession = {
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

export type BoxeTableSession = {
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

export async function loadBoxeTableSessionLimits(
  token: string,
  walletType: "cash" | "bonus",
): Promise<BoxeTableSessionLimits> {
  return apiRequest<BoxeTableSessionLimits>(
    `/table-sessions/limits?wallet_type=${walletType}&game_code=boxe`,
    {},
    token,
  );
}

export async function createBoxeAccessSession(
  input: {
    titleCode: string;
    token: string;
  },
): Promise<BoxeAccessSession> {
  return apiRequest<BoxeAccessSession>(
    "/access-sessions",
    {
      method: "POST",
      body: JSON.stringify({
        game_code: "boxe",
        title_code: input.titleCode,
        site_code: "casinoking",
      }),
    },
    input.token,
  );
}

export async function closeBoxeAccessSession(input: {
  accessSessionId: string;
  token: string;
}): Promise<BoxeAccessSession> {
  return apiRequest<BoxeAccessSession>(
    `/access-sessions/${encodeURIComponent(input.accessSessionId)}/close`,
    { method: "POST" },
    input.token,
  );
}

export async function createBoxeTableSession(
  input: {
    titleCode: string;
    walletType: "cash" | "bonus";
    tableBudgetAmount: string;
    accessSessionId: string;
    token: string;
  },
): Promise<BoxeTableSession> {
  return apiRequest<BoxeTableSession>(
    "/table-sessions",
    {
      method: "POST",
      body: JSON.stringify({
        game_code: "boxe",
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

export async function startBoxeRound(
  input: {
    titleCode: string;
    rows: number;
    difficulty: string;
    betAmount: string;
    walletSource: BoxeWalletSource;
    token: string;
    idempotencyKey: string;
    tableSessionId?: string | null;
    accessSessionId?: string | null;
    launchToken?: string;
  },
): Promise<BoxeStartRoundResponse> {
  return apiRequest<BoxeStartRoundResponse>(
    "/games/boxe/start",
    {
      method: "POST",
      headers: {
        "Idempotency-Key": input.idempotencyKey,
        ...(input.launchToken ? { "X-Game-Launch-Token": input.launchToken } : {}),
      },
      body: JSON.stringify({
        title_code: input.titleCode,
        rows: input.rows,
        difficulty: input.difficulty,
        bet_amount: input.betAmount,
        wallet_source: input.walletSource,
        client_seed: `boxe-ui:${input.idempotencyKey}`,
        table_session_id: input.tableSessionId ?? null,
        access_session_id: input.accessSessionId ?? null,
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

export async function fetchBoxeLatestReplaySessions(input: {
  titleCode: string;
  token: string;
}): Promise<GameLatestAccessSessionHistory<BoxeRoundReplay>[]> {
  const params = new URLSearchParams();
  params.set("title_code", input.titleCode);
  return apiRequest<GameLatestAccessSessionHistory<BoxeRoundReplay>[]>(
    `/games/boxe/access-sessions/latest?${params.toString()}`,
    {},
    input.token,
  );
}
