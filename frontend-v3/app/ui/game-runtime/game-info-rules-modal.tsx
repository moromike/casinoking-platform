"use client";

import { useEffect, type ReactNode } from "react";

export type GameInfoRulesModalTab = {
  id: string;
  label: string;
  disabled?: boolean;
};

type GameInfoRulesModalProps = {
  activeTab: string;
  children: ReactNode;
  copy: {
    dialogAriaLabel: string;
    title: string;
    intro: string;
    closeAriaLabel: string;
  };
  onClose: () => void;
  onTabChange: (tab: string) => void;
  tabs: GameInfoRulesModalTab[];
};

export function GameInfoRulesModal({
  activeTab,
  children,
  copy,
  onClose,
  onTabChange,
  tabs,
}: GameInfoRulesModalProps) {
  const shouldShowTabs = tabs.length > 1;

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="game-info-rules-overlay" role="presentation" onClick={onClose}>
      <article
        className="game-info-rules-modal"
        role="dialog"
        aria-modal="true"
        aria-label={copy.dialogAriaLabel}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="game-info-rules-header">
          <div>
            <h3>{copy.title}</h3>
            <p>{copy.intro}</p>
          </div>
          <button
            className="button-ghost game-info-rules-close"
            type="button"
            aria-label={copy.closeAriaLabel}
            onClick={onClose}
          >
            X
          </button>
        </div>
        {shouldShowTabs ? (
          <div className="game-info-rules-tabs" role="tablist" aria-label={copy.title}>
            {tabs.map((tab) => (
              <button
                className={`game-info-rules-tab${activeTab === tab.id ? " is-active" : ""}`}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-disabled={tab.disabled}
                onClick={() => onTabChange(tab.id)}
                key={tab.id}
              >
                {tab.label}
              </button>
            ))}
          </div>
        ) : null}

        {children}
      </article>
    </div>
  );
}
