"use client";

import { useEffect, useMemo, useState } from "react";

import { formatChipAmount, formatDateTime, toNumericAmount } from "@/app/lib/helpers";

import {
  createHiLoCopyResolver,
  type HiLoCopyResolver,
} from "./hi-lo-i18n/hi-lo-copy-defaults";
import type { HiLoCard, HiLoReplayAction, HiLoRoundReplay } from "./use-hi-lo-runtime";

type HiLoReplayViewerProps = {
  copy?: HiLoCopyResolver;
  replay: HiLoRoundReplay;
};

const PLAYBACK_INTERVAL_MS = 900;

export function HiLoReplayViewer({
  copy = createHiLoCopyResolver("it"),
  replay,
}: HiLoReplayViewerProps) {
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
    <section className="hi-lo-replay-viewer" aria-label={copy("runtime.replay.aria")}>
      <div className="hi-lo-replay-header">
        <div>
          <span>{copy("runtime.replay.title")}</span>
          <strong>{readOutcomeLabel(replay, copy)}</strong>
        </div>
        <span className={`hi-lo-replay-status is-${replay.outcome ?? "active"}`}>
          {readStatusLabel(replay, copy)}
        </span>
      </div>

      <div className="hi-lo-replay-layout">
        <div className="hi-lo-replay-stage">
          <ReplayCard card={currentCard} copy={copy} />
          <div className="hi-lo-replay-controls" aria-label={copy("runtime.replay.controls_aria")}>
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex(0);
              }}
              disabled={stepIndex === 0}
            >
              {copy("runtime.replay.start")}
            </button>
            <button type="button" onClick={handlePlayPause} disabled={maxStep === 0}>
              {isPlaying
                ? copy("runtime.replay.pause")
                : stepIndex >= maxStep
                  ? copy("runtime.replay.replay")
                  : copy("runtime.replay.play")}
            </button>
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex((current) => Math.min(maxStep, current + 1));
              }}
              disabled={stepIndex >= maxStep}
            >
              {copy("runtime.replay.step")}
            </button>
            <button
              type="button"
              onClick={() => {
                setIsPlaying(false);
                setStepIndex(maxStep);
              }}
              disabled={stepIndex >= maxStep}
            >
              {copy("runtime.replay.skip")}
            </button>
          </div>
          <div className="hi-lo-replay-progress">
            {copy("runtime.replay.progress", {
              current: String(stepIndex),
              total: String(maxStep),
            })}
          </div>
        </div>

        <div className="hi-lo-replay-side">
          <div className="hi-lo-replay-meta-grid">
            <div>
              <span>{copy("runtime.replay.bet")}</span>
              <strong>{formatChipAmount(toNumericAmount(replay.bet_amount))} {copy("runtime.balance.chip_suffix")}</strong>
            </div>
            <div>
              <span>{copy("runtime.replay.payout")}</span>
              <strong>{formatChipAmount(toNumericAmount(replay.final_payout_amount ?? "0"))} {copy("runtime.balance.chip_suffix")}</strong>
            </div>
            <div>
              <span>{copy("runtime.replay.correct")}</span>
              <strong>{countSuccessfulPredictions(orderedActions)}</strong>
            </div>
            <div>
              <span>{copy("runtime.replay.started")}</span>
              <strong>{formatDateTime(replay.created_at)}</strong>
            </div>
            <div>
              <span>{copy("runtime.replay.closed")}</span>
              <strong>{replay.closed_at ? formatDateTime(replay.closed_at) : "-"}</strong>
            </div>
            <div>
              <span>{copy("runtime.replay.version")}</span>
              <strong>{replay.fairness_version}</strong>
            </div>
          </div>

          <ol className="hi-lo-replay-timeline" aria-label={copy("runtime.replay.timeline_aria")}>
            {orderedActions.map((action, index) => (
              <li
                className={`hi-lo-replay-step ${index < stepIndex ? "is-visible" : ""} ${readActionStateClass(action)}`}
                key={`${action.action_index}:${action.created_at}`}
              >
                <span>{readActionLabel(action, copy)}</span>
                <strong>{action.drawn_card?.rank_label ?? "-"}</strong>
                <small>{formatReplayMultiplier(action.multiplier_after)}x</small>
              </li>
            ))}
          </ol>

          <div className="hi-lo-replay-fairness">
            <span>{copy("runtime.replay.fairness")}</span>
            <dl>
              <div>
                <dt>{copy("runtime.replay.server_seed_hash")}</dt>
                <dd>{shortenHash(replay.server_seed_hash)}</dd>
              </div>
              <div>
                <dt>{copy("runtime.replay.client_seed")}</dt>
                <dd>{shortenHash(replay.client_seed)}</dd>
              </div>
              <div>
                <dt>{copy("runtime.replay.outcome_verification")}</dt>
                <dd>{shortenHash(replay.draw_sequence_hash)}</dd>
              </div>
              {replay.server_seed ? (
                <div>
                  <dt>{copy("runtime.replay.server_seed")}</dt>
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

function ReplayCard({ card, copy }: { card: HiLoCard | null; copy: HiLoCopyResolver }) {
  const suit = card?.suit ?? "clubs";
  const color = card?.color ?? "black";

  return (
    <div
      className={`hi-lo-card hi-lo-replay-card is-${color} suit-${suit}`}
      aria-label={card ? `${card.rank_label} ${suit}` : copy("runtime.replay.card_pending_aria")}
    >
      {card ? (
        <>
          <span className="hi-lo-card-corner">{card.rank_label}</span>
          <strong>{card.rank_label}</strong>
          <span className="hi-lo-card-suit">{suit}</span>
          <span className="hi-lo-card-corner is-bottom">{card.rank_label}</span>
        </>
      ) : (
        <strong className="hi-lo-card-rank">?</strong>
      )}
    </div>
  );
}

function readStatusLabel(replay: HiLoRoundReplay, copy: HiLoCopyResolver) {
  if (replay.outcome === "cashout") {
    return copy("runtime.replay.status_cashout");
  }
  if (replay.outcome === "loss") {
    return copy("runtime.replay.status_loss");
  }
  if (replay.outcome === "expired") {
    return copy("runtime.replay.status_expired");
  }
  if (replay.outcome === "quarantined") {
    return copy("runtime.replay.status_quarantined");
  }
  return replay.status;
}

function readOutcomeLabel(replay: HiLoRoundReplay, copy: HiLoCopyResolver) {
  if (replay.outcome === "cashout") {
    return copy("runtime.replay.outcome_cashout", {
      amount: formatChipAmount(toNumericAmount(replay.final_payout_amount ?? "0")),
      chip: copy("runtime.balance.chip_suffix"),
    });
  }
  if (replay.outcome === "loss") {
    return copy("runtime.replay.outcome_loss");
  }
  return copy("runtime.replay.outcome_snapshot");
}

function readActionLabel(action: HiLoReplayAction, copy: HiLoCopyResolver) {
  if (action.action_type === "start") {
    return copy("runtime.replay.action_start");
  }
  if (action.action_type === "active_skip") {
    return copy("runtime.replay.action_skip");
  }
  if (action.action_type === "cashout") {
    return copy("runtime.replay.action_collect");
  }
  if (action.prediction_action === "black") {
    return copy("runtime.replay.action_black");
  }
  if (action.prediction_action === "red") {
    return copy("runtime.replay.action_red");
  }
  if (action.prediction_action === "down") {
    return copy("runtime.replay.action_down");
  }
  if (action.prediction_action === "up") {
    return copy("runtime.replay.action_up");
  }
  return copy("runtime.replay.action_prediction");
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
