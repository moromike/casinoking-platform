/**
 * MinesStageHeader — Stage header card for Mines (wordmark, subtitle, payout preview, exit).
 *
 * Extracted from mines-standalone.tsx (P1-WP8).
 * Follows the stateless props pattern established by mines-board.tsx.
 */

import { useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import type { SessionSnapshot } from "@/app/lib/types";

type MinesStageHeaderProps = {
  gameTitle: string;
  titleLogoUrl?: string | null;
  titleRenderMode?: "text" | "image";
  exitAriaLabel: string;
  stageSubtitle: string | null;
  stageSubtitleTone: "won" | "lost" | null;
  previewMultipliers: string[];
  multiplierSuffix: string;
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
  gameTitle,
  titleLogoUrl = null,
  titleRenderMode = "text",
  exitAriaLabel,
  stageSubtitle,
  stageSubtitleTone,
  previewMultipliers,
  multiplierSuffix,
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
  const headingRef = useRef<HTMLDivElement | null>(null);
  const wordmarkRef = useRef<HTMLHeadingElement | null>(null);
  const [wordmarkFontSize, setWordmarkFontSize] = useState<number | null>(null);
  const shouldRenderLogo = titleRenderMode === "image" && Boolean(titleLogoUrl);
  const wordmarkStyle =
    wordmarkFontSize === null
      ? undefined
      : ({ "--mines-wordmark-font-size": `${wordmarkFontSize}px` } as CSSProperties);

  useEffect(() => {
    if (useMobileLayout || shouldRenderLogo) {
      setWordmarkFontSize(null);
      return;
    }

    const heading = headingRef.current;
    const wordmark = wordmarkRef.current;
    if (!heading || !wordmark) {
      return;
    }

    let frameId = 0;

    const syncWordmarkSize = () => {
      window.cancelAnimationFrame(frameId);
      frameId = window.requestAnimationFrame(() => {
        const styles = window.getComputedStyle(heading);
        const wordmarkStyles = window.getComputedStyle(wordmark);
        const maxFontSize = Math.max(18, parseFloat(styles.getPropertyValue("--mines-wordmark-max-font-size")) || 96);
        const minFontSize = Math.max(12, parseFloat(styles.getPropertyValue("--mines-wordmark-min-font-size")) || 18);
        const availableWidth = Math.max(1, heading.clientWidth - 24);
        const availableHeight = Math.max(
          1,
          parseFloat(styles.getPropertyValue("--mines-stage-title-slot-height")) ||
            wordmark.clientHeight ||
            maxFontSize,
        );
        const measurer = document.createElement("span");
        measurer.textContent = gameTitle;
        measurer.style.position = "fixed";
        measurer.style.left = "-9999px";
        measurer.style.top = "-9999px";
        measurer.style.visibility = "hidden";
        measurer.style.whiteSpace = "nowrap";
        measurer.style.fontFamily = wordmarkStyles.fontFamily;
        measurer.style.fontSize = `${maxFontSize}px`;
        measurer.style.fontWeight = wordmarkStyles.fontWeight;
        measurer.style.fontStyle = wordmarkStyles.fontStyle;
        measurer.style.letterSpacing = wordmarkStyles.letterSpacing;
        measurer.style.lineHeight = wordmarkStyles.lineHeight;
        measurer.style.textTransform = wordmarkStyles.textTransform;
        document.body.appendChild(measurer);
        const measuredBox = measurer.getBoundingClientRect();
        measurer.remove();
        const measuredWidth = Math.max(1, measuredBox.width);
        const measuredHeight = Math.max(1, measuredBox.height);
        const nextFontSize = Math.max(
          minFontSize,
          Math.min(
            maxFontSize,
            maxFontSize * (availableWidth / measuredWidth),
            maxFontSize * (availableHeight / measuredHeight),
          ),
        );

        setWordmarkFontSize((current) =>
          current !== null && Math.abs(current - nextFontSize) < 0.5 ? current : nextFontSize,
        );
      });
    };

    syncWordmarkSize();
    window.setTimeout(syncWordmarkSize, 250);
    if ("fonts" in document) {
      void document.fonts.ready.then(syncWordmarkSize);
    }
    const resizeObserver = new ResizeObserver(syncWordmarkSize);
    resizeObserver.observe(heading);
    window.addEventListener("resize", syncWordmarkSize);

    return () => {
      window.cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      window.removeEventListener("resize", syncWordmarkSize);
    };
  }, [gameTitle, shouldRenderLogo, useMobileLayout]);

  return (
    <article className="mines-stage-card">
      <div className="mines-stage-topbar">
        <div className="mines-stage-heading" ref={headingRef}>
          {mobileStageTools}
          {shouldRenderLogo ? (
            <img className="mines-title-logo" src={titleLogoUrl ?? ""} alt={gameTitle} />
          ) : (
            <h3 className="mines-wordmark" ref={wordmarkRef} style={wordmarkStyle}>{gameTitle}</h3>
          )}
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
                  {multiplier}{multiplierSuffix}
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
              aria-label={exitAriaLabel}
            >
              X
            </button>
          </div>
        ) : null}
      </div>
    </article>
  );
}
