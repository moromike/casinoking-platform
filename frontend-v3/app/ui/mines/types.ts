import type { MinesRoundReplay } from "./mines-replay-viewer";

export type MinesRevealResult = {
  outcome: "safe" | "mine" | "won";
  minePositions: number[] | null;
  payout: string | null;
};

export type MinesCashoutResult = {
  payout: string;
  minePositions: number[];
};

export type LatestAccessSessionHistory = {
  id: string;
  game_code: string;
  title_code: string;
  site_code: string;
  status: "active" | "closed" | "timed_out";
  started_at: string;
  last_activity_at: string;
  ended_at: string | null;
  rounds: MinesRoundReplay[];
};
