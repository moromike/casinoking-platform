"use client";

import { formatChipAmount, toNumericAmount } from "@/app/lib/helpers";

import type { MinesReplayStep, MinesReplayViewerCopy } from "./mines-replay-viewer";

export const DEFAULT_MINES_REPLAY_COPY: MinesReplayViewerCopy = {
  title: "Replay mano",
  statusLabel: "Esito",
  configLabel: "Config",
  betLabel: "Puntata",
  payoutLabel: "Vinto",
  revealedLabel: "Safe reveal",
  fairnessLabel: "Fairness",
  boardHashLabel: "Board hash",
  seedHashLabel: "Seed hash",
  nonceLabel: "Nonce",
  startAction: "Inizio",
  previousAction: "Indietro",
  nextAction: "Avanti",
  finalAction: "Finale",
  noStepsLabel: "Nessuna scelta registrata per questo round.",
  activeRoundWarning: "Round ancora aperto: le mine nascoste non vengono mostrate.",
  formatStatus: (status) => readReplayStatusLabel(status),
  formatConfig: (gridSize, mineCount) => `${gridSize} celle - ${mineCount} mine`,
  formatFrame: (currentFrame, totalFrames, stage) => {
    if (stage === "start") {
      return `Inizio replay ${currentFrame}/${totalFrames}`;
    }
    if (stage === "final") {
      return `Board finale ${currentFrame}/${totalFrames}`;
    }
    return `Scelta ${currentFrame - 1} - frame ${currentFrame}/${totalFrames}`;
  },
  formatStep: (step: MinesReplayStep) => {
    const resultLabel = step.result === "mine" ? "mina" : "safe";
    const payout = formatChipAmount(toNumericAmount(step.payout_amount));
    return `Cella ${step.cell_index + 1} - ${resultLabel} - payout ${payout} CHIP`;
  },
  board: {
    mineAriaLabel: (cell) => `Cella ${cell}, mina`,
    safeAriaLabel: (cell) => `Cella ${cell}, sicura`,
    hiddenAriaLabel: (cell) => `Cella ${cell}, coperta`,
    mineFace: "MINA",
    safeFace: "SICURA",
    hiddenFace: "COPERTA",
  },
};

function readReplayStatusLabel(status: "active" | "won" | "lost" | "cancelled"): string {
  switch (status) {
    case "active":
      return "In corso";
    case "won":
      return "Vinta";
    case "lost":
      return "Persa";
    case "cancelled":
      return "Annullata";
    default:
      return status;
  }
}
