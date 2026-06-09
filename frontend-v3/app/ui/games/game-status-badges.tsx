"use client";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

type BadgeTone = "success" | "warning" | "error" | "info";

function normalizeStatus(value: string) {
  return value.replace(/_/g, " ");
}

function statusTone(status: string): BadgeTone {
  if (status === "active" || status === "visible") {
    return "success";
  }

  if (status === "inactive" || status === "hidden") {
    return "warning";
  }

  return "info";
}

export function GameStatusBadges({
  title,
  includeType = false,
}: {
  title: CatalogTitle;
  includeType?: boolean;
}) {
  return (
    <div className="games-status-badges" aria-label="Game status">
      {includeType ? (
        <span className={`status-inline ${title.is_master ? "warning" : "success"}`}>
          {title.is_master ? "Master" : "Variant"}
        </span>
      ) : null}
      {title.is_archived === true ? (
        <span className="status-inline error">Archived</span>
      ) : null}
      {title.is_test === true ? (
        <span className="status-inline info">Test</span>
      ) : null}
      <span className={`status-inline ${statusTone(title.status)}`}>
        {normalizeStatus(title.status)}
      </span>
      <span className={`status-inline ${statusTone(title.site_title_status)}`}>
        Site {normalizeStatus(title.site_title_status)}
      </span>
    </div>
  );
}

export function GamePublicationBadges({ title }: { title: CatalogTitle }) {
  const isVisible = title.publication.lobby_visibility === "visible";

  return (
    <div className="games-status-badges" aria-label="Publication status">
      <span className={`status-inline ${isVisible ? "success" : "warning"}`}>
        {isVisible ? "Visible" : "Hidden"}
      </span>
      <span className={`status-inline ${title.publication.demo_enabled ? "success" : "warning"}`}>
        Demo {title.publication.demo_enabled ? "on" : "off"}
      </span>
      <span className={`status-inline ${title.publication.real_enabled ? "success" : "warning"}`}>
        Real {title.publication.real_enabled ? "on" : "off"}
      </span>
    </div>
  );
}
