"use client";

import type { ReactNode } from "react";
import { GameInfoRulesModal } from "@/app/ui/game-runtime/game-info-rules-modal";
import type { BoxeCopyResolver } from "./boxe-i18n/boxe-copy-defaults";
import type { BoxeRuntimeConfig } from "./use-boxe-runtime";

export type BoxeRulesModalTab = "rules" | "replay";

type BoxeRulesModalProps = {
  activeTab?: BoxeRulesModalTab;
  copy: BoxeCopyResolver;
  gameTitle: string;
  locale: string;
  onTabChange?: (tab: BoxeRulesModalTab) => void;
  replayAvailable?: boolean;
  replayContent?: ReactNode;
  runtimeConfig: BoxeRuntimeConfig;
  onClose: () => void;
};

export function BoxeRulesModal({
  activeTab = "rules",
  copy,
  gameTitle,
  locale,
  onTabChange = () => {},
  replayAvailable = false,
  replayContent,
  runtimeConfig,
  onClose,
}: BoxeRulesModalProps) {
  const rulesHtml =
    readBoxeRulesHtml(runtimeConfig, locale) ?? `<p>${escapeHtml(copy("rules.bet_collect"))}</p>`;
  const tabs = [
    { id: "rules", label: copy("rules.rules_tab") },
    ...(replayContent
      ? [{ id: "replay", label: copy("rules.replay_tab"), disabled: !replayAvailable }]
      : []),
  ];

  function handleTabChange(tab: string) {
    if (tab === "replay" && !replayAvailable) {
      return;
    }
    if (tab === "rules" || tab === "replay") {
      onTabChange(tab);
    }
  }

  return (
    <GameInfoRulesModal
      activeTab={activeTab}
      copy={{
        dialogAriaLabel: copy("rules.dialog_aria", { gameTitle }),
        title: copy("rules.header_title", { gameTitle }),
        intro: copy("rules.intro"),
        closeAriaLabel: copy("rules.close_aria"),
      }}
      onClose={onClose}
      onTabChange={handleTabChange}
      tabs={tabs}
    >
      {activeTab === "replay" ? (
        <div className="mines-rules-body mines-rules-replay-body boxe-rules-replay-body">
          {replayAvailable ? replayContent : <p className="empty-state">{copy("rules.replay_unavailable")}</p>}
        </div>
      ) : (
        <div className="mines-rules-body boxe-rules-body">
          <section>
            <h4>{copy("rules.bet_collect_heading")}</h4>
            <div dangerouslySetInnerHTML={{ __html: rulesHtml }} />
          </section>
        </div>
      )}
    </GameInfoRulesModal>
  );
}

function readBoxeRulesHtml(
  runtimeConfig: BoxeRuntimeConfig,
  locale: string,
): string | null {
  const rulesByLocale = runtimeConfig.presentation_config?.rules_html;
  if (!rulesByLocale) {
    return null;
  }

  const defaultLocale = runtimeConfig.presentation_config?.default_locale ?? "it";
  const localeRules = rulesByLocale[locale] ?? rulesByLocale[defaultLocale] ?? rulesByLocale.it;
  const rulesHtml = localeRules?.bet_collect;
  if (!rulesHtml?.trim()) {
    return null;
  }
  return rulesHtml;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
