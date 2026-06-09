"use client";

import { useEffect, useState } from "react";

export function BoxeWinCelebration({
  amount,
  kind,
  onDismiss,
}: {
  amount: string;
  kind: "cashout" | "top_row";
  onDismiss: () => void;
}) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
    const timer = window.setTimeout(() => {
      setVisible(false);
      onDismiss();
    }, 2600);
    return () => window.clearTimeout(timer);
  }, [amount, kind, onDismiss]);

  if (!visible) {
    return null;
  }

  return (
    <button
      aria-label="Chiudi celebrazione vincita"
      className="boxe-win-celebration"
      data-testid="boxe-win-celebration"
      onClick={() => {
        setVisible(false);
        onDismiss();
      }}
      type="button"
    >
      <span className="boxe-win-copy">
        <strong>{kind === "top_row" ? "Top row!" : "Win!"}</strong>
        <em>{amount} CHIP</em>
      </span>
      {Array.from({ length: 12 }, (_item, index) => (
        <i aria-hidden="true" className="boxe-win-confetti" key={index} />
      ))}
    </button>
  );
}
