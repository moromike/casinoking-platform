"use client";

import type { ReactNode } from "react";
import { GameInfoRulesModal } from "@/app/ui/game-runtime/game-info-rules-modal";
import {
  createHiLoCopyResolver,
  HI_LO_DEFAULT_RULE_SECTIONS,
  HI_LO_RULE_SECTION_DEFINITIONS,
  HI_LO_RULE_SECTION_KEYS,
  type HiLoCopyKey,
  type HiLoCopyResolver,
  type HiLoRuleSectionKey,
} from "./hi-lo-i18n/hi-lo-copy-defaults";
import type { HiLoRuntimeConfig } from "./use-hi-lo-runtime";

export type HiLoRulesModalTab = "rules" | "replay";

type HiLoRulesModalProps = {
  activeTab?: HiLoRulesModalTab;
  copy?: HiLoCopyResolver;
  gameTitle: string;
  locale: string;
  onTabChange?: (tab: HiLoRulesModalTab) => void;
  replayAvailable?: boolean;
  replayContent?: ReactNode;
  runtimeConfig: HiLoRuntimeConfig;
  onClose: () => void;
};

export function HiLoRulesModal({
  activeTab = "rules",
  copy: providedCopy,
  gameTitle,
  locale,
  onTabChange = () => {},
  replayAvailable = false,
  replayContent,
  runtimeConfig,
  onClose,
}: HiLoRulesModalProps) {
  const copy = providedCopy ?? createHiLoCopyResolver(locale);
  const rulesSections = readHiLoRuleSections(runtimeConfig, locale);
  const visibleRulesSections = HI_LO_RULE_SECTION_DEFINITIONS.map((section) => ({
    key: section.key,
    heading: copy(readHiLoRuleSectionHeadingKey(section.key)),
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
        <div className="mines-rules-body mines-rules-replay-body hi-lo-rules-replay-body">
          {replayAvailable ? replayContent : <p className="empty-state">{copy("rules.replay_unavailable")}</p>}
        </div>
      ) : (
        <div className="mines-rules-body hi-lo-rules-body">
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

function readHiLoRuleSectionHeadingKey(sectionKey: HiLoRuleSectionKey): HiLoCopyKey {
  return sectionKey === "bet_predict_collect"
    ? "rules.bet_predict_collect_heading"
    : (`rules.${sectionKey}` as HiLoCopyKey);
}

function readHiLoRuleSections(
  runtimeConfig: HiLoRuntimeConfig,
  locale: string,
): Record<HiLoRuleSectionKey, string> {
  const localeCode = resolveModalLocale(locale);
  const defaultLocale = resolveModalLocale(runtimeConfig.presentation_config?.default_locale);
  const rulesByLocale = runtimeConfig.presentation_config?.rules_html;
  const localeRules =
    rulesByLocale?.[locale] ??
    rulesByLocale?.[localeCode] ??
    rulesByLocale?.[defaultLocale] ??
    rulesByLocale?.it;
  const defaultSections = HI_LO_DEFAULT_RULE_SECTIONS[localeCode] ?? HI_LO_DEFAULT_RULE_SECTIONS.it;
  const sections = {} as Record<HiLoRuleSectionKey, string>;

  for (const key of HI_LO_RULE_SECTION_KEYS) {
    sections[key] =
      readRuleSectionHtml(localeRules?.[key]) ??
      defaultSections[key]?.body_html ??
      `<p>${escapeHtml(key)}</p>`;
  }

  return sections;
}

function resolveModalLocale(locale: string | undefined) {
  const normalized = (locale ?? "it").slice(0, 2).toLowerCase();
  return normalized === "en" || normalized === "de" || normalized === "es" ? normalized : "it";
}

function readRuleSectionHtml(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  if (value && typeof value === "object" && "body_html" in value) {
    const body = (value as { body_html?: unknown }).body_html;
    return typeof body === "string" && body.trim().length > 0 ? body : null;
  }
  return null;
}

function escapeHtml(value: string) {
  return value
    .split("&").join("&amp;")
    .split("<").join("&lt;")
    .split(">").join("&gt;")
    .split('"').join("&quot;")
    .split("'").join("&#039;");
}
