"use client";

import { type FormEvent, useEffect, useState } from "react";

import { ADMIN_STORAGE_KEYS } from "../lib/admin-storage";
import { apiRequest, readErrorMessage } from "../lib/api";
import { SiteV3AdminBuilder } from "./site-v3-admin/site-v3-admin-builder";

type AdminLoginResponse = {
  access_token: string;
  token_type: string;
  role: string;
};

type AdminProfile = {
  id: string;
  email: string;
  role: string;
  status: string;
  is_superadmin?: boolean;
  areas?: string[];
};

type AdminStatus = {
  kind: "success" | "error" | "info";
  text: string;
};

export function AdminSiteV3Page() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [status, setStatus] = useState<AdminStatus | null>({ kind: "info", text: "Checking admin session." });
  const [isChecking, setIsChecking] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(ADMIN_STORAGE_KEYS.accessToken);
    const storedEmail = window.localStorage.getItem(ADMIN_STORAGE_KEYS.email);
    if (storedEmail) {
      setEmail(storedEmail);
    }
    if (!storedToken) {
      setIsChecking(false);
      setStatus(null);
      return;
    }
    void validateStoredSession(storedToken);
  }, []);

  async function validateStoredSession(token: string) {
    setIsChecking(true);
    try {
      const nextProfile = await apiRequest<AdminProfile>("/admin/auth/me", {}, token);
      setAccessToken(token);
      setProfile(nextProfile);
      setEmail(nextProfile.email);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.email, nextProfile.email);
      setStatus({ kind: "success", text: "Admin session restored." });
    } catch {
      clearStoredSession();
      setStatus(null);
    } finally {
      setIsChecking(false);
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatus(null);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      const login = await apiRequest<AdminLoginResponse>("/admin/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: normalizedEmail,
          password,
        }),
      });
      if (login.role !== "admin") {
        throw new Error("The authenticated user is not an admin.");
      }

      const nextProfile = await apiRequest<AdminProfile>("/admin/auth/me", {}, login.access_token);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.accessToken, login.access_token);
      window.localStorage.setItem(ADMIN_STORAGE_KEYS.email, nextProfile.email);
      setAccessToken(login.access_token);
      setProfile(nextProfile);
      setPassword("");
      setStatus({ kind: "success", text: "Admin sign-in completed." });
    } catch (error) {
      clearStoredSession();
      setStatus({ kind: "error", text: readErrorMessage(error, "Admin sign-in failed.") });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSignOut() {
    clearStoredSession();
    setAccessToken(null);
    setProfile(null);
    setPassword("");
    setStatus(null);
  }

  function clearStoredSession() {
    window.localStorage.removeItem(ADMIN_STORAGE_KEYS.accessToken);
    window.localStorage.removeItem(ADMIN_STORAGE_KEYS.sessionId);
  }

  if (isChecking) {
    return (
      <main className="site-v3-admin-page">
        <section className="site-v3-admin-login" aria-live="polite">
          <span className="site-v3-admin-kicker">CasinoKing CMS</span>
          <h1>Site V3 Admin</h1>
          <p>Checking the current admin session.</p>
        </section>
      </main>
    );
  }

  if (!accessToken) {
    return (
      <main className="site-v3-admin-page">
        <section className="site-v3-admin-login">
          <span className="site-v3-admin-kicker">CasinoKing CMS</span>
          <h1>Site V3 Admin</h1>
          <form onSubmit={handleLogin}>
            <label>
              <span>Email</span>
              <input
                autoComplete="username"
                inputMode="email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </label>
            <label>
              <span>Password</span>
              <input
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </label>
            {status ? <p className={`site-v3-admin-status is-${status.kind}`}>{status.text}</p> : null}
            <button className="site-v3-button" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Signing in" : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="site-v3-admin-page">
      <header className="site-v3-admin-topbar">
        <div>
          <span className="site-v3-admin-kicker">CasinoKing CMS</span>
          <strong>Site V3 Admin</strong>
          {profile ? <small>{profile.email}</small> : null}
        </div>
        <div className="site-v3-admin-topbar-actions">
          <a className="site-v3-button is-secondary" href="/">
            Public site
          </a>
          <button className="site-v3-button is-secondary" onClick={handleSignOut} type="button">
            Sign out
          </button>
        </div>
      </header>
      <SiteV3AdminBuilder accessToken={accessToken} />
    </main>
  );
}

