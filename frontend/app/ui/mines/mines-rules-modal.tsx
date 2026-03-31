/**
 * MinesRulesModal — Game info / rules overlay for Mines.
 *
 * Extracted from mines-standalone.tsx (P1-WP4).
 * Follows the stateless props pattern established by mines-board.tsx.
 * Preserves dangerouslySetInnerHTML intentionally (rules come from backoffice config).
 */

type MinesRulesModalProps = {
  rulesSections: Record<string, string>;
  payoutLadder: string[];
  selectedGridSize: number;
  selectedMineCount: number;
  onClose: () => void;
};

export function MinesRulesModal({
  rulesSections,
  payoutLadder,
  selectedGridSize,
  selectedMineCount,
  onClose,
}: MinesRulesModalProps) {
  return (
    <div className="mines-rules-overlay" role="presentation" onClick={onClose}>
      <article
        className="mines-rules-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Game info Mines"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mines-rules-header">
          <div>
            <h3>GAME INFO - MINES</h3>
            <p>Rules readable from the table, focused on actual gameplay.</p>
          </div>
          <button className="button-ghost mines-rules-close" type="button" onClick={onClose}>
            x
          </button>
        </div>
        <div className="mines-rules-body">
          <section>
            <h4>Ways to win</h4>
            <div dangerouslySetInnerHTML={{ __html: rulesSections.ways_to_win ?? "" }} />
          </section>
          <section>
            <h4>Payout display</h4>
            <div dangerouslySetInnerHTML={{ __html: rulesSections.payout_display ?? "" }} />
            <div className="payout-ladder-list">
              {payoutLadder.slice(0, 8).map((multiplier, index) => (
                <article className="payout-ladder-row" key={`${selectedGridSize}-${selectedMineCount}-${index}`}>
                  <span className="list-muted">Safe reveal {String(index + 1).padStart(2, "0")}</span>
                  <strong>{multiplier}x</strong>
                </article>
              ))}
            </div>
          </section>
          <section>
            <h4>Settings menu</h4>
            <div dangerouslySetInnerHTML={{ __html: rulesSections.settings_menu ?? "" }} />
          </section>
          <section>
            <h4>Bet & collect</h4>
            <div dangerouslySetInnerHTML={{ __html: rulesSections.bet_collect ?? "" }} />
          </section>
        </div>
      </article>
    </div>
  );
}
