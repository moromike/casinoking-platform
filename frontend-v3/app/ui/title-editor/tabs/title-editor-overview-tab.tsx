"use client";

import type { TitleEditorOverviewSection } from "./types";

type TitleEditorOverviewTabProps = {
  sections: readonly TitleEditorOverviewSection[];
  className?: string;
};

export function TitleEditorOverviewTab({
  sections,
  className = "admin-grid admin-grid-three",
}: TitleEditorOverviewTabProps) {
  return (
    <div className={className}>
      {sections.map((section) => (
        <article className="admin-card" key={section.id}>
          {section.badge || section.description ? (
            <div className="admin-card-heading">
              <div>
                <h3>{section.title}</h3>
                {section.description ? <p>{section.description}</p> : null}
              </div>
              {section.badge}
            </div>
          ) : (
            <h3>{section.title}</h3>
          )}
          {section.metrics?.map((metric, index) => (
            <div className="admin-metric-row" key={`${section.id}-${index}`}>
              <span className="list-muted">{metric.label}</span>
              <span className={metric.valueClassName}>{metric.value}</span>
            </div>
          ))}
          {section.children}
        </article>
      ))}
    </div>
  );
}
