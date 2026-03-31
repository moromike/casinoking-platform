/**
 * MinesActionButtons — Bet and Collect action buttons for Mines.
 *
 * Extracted from mines-standalone.tsx (P1-WP6).
 * Follows the stateless props pattern established by mines-board.tsx.
 *
 * IMPORTANT: Bet button must be type="submit", Collect button must be type="button".
 */

type MinesActionButtonsProps = {
  useMobileLayout: boolean;
  betButtonLabel: string;
  collectButtonLabel: string;
  isBetDisabled: boolean;
  isCollectDisabled: boolean;
  onCashout: () => void;
};

export function MinesActionButtons({
  useMobileLayout,
  betButtonLabel,
  collectButtonLabel,
  isBetDisabled,
  isCollectDisabled,
  onCashout,
}: MinesActionButtonsProps) {
  return (
    <div className={`actions mines-action-buttons ${useMobileLayout ? "mines-mobile-actions" : "mines-desktop-actions"}`}>
      <button
        className="button"
        type="submit"
        disabled={isBetDisabled}
      >
        {betButtonLabel}
      </button>
      <button
        className="button-secondary"
        type="button"
        disabled={isCollectDisabled}
        onClick={onCashout}
      >
        {collectButtonLabel}
      </button>
    </div>
  );
}
