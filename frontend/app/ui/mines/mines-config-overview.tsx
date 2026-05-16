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
  return (
    <div className="admin-grid admin-grid-three">
      <article className="admin-card">
        <h3>Official runtime</h3>
        <div className="admin-metric-row"><span className="list-muted">Launch key</span><span className="mono">mines</span></div>
        <div className="admin-metric-row"><span className="list-muted">Player route</span><span className="mono">/mines</span></div>
        <div className="admin-metric-row"><span className="list-muted">Supported grids</span><span className="list-strong">{runtimeConfig.supported_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
        <div className="admin-metric-row"><span className="list-muted">Payout runtime</span><span className="mono">{runtimeConfig.payout_runtime_file}</span></div>
        <div className="admin-metric-row"><span className="list-muted">Fairness version</span><span className="list-strong">{runtimeConfig.fairness_version}</span></div>
      </article>

      <article className="admin-card">
        <h3>Published configuration</h3>
        <div className="admin-metric-row"><span className="list-muted">Grid live</span><span className="list-strong">{publishedConfig?.published_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
        {publishedConfig?.published_grid_sizes.map((gridSize) => (
          <div className="admin-metric-row" key={gridSize}>
            <span className="list-muted">{formatGridChoiceLabel(gridSize)}</span>
            <span>{(publishedConfig?.published_mine_counts[String(gridSize)] ?? []).join(", ")} &middot; default {(publishedConfig?.default_mine_counts[String(gridSize)] ?? "n/a")}</span>
          </div>
        ))}
        <div className="admin-metric-row"><span className="list-muted">Published by</span><span>{backofficeState?.published_updated_by_admin_user_id ? shortId(backofficeState.published_updated_by_admin_user_id) : "default runtime"}</span></div>
        <div className="admin-metric-row"><span className="list-muted">Published at</span><span>{backofficeState?.published_at ? formatDateTime(backofficeState.published_at) : "default runtime"}</span></div>
      </article>

      <article className="admin-card">
        <h3>Current draft</h3>
        <div className="admin-metric-row"><span className="list-muted">Draft grids</span><span className="list-strong">{activeConfig.published_grid_sizes.map((gridSize) => formatGridChoiceLabel(gridSize)).join(", ")}</span></div>
        {activeConfig.published_grid_sizes.map((gridSize) => (
          <div className="admin-metric-row" key={`draft-${gridSize}`}>
            <span className="list-muted">{formatGridChoiceLabel(gridSize)}</span>
            <span>{(activeConfig.published_mine_counts[String(gridSize)] ?? []).join(", ")} &middot; default {(activeConfig.default_mine_counts[String(gridSize)] ?? "n/a")}</span>
          </div>
        ))}
        <div className="admin-metric-row"><span className="list-muted">Draft by</span><span>{backofficeState?.draft_updated_by_admin_user_id ? shortId(backofficeState.draft_updated_by_admin_user_id) : "default runtime"}</span></div>
        <div className="admin-metric-row"><span className="list-muted">Draft at</span><span>{backofficeState?.draft_updated_at ? formatDateTime(backofficeState.draft_updated_at) : "default runtime"}</span></div>
      </article>

      <article className="admin-card">
        <h3>Fairness live Mines</h3>
        {adminFairnessCurrent ? (
          <>
            <div className="admin-metric-row"><span className="list-muted">Version</span><span className="list-strong">{adminFairnessCurrent.fairness_version}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Phase</span><span className="list-strong">{adminFairnessCurrent.fairness_phase}</span></div>
            <div className="admin-metric-row"><span className="list-muted">User verifiable</span><span className={`status-inline ${adminFairnessCurrent.user_verifiable ? "success" : "warning"}`}>{adminFairnessCurrent.user_verifiable ? "yes" : "no"}</span></div>
            <div className="admin-metric-row"><span className="list-muted">Seed activated</span><span>{adminFairnessCurrent.seed_activated_at ? formatDateTime(adminFairnessCurrent.seed_activated_at) : "n/a"}</span></div>
          </>
        ) : (
          <p className="empty-state">Load the fairness status.</p>
        )}
      </article>
    </div>
  );
}
