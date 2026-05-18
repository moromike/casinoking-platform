"use client";

export function BoxePayoutDisplay({
  multipliers,
  currentStep,
  activeRow,
}: {
  multipliers: string[];
  currentStep: number;
  activeRow: number | null;
}) {
  return (
    <section className="boxe-payout-display" aria-label="BOXE multiplier ladder">
      <div className="boxe-payout-ladder">
        {multipliers.map((multiplier, index) => {
          const step = index + 1;
          const isReached = step <= currentStep;
          const isCurrent = step === currentStep && currentStep > 0;
          const isNext = activeRow !== null && step === activeRow + 1;
          return (
            <span
              className={[
                "boxe-payout-step",
                isReached ? "reached" : "",
                isCurrent ? "current" : "",
                isNext ? "next" : "",
              ].filter(Boolean).join(" ")}
              data-current={isCurrent ? "true" : "false"}
              data-testid={isCurrent ? "boxe-payout-current" : undefined}
              key={`${multiplier}-${step}`}
            >
              <strong>{multiplier}x</strong>
              {isNext ? <em>mine risk</em> : null}
            </span>
          );
        })}
      </div>
    </section>
  );
}
