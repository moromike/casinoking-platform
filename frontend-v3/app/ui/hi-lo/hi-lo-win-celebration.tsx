"use client";

import { useEffect, useState } from "react";

export function HiLoWinCelebration({
  amount,
  onDismiss,
}: {
  amount: string;
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
  }, [amount, onDismiss]);

  if (!visible) {
    return null;
  }

  return (
    <button
      aria-label="Chiudi celebrazione vincita"
      className="hi-lo-win-celebration"
      data-testid="hi-lo-win-celebration"
      onClick={() => {
        setVisible(false);
        onDismiss();
      }}
      type="button"
    >
      <span className="hi-lo-win-copy">
        <strong>Win!</strong>
        <em>{amount} CHIP</em>
      </span>
      {Array.from({ length: 13 }, (_item, index) => (
        <i aria-hidden="true" className="hi-lo-win-confetti" key={index} />
      ))}
    </button>
  );
}
