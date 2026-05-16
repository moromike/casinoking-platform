"use client";

import { type FormEvent, useEffect, useState } from "react";
import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { AccessLog } from "./access-log";

type AdminManagementProps = {
  accessToken: string;
  isSuperadmin: boolean;
};

type AdminEntry = {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
  is_superadmin: boolean;
  areas: string[];
  last_login_at: string | null;
};

type AdminProfile = {
  user_id: string;
  email: string;
  role: string;
  status: string;
  is_superadmin: boolean;
  areas: string[];
};

const VALID_AREAS = ["finance", "end_user", "mines"] as const;
type Area = (typeof VALID_AREAS)[number];

const AREA_LABELS: Record<Area, string> = {
  finance: "Finance",
  end_user: "Player admin",
  mines: "Games",
};

type AdminMgmtView = "list" | "create" | "access_logs";

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AdminManagement({ accessToken, isSuperadmin }: AdminManagementProps) {
  const [view, setView] = useState<AdminMgmtView>("list");

  // Admin list
  const [adminList, setAdminList] = useState<AdminEntry[]>([]);
  const [adminEmailSearch, setAdminEmailSearch] = useState("");
  const [listBusy, setListBusy] = useState(false);
  const [listStatus, setListStatus] = useState<string | null>(null);

  // Selected admin detail
  const [selectedAdmin, setSelectedAdmin] = useState<AdminEntry | null>(null);
  const [editAreas, setEditAreas] = useState<Area[]>([]);
  const [editIsSuperadmin, setEditIsSuperadmin] = useState(false);
  const [editBusy, setEditBusy] = useState(false);
  const [editStatus, setEditStatus] = useState<string | null>(null);
  const [resetPwd, setResetPwd] = useState("");
  const [resetPwdBusy, setResetPwdBusy] = useState(false);

  // Create admin
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newIsSuperadmin, setNewIsSuperadmin] = useState(false);
  const [newAreas, setNewAreas] = useState<Area[]>([]);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createBusy, setCreateBusy] = useState(false);

  // Auto-load lista quando si entra nel tab "list"
  useEffect(() => {
    if (view === "list" && adminList.length === 0) {
      void handleLoadAdmins();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  function selectAdmin(admin: AdminEntry) {
    setSelectedAdmin(admin);
    setEditAreas(admin.areas.filter((a): a is Area => VALID_AREAS.includes(a as Area)));
    setEditIsSuperadmin(admin.is_superadmin);
    setEditStatus(null);
    setResetPwd("");
  }

  function deselectAdmin() {
    setSelectedAdmin(null);
    setEditStatus(null);
    setResetPwd("");
  }

  async function handleLoadAdmins() {
    setListBusy(true);
    setListStatus(null);
    try {
      const params = adminEmailSearch.trim() ? `?email=${encodeURIComponent(adminEmailSearch.trim())}` : "";
      const data = await apiRequest<AdminEntry[]>(`/admin/admins${params}`, {}, accessToken);
      setAdminList(data);
      if (data.length === 0) setListStatus("No admins found.");
    } catch (error) {
      setListStatus(readErrorMessage(error, "Admin list loading failed."));
    } finally {
      setListBusy(false);
    }
  }

  async function handleUpdateAdminProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAdmin) return;
    setEditBusy(true);
    setEditStatus(null);
    try {
      await apiRequest<AdminProfile>(
        `/admin/admins/${selectedAdmin.id}/profile`,
        {
          method: "PUT",
          body: JSON.stringify({
            is_superadmin: editIsSuperadmin,
            areas: editIsSuperadmin ? [] : editAreas,
          }),
        },
        accessToken,
      );
      setEditStatus(`Profile for ${selectedAdmin.email} updated.`);
      await handleLoadAdmins();
      setSelectedAdmin((prev) =>
        prev ? { ...prev, is_superadmin: editIsSuperadmin, areas: editIsSuperadmin ? [] : editAreas } : null,
      );
    } catch (error) {
      setEditStatus(readErrorMessage(error, "Profile update failed."));
    } finally {
      setEditBusy(false);
    }
  }

  async function handleResetAdminPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAdmin) return;
    if (resetPwd.trim().length < 8) {
      setEditStatus("The new password must be at least 8 characters long.");
      return;
    }
    setResetPwdBusy(true);
    setEditStatus(null);
    try {
      await apiRequest<{ target_admin_id: string; email: string; password_reset: boolean }>(
        `/admin/admins/${selectedAdmin.id}/password-reset`,
        {
          method: "POST",
          body: JSON.stringify({ new_password: resetPwd.trim() }),
        },
        accessToken,
      );
      setResetPwd("");
      setEditStatus(`Password for ${selectedAdmin.email} reset successfully.`);
    } catch (error) {
      setEditStatus(readErrorMessage(error, "Password reset failed."));
    } finally {
      setResetPwdBusy(false);
    }
  }

  async function handleSuspendAdmin() {
    if (!selectedAdmin) return;
    setEditBusy(true);
    setEditStatus(null);
    try {
      await apiRequest(
        `/admin/admins/${selectedAdmin.id}/suspend`,
        { method: "POST" },
        accessToken,
      );
      setEditStatus(`Account ${selectedAdmin.email} suspended.`);
      await handleLoadAdmins();
      setSelectedAdmin((prev) => (prev ? { ...prev, status: "suspended" } : null));
    } catch (error) {
      setEditStatus(readErrorMessage(error, "Suspension failed."));
    } finally {
      setEditBusy(false);
    }
  }

  async function handleCreateAdmin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) { setCreateStatus("Admin session is not available."); return; }
    if (!newEmail.trim()) { setCreateStatus("Email is required."); return; }
    if (newPassword.length < 8) { setCreateStatus("The password must be at least 8 characters long."); return; }

    setCreateBusy(true);
    setCreateStatus(null);
    try {
      const result = await apiRequest<AdminProfile>(
        "/admin/admins",
        {
          method: "POST",
          body: JSON.stringify({
            email: newEmail.trim().toLowerCase(),
            password: newPassword,
            is_superadmin: newIsSuperadmin,
            areas: newAreas,
          }),
        },
        accessToken,
      );
      setNewEmail("");
      setNewPassword("");
      setNewIsSuperadmin(false);
      setNewAreas([]);
      setCreateStatus(
        `Admin ${result.email} created.${result.is_superadmin ? " Role: Superadmin." : ` Areas: ${result.areas.join(", ") || "none"}.`}`,
      );
      // Reload the list if it was already loaded.
      if (adminList.length > 0) await handleLoadAdmins();
    } catch (error) {
      setCreateStatus(readErrorMessage(error, "Admin creation failed."));
    } finally {
      setCreateBusy(false);
    }
  }

  // ── NAV ──
  const navItems: Array<{ key: AdminMgmtView; label: string }> = [
    { key: "list", label: "Registered admins" },
    { key: "create", label: "Create admin" },
    { key: "access_logs", label: "Admin accesses" },
  ];

  return (
    <div className="stack">
      {/* Sub-nav */}
      <div className="admin-subnav admin-management-subnav">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={view === item.key ? "button" : "button-secondary"}
            type="button"
            onClick={() => { setView(item.key); deselectAdmin(); }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Registered admins view */}
      {view === "list" ? (
        <div className="stack">
          {selectedAdmin ? (
            /* Selected admin detail */
            <div className="stack">
              <div className="actions">
                <button className="button-secondary" type="button" onClick={deselectAdmin}>
                  Back to admin list
                </button>
              </div>
              <article className="admin-card">
                <h3>{selectedAdmin.email}</h3>
                <div className="admin-metric-row">
                  <span className="list-muted">Status</span>
                  <span className={`status-inline ${selectedAdmin.status === "active" ? "success" : "warning"}`}>
                    {selectedAdmin.status}
                  </span>
                </div>
                <div className="admin-metric-row">
                  <span className="list-muted">Areas</span>
                  <span>{selectedAdmin.is_superadmin ? "Superadmin" : selectedAdmin.areas.join(", ") || "none"}</span>
                </div>
                <div className="admin-metric-row">
                  <span className="list-muted">Last login</span>
                  <span>{formatDateTime(selectedAdmin.last_login_at)}</span>
                </div>
                <div className="admin-metric-row">
                  <span className="list-muted">Created at</span>
                  <span>{formatDateTime(selectedAdmin.created_at)}</span>
                </div>

                <form className="stack" onSubmit={(e) => void handleUpdateAdminProfile(e)}>
                  <div className="field">
                    <label>Access areas</label>
                    <div className="inline-actions">
                      {VALID_AREAS.map((area) => (
                        <button
                          key={area}
                          type="button"
                          className={editAreas.includes(area) ? "button" : "button-secondary"}
                          onClick={() =>
                            setEditAreas((prev) =>
                              prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area],
                            )
                          }
                          disabled={editIsSuperadmin}
                        >
                          {AREA_LABELS[area]}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="field">
                    <label className="inline-actions">
                      <input
                        type="checkbox"
                        checked={editIsSuperadmin}
                        onChange={(e) => {
                          setEditIsSuperadmin(e.target.checked);
                          if (e.target.checked) setEditAreas([]);
                        }}
                      />
                      <span>Superadmin</span>
                    </label>
                  </div>
                  <div className="actions">
                    <button className="button-secondary" type="submit" disabled={editBusy}>
                      {editBusy ? "Saving..." : "Save areas"}
                    </button>
                  </div>
                </form>

                <form className="stack" onSubmit={(e) => void handleResetAdminPassword(e)}>
                  <div className="field">
                    <label htmlFor="admin-reset-pwd">Reset password</label>
                    <input
                      id="admin-reset-pwd"
                      type="password"
                      value={resetPwd}
                      onChange={(e) => setResetPwd(e.target.value)}
                      placeholder="New password (min. 8 characters)"
                      autoComplete="new-password"
                    />
                  </div>
                  <div className="actions">
                    <button
                      className="button-ghost"
                      type="submit"
                      disabled={resetPwdBusy || resetPwd.trim().length < 8}
                    >
                      {resetPwdBusy ? "Resetting..." : "Reset password"}
                    </button>
                  </div>
                </form>

                {isSuperadmin ? (
                  <div className="actions">
                    <button
                      className="button-ghost"
                      type="button"
                      disabled={editBusy || selectedAdmin.status === "suspended"}
                      onClick={() => void handleSuspendAdmin()}
                    >
                      {editBusy ? "Suspending..." : "Suspend account"}
                    </button>
                  </div>
                ) : null}

                {editStatus ? <p className="helper">{editStatus}</p> : null}
              </article>
            </div>
          ) : (
            /* Admin list */
            <div className="stack">
              <div className="admin-surface admin-surface-section">
                <div className="field-grid">
                  <div className="field">
                    <label htmlFor="admin-search-email">Filter by email</label>
                    <input
                      id="admin-search-email"
                      value={adminEmailSearch}
                      onChange={(e) => setAdminEmailSearch(e.target.value)}
                      placeholder="email fragment or empty for all"
                    />
                  </div>
                </div>
                <div className="actions">
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={listBusy}
                    onClick={() => void handleLoadAdmins()}
                  >
                    {listBusy ? "Loading..." : "Refresh list"}
                  </button>
                </div>
                {listStatus ? <p className="helper">{listStatus}</p> : null}
              </div>

              {adminList.length > 0 ? (
                <div className="admin-list admin-list-static">
                  {adminList.map((admin) => (
                    <article className="admin-list-card" key={admin.id}>
                      <div className="list-row">
                        <span className="list-strong">{admin.email}</span>
                        <span className={`status-inline ${admin.status === "active" ? "success" : "warning"}`}>
                          {admin.status}
                        </span>
                      </div>
                      <div className="admin-metric-row">
                        <span className="list-muted">Areas</span>
                        <span className="meta-pill">
                          {admin.is_superadmin ? "Superadmin" : admin.areas.join(", ") || "no areas"}
                        </span>
                      </div>
                      <div className="admin-metric-row">
                        <span className="list-muted">Last login</span>
                        <span>{formatDateTime(admin.last_login_at)}</span>
                      </div>
                      <div className="actions">
                        <button
                          className="button-secondary"
                          type="button"
                          onClick={() => selectAdmin(admin)}
                        >
                          Open detail
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              ) : listBusy ? null : (
                <p className="empty-state">No admins loaded.</p>
              )}
            </div>
          )}
        </div>
      ) : null}

      {/* Create admin view */}
      {view === "create" ? (
        <article className="admin-card">
          <h3>New admin account</h3>
          <form className="stack" onSubmit={(event) => void handleCreateAdmin(event)}>
            <div className="field-grid">
              <div className="field">
                <label htmlFor="new-admin-email">Email</label>
                <input
                  id="new-admin-email"
                  type="email"
                  autoComplete="off"
                  value={newEmail}
                  onChange={(event) => setNewEmail(event.target.value)}
                  placeholder="admin@example.com"
                />
              </div>
              <div className="field">
                <label htmlFor="new-admin-password">Password</label>
                <input
                  id="new-admin-password"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  placeholder="at least 8 characters"
                />
              </div>
            </div>
            <div className="field">
              <label>Access areas</label>
              <div className="inline-actions">
                {VALID_AREAS.map((area) => (
                  <button
                    key={area}
                    type="button"
                    className={newAreas.includes(area) ? "button" : "button-secondary"}
                    onClick={() =>
                      setNewAreas((prev) =>
                        prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area],
                      )
                    }
                    disabled={newIsSuperadmin}
                  >
                    {AREA_LABELS[area]}
                  </button>
                ))}
              </div>
            </div>
            <div className="field">
              <label className="admin-checkbox-row">
                <input
                  type="checkbox"
                  checked={newIsSuperadmin}
                  onChange={(event) => {
                    setNewIsSuperadmin(event.target.checked);
                    if (event.target.checked) setNewAreas([]);
                  }}
                />
                <span>Superadmin (full access to all areas)</span>
              </label>
            </div>
            <div className="actions">
              <button className="button" type="submit" disabled={createBusy}>
                {createBusy ? "Creating..." : "Create admin"}
              </button>
            </div>
            {createStatus ? <p className="helper">{createStatus}</p> : null}
          </form>
        </article>
      ) : null}

      {/* Admin accesses view */}
      {view === "access_logs" ? (
        <AccessLog
          accessToken={accessToken}
          defaultRole="admin"
          showRoleFilter={false}
        />
      ) : null}
    </div>
  );
}
