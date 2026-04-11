/**
 * MinesActionButtons — Bet and Collect action buttons for Mines.
 *
 * Extracted from mines-standalone.tsx (P1-WP6).
 * Follows the stateless props pattern established by mines-board.tsx.
 *
 * IMPORTANT: Bet button must be type="submit", Collect button must be type="button".
 */

import { Button } from "../components/button";

type MinesActionButtonsProps = {
  useMobileLayout: boolean;
  betButtonLabel: string;
  collectButtonLabel: string;
  isBetDisabled: boolean;
  isCollectDisabled: boolean;
  isBetLoading: boolean;
  isCollectLoading: boolean;
  onCashout: () => void;
};

export function MinesActionButtons({
  useMobileLayout,
  betButtonLabel,
  collectButtonLabel,
  isBetDisabled,
  isCollectDisabled,
  isBetLoading,
  isCollectLoading,
  onCashout,
}: MinesActionButtonsProps) {
  return (
    <div className={`actions mines-action-buttons ${useMobileLayout ? "mines-mobile-actions" : "mines-desktop-actions"}`}>
      <Button type="submit" disabled={isBetDisabled} isLoading={isBetLoading}>
        {betButtonLabel}
      </Button>
      <Button
        type="button"
        disabled={isCollectDisabled}
        isLoading={isCollectLoading}
        variant="secondary"
        onClick={onCashout}
      >
        {collectButtonLabel}
      </Button>
    </div>
  );
}
