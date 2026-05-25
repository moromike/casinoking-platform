"use client";

import type { ReactNode } from "react";

import { BoxeReplayViewer } from "@/app/ui/boxe/boxe-replay-viewer";
import type { BoxeRoundReplay } from "@/app/ui/boxe/use-boxe-runtime";
import { HiLoReplayViewer } from "@/app/ui/hi-lo/hi-lo-replay-viewer";
import type { HiLoRoundReplay } from "@/app/ui/hi-lo/use-hi-lo-runtime";
import { DEFAULT_MINES_REPLAY_COPY } from "@/app/ui/mines/mines-replay-copy";
import {
  MinesReplayViewer,
  type MinesRoundReplay,
} from "@/app/ui/mines/mines-replay-viewer";
import type { PlayerGameCode } from "@/app/ui/player-game-registry";

type GameStatus = "active" | "won" | "lost" | "cancelled";

export type GameAccountHistoryItem = {
  game_code: string;
  game_session_id: string;
  status: GameStatus;
  title_code?: string;
  site_code?: string;
  replay_round_id?: string;
  grid_size: number;
  mine_count: number;
  rows?: number;
  difficulty?: string;
  outcome?: string | null;
  bet_amount: string;
  wallet_type: string;
  safe_reveals_count: number;
  revealed_cells_count: number;
  multiplier_current: string;
  potential_payout: string;
  access_session_id: string | null;
  access_session: {
    id: string;
    game_code: string;
    status: "active" | "closed" | "timed_out";
    started_at: string;
    last_activity_at: string;
    ended_at: string | null;
  } | null;
  created_at: string;
  closed_at: string | null;
};

type MinesSessionHistoryItem = Omit<GameAccountHistoryItem, "game_code"> & {
  game_code?: "mines";
};

type BoxeSessionHistoryItem = {
  game_code: "boxe";
  session_id: string;
  title_code: string;
  site_code: string;
  last_round_id: string;
  status: string;
  outcome: "cashout" | "top_row" | "loss" | "expired" | "quarantined" | null;
  rows: number;
  difficulty: string;
  bet_amount: string;
  wallet_source?: string | null;
  safe_picks_count: number;
  created_at: string;
  closed_at: string | null;
  payout_amount: string;
};

type HiLoSessionHistoryItem = {
  game_code?: "hi_lo";
  session_id: string;
  round_id: string;
  title_code: string;
  site_code: string;
  status: string;
  wallet_source: string;
  outcome: "cashout" | "loss" | "expired" | "quarantined" | null;
  bet_amount: string;
  final_payout_amount: string | null;
  correct_predictions_count: number;
  created_at: string;
  closed_at: string | null;
};

export type GameReplayPayload = MinesRoundReplay | BoxeRoundReplay | HiLoRoundReplay;

type PlayerHistoryPathOptions = {
  limit: number;
  cursor?: string | null;
};

type GameReportingDescriptor = {
  gameCode: PlayerGameCode;
  runtimeDescriptor: {
    payoutRuntimeSource: string;
    mathSource: string;
    rtpSource: string;
    replayVerificationSource: string;
    specPaths: string[];
  };
  buildPlayerHistoryPath: (options: PlayerHistoryPathOptions) => string;
  mapPlayerHistoryItems: (items: unknown[]) => GameAccountHistoryItem[];
  buildPlayerReplayPath: (round: GameAccountHistoryItem) => string | null;
  buildAdminReplayPath: (platformRoundId: string) => string;
  renderPlayerReplay: (replay: GameReplayPayload) => ReactNode;
  renderAdminReplay: (replay: GameReplayPayload) => ReactNode;
  readConfigLabel: (round: GameAccountHistoryItem) => string;
  readProgressLabel: (round: GameAccountHistoryItem) => string;
};

function buildPath(path: string, options: PlayerHistoryPathOptions): string {
  const params = new URLSearchParams({ limit: String(options.limit) });
  if (options.cursor) {
    params.set("cursor", options.cursor);
  }
  return `${path}?${params.toString()}`;
}

function mapMinesHistoryItems(items: unknown[]): GameAccountHistoryItem[] {
  return (items as MinesSessionHistoryItem[]).map((item) => ({
    ...item,
    game_code: "mines",
  }));
}

