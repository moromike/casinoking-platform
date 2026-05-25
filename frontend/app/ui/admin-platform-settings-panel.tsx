"use client";

import { Fragment, useEffect, useMemo, useState } from "react";

import { ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";

type PlatformSettingState = {
  configured: boolean;
  display_value?: string;
  status: "ok" | "gap" | "pending";
};

type PlatformSettingRow = {
  key: string;
  label: string;
  source_of_truth: string;
  owner: string;
  visibility: "hidden" | "masked" | "read_only" | "editable_future";
  risk_class: "low" | "medium" | "high" | "critical";
  environment_scope: string;
  restart_required: "yes" | "no" | "unknown";
  audit_required: "yes" | "no" | "future";
  editable_now: false;
  masking_rule: string;
  evidence: string;
  category: string;
  status: "ok" | "gap" | "pending";
  state: PlatformSettingState;
  notes: string[];
  explanation: {
    it: string;
    en: string;
  };
  editable_when?: string;
};

type GapRisk = {
  key: string;
  severity: "critical" | "high" | "medium" | "low";
  impact: string;
  mvp_mitigation: string;
  long_term_mitigation: string;
  follow_up_wp: string;
  evidence: string;
};

type GameHealthCheck = {
  status: "present" | "gap" | "pending";
  evidence: string;
  notes: string[];
};

type GameRegistryHealth = {
  game_code: string;
  source_of_truth: string;
  status: "present" | "gap" | "pending";
  checks: Record<string, GameHealthCheck>;
};

type ErrorMatrixRow = {
  code: string;
  http_status: number;
  message: string;
  retryable: boolean;
  log_level: string;
};

type PlatformSettingsInventory = {
  generated_at: string;
  summary: {
    total_descriptors: number;
    gap_count: number;
    pending_count: number;
    hidden_count: number;
    masked_count: number;
    editable_now_count: number;
  };
  inventory: PlatformSettingRow[];
  gap_risks: GapRisk[];
  game_registry_health: GameRegistryHealth[];
  error_matrix: {
    status: "available" | "pending";
    source: string;
    codes: ErrorMatrixRow[];
    notes: string[];
  };
};

type AdminPlatformSettingsPanelProps = {
  accessToken: string;
};

const CATEGORY_ORDER = [
  "Environment",
  "Security-sensitive values",
  "Session/table/recovery policy",
  "Game registry health",
  "Error Matrix status",
  "Finance/replay/retention status",
  "Gap risk write-up",
];

type StatusFilter = "all" | PlatformSettingRow["status"];
type RiskFilter = "all" | PlatformSettingRow["risk_class"];
type VisibilityFilter = "all" | PlatformSettingRow["visibility"];

const STATUS_FILTERS: StatusFilter[] = ["all", "gap", "pending", "ok"];
const RISK_FILTERS: RiskFilter[] = ["all", "critical", "high", "medium", "low"];
const VISIBILITY_FILTERS: VisibilityFilter[] = [
  "all",
  "hidden",
  "masked",
  "read_only",
  "editable_future",
];

export function AdminPlatformSettingsPanel({
  accessToken,
}: AdminPlatformSettingsPanelProps) {
  const [inventory, setInventory] = useState<PlatformSettingsInventory | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [visibilityFilter, setVisibilityFilter] = useState<VisibilityFilter>("all");
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoadError(null);
    apiRequest<PlatformSettingsInventory>("/admin/platform-settings", {}, accessToken)
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setInventory(data);
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setInventory(null);
        const prefix =
          error instanceof ApiRequestError && error.status === 403
            ? "Platform Settings requires an explicit superadmin profile."
            : "Platform Settings inventory could not be loaded.";
        setLoadError(readErrorMessage(error, prefix));
      });

    return () => {
      isMounted = false;
    };
  }, [accessToken]);

  const filteredRows = useMemo(() => {
    return (inventory?.inventory ?? []).filter((row) => {
      if (statusFilter !== "all" && row.status !== statusFilter) {
        return false;
      }
      if (riskFilter !== "all" && row.risk_class !== riskFilter) {
        return false;
      }
      if (visibilityFilter !== "all" && row.visibility !== visibilityFilter) {
        return false;
      }
      return true;
    });
  }, [inventory, riskFilter, statusFilter, visibilityFilter]);

  const rowsByCategory = useMemo(() => {
    const grouped = new Map<string, PlatformSettingRow[]>();
    for (const row of filteredRows) {
      const group = grouped.get(row.category) ?? [];
      group.push(row);
      grouped.set(row.category, group);
    }
    return grouped;
  }, [filteredRows]);

  if (loadError) {
    return (
      <article className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>Platform Settings</h3>
            <p>{loadError}</p>
          </div>
        </div>
      </article>
    );
  }

  if (!inventory) {
    return (
      <article className="admin-card">
        <p className="empty-state">Loading Platform Settings inventory.</p>
      </article>
    );
  }

  return (
    <div className="stack platform-settings-panel">
      <section className="admin-summary-strip" aria-label="Platform Settings summary">
        <span className="meta-pill">{inventory.summary.total_descriptors} descriptors</span>
        <span className="meta-pill warning">{inventory.summary.gap_count} gaps</span>
        <span className="meta-pill">{inventory.summary.pending_count} pending</span>
        <span className="meta-pill">{inventory.summary.hidden_count} hidden</span>
        <span className="meta-pill">{inventory.summary.masked_count} masked</span>
        <span className="meta-pill">{inventory.summary.editable_now_count} editable</span>
      </section>

      <section className="admin-card platform-settings-filter-panel">
        <div className="admin-card-heading">
          <div>
            <h3>Filters</h3>
            <p>Use these controls to narrow the inventory. Click any setting name to open the explanation.</p>
          </div>
          <span className="meta-pill">{filteredRows.length} visible</span>
        </div>
        <div className="platform-settings-filter-grid">
          <FilterGroup
            label="Status"
            options={STATUS_FILTERS}
            active={statusFilter}
            onSelect={setStatusFilter}
          />
          <FilterGroup
            label="Risk"
            options={RISK_FILTERS}
            active={riskFilter}
            onSelect={setRiskFilter}
          />
          <FilterGroup
            label="Visibility"
            options={VISIBILITY_FILTERS}
            active={visibilityFilter}
            onSelect={setVisibilityFilter}
          />
        </div>
      </section>

      {filteredRows.length === 0 ? (
        <section className="admin-card">
          <p className="empty-state">No settings match the selected filters.</p>
        </section>
      ) : null}

      {CATEGORY_ORDER.map((category) => {
        const rows = rowsByCategory.get(category) ?? [];
        if (rows.length === 0) {
          return null;
        }
        return (
          <section className="admin-card" key={category}>
            <div className="admin-card-heading">
              <div>
                <h3>{category}</h3>
              </div>
            </div>
            <div className="platform-settings-table-shell">
              <table className="platform-settings-table">
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Status</th>
                    <th>Value</th>
                    <th>Visibility</th>
                    <th>Risk</th>
                    <th>Owner</th>
                    <th>Source</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const isExpanded = expandedKey === row.key;
                    return (
                      <Fragment key={row.key}>
                        <tr>
                          <td>
                            <button
                              aria-expanded={isExpanded}
                              className="platform-settings-row-toggle"
                              type="button"
                              onClick={() => setExpandedKey(isExpanded ? null : row.key)}
                            >
                              <strong>{row.label}</strong>
                              <span className="mono">{row.key}</span>
                            </button>
                          </td>
                          <td>
                            <StatusPill status={row.status} />
                          </td>
                          <td>{formatSettingValue(row)}</td>
                          <td>{row.visibility}</td>
                          <td>
                            <RiskPill risk={row.risk_class} />
                          </td>
                          <td>{row.owner}</td>
                          <td>{row.source_of_truth}</td>
                          <td>
                            <span className="mono">{row.evidence}</span>
                          </td>
                        </tr>
                        {isExpanded ? (
                          <tr className="platform-settings-detail-row">
                            <td colSpan={8}>
                              <SettingExplanation row={row} />
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}

      <section className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>Gap Risk Write-Up</h3>
          </div>
        </div>
        <div className="platform-settings-gap-list">
          {inventory.gap_risks.length === 0 ? (
            <p className="empty-state">No security gap write-ups are currently registered.</p>
          ) : null}
          {inventory.gap_risks.map((gap) => (
            <article className="platform-settings-gap-row" key={gap.key}>
              <div>
                <strong>{gap.key}</strong>
                <span className="mono">{gap.evidence}</span>
              </div>
              <RiskPill risk={gap.severity} />
              <p>{gap.impact}</p>
              <p>{gap.mvp_mitigation}</p>
              <p>{gap.long_term_mitigation}</p>
              <span className="status-inline warning">{gap.follow_up_wp}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>Game Registry Health</h3>
          </div>
        </div>
        <div className="platform-settings-game-grid">
          {inventory.game_registry_health.map((game) => (
            <article className="platform-settings-game-row" key={game.game_code}>
              <div className="platform-settings-game-heading">
                <strong>{game.game_code}</strong>
                <StatusPill status={game.status === "present" ? "ok" : game.status} />
              </div>
              <dl>
                {Object.entries(game.checks).map(([name, check]) => (
                  <div key={name}>
                    <dt>{name.replace(/_/g, " ")}</dt>
                    <dd>
                      <StatusPill status={check.status === "present" ? "ok" : check.status} />
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="admin-card">
        <div className="admin-card-heading">
          <div>
            <h3>Error Matrix</h3>
          </div>
        </div>
        <div className="platform-settings-table-shell">
          <table className="platform-settings-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>HTTP</th>
                <th>Retryable</th>
                <th>Log</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {inventory.error_matrix.codes.map((row) => (
                <tr key={row.code}>
                  <td>
                    <span className="mono">{row.code}</span>
                  </td>
                  <td>{row.http_status}</td>
                  <td>{row.retryable ? "yes" : "no"}</td>
                  <td>{row.log_level}</td>
                  <td>{row.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function FilterGroup<T extends string>({
  label,
  options,
  active,
  onSelect,
}: {
  label: string;
  options: T[];
  active: T;
  onSelect: (value: T) => void;
}) {
  return (
    <div className="platform-settings-filter-group">
      <span>{label}</span>
      <div>
        {options.map((option) => (
          <button
            className={active === option ? "is-active" : ""}
            key={option}
            type="button"
            onClick={() => onSelect(option)}
          >
            {option.replace(/_/g, " ")}
          </button>
        ))}
      </div>
    </div>
  );
}

function SettingExplanation({ row }: { row: PlatformSettingRow }) {
  return (
    <div className="platform-settings-explanation">
      <div>
        <h4>Spiegazione</h4>
        <p>{row.explanation.it}</p>
      </div>
      <div>
        <h4>Explanation</h4>
        <p>{row.explanation.en}</p>
      </div>
      {row.notes.length > 0 || row.editable_when ? (
        <div className="platform-settings-explanation-notes">
          {row.notes.map((note) => (
            <p key={note}>{note}</p>
          ))}
          {row.editable_when ? <p>Editable later: {row.editable_when}</p> : null}
        </div>
      ) : null}
    </div>
  );
}

function formatSettingValue(row: PlatformSettingRow): string {
  if (row.visibility === "hidden") {
    return row.state.configured ? "Configured" : "Missing";
  }
  return row.state.display_value ?? (row.state.configured ? "Configured" : "Missing");
}

function StatusPill({ status }: { status: "ok" | "gap" | "pending" }) {
  const className =
    status === "ok" ? "success" : status === "gap" ? "error" : "warning";
  return <span className={`status-inline ${className}`}>{status}</span>;
}

function RiskPill({ risk }: { risk: "low" | "medium" | "high" | "critical" }) {
  const className = risk === "critical" ? "error" : risk === "high" ? "warning" : "info";
  return <span className={`status-inline ${className}`}>{risk}</span>;
}
