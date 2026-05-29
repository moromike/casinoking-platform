"use client";

import type { ReactNode } from "react";
import type { TitleEditorTabDefinition } from "./types";

type TitleEditorTabFrameProps<TTab extends string> = {
  activeTab: TTab;
  tabs: readonly TitleEditorTabDefinition<TTab>[];
  onTabChange: (tab: TTab) => void;
  children: ReactNode;
};

export function TitleEditorTabFrame<TTab extends string>({
  activeTab,
  tabs,
  onTabChange,
  children,
}: TitleEditorTabFrameProps<TTab>) {
  return (
    <>
      <div className="admin-subnav editor-subnav">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab.id ? "button" : "button-secondary"}
            key={tab.id}
            type="button"
            onClick={() => {
              tab.onSelect?.();
              onTabChange(tab.id);
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {children}
    </>
  );
}
