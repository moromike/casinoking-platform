/**
 * MinesMobileSettingsSheet — Mobile settings overlay for Mines.
 *
 * Extracted from mines-standalone.tsx (P1-WP7).
 * Follows the stateless props pattern established by mines-board.tsx.
 * Receives configFields as children.
 */

import type { ReactNode } from "react";

type MinesMobileSettingsSheetProps = {
  isDemoPlayer: boolean;
  title: string;
  doneLabel: string;
  demoBadgeLabel: string;
  onClose: () => void;
  children: ReactNode;
};

export function MinesMobileSettingsSheet({
  isDemoPlayer,
  title,
  doneLabel,
  demoBadgeLabel,
  onClose,
  children,
}: MinesMobileSettingsSheetProps) {
  return (
    <div
      className="mines-mobile-settings-overlay"
      role="presentation"
      onClick={onClose}
    >
      <section
        className="session-actions mines-control-rail mines-control-rail-clean mines-mobile-settings-sheet"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mines-mobile-settings-header">
          <div>
            <h3>{title}</h3>
            {isDemoPlayer ? (
              <span className="status-badge info mines-mode-badge">{demoBadgeLabel}</span>
            ) : null}
          </div>
          <button
            className="button-ghost mines-mobile-settings-close"
            type="button"
            onClick={onClose}
          >
            {doneLabel}
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