function mapBoxeHistoryItems(items: unknown[]): GameAccountHistoryItem[] {
  return (items as BoxeSessionHistoryItem[]).map((item) => {
    const mappedStatus: GameStatus =
      item.outcome === "loss" || item.status === "failed_mine"
        ? "lost"
        : item.outcome === "expired" || item.outcome === "quarantined"
          ? "cancelled"
          : "won";

    return {
      game_code: "boxe",
      game_session_id: item.last_round_id,
      replay_round_id: item.last_round_id,
      status: mappedStatus,
      title_code: item.title_code,
      site_code: item.site_code,
      grid_size: 0,
      mine_count: 0,
      rows: item.rows,
      difficulty: item.difficulty,
      outcome: item.outcome,
      bet_amount: item.bet_amount,
      wallet_type: item.wallet_source ?? "legacy",
      safe_reveals_count: item.safe_picks_count,
      revealed_cells_count: item.safe_picks_count,
      multiplier_current: "0",
      potential_payout: item.payout_amount,
      access_session_id: null,
      access_session: null,
      created_at: item.created_at,
      closed_at: item.closed_at,
    };
  });
}

function mapHiLoHistoryItems(items: unknown[]): GameAccountHistoryItem[] {
  return (items as HiLoSessionHistoryItem[]).map((item) => {
    const mappedStatus: GameStatus =
      item.outcome === "loss" || item.status === "failed_prediction"
        ? "lost"
        : item.outcome === "expired" || item.outcome === "quarantined"
          ? "cancelled"
          : item.status === "active"
            ? "active"
            : "won";

    return {
      game_code: "hi_lo",
      game_session_id: item.round_id,
      replay_round_id: item.round_id,
      status: mappedStatus,
      title_code: item.title_code,
      site_code: item.site_code,
      grid_size: 0,
      mine_count: 0,
      outcome: item.outcome,
      bet_amount: item.bet_amount,
      wallet_type: item.wallet_source,
      safe_reveals_count: item.correct_predictions_count,
      revealed_cells_count: item.correct_predictions_count,
      multiplier_current: "0",
      potential_payout: item.final_payout_amount ?? "0",
      access_session_id: null,
      access_session: null,
      created_at: item.created_at,
      closed_at: item.closed_at,
    };
  });
}

