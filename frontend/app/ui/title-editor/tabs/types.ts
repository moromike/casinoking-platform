"use client";

import type { ReactNode } from "react";

export type TitleEditorStatusTone = "success" | "info" | "warning" | "error";

export type TitleEditorStatusModel = {
  label: string;
  toneClass: TitleEditorStatusTone | string;
  eyebrow?: string;
  description?: ReactNode;
  isBusy?: boolean;
  testId?: string;
};

export type TitleEditorTabDefinition<TTab extends string = string> = {
  id: TTab;
  label: ReactNode;
  onSelect?: () => void;
};

export type ValidationIssue = {
  id: string;
  message: string;
  path?: string;
  severity?: "error" | "warning" | "info";
};

export type TitleEditorOverviewMetric = {
  label: ReactNode;
  value: ReactNode;
  valueClassName?: string;
};

export type TitleEditorOverviewSection = {
  id: string;
  title: ReactNode;
  badge?: ReactNode;
  description?: ReactNode;
  metrics?: readonly TitleEditorOverviewMetric[];
  children?: ReactNode;
};

export type ChoiceSetWithDefaultField<TValue extends string | number> = {
  kind: "choiceSetWithDefault";
  id: string;
  title: ReactNode;
  description?: ReactNode;
  choices: readonly TValue[];
  selectedValues: readonly TValue[];
  defaultValue: TValue;
  formatChoice?: (value: TValue) => ReactNode;
  formatDefaultChoice?: (value: TValue) => ReactNode;
  onToggleChoice: (value: TValue) => void;
  onDefaultChange: (value: TValue) => void;
};

export type CustomConfigField = {
  kind: "custom";
  id: string;
  render: () => ReactNode;
};

export type TitleEditorConfigField<TValue extends string | number = string | number> =
  | ChoiceSetWithDefaultField<TValue>
  | CustomConfigField;
