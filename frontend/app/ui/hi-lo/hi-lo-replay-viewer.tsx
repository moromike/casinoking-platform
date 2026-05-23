"use client";

import { useEffect, useMemo, useState } from "react";

import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";

import type { HiLoCard, HiLoReplayAction, HiLoRoundReplay } from "./use-hi-lo-runtime";

type HiLoReplayViewerProps = {
  replay: HiLoRoundReplay;
};

const PLAYBACK_INTERVAL_MS = 900;

export function HiLoReplayViewer({ replay }: HiLoReplayViewerProps) {
  const orderedActions = useMemo(
    () => [...replay.actions].sort((left, right) => left.action_index - right.action_index),
    [replay.actions],
  );
  const maxStep = orderedActions.length;
  const [stepIndex, setStepIndex] = useState(maxStep);
  const [isPlaying, setIsPlaying] = useState(false);
  const visibleActions = orderedActions.slice(0, stepIndex);
  const currentAction = visibleActions.at(-1) ?? orderedActions[0] ?? null;
  const currentCard = currentAction?.drawn_card ?? currentAction?.previous_card ?? null;

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
    <section className="hi-lo-replay-viewer" aria-label="HI-LO replay">
      <div className="hi-lo-replay-header">
        <div>
          <span>Replay HI-LO</span>
          <strong>{readOutcomeLabel(replay)}</strong>
        </div>
        <span className={`hi-lo-replay-status is-${replay.outcome ?? "active"}`}>
          {readStatusLabel(replay)}
        </span>
      </div>

      <div className="hi-lo-replay-layout">
        <div className="hi-lo-replay-stage">
          <ReplayCard card={currentCard} />
          <div className="hi-lo-replay-controls" aria-label="Replay controls">
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
          <div className="hi-lo-replay-progress">
            Step {stepIndex} / {maxStep}
          </div>
        </div>

        <div className="hi-lo-replay-side">
          <div className="hi-lo-replay-meta-grid">
            <div>
              <span>Bet</span>
              <strong>{formatChipAmount(toNumericAmount(replay.bet_amount))} CHIP</strong>
            </div>
            <div>
              <span>Payout</span>
              <strong>{formatChipAmount(toNumericAmount(replay.final_payout_amount ?? "0"))} CHIP</strong>
            </div>
            <div>
              <span>Correct</span>
              <strong>{countSuccessfulPredictions(orderedActions)}</strong>
            </div>
            <div>
              <span>Started</span>
              <strong>{formatDateTime(replay.created_at)}</strong>
            </div>
            <div>
              <span>Closed</span>
              <strong>{replay.closed_at ? formatDateTime(replay.closed_at) : "-"}</strong>
            </div>
            <div>
              <span>Version</span>
              <strong>{replay.fairness_version}</strong>
            </div>
          </div>

          <ol className="hi-lo-replay-timeline" aria-label="HI-LO replay timeline">
            {orderedActions.map((action, index) => (
              <li
                className={`hi-lo-replay-step ${index < stepIndex ? "is-visible" : ""} ${readActionStateClass(action)}`}
                key={`${action.action_index}:${action.created_at}`}
              >
                <span>{readActionLabel(action)}</span>
                <strong>{action.drawn_card?.rank_label ?? "-"}</strong>
                <small>{formatReplayMultiplier(action.multiplier_after)}x</small>
              </li>
            ))}
          </ol>

          <div className="hi-lo-replay-fairness">
            <span>Fairness</span>
            <dl>
              <div>
                <dt>Server seed hash</dt>
                <dd>{shortenHash(replay.server_seed_hash)}</dd>
              </div>
              <div>
                <dt>Client seed</dt>
                <dd>{shortenHash(replay.client_seed)}</dd>
              </div>
              <div>
                <dt>Outcome verification</dt>
                <dd>{shortenHash(replay.draw_sequence_hash)}</dd>
              </div>
              {replay.server_seed ? (
                <div>
                  <dt>Server seed</dt>
                  <dd>{shortenHash(replay.server_seed)}</dd>
                </div>
              ) : null}
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}

function ReplayCard({ card }: { card: HiLoCard | null }) {
  const suit = card?.suit ?? "clubs";
  const color = card?.color ?? "black";

  return (
    <div
      className={`hi-lo-card hi-lo-replay-card is-${color} suit-${suit}`}
      aria-label={card ? `${card.rank_label} ${suit}` : "Card back"}
    >
      {card ? (
        <>
          <span className="hi-lo-card-corner">{card.rank_label}</span>
          <strong>{card.rank_label}</strong>
          <span className="hi-lo-card-suit">{suit}</span>
          <span className="hi-lo-card-corner is-bottom">{card.rank_label}</span>
        </>
      ) : (
        <span className="hi-lo-card-back">HI-LO</span>
      )}
    </div>
  );
}

function readStatusLabel(replay: HiLoRoundReplay) {
  if (replay.outcome === "cashout") {
    return "Cashout";
  }
  if (replay.outcome === "loss") {
    return "Loss";
  }
  if (replay.outcome === "expired") {
    return "Expired";
  }
  if (replay.outcome === "quarantined") {
    return "Quarantined";
  }
  return replay.status;
}

function readOutcomeLabel(replay: HiLoRoundReplay) {
  if (replay.outcome === "cashout") {
    return `Cashout ${formatChipAmount(toNumericAmount(replay.final_payout_amount ?? "0"))} CHIP`;
  }
  if (replay.outcome === "loss") {
    return "Prediction missed";
  }
  return "Snapshot";
}

function readActionLabel(action: HiLoReplayAction) {
  if (action.action_type === "start") {
    return "Start";
  }
  if (action.action_type === "active_skip") {
    return "Skip";
  }
  if (action.action_type === "cashout") {
    return "Collect";
  }
  if (action.prediction_action === "black") {
    return "Black";
  }
  if (action.prediction_action === "red") {
    return "Red";
  }
  if (action.prediction_action === "down") {
    return "Down";
  }
  if (action.prediction_action === "up") {
    return "Up";
  }
  return "Prediction";
}

function readActionStateClass(action: HiLoReplayAction) {
  if (action.action_type === "cashout") {
    return "is-cashout";
  }
  if (action.action_type === "active_skip") {
    return "is-skip";
  }
  if (action.success === true) {
    return "is-correct";
  }
  if (action.success === false) {
    return "is-wrong";
  }
  return "is-start";
}

function countSuccessfulPredictions(actions: HiLoReplayAction[]) {
  return actions.filter((action) => action.action_type === "prediction" && action.success === true).length;
}

function formatReplayMultiplier(value: string) {
  const numeric = Number.parseFloat(value);
  if (!Number.isFinite(numeric)) {
    return value;
  }
  return numeric.toFixed(4);
}

function shortenHash(value: string) {
  if (value.length <= 18) {
    return value;
  }
  return `${value.slice(0, 9)}...${value.slice(-8)}`;
}
