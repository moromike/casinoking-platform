"use client";

import { useEffect, useState } from "react";
import { apiRequest, readErrorMessage } from "@/app/lib/api";

type AccessLogEntry = {
  id: string;
  user_id: string;
  user_email: string;
  user_role: string;
  ip_address: string | null;
  action: string;
  logged_at: string;
};

type AccessLogData = {
  entries: AccessLogEntry[];
  pagination: { page: number; limit: number; total_items: number; total_pages: number };
};

type AccessLogProps = {
  accessToken: string;
  defaultRole?: "" | "player" | "admin";
  defaultEmail?: string;
  showRoleFilter?: boolean;
};

export function AccessLog({ accessToken, defaultRole = "", defaultEmail = "", showRoleFilter = false }: AccessLogProps) {
  const [role, setRole] = useState<"" | "player" | "admin">(defaultRole);
  const [email, setEmail] = useState(defaultEmail);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<AccessLogData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(
    p = 1,
    overrides?: {
      role?: "" | "player" | "admin";
      email?: string;
      dateFrom?: string;
      dateTo?: string;
    },
  ) {
    if (!accessToken) return;
    setBusy(true);
    setError(null);
    try {
      const effectiveRole = overrides?.role ?? role;
      const effectiveEmail = overrides?.email ?? email;
      const effectiveDateFrom = overrides?.dateFrom ?? dateFrom;
      const effectiveDateTo = overrides?.dateTo ?? dateTo;
      const params = new URLSearchParams();
      if (effectiveRole) params.set("role", effectiveRole);
      if (effectiveEmail.trim()) params.set("email", effectiveEmail.trim());
      if (effectiveDateFrom) params.set("date_from", effectiveDateFrom);
      if (effectiveDateTo) params.set("date_to", effectiveDateTo);
      params.set("page", String(p));
      params.set("limit", "50");
      const result = await apiRequest<AccessLogData>(
        `/admin/access-logs?${params.toString()}`,
        {},
        accessToken,
      );
      setData(result);
      setPage(p);
    } catch (err) {
      setError(readErrorMessage(err, "Caricamento access log fallito."));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    setRole(defaultRole);
    setEmail(defaultEmail);
    setDateFrom("");
    setDateTo("");
    void load(1, {
      role: defaultRole,
      email: defaultEmail,
      dateFrom: "",
      dateTo: "",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, defaultRole, defaultEmail]);

  return (
    <div className="stack">
      <div className="admin-surface admin-surface-section">
        <div className="field-grid">
          {showRoleFilter ? (
            <div className="field">
              <label htmlFor="al-role">Ruolo</label>
              <select
                id="al-role"
                value={role}
                onChange={(e) => setRole(e.target.value as "" | "player" | "admin")}
              >
                <option value="">Tutti</option>
                <option value="player">Player</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          ) : null}
          <div className="field">
            <label htmlFor="al-email">Email</label>
            <input
              id="al-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="frammento email"
            />
          </div>
          <div className="field">
            <label htmlFor="al-date-from">Dal</label>
            <input
              id="al-date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="al-date-to">Al</label>
            <input
              id="al-date-to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
        <div className="actions">
          <button
            className="button-secondary"
            type="button"
            disabled={!accessToken || busy}
            onClick={() => void load(1)}
          >
            {busy ? "Carico..." : "Carica log"}
          </button>
        </div>
        {error ? <p className="helper error">{error}</p> : null}
      </div>

      {data ? (
        <article className="admin-card">
          <div className="admin-summary-strip">
            <span className="meta-pill">{data.pagination.total_items} accessi totali</span>
            <span className="meta-pill">pagina {data.pagination.page} / {data.pagination.total_pages}</span>
          </div>
          {data.entries.length > 0 ? (
            <div className="admin-list admin-list-static">
              {data.entries.map((entry) => (
                <article className="admin-list-card" key={entry.id}>
                  <div className="list-row">
                    <span className="list-strong">{entry.user_email}</span>
                    <span className={`status-inline ${entry.user_role === "admin" ? "warning" : "info"}`}>
                      {entry.user_role}
                    </span>
                  </div>
                  <div className="admin-metric-row">
                    <span className="list-muted">IP</span>
                    <span className="mono">{entry.ip_address ?? "—"}</span>
                  </div>
                  <div className="admin-metric-row">
                    <span className="list-muted">Data/ora</span>
                    <span>{new Date(entry.logged_at).toLocaleString("it-IT")}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">Nessun accesso nel periodo selezionato.</p>
          )}
          <div className="actions">
            <button
              className="button-secondary"
              type="button"
              disabled={busy || page <= 1}
              onClick={() => void load(page - 1)}
            >
              Precedente
            </button>
            <button
              className="button-secondary"
              type="button"
              disabled={busy || page >= data.pagination.total_pages}
              onClick={() => void load(page + 1)}
            >
              Successiva
            </button>
          </div>
        </article>
      ) : null}
    </div>
  );
}
