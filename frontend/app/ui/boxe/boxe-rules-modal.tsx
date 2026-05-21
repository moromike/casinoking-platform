"use client";

import type { ReactNode } from "react";
import { GameInfoRulesModal } from "@/app/ui/game-runtime/game-info-rules-modal";
import {
  BOXE_DEFAULT_RULE_SECTIONS,
  BOXE_RULE_SECTION_DEFINITIONS,
  BOXE_RULE_SECTION_KEYS,
  BOXE_SUPPORTED_LOCALES,
  type BoxeCopyKey,
  type BoxeCopyResolver,
  type BoxeLocale,
  type BoxeRuleSectionKey,
} from "./boxe-i18n/boxe-copy-defaults";
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
  const rulesSections = readBoxeRuleSections(runtimeConfig, locale);
  const visibleRulesSections = BOXE_RULE_SECTION_DEFINITIONS.map((section) => ({
    key: section.key,
    heading: copy(readBoxeRuleSectionHeadingKey(section.key)),
  }));
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
          {visibleRulesSections.map((section) => (
            <section key={section.key}>
              <h4>{section.heading}</h4>
              <div dangerouslySetInnerHTML={{ __html: rulesSections[section.key] }} />
            </section>
          ))}
        </div>
      )}
    </GameInfoRulesModal>
  );
}

function readBoxeRuleSectionHeadingKey(sectionKey: BoxeRuleSectionKey): BoxeCopyKey {
  return sectionKey === "bet_collect"
    ? "rules.bet_collect_heading"
    : (`rules.${sectionKey}` as BoxeCopyKey);
}

function readBoxeRuleSections(
  runtimeConfig: BoxeRuntimeConfig,
  locale: string,
): Record<BoxeRuleSectionKey, string> {
  const localeCode = resolveModalLocale(locale);
  const defaultLocale = resolveModalLocale(runtimeConfig.presentation_config?.default_locale);
  const rulesByLocale = runtimeConfig.presentation_config?.rules_html;
  const localeRules =
    rulesByLocale?.[locale] ??
    rulesByLocale?.[localeCode] ??
    rulesByLocale?.[defaultLocale] ??
    rulesByLocale?.it;
  const defaultSections = BOXE_DEFAULT_RULE_SECTIONS[localeCode] ?? BOXE_DEFAULT_RULE_SECTIONS.it;
  const sections = {} as Record<BoxeRuleSectionKey, string>;

  for (const key of BOXE_RULE_SECTION_KEYS) {
    sections[key] =
      readRuleSectionHtml(localeRules?.[key]) ??
      defaultSections[key]?.body_html ??
      `<p>${escapeHtml(key)}</p>`;
  }

  return sections;
}

function resolveModalLocale(locale: string | undefined): BoxeLocale {
  const normalized = (locale ?? "it").slice(0, 2).toLowerCase();
  return BOXE_SUPPORTED_LOCALES.includes(normalized as BoxeLocale)
    ? (normalized as BoxeLocale)
    : "it";
}

function readRuleSectionHtml(value: string | undefined): string | null {
  if (!value) {
    return null;
  }

  const plainText = value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
  if (!plainText || plainText === "x") {
    return null;
  }

  return value;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
