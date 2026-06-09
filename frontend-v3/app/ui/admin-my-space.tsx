"use client";

import { type FormEvent, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";

type AdminMySpaceProps = {
  adminEmail: string;
  accessToken: string;
};

export function AdminMySpace({ adminEmail, accessToken }: AdminMySpaceProps) {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [formStatus, setFormStatus] = useState<string | null>(null);

  async function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!accessToken) {
      setFormStatus("Admin session is not available.");
      return;
    }

    setBusy(true);
    setFormStatus(null);

    try {
      await apiRequest<{ password_changed: boolean }>(
        "/admin/auth/password/change",
        {
          method: "POST",
          body: JSON.stringify({
            old_password: oldPassword,
            new_password: newPassword,
          }),
        },
        accessToken,
      );
      setOldPassword("");
      setNewPassword("");
      setFormStatus("Password updated successfully.");
    } catch (error) {
      setFormStatus(readErrorMessage(error, "Password change failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div className="admin-surface admin-surface-section">
        <div className="field-grid">
          <div className="field">
            <label>Admin account</label>
            <span className="list-strong">{adminEmail || "—"}</span>
          </div>
        </div>
      </div>

      <div className="admin-grid">
        <article className="admin-card">
          <h3>Change password</h3>
          <form className="stack" onSubmit={(event) => void handlePasswordChange(event)}>
            <div className="field-grid">
              <div className="field">
                <label htmlFor="admin-old-password">Current password</label>
                <input
                  id="admin-old-password"
                  type="password"
                  value={oldPassword}
                  onChange={(event) => setOldPassword(event.target.value)}
                  autoComplete="current-password"
                />
              </div>
              <div className="field">
                <label htmlFor="admin-new-password">New password</label>
                <input
                  id="admin-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  autoComplete="new-password"
                />
              </div>
            </div>
            <div className="actions">
              <button className="button" type="submit" disabled={busy}>
                {busy ? "Updating..." : "Change password"}
              </button>
            </div>
            {formStatus ? (
              <p className="helper">{formStatus}</p>
            ) : null}
          </form>
        </article>
      </div>
    </div>
  );
}
