/**
 * MinesStageHeader — Stage header card for Mines (wordmark, subtitle, payout preview, exit).
 *
 * Extracted from mines-standalone.tsx (P1-WP8).
 * Follows the stateless props pattern established by mines-board.tsx.
 */

import type { ReactNode } from "react";
import type { SessionSnapshot } from "@/app/lib/types";

type MinesStageHeaderProps = {
  stageSubtitle: string | null;
  stageSubtitleTone: "won" | "lost" | null;
  previewMultipliers: string[];
  previewWindowStart: number;
  visibleGridSize: number;
  selectedMineCount: number;
  currentSession: SessionSnapshot | null;
  isEmbeddedView: boolean;
  isHostFullscreen: boolean;
  useMobileLayout: boolean;
  mobileStageTools: ReactNode;
  onExit: () => void;
};

export function MinesStageHeader({
  stageSubtitle,
  stageSubtitleTone,
  previewMultipliers,
  previewWindowStart,
  visibleGridSize,
  selectedMineCount,
  currentSession,
  isEmbeddedView,
  isHostFullscreen,
  useMobileLayout,
  mobileStageTools,
  onExit,
}: MinesStageHeaderProps) {
  return (
    <article className="mines-stage-card">
      <div className="mines-stage-topbar">
        <div className="mines-stage-heading">
          {mobileStageTools}
          <h3 className="mines-wordmark">MINES</h3>
          <p className={stageSubtitleTone ? `mines-stage-subtitle mines-stage-subtitle-${stageSubtitleTone}` : "mines-stage-subtitle"}>
            {stageSubtitle ?? "\u00A0"}
          </p>
          <div className="mines-stage-quickbar">
            <div className="mines-payout-preview">
              {previewMultipliers.map((multiplier, index) => (
                <span
                  className={
                    index === 0
                      ? "mines-preview-chip active"
                      : "mines-preview-chip"
                  }
                  key={`${visibleGridSize}-${currentSession?.mine_count ?? selectedMineCount}-${previewWindowStart + index}`}
                >
                  {multiplier}x
                </span>
              ))}
            </div>
          </div>
        </div>
        {!isEmbeddedView && !isHostFullscreen && !useMobileLayout ? (
          <div className="mines-stage-actions">
            <button
              className="button-ghost mines-icon-close"
              type="button"
              onClick={onExit}
              aria-label="Exit Mines"
            >
              X
            </button>
          </div>
        ) : null}
      </div>
    </article>
  );
}
