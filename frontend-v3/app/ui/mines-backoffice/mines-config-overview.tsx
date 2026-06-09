"use client";

import {
  formatDateTime,
  formatGridChoiceLabel,
  shortId,
} from "@/app/lib/helpers";
import type {
  FairnessCurrentConfig,
  MinesPresentationConfig,
  MinesRuntimeConfig,
} from "@/app/lib/types";
import { TitleEditorOverviewTab } from "@/app/ui/title-editor/tabs";

type MinesConfigOverviewProps = {
  runtimeConfig: MinesRuntimeConfig;
  activeConfig: MinesPresentationConfig;
  publishedConfig: MinesPresentationConfig | null;
  backofficeState: {
    draft_updated_by_admin_user_id?: string | null;
    draft_updated_at?: string | null;
    published_updated_by_admin_user_id?: string | null;
    published_at?: string | null;
  } | null;
  adminFairnessCurrent: FairnessCurrentConfig | null;
};

export function MinesConfigOverview({
  runtimeConfig,
  activeConfig,
  publishedConfig,
  backofficeState,
  adminFairnessCurrent,
}: MinesConfigOverviewProps) {
  const sections = [
    {
      id: "runtime",
      title: "Official runtime",
      metrics: [
        { label: "Launch key", value: <span className="mono">mines</span> },
        { label: "Player route", value: <span className="mono">/mines</span> },
        {
          label: "Supported grids",
          value: runtimeConfig.supported_grid_sizes
            .map((gridSize) => formatGridChoiceLabel(gridSize))
            .join(", "),
          valueClassName: "list-strong",
        },
        {
          label: "Payout runtime",
          value: <span className="mono">{runtimeConfig.payout_runtime_file}</span>,
        },
        {
          label: "Fairness version",
          value: runtimeConfig.fairness_version,
          valueClassName: "list-strong",
        },
      ],
    },
    {
      id: "published",
      title: "Published configuration",
      metrics: [
        {
          label: "Grid live",
          value: publishedConfig?.published_grid_sizes
            .map((gridSize) => formatGridChoiceLabel(gridSize))
            .join(", "),
          valueClassName: "list-strong",
        },
        ...(publishedConfig?.published_grid_sizes.map((gridSize) => ({
          label: formatGridChoiceLabel(gridSize),
          value: (
            <>
              {(publishedConfig?.published_mine_counts[String(gridSize)] ?? []).join(", ")}
              {" "}
              &middot; default {publishedConfig?.default_mine_counts[String(gridSize)] ?? "n/a"}
            </>
          ),
        })) ?? []),
        {
          label: "Published by",
          value: backofficeState?.published_updated_by_admin_user_id
            ? shortId(backofficeState.published_updated_by_admin_user_id)
            : "default runtime",
        },
        {
          label: "Published at",
          value: backofficeState?.published_at
            ? formatDateTime(backofficeState.published_at)
            : "default runtime",
        },
      ],
    },
    {
      id: "draft",
      title: "Current draft",
      metrics: [
        {
          label: "Draft grids",
          value: activeConfig.published_grid_sizes
            .map((gridSize) => formatGridChoiceLabel(gridSize))
            .join(", "),
          valueClassName: "list-strong",
        },
        ...activeConfig.published_grid_sizes.map((gridSize) => ({
          label: formatGridChoiceLabel(gridSize),
          value: (
            <>
              {(activeConfig.published_mine_counts[String(gridSize)] ?? []).join(", ")}
              {" "}
              &middot; default {activeConfig.default_mine_counts[String(gridSize)] ?? "n/a"}
            </>
          ),
        })),
        {
          label: "Draft by",
          value: backofficeState?.draft_updated_by_admin_user_id
            ? shortId(backofficeState.draft_updated_by_admin_user_id)
            : "default runtime",
        },
        {
          label: "Draft at",
          value: backofficeState?.draft_updated_at
            ? formatDateTime(backofficeState.draft_updated_at)
            : "default runtime",
        },
      ],
    },
    {
      id: "fairness",
      title: "Fairness live Mines",
      children: adminFairnessCurrent ? (
        <>
          <div className="admin-metric-row"><span className="list-muted">Version</span><span className="list-strong">{adminFairnessCurrent.fairness_version}</span></div>
          <div className="admin-metric-row"><span className="list-muted">Phase</span><span className="list-strong">{adminFairnessCurrent.fairness_phase}</span></div>
          <div className="admin-metric-row"><span className="list-muted">User verifiable</span><span className={`status-inline ${adminFairnessCurrent.user_verifiable ? "success" : "warning"}`}>{adminFairnessCurrent.user_verifiable ? "yes" : "no"}</span></div>
          <div className="admin-metric-row"><span className="list-muted">Seed activated</span><span>{adminFairnessCurrent.seed_activated_at ? formatDateTime(adminFairnessCurrent.seed_activated_at) : "n/a"}</span></div>
        </>
      ) : (
        <p className="empty-state">Load the fairness status.</p>
      ),
    },
  ];

  return (
    <TitleEditorOverviewTab sections={sections} />
  );
}
