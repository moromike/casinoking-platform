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
  copy: {
    dialogAriaLabel: string;
    title: string;
    intro: string;
    closeAriaLabel: string;
    waysToWin: string;
    payoutDisplay: string;
    safeRevealLabel: (step: number) => string;
    multiplierSuffix: string;
    settingsMenu: string;
    betCollect: string;
  };
  onClose: () => void;
};

export function MinesRulesModal({
  rulesSections,
  payoutLadder,
  selectedGridSize,
  selectedMineCount,
  copy,
  onClose,
}: MinesRulesModalProps) {
  const waysToWinHtml = readRuleSectionHtml(rulesSections.ways_to_win);
  const payoutDisplayHtml = readRuleSectionHtml(rulesSections.payout_display);
  const settingsMenuHtml = readRuleSectionHtml(rulesSections.settings_menu);
  const betCollectHtml = readRuleSectionHtml(rulesSections.bet_collect);

  return (
    <div className="mines-rules-overlay" role="presentation" onClick={onClose}>
      <article
        className="mines-rules-modal"
        role="dialog"
        aria-modal="true"
        aria-label={copy.dialogAriaLabel}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mines-rules-header">
          <div>
            <h3>{copy.title}</h3>
            <p>{copy.intro}</p>
          </div>
          <button
            className="button-ghost mines-rules-close"
            type="button"
            aria-label={copy.closeAriaLabel}
            onClick={onClose}
          >
            X
          </button>
        </div>
        <div className="mines-rules-body">
          <section>
            <h4>{copy.waysToWin}</h4>
            <div dangerouslySetInnerHTML={{ __html: waysToWinHtml }} />
          </section>
          <section>
            <h4>{copy.payoutDisplay}</h4>
            <div dangerouslySetInnerHTML={{ __html: payoutDisplayHtml }} />
            <div className="payout-ladder-list">
              {payoutLadder.slice(0, 8).map((multiplier, index) => (
                <article className="payout-ladder-row" key={`${selectedGridSize}-${selectedMineCount}-${index}`}>
                  <span className="list-muted">
                    {copy.safeRevealLabel(index + 1)}
                  </span>
                  <strong>{multiplier}{copy.multiplierSuffix}</strong>
                </article>
              ))}
            </div>
          </section>
          <section>
            <h4>{copy.settingsMenu}</h4>
            <div dangerouslySetInnerHTML={{ __html: settingsMenuHtml }} />
          </section>
          <section>
            <h4>{copy.betCollect}</h4>
            <div dangerouslySetInnerHTML={{ __html: betCollectHtml }} />
          </section>
        </div>
      </article>
    </div>
  );
}

function readRuleSectionHtml(value: string | undefined): string {
  if (!value) {
    return "";
  }

  const plainText = value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
  if (!plainText || plainText === "x") {
    return "";
  }

  return value;
}
