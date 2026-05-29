"use client";

import type { MinesReplayViewerCopy } from "./mines-replay-viewer";

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
  snapshotLabel: "Fotografia finale",
  activeRoundWarning: "Round ancora aperto: le mine nascoste non vengono mostrate.",
  formatStatus: (status) => readReplayStatusLabel(status),
  formatConfig: (gridSize, mineCount) => `${gridSize} celle - ${mineCount} mine`,
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
