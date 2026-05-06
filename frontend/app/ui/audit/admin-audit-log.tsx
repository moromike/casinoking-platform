"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { shortId } from "@/app/lib/helpers";

type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
type JsonObject = { [key: string]: JsonValue };

type AuditLogEvent = {
  id: string;
  admin_user_id: string;
  action_kind: string;
  resource_kind: string;
  resource_id: string;
  payload_json: JsonValue;
  request_fingerprint: string;
  created_at: string;
};

type AuditLogResponse = {
  events: AuditLogEvent[];
  pagination: {
    page: number;
    limit: number;
    total_items: number;
    total_pages: number;
  };
};

type AuditLogFilters = {
  actionKind: string;
  resourceKind: string;
  resourceId: string;
  adminUserId: string;
  dateFrom: string;
  dateTo: string;
};

type AdminAuditLogProps = {
  accessToken: string;
};

const DEFAULT_FILTERS: AuditLogFilters = {
  actionKind: "",
  resourceKind: "",
  resourceId: "",
  adminUserId: "",
  dateFrom: "",
  dateTo: "",
};

const PAGE_LIMIT = 50;

export function AdminAuditLog({ accessToken }: AdminAuditLogProps) {
  const [filters, setFilters] = useState<AuditLogFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<AuditLogResponse | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedEvent = useMemo(
    () => data?.events.find((event) => event.id === selectedEventId) ?? data?.events[0] ?? null,
    [data, selectedEventId],
  );

  async function loadAuditLog(page = 1, nextFilters = filters) {
    if (!accessToken) {
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const params = buildAuditLogParams(nextFilters, page);
      const result = await apiRequest<AuditLogResponse>(
        `/admin/audit-log?${params.toString()}`,
        {},
        accessToken,
      );
      setData(result);
      setSelectedEventId((currentSelectedId) => {
        if (result.events.length === 0) {
          return null;
        }
        if (currentSelectedId && result.events.some((event) => event.id === currentSelectedId)) {
          return currentSelectedId;
        }
        return result.events[0].id;
      });
    } catch (caughtError) {
      setError(readErrorMessage(caughtError, "Audit log could not be loaded."));
    } finally {
      setBusy(false);
    }
  }

  function handleFilterChange(key: keyof AuditLogFilters, value: string) {
    setFilters((currentFilters) => ({
      ...currentFilters,
      [key]: value,
    }));
  }

  function handleApplyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadAuditLog(1);
  }

  function handleResetFilters() {
    setFilters(DEFAULT_FILTERS);
    void loadAuditLog(1, DEFAULT_FILTERS);
  }

  useEffect(() => {
    void loadAuditLog(1, DEFAULT_FILTERS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const pagination = data?.pagination ?? {
    page: 1,
    limit: PAGE_LIMIT,
    total_items: 0,
    total_pages: 0,
  };
  const canLoadPreviousPage = pagination.page > 1;
  const canLoadNextPage = pagination.total_pages > 0 && pagination.page < pagination.total_pages;

  return (
    <div className="audit-log-panel">
      <form className="audit-log-filters" onSubmit={handleApplyFilters}>
        <div className="audit-log-filter-grid">
          <label>
            <span>Action kind</span>
            <input
              value={filters.actionKind}
              onChange={(event) => handleFilterChange("actionKind", event.target.value)}
              placeholder="title_config_publish"
            />
          </label>
          <label>
            <span>Resource kind</span>
            <input
              value={filters.resourceKind}
              onChange={(event) => handleFilterChange("resourceKind", event.target.value)}
              placeholder="title"
            />
          </label>
          <label>
            <span>Resource id</span>
            <input
              value={filters.resourceId}
              onChange={(event) => handleFilterChange("resourceId", event.target.value)}
              placeholder="mines_classic"
            />
          </label>
          <label>
            <span>Admin id</span>
            <input
              value={filters.adminUserId}
              onChange={(event) => handleFilterChange("adminUserId", event.target.value)}
              placeholder="uuid"
            />
          </label>
          <label>
            <span>Date from</span>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(event) => handleFilterChange("dateFrom", event.target.value)}
            />
          </label>
          <label>
            <span>Date to</span>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(event) => handleFilterChange("dateTo", event.target.value)}
            />
          </label>
        </div>
        <div className="audit-log-actions">
          <button className="button-secondary" type="submit" disabled={!accessToken || busy}>
            {busy ? "Loading..." : "Apply"}
          </button>
          <button className="button-ghost" type="button" disabled={busy} onClick={handleResetFilters}>
            Reset
          </button>
        </div>
      </form>

      {error ? <p className="audit-log-state audit-log-state-error">{error}</p> : null}

      <div className="audit-log-workspace">
        <section className="audit-log-events" aria-label="Audit log events">
          <div className="audit-log-summary">
            <span>{pagination.total_items} events</span>
            <span>
              Page {pagination.total_items > 0 ? pagination.page : 0} of {pagination.total_pages}
            </span>
          </div>

          {busy && !data ? <p className="audit-log-state">Loading audit events...</p> : null}

          {data && data.events.length === 0 ? (
            <p className="audit-log-state">No audit events match the current filters.</p>
          ) : null}

          {data && data.events.length > 0 ? (
            <>
              <div className="audit-log-table-shell">
                <table className="audit-log-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Action</th>
                      <th>Resource</th>
                      <th>Admin</th>
                      <th>Changed fields</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.events.map((event) => {
                      const isSelected = selectedEvent?.id === event.id;
                      return (
                        <tr
                          className={isSelected ? "is-selected" : undefined}
                          key={event.id}
                          onClick={() => setSelectedEventId(event.id)}
                        >
                          <td>{formatAuditDateTime(event.created_at)}</td>
                          <td>
                            <button
                              className="audit-log-row-button"
                              type="button"
                              onClick={() => setSelectedEventId(event.id)}
                              aria-pressed={isSelected}
                            >
                              {event.action_kind}
                            </button>
                          </td>
                          <td>
                            <span className="audit-log-resource-kind">{event.resource_kind}</span>
                            <span className="audit-log-resource-id">{event.resource_id}</span>
                          </td>
                          <td className="audit-log-mono">{shortId(event.admin_user_id)}</td>
                          <td>{summarizeChangedFields(event.payload_json)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="audit-log-pagination">
                <span>
                  {pagination.total_items > 0
                    ? `${pagination.limit} per page`
                    : "No pages"}
                </span>
                <div className="audit-log-actions">
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={busy || !canLoadPreviousPage}
                    onClick={() => void loadAuditLog(pagination.page - 1)}
                  >
                    Previous
                  </button>
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={busy || !canLoadNextPage}
                    onClick={() => void loadAuditLog(pagination.page + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </section>

        <aside className="audit-log-detail" aria-label="Selected audit event detail">
          {selectedEvent ? (
            <>
              <div className="audit-log-detail-header">
                <div>
                  <span>Selected event</span>
                  <strong>{selectedEvent.action_kind}</strong>
                </div>
                <span className="audit-log-mono">{shortId(selectedEvent.id)}</span>
              </div>
              <dl className="audit-log-detail-list">
                <div>
                  <dt>Resource</dt>
                  <dd>
                    {selectedEvent.resource_kind} / {selectedEvent.resource_id}
                  </dd>
                </div>
                <div>
                  <dt>Admin id</dt>
                  <dd className="audit-log-mono">{selectedEvent.admin_user_id}</dd>
                </div>
                <div>
                  <dt>Request fingerprint</dt>
                  <dd className="audit-log-mono">{selectedEvent.request_fingerprint}</dd>
                </div>
              </dl>
              <pre className="audit-log-json">{formatJson(selectedEvent.payload_json)}</pre>
            </>
          ) : (
            <p className="audit-log-state">Select an event to inspect payload metadata.</p>
          )}
        </aside>
      </div>
    </div>
  );
}

function buildAuditLogParams(filters: AuditLogFilters, page: number): URLSearchParams {
  const params = new URLSearchParams();
  appendIfPresent(params, "action_kind", filters.actionKind);
  appendIfPresent(params, "resource_kind", filters.resourceKind);
  appendIfPresent(params, "resource_id", filters.resourceId);
  appendIfPresent(params, "admin_user_id", filters.adminUserId);
  appendIfPresent(params, "date_from", filters.dateFrom);
  appendIfPresent(params, "date_to", filters.dateTo);
  params.set("page", String(page));
  params.set("limit", String(PAGE_LIMIT));
  return params;
}

function appendIfPresent(params: URLSearchParams, key: string, value: string) {
  const normalizedValue = value.trim();
  if (normalizedValue) {
    params.set(key, normalizedValue);
  }
}

function formatAuditDateTime(value: string): string {
  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(parsedDate);
}

function summarizeChangedFields(payload: JsonValue): string {
  const changedFields = extractChangedFields(payload);
  if (changedFields.length === 0) {
    return "No field summary";
  }
  if (changedFields.length <= 4) {
    return changedFields.join(", ");
  }
  return `${changedFields.slice(0, 4).join(", ")} +${changedFields.length - 4}`;
}

function extractChangedFields(payload: JsonValue): string[] {
  if (!isJsonObject(payload)) {
    return [];
  }

  const explicitFields = readStringArray(payload.changed_fields) ?? readStringArray(payload.changedFields);
  if (explicitFields) {
    return explicitFields;
  }

  const changes = payload.changes ?? payload.diff;
  if (isJsonObject(changes)) {
    return Object.keys(changes);
  }

  const before = payload.before;
  const after = payload.after;
  if (isJsonObject(before) && isJsonObject(after)) {
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    return Array.from(keys).filter((key) => formatJson(before[key]) !== formatJson(after[key]));
  }

  return [];
}

function readStringArray(value: JsonValue | undefined): string[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const fields = value.filter((item): item is string => typeof item === "string");
  return fields.length > 0 ? fields : null;
}

function isJsonObject(value: JsonValue | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatJson(value: JsonValue): string {
  return JSON.stringify(value, null, 2);
}
