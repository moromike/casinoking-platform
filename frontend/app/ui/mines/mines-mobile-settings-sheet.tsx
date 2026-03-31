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
  onClose: () => void;
  children: ReactNode;
};

export function MinesMobileSettingsSheet({
  isDemoPlayer,
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
        aria-label="Game settings"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mines-mobile-settings-header">
          <div>
            <h3>Game settings</h3>
            {isDemoPlayer ? <span className="status-badge info mines-mode-badge">DEMO MODE</span> : null}
          </div>
          <button
            className="button-ghost mines-mobile-settings-close"
            type="button"
            onClick={onClose}
          >
            Done
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
