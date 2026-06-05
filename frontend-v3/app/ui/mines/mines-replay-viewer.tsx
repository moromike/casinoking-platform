"use client";

import { useEffect, useMemo, useState } from "react";

import { formatChipAmount, toNumericAmount } from "@/app/lib/helpers";

import { MinesBoard } from "./mines-board";

const PLAYBACK_INTERVAL_MS = 900;

export type MinesRoundReplay = {
  game_session_id: string;
  status: "active" | "won" | "lost" | "cancelled";
  title_code: string;
  site_code: string;
  wallet_type: string;
  grid_size: number;
  mine_count: number;
  bet_amount: string;
  payout_amount: string;
  safe_reveals_count: number;
  revealed_cells: number[];
  mine_positions: number[];
  mine_positions_available: boolean;
  final_revealed_cells: number[];
  multiplier_current: string;
  potential_payout: string;
  access_session_id: string | null;
  table_session_id: string | null;
  start_ledger_transaction_id: string | null;
  settlement_ledger_transaction_id: string | null;
  created_at: string;
  closed_at: string | null;
  board_reveal_available: boolean;
  replay_version: string;
  fairness: {
    fairness_version: string;
    nonce: number;
    server_seed_hash: string;
    board_hash: string;
    user_verifiable: boolean;
  };
};

export type MinesReplayViewerCopy = {
  title: string;
  statusLabel: string;
  configLabel: string;
  betLabel: string;
  payoutLabel: string;
  revealedLabel: string;
  fairnessLabel: string;
  boardHashLabel: string;
  seedHashLabel: string;
  nonceLabel: string;
  snapshotLabel: string;
  activeRoundWarning: string;
  formatStatus: (status: MinesRoundReplay["status"]) => string;
  formatConfig: (gridSize: number, mineCount: number) => string;
  board: {
    mineAriaLabel: (cell: number) => string;
    safeAriaLabel: (cell: number) => string;
    hiddenAriaLabel: (cell: number) => string;
    mineFace: string;
    safeFace: string;
    hiddenFace: string;
  };
};

type MinesReplayViewerProps = {
  replay: MinesRoundReplay;
  copy: MinesReplayViewerCopy;
};

export function MinesReplayViewer({ replay, copy }: MinesReplayViewerProps) {
  const boardSide = Math.sqrt(replay.grid_size);
  const maxStep = replay.revealed_cells.length;
  const [stepIndex, setStepIndex] = useState(maxStep);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    setStepIndex(maxStep);
    setIsPlaying(false);
  }, [maxStep, replay.game_session_id]);

  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    if (stepIndex >= maxStep) {
      setIsPlaying(false);
      return;
    }
    const timer = window.setTimeout(() => {
      setStepIndex((current) => Math.min(maxStep, current + 1));
    }, PLAYBACK_INTERVAL_MS);
    return () => window.clearTimeout(timer);
  }, [isPlaying, maxStep, stepIndex]);

  const revealedCells = useMemo(
    () => replay.revealed_cells.slice(0, stepIndex),
    [replay.revealed_cells, stepIndex],
  );
  const minePositions =
    stepIndex === maxStep && replay.board_reveal_available ? replay.mine_positions : [];

  function handlePlayPause() {
    if (stepIndex >= maxStep) {
      setStepIndex(0);
      setIsPlaying(maxStep > 0);
      return;
    }
    setIsPlaying((current) => !current);
  }

  return (
    <section className="mines-replay-viewer" aria-label={copy.title}>
      <div className="mines-replay-header">
        <div>
          <span>{copy.title}</span>
          <strong>{copy.snapshotLabel}</strong>
        </div>
        <span className={`mines-replay-status is-${replay.status}`}>
          {copy.formatStatus(replay.status)}
        </span>
      </div>

      <div className="mines-replay-layout">
        <div className="mines-replay-board">
          <MinesBoard
            cellCount={replay.grid_size}
            boardSide={boardSide}
            revealedCells={revealedCells}
            minePositions={minePositions}
            busy={false}
            isInteractiveRound={false}
            onRevealCell={() => undefined}
            copy={copy.board}
            closed
          />
          <div className="mines-replay-controls" aria-label="Replay controls">
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex(0);
              }}
              disabled={stepIndex === 0}
            >
              Start
            </button>
            <button type="button" onClick={handlePlayPause} disabled={maxStep === 0}>
              {isPlaying ? "Pause" : stepIndex >= maxStep ? "Replay" : "Play"}
            </button>
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex((current) => Math.min(maxStep, current + 1));
              }}
              disabled={stepIndex >= maxStep}
            >
              Step
            </button>
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex(maxStep);
              }}
              disabled={stepIndex >= maxStep}
            >
              Skip
            </button>
          </div>
          <div className="mines-replay-progress">
            Step {stepIndex} / {maxStep}
          </div>
        </div>

        <div className="mines-replay-side">
          <div className="mines-replay-meta-grid">
            <div>
              <span>{copy.statusLabel}</span>
              <strong>{copy.formatStatus(replay.status)}</strong>
            </div>
            <div>
              <span>{copy.configLabel}</span>
              <strong>{copy.formatConfig(replay.grid_size, replay.mine_count)}</strong>
            </div>
            <div>
              <span>{copy.betLabel}</span>
              <strong>{formatChipAmount(toNumericAmount(replay.bet_amount))} CHIP</strong>
            </div>
            <div>
              <span>{copy.payoutLabel}</span>
              <strong>{formatChipAmount(toNumericAmount(replay.payout_amount))} CHIP</strong>
            </div>
            <div>
              <span>{copy.revealedLabel}</span>
              <strong>{replay.safe_reveals_count}</strong>
            </div>
          </div>

          {!replay.board_reveal_available ? (
            <div className="mines-replay-warning">{copy.activeRoundWarning}</div>
          ) : null}

          <div className="mines-replay-fairness">
            <span>{copy.fairnessLabel}</span>
            <dl>
              <div>
                <dt>{copy.boardHashLabel}</dt>
                <dd>{shortenHash(replay.fairness.board_hash)}</dd>
              </div>
              <div>
                <dt>{copy.seedHashLabel}</dt>
                <dd>{shortenHash(replay.fairness.server_seed_hash)}</dd>
              </div>
              <div>
                <dt>{copy.nonceLabel}</dt>
                <dd>{replay.fairness.nonce}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}

function shortenHash(value: string): string {
  if (value.length <= 16) {
    return value;
  }
  return `${value.slice(0, 8)}...${value.slice(-8)}`;
}
