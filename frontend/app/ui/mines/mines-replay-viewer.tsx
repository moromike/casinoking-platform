"use client";

import { useEffect, useMemo, useState } from "react";

import { formatChipAmount, toNumericAmount } from "@/app/lib/helpers";
import { Button } from "@/app/ui/components/button";

import { MinesBoard } from "./mines-board";

export type MinesReplayStep = {
  step_index: number;
  cell_index: number;
  result: "safe" | "mine";
  safe_reveals_count: number;
  multiplier: string;
  payout_amount: string;
};

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
  steps: MinesReplayStep[];
  fairness: {
    fairness_version: string;
    nonce: number;
    server_seed_hash: string;
    board_hash: string;
    user_verifiable: boolean;
  };
};

type MinesReplayStage = "start" | "step" | "final";

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
  startAction: string;
  previousAction: string;
  nextAction: string;
  finalAction: string;
  noStepsLabel: string;
  activeRoundWarning: string;
  formatStatus: (status: MinesRoundReplay["status"]) => string;
  formatConfig: (gridSize: number, mineCount: number) => string;
  formatFrame: (currentFrame: number, totalFrames: number, stage: MinesReplayStage) => string;
  formatStep: (step: MinesReplayStep) => string;
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
  const totalFrames = 1 + replay.steps.length + (replay.board_reveal_available ? 1 : 0);
  const lastFrameIndex = Math.max(totalFrames - 1, 0);
  const [frameIndex, setFrameIndex] = useState(lastFrameIndex);

  useEffect(() => {
    setFrameIndex(lastFrameIndex);
  }, [lastFrameIndex, replay.game_session_id]);

  const frame = useMemo(
    () => buildReplayFrame({ replay, frameIndex }),
    [frameIndex, replay],
  );
  const boardSide = Math.sqrt(replay.grid_size);
  const activeStep = frame.stage === "step" ? replay.steps[frameIndex - 1] ?? null : null;

  return (
    <section className="mines-replay-viewer" aria-label={copy.title}>
      <div className="mines-replay-header">
        <div>
          <span>{copy.title}</span>
          <strong>{copy.formatFrame(frameIndex + 1, totalFrames, frame.stage)}</strong>
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
            revealedCells={frame.revealedCells}
            minePositions={frame.minePositions}
            busy={false}
            isInteractiveRound={false}
            onRevealCell={() => undefined}
            copy={copy.board}
            closed
          />
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

          {activeStep ? (
            <div className={`mines-replay-step is-${activeStep.result}`}>
              {copy.formatStep(activeStep)}
            </div>
          ) : replay.steps.length === 0 ? (
            <div className="mines-replay-step">{copy.noStepsLabel}</div>
          ) : null}

          {!replay.board_reveal_available ? (
            <div className="mines-replay-warning">{copy.activeRoundWarning}</div>
          ) : null}

          <div className="mines-replay-controls">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setFrameIndex(0)}
              disabled={frameIndex === 0}
            >
              {copy.startAction}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setFrameIndex((current) => Math.max(0, current - 1))}
              disabled={frameIndex === 0}
            >
              {copy.previousAction}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setFrameIndex((current) => Math.min(lastFrameIndex, current + 1))}
              disabled={frameIndex >= lastFrameIndex}
            >
              {copy.nextAction}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setFrameIndex(lastFrameIndex)}
              disabled={frameIndex >= lastFrameIndex}
            >
              {copy.finalAction}
            </Button>
          </div>

          <div className="mines-replay-timeline" aria-label={copy.title}>
            {Array.from({ length: totalFrames }, (_, index) => (
              <button
                key={`${replay.game_session_id}-${index}`}
                type="button"
                className={`mines-replay-timeline-dot${index === frameIndex ? " is-active" : ""}`}
                aria-label={copy.formatFrame(index + 1, totalFrames, readReplayStage(index, replay))}
                onClick={() => setFrameIndex(index)}
              />
            ))}
          </div>

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

function buildReplayFrame({
  replay,
  frameIndex,
}: {
  replay: MinesRoundReplay;
  frameIndex: number;
}): { stage: MinesReplayStage; revealedCells: number[]; minePositions: number[] } {
  if (frameIndex <= 0) {
    return {
      stage: "start",
      revealedCells: [],
      minePositions: [],
    };
  }

  if (frameIndex <= replay.steps.length) {
    const visibleSteps = replay.steps.slice(0, frameIndex);
    return {
      stage: "step",
      revealedCells: visibleSteps.map((step) => step.cell_index),
      minePositions: visibleSteps
        .filter((step) => step.result === "mine")
        .map((step) => step.cell_index),
    };
  }

  return {
    stage: "final",
    revealedCells: replay.final_revealed_cells,
    minePositions: replay.mine_positions,
  };
}

function readReplayStage(frameIndex: number, replay: MinesRoundReplay): MinesReplayStage {
  if (frameIndex <= 0) {
    return "start";
  }
  return frameIndex <= replay.steps.length ? "step" : "final";
}

function shortenHash(value: string): string {
  if (value.length <= 16) {
    return value;
  }
  return `${value.slice(0, 8)}...${value.slice(-8)}`;
}