export const GAME_REPORTING_REGISTRY: Record<PlayerGameCode, GameReportingDescriptor> = {
  mines: {
    gameCode: "mines",
    runtimeDescriptor: {
      payoutRuntimeSource: "docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json",
      mathSource: "backend/app/modules/games/mines/runtime.py",
      rtpSource: "docs/games/mines/MATH_SPEC.md#11",
      replayVerificationSource: "backend/app/modules/games/mines/service.py:_replay_payload",
      specPaths: ["docs/games/mines/MATH_SPEC.md"],
    },
    buildPlayerHistoryPath: (options) => buildPath("/games/mines/sessions", options),
    mapPlayerHistoryItems: mapMinesHistoryItems,
    buildPlayerReplayPath: (round) =>
      `/games/mines/session/${encodeURIComponent(round.game_session_id)}/replay`,
    buildAdminReplayPath: (platformRoundId) =>
      `/games/mines/admin/session/${encodeURIComponent(platformRoundId)}/replay`,
    renderPlayerReplay: (replay) => (
      <MinesReplayViewer replay={replay as MinesRoundReplay} copy={DEFAULT_MINES_REPLAY_COPY} />
    ),
    renderAdminReplay: (replay) => (
      <MinesReplayViewer replay={replay as MinesRoundReplay} copy={DEFAULT_MINES_REPLAY_COPY} />
    ),
    readConfigLabel: (round) => `${round.grid_size} celle - ${round.mine_count} mine`,
    readProgressLabel: (round) =>
      `${round.safe_reveals_count} safe / ${round.revealed_cells_count} scoperte`,
  },
  boxe: {
    gameCode: "boxe",
    runtimeDescriptor: {
      payoutRuntimeSource: "backend/app/modules/games/boxe/math.py",
      mathSource: "backend/app/modules/games/boxe/math.py",
      rtpSource: "docs/games/boxe/MATH_SPEC.md",
      replayVerificationSource: "backend/app/modules/games/boxe/service.py:_replay_payload",
      specPaths: ["docs/games/boxe/SPEC.md", "docs/games/boxe/MATH_SPEC.md"],
    },
    buildPlayerHistoryPath: (options) => buildPath("/games/boxe/sessions", options),
    mapPlayerHistoryItems: mapBoxeHistoryItems,
    buildPlayerReplayPath: (round) =>
      `/games/boxe/round/${encodeURIComponent(round.replay_round_id ?? round.game_session_id)}/replay`,
    buildAdminReplayPath: (platformRoundId) =>
      `/games/boxe/admin/round/${encodeURIComponent(platformRoundId)}/replay`,
    renderPlayerReplay: (replay) => <BoxeReplayViewer replay={replay as BoxeRoundReplay} />,
    renderAdminReplay: (replay) => <BoxeReplayViewer replay={replay as BoxeRoundReplay} />,
    readConfigLabel: (round) => `${round.rows ?? 0} rows - ${round.difficulty ?? "-"}`,
    readProgressLabel: (round) => `${round.safe_reveals_count} safe picks`,
  },
  hi_lo: {
    gameCode: "hi_lo",
    runtimeDescriptor: {
      payoutRuntimeSource: "backend/app/modules/games/hi_lo/math.py",
      mathSource: "backend/app/modules/games/hi_lo/math.py",
      rtpSource: "docs/games/hi-lo/MATH_SPEC.md",
      replayVerificationSource: "backend/app/modules/games/hi_lo/service.py:get_round_replay",
      specPaths: ["docs/games/hi-lo/SPEC.md", "docs/games/hi-lo/MATH_SPEC.md"],
    },
    buildPlayerHistoryPath: (options) => buildPath("/games/hi-lo/sessions", options),
    mapPlayerHistoryItems: mapHiLoHistoryItems,
    buildPlayerReplayPath: (round) =>
      `/games/hi-lo/round/${encodeURIComponent(round.replay_round_id ?? round.game_session_id)}/replay`,
    buildAdminReplayPath: (platformRoundId) =>
      `/games/hi-lo/admin/round/${encodeURIComponent(platformRoundId)}/replay`,
    renderPlayerReplay: (replay) => <HiLoReplayViewer replay={replay as HiLoRoundReplay} />,
    renderAdminReplay: (replay) => <HiLoReplayViewer replay={replay as HiLoRoundReplay} />,
    readConfigLabel: () => "52-card deck",
    readProgressLabel: (round) => `${round.safe_reveals_count} previsioni corrette`,
  },
};

export const GAME_ACCOUNT_HISTORY_DESCRIPTORS = Object.values(GAME_REPORTING_REGISTRY);

export function readGameReportingDescriptor(
  gameCode: string | null | undefined,
): GameReportingDescriptor | null {
  if (!gameCode) {
    return null;
  }
  return gameCode in GAME_REPORTING_REGISTRY
    ? GAME_REPORTING_REGISTRY[gameCode as PlayerGameCode]
    : null;
}

export function readGameReplayStateKey(round: GameAccountHistoryItem): string {
  return `${round.game_code}:${round.replay_round_id ?? round.game_session_id}`;
}

export function readPlayerGameReplayEndpoint(round: GameAccountHistoryItem): string | null {
  return readGameReportingDescriptor(round.game_code)?.buildPlayerReplayPath(round) ?? null;
}

export function renderPlayerGameReplay(
  gameCode: string | null | undefined,
  replay: GameReplayPayload,
): ReactNode {
  return readGameReportingDescriptor(gameCode)?.renderPlayerReplay(replay) ?? null;
}

export function readAdminGameReplayEndpoint(
  gameCode: string | null | undefined,
  platformRoundId: string,
): string | null {
  return readGameReportingDescriptor(gameCode)?.buildAdminReplayPath(platformRoundId) ?? null;
}

export function renderAdminGameReplay(
  gameCode: string | null | undefined,
  replay: GameReplayPayload,
): ReactNode {
  return readGameReportingDescriptor(gameCode)?.renderAdminReplay(replay) ?? null;
}

export function hasAdminGameReplay(gameCode: string | null | undefined): boolean {
  return readGameReportingDescriptor(gameCode) !== null;
}
