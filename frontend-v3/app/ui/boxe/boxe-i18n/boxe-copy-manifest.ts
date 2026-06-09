"use client";

import {
  BOXE_COPY_DEFINITIONS,
  BOXE_RULE_SECTION_KEYS,
  type BoxeCopyKey,
  type BoxeLocale,
  type BoxeRuleSectionKey,
} from "./boxe-copy-defaults";

export type BoxeCopyFormat = "plain" | "template" | "suffix";

export type BoxeCopyManifestDefinition = {
  key: BoxeCopyKey;
  label: string;
  required: true;
  maxLength: number;
  format: BoxeCopyFormat;
  placeholders?: string[];
  helper?: string;
};

export type BoxeCopyValidationIssue = {
  id: string;
  path: string;
  message: string;
  severity: "error";
};

type BoxeCopyValidationPayload = {
  copy: Partial<Record<BoxeLocale, Partial<Record<BoxeCopyKey, string>>>>;
  rules_html: Partial<Record<BoxeLocale, Partial<Record<BoxeRuleSectionKey, string>>>>;
};

const BOXE_COPY_PLACEHOLDERS: Partial<Record<BoxeCopyKey, string[]>> = {
  "actions.collect_with_amount": ["amount"],
  "actions.exit_aria": ["gameTitle"],
  "round.won_notice": ["amount"],
  "round.top_row_win": ["amount"],
  "round.won_amount": ["amount"],
  "settings.row_count_label": ["count"],
  "settings.difficulty_label": ["difficulty"],
  "balance.wallet": ["walletType"],
  "rules.dialog_aria": ["gameTitle"],
  "rules.header_title": ["gameTitle"],
  "format.cells": ["count"],
  "format.rows": ["count"],
  "launch.available_balance": ["amount"],
  "launch_cashier.cash_balance": ["amount"],
  "launch_cashier.bonus_balance": ["amount"],
  "launch_cashier.demo_balance_value": ["amount"],
  "runtime.session_expiring_text": ["seconds"],
  "board.aria.mine": ["cell"],
  "board.aria.safe": ["cell"],
  "board.aria.hidden": ["cell"],
};

const BOXE_COPY_HELPERS: Partial<Record<BoxeCopyKey, string>> = {
  "settings.rows": "Player-selectable row count label; supported values are 4-8.",
  "settings.difficulty": "Player-selectable difficulty label for easy, medium and hard.",
  "settings.row_count_label": "Template for the selected row count.",
  "settings.difficulty_label": "Template for the selected difficulty.",
  "rules.payout_display": "Heading for the multiplier ladder section.",
  "rules.payout_rules": "Heading for backend-owned payout rules.",
  "rules.fairness_explain": "Heading for server-authoritative fairness and RTP notes.",
  "rules.board_mechanics": "Heading for pyramid and reveal rules.",
  "rules.difficulty_semantics": "Heading for easy, medium and hard semantics.",
  "rules.max_win_cap": "Heading for the v1 max win cap note.",
  "info.payout_display": "Short player-facing summary for the multiplier ladder.",
  "info.payout_rules": "Short player-facing summary for payout calculation.",
  "info.fairness_explain": "Short player-facing summary for server authority and RTP.",
  "info.board_mechanics": "Short player-facing summary for pyramid mechanics.",
  "info.difficulty_semantics": "Short player-facing summary for difficulty risk.",
  "info.max_win_cap": "Short player-facing summary for the v1 cap behavior.",
  "states.choose_safe": "Runtime state shown while the player must pick a safe box.",
  "states.pick_next": "Runtime state shown after a safe pick advances the round.",
};

export const BOXE_COPY_MANIFEST: readonly BoxeCopyManifestDefinition[] =
  BOXE_COPY_DEFINITIONS.map((definition) => {
    const placeholders = BOXE_COPY_PLACEHOLDERS[definition.key];
    const format: BoxeCopyFormat = definition.key.endsWith("_suffix")
      ? "suffix"
      : placeholders?.length
        ? "template"
        : "plain";

    return {
      ...definition,
      required: true,
      format,
      ...(placeholders ? { placeholders } : {}),
      ...(BOXE_COPY_HELPERS[definition.key]
        ? { helper: BOXE_COPY_HELPERS[definition.key] }
        : {}),
    };
  });

export const BOXE_COPY_KEYS = BOXE_COPY_MANIFEST.map((entry) => entry.key);

export function validateBoxeCopyAndRulesPayload(
  payload: BoxeCopyValidationPayload,
  locales: readonly BoxeLocale[],
): BoxeCopyValidationIssue[] {
  const issues: BoxeCopyValidationIssue[] = [];

  for (const locale of locales) {
    for (const definition of BOXE_COPY_MANIFEST) {
      const value = payload.copy[locale]?.[definition.key] ?? "";
      const path = `${locale}.copy.${definition.key}`;
      const detail = formatDefinitionDetail(definition);
      if (definition.required && !value.trim()) {
        issues.push({
          id: `${path}.required`,
          path,
          message: `Required copy is empty.${detail}`,
          severity: "error",
        });
      }
      if (value.length > definition.maxLength) {
        issues.push({
          id: `${path}.maxLength`,
          path,
          message: `Copy is ${value.length} characters; maximum is ${definition.maxLength}.${detail}`,
          severity: "error",
        });
      }
    }

    for (const key of BOXE_RULE_SECTION_KEYS) {
      const path = `${locale}.rules_html.${key}`;
      if (!payload.rules_html[locale]?.[key]?.trim()) {
        issues.push({
          id: `${path}.required`,
          path,
          message: "Required rules HTML is empty.",
          severity: "error",
        });
      }
    }
  }

  return issues;
}

function formatDefinitionDetail(definition: BoxeCopyManifestDefinition) {
  const parts = [`format: ${definition.format}`];
  if (definition.placeholders?.length) {
    parts.push(`placeholders: ${definition.placeholders.join(", ")}`);
  }
  if (definition.helper) {
    parts.push(definition.helper);
  }
  return ` ${parts.join("; ")}.`;
}
