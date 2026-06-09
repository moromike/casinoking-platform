"use client";

import type { ValidationIssue } from "./types";

type TitleEditorValidationDisplayProps = {
  issues: readonly ValidationIssue[];
  title?: string;
};

export function TitleEditorValidationDisplay({
  issues,
  title = "Validation errors",
}: TitleEditorValidationDisplayProps) {
  if (issues.length === 0) {
    return null;
  }

  return (
    <article className="admin-card">
      <h3>{title}</h3>
      <ul className="stack compact">
        {issues.map((issue) => (
          <li key={issue.id}>
            {issue.path ? <span className="mono">{issue.path}: </span> : null}
            {issue.message}
          </li>
        ))}
      </ul>
    </article>
  );
}
