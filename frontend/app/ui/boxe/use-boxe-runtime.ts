"use client";

import { apiRequest } from "@/app/lib/api";

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
};

export async function loadBoxeRuntimeConfig(titleCode: string): Promise<BoxeRuntimeConfig> {
  const params = new URLSearchParams({ title_code: titleCode });
  return apiRequest<BoxeRuntimeConfig>(`/games/boxe/config?${params.toString()}`);
}
