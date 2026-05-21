"use client";

import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";

import { getBoxeCellsForRow } from "./boxe-pyramid-board";
import type {
  BoxePyramidFullReveal,
  BoxeReplayPick,
  BoxeRoundReplay,
} from "./use-boxe-runtime";

type BoxeReplayViewerProps = {
  replay: BoxeRoundReplay;
};

type ReplayCellState = "covered" | "safe" | "mine" | "opaque";
type ReplayRevealCell = {
  row: number;
  position: number;
  outcome: "safe" | "mine";
};

const PLAYBACK_INTERVAL_MS = 900;

export function BoxeReplayViewer({ replay }: BoxeReplayViewerProps) {
  const maxStep = replay.picks.length;
  const [stepIndex, setStepIndex] = useState(maxStep);
  const [isPlaying, setIsPlaying] = useState(false);
  const fullRevealCells = useMemo(
    () => normalizeFullReveal(replay.pyramid_full_reveal),
    [replay.pyramid_full_reveal],
  );
  const visiblePicks = replay.picks.slice(0, stepIndex);
  const showFullReveal = stepIndex === maxStep && fullRevealCells.length > 0;

  useEffect(() => {
    setStepIndex(maxStep);
    setIsPlaying(false);
  }, [maxStep, replay.round_id]);

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

  function handlePlayPause() {
    if (stepIndex >= maxStep) {
      setStepIndex(0);
      setIsPlaying(maxStep > 0);
      return;
    }
    setIsPlaying((current) => !current);
  }

  return (
    <section className="boxe-replay-viewer" aria-label="BOXE replay">
      <div className="boxe-replay-header">
        <div>
          <span>Replay BOXE</span>
          <strong>{readOutcomeLabel(replay)}</strong>
        </div>
        <span className={`boxe-replay-status is-${replay.outcome ?? "active"}`}>
          {readStatusLabel(replay)}
        </span>
      </div>

      <div className="boxe-replay-layout">
        <div className="boxe-replay-board-shell">
          <ReplayPyramid
            rows={replay.rows}
            visiblePicks={visiblePicks}
            fullRevealCells={showFullReveal ? fullRevealCells : []}
          />
          <div className="boxe-replay-controls" aria-label="Replay controls">
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
          <div className="boxe-replay-progress">
            Step {stepIndex} / {maxStep}
          </div>
        </div>

        <div className="boxe-replay-side">
          <div className="boxe-replay-meta-grid">
            <div>
              <span>Config</span>
              <strong>
                {replay.rows} rows / {replay.difficulty}
              </strong>
            </div>
            <div>
              <span>Bet</span>
              <strong>{formatChipAmount(toNumericAmount(replay.bet_amount))} CHIP</strong>
            </div>
            <div>
              <span>Payout</span>
              <strong>{formatChipAmount(toNumericAmount(replay.payout_amount))} CHIP</strong>
            </div>
            <div>
              <span>Opened</span>
              <strong>{replay.safe_path.length}</strong>
            </div>
            <div>
              <span>Started</span>
              <strong>{formatDateTime(replay.created_at)}</strong>
            </div>
            <div>
              <span>Closed</span>
              <strong>{replay.closed_at ? formatDateTime(replay.closed_at) : "-"}</strong>
            </div>
          </div>

          <div className="boxe-replay-fairness">
            <span>Fairness</span>
            <dl>
              <div>
                <dt>Server seed hash</dt>
                <dd>{shortenHash(replay.fairness.server_seed_hash)}</dd>
              </div>
              <div>
                <dt>Client seed</dt>
                <dd>{shortenHash(replay.fairness.client_seed)}</dd>
              </div>
              <div>
                <dt>Outcome verification</dt>
                <dd>{shortenHash(replay.fairness.outcome_verification || replay.fairness.round_path_hash)}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}

function ReplayPyramid({
  rows,
  visiblePicks,
  fullRevealCells,
}: {
  rows: number;
  visiblePicks: BoxeReplayPick[];
  fullRevealCells: ReplayRevealCell[];
}) {
  const visualRows = Array.from({ length: rows }, (_item, index) => rows - index - 1);

  return (
    <section className="boxe-replay-pyramid" aria-label="Replay pyramid">
      {visualRows.map((row) => {
        const cellCount = getBoxeCellsForRow(row, rows);

        return (
          <div
            className="boxe-pyramid-row boxe-replay-pyramid-row"
            data-row={row}
            key={row}
            style={{ "--boxe-row-cells": cellCount } as CSSProperties}
          >
            {Array.from({ length: cellCount }, (_box, position) => {
              const state = readCellState(row, position, visiblePicks, fullRevealCells);
              return (
                <span
                  aria-label={`BOXE replay row ${row + 1} position ${position + 1}`}
                  className={`boxe-pyramid-cell boxe-replay-cell ${state}`}
                  data-state={state}
                  key={position}
                >
                  <span className="boxe-cell-face" aria-hidden="true">
                    {state === "safe" ? (
                      <img src="/game-assets/boxe/diamond_green_v001.png" alt="" draggable={false} />
                    ) : null}
                    {state === "mine" ? (
                      <img src="/game-assets/boxe/mine_fucsia_002.png" alt="" draggable={false} />
                    ) : null}
                  </span>
                </span>
              );
            })}
          </div>
        );
      })}
    </section>
  );
}

function readCellState(
  row: number,
  position: number,
  visiblePicks: BoxeReplayPick[],
  fullRevealCells: ReplayRevealCell[],
): ReplayCellState {
  const picked = visiblePicks.find((pick) => pick.row === row && pick.position === position);
  if (picked) {
    return picked.safe ? "safe" : "mine";
  }
  const revealed = fullRevealCells.find((cell) => cell.row === row && cell.position === position);
  if (revealed) {
    return revealed.outcome;
  }
  return "covered";
}

function normalizeFullReveal(value: BoxePyramidFullReveal | null): ReplayRevealCell[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((row) => {
    if (!row || typeof row !== "object" || !Array.isArray(row.cells)) {
      return [];
    }
    const rowIndex = Number(row.row);
    if (!Number.isInteger(rowIndex)) {
      return [];
    }
    return row.cells
      .map((cell) => {
        const position = Number(cell.position);
        if (!Number.isInteger(position)) {
          return null;
        }
        if (cell.state !== "safe" && cell.state !== "mine") {
          return null;
        }
        return { row: rowIndex, position, outcome: cell.state };
      })
      .filter((cell): cell is ReplayRevealCell => cell !== null);
  });
}

function readStatusLabel(replay: BoxeRoundReplay): string {
  if (replay.outcome === "cashout") {
    return "Cashout";
  }
  if (replay.outcome === "top_row") {
    return "Top row";
  }
  if (replay.outcome === "loss") {
    return "Loss";
  }
  return replay.status;
}

function readOutcomeLabel(replay: BoxeRoundReplay): string {
  if (replay.outcome === "loss") {
    return "Mine hit";
  }
  if (replay.outcome === "cashout") {
    return `Cashout ${replay.cashout_multiplier ?? replay.multiplier_final}x`;
  }
  if (replay.outcome === "top_row") {
    return "Completed pyramid";
  }
  return "Snapshot";
}

function shortenHash(value: string): string {
  if (value.length <= 18) {
    return value;
  }
  return `${value.slice(0, 9)}...${value.slice(-8)}`;
}
