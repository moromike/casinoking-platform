"use client";

import { GameInfoRulesModal } from "@/app/ui/game-runtime/game-info-rules-modal";
import type { BoxeCopyResolver } from "./boxe-i18n/boxe-copy-defaults";
import type { BoxeRuntimeConfig } from "./use-boxe-runtime";

type BoxeRulesModalProps = {
  copy: BoxeCopyResolver;
  gameTitle: string;
  locale: string;
  runtimeConfig: BoxeRuntimeConfig;
  onClose: () => void;
};

export function BoxeRulesModal({
  copy,
  gameTitle,
  locale,
  runtimeConfig,
  onClose,
}: BoxeRulesModalProps) {
  const rulesHtml =
    readBoxeRulesHtml(runtimeConfig, locale) ?? `<p>${escapeHtml(copy("rules.bet_collect"))}</p>`;

  return (
    <GameInfoRulesModal
      activeTab="rules"
      copy={{
        dialogAriaLabel: copy("rules.dialog_aria", { gameTitle }),
        title: copy("rules.header_title", { gameTitle }),
        intro: copy("rules.intro"),
        closeAriaLabel: copy("rules.close_aria"),
      }}
      onClose={onClose}
      onTabChange={() => {}}
      tabs={[{ id: "rules", label: copy("rules.rules_tab") }]}
    >
      <div className="mines-rules-body boxe-rules-body">
        <section>
          <h4>{copy("rules.bet_collect_heading")}</h4>
          <div dangerouslySetInnerHTML={{ __html: rulesHtml }} />
        </section>
      </div>
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
