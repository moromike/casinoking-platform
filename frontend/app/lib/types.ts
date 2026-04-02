/**
 * Shared type definitions for CasinoKing platform.
 *
 * Single source of truth — imported by:
 *   - casinoking-console.tsx
 *   - mines-standalone.tsx
 *   - helpers.ts
 *
 * Rules:
 *   - Use superset with optional fields when two consumers differ.
 *   - Do NOT add file-local types here (e.g. DemoAuthResponse, PlayerView).
 *   - Keep alphabetical within each section.
 */

/* ------------------------------------------------------------------ */
/*  Generic UI                                                         */
/* ------------------------------------------------------------------ */

export type StatusKind = "success" | "error" | "info";

export type StatusMessage = {
  kind: StatusKind;
  text: string;
};

/* ------------------------------------------------------------------ */
/*  API envelope                                                       */
/* ------------------------------------------------------------------ */

export type ApiErrorShape = {
  code: string;
  message: string;
};

export type ApiEnvelope<T> =
  | { success: true; data: T }
  | { success: false; error: ApiErrorShape; detail?: unknown };

/* ------------------------------------------------------------------ */
/*  Wallet                                                             */
/* ------------------------------------------------------------------ */

/**
 * Superset wallet type.
 *   - `mines-standalone.tsx` uses only `wallet_type` + `balance_snapshot`.
 *   - `casinoking-console.tsx` also uses `currency_code`, `status`, `ledger_account_code`.
 */
export type Wallet = {
  wallet_type: string;
  balance_snapshot: string;
  currency_code?: string;
  status?: string;
  ledger_account_code?: string;
};

/* ------------------------------------------------------------------ */
/*  Mines presentation / runtime config                                */
/* ------------------------------------------------------------------ */

export type MinesPresentationConfig = {
  rules_sections: Record<string, string>;
  published_grid_sizes: number[];
  published_mine_counts: Record<string, number[]>;
  default_mine_counts: Record<string, number>;
  ui_labels: Record<string, Record<string, string>>;
  board_assets?: {
    safe_icon_data_url?: string | null;
    mine_icon_data_url?: string | null;
  };
};

/**
 * Superset runtime config.
 *   - `casinoking-console.tsx` has required `game_code`, `payout_runtime_file`.
 *   - `mines-standalone.tsx` has them optional.
 *   - Helpers use `MinesRuntimeLike` (a structural subset) — see below.
 */
export type MinesRuntimeConfig = {
  game_code?: string;
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
  payout_runtime_file?: string;
  fairness_version: string;
  presentation_config?: MinesPresentationConfig;
};

/**
 * Structural subset used by helper functions.
 * `MinesRuntimeConfig` satisfies this interface.
 */
export type MinesRuntimeLike = {
  supported_grid_sizes: number[];
  supported_mine_counts: Record<string, number[]>;
  payout_ladders: Record<string, Record<string, string[]>>;
  presentation_config?: {
    rules_sections: Record<string, string>;
    published_grid_sizes: number[];
    published_mine_counts: Record<string, number[]>;
    default_mine_counts: Record<string, number>;
    ui_labels: Record<string, Record<string, string>>;
    board_assets?: {
      safe_icon_data_url?: string | null;
      mine_icon_data_url?: string | null;
    };
  };
};

/* ------------------------------------------------------------------ */
/*  Fairness                                                           */
/* ------------------------------------------------------------------ */

/**
 * Superset fairness config.
 *   - `mines-standalone.tsx` uses a minimal subset.
 *   - `casinoking-console.tsx` adds `game_code`, `random_source`, etc.
 */
export type FairnessCurrentConfig = {
  fairness_version: string;
  fairness_phase: string;
  active_server_seed_hash: string;
  user_verifiable: boolean;
  game_code?: string;
  random_source?: string;
  board_hash_persisted?: boolean;
  server_seed_hash_persisted?: boolean;
  seed_activated_at?: string;
  payout_runtime_file?: string;
};

/* ------------------------------------------------------------------ */
/*  Session                                                            */
/* ------------------------------------------------------------------ */

export type SessionSnapshot = {
  game_session_id: string;
  status: "active" | "won" | "lost";
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  wallet_type: string;
  safe_reveals_count: number;
  revealed_cells: number[];
  multiplier_current: string;
  potential_payout: string;
  wallet_balance_after_start: string;
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  ledger_transaction_id: string;
  created_at: string;
  closed_at: string | null;
};

/**
 * Superset session fairness.
 *   - `casinoking-console.tsx` includes `game_session_id`.
 *   - `mines-standalone.tsx` omits it.
 */
export type SessionFairness = {
  game_session_id?: string;
  fairness_version: string;
  nonce: number;
  server_seed_hash: string;
  board_hash: string;
  user_verifiable: boolean;
};
