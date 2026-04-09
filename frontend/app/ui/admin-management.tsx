"use client";

import { type FormEvent, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";

type AdminManagementProps = {
  accessToken: string;
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
  mines: "Mines backoffice",
};

export function AdminManagement({ accessToken }: AdminManagementProps) {
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newIsSuperadmin, setNewIsSuperadmin] = useState(false);
  const [newAreas, setNewAreas] = useState<Area[]>([]);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createBusy, setCreateBusy] = useState(false);

  function toggleArea(area: Area) {
    setNewAreas((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area],
    );
  }

  async function handleCreateAdmin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      setCreateStatus("Sessione admin non disponibile.");
      return;
    }
    if (!newEmail.trim()) {
      setCreateStatus("Email obbligatoria.");
      return;
    }
    if (newPassword.length < 8) {
      setCreateStatus("La password deve essere di almeno 8 caratteri.");
      return;
    }

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
        `Admin ${result.email} creato correttamente.${result.is_superadmin ? " Ruolo: Superadmin." : ` Aree: ${result.areas.join(", ") || "nessuna"}.`}`,
      );
    } catch (error) {
      setCreateStatus(readErrorMessage(error, "Creazione admin fallita."));
    } finally {
      setCreateBusy(false);
    }
  }

  return (
    <div className="stack">
      <div className="admin-grid">
        <article className="admin-card">
          <h3>Crea nuovo admin</h3>
          <form
            className="stack"
            onSubmit={(event) => void handleCreateAdmin(event)}
          >
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
                  placeholder="almeno 8 caratteri"
                />
              </div>
            </div>

            <div className="field">
              <label>Aree di accesso</label>
              <div className="inline-actions">
                {VALID_AREAS.map((area) => (
                  <button
                    key={area}
                    type="button"
                    className={newAreas.includes(area) ? "button" : "button-secondary"}
                    onClick={() => toggleArea(area)}
                    disabled={newIsSuperadmin}
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
                  checked={newIsSuperadmin}
                  onChange={(event) => {
                    setNewIsSuperadmin(event.target.checked);
                    if (event.target.checked) {
                      setNewAreas([]);
                    }
                  }}
                />
                <span>Superadmin (accesso completo a tutte le aree)</span>
              </label>
            </div>

            <div className="actions">
              <button className="button" type="submit" disabled={createBusy}>
                {createBusy ? "Creazione..." : "Crea admin"}
              </button>
            </div>

            {createStatus ? (
              <p className="helper">{createStatus}</p>
            ) : null}
          </form>
        </article>
      </div>
    </div>
  );
}
