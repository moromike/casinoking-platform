"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";

const PLAYER_AUTH_EVENT = "player-auth-changed";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

type PasswordResetResponse = {
  reset_requested: boolean;
  reset_token?: string | null;
};

export function PlayerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showReset, setShowReset] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("login");
    setStatus(null);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      const data = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: normalizedEmail, password }),
      });

      window.localStorage.setItem(PLAYER_STORAGE_KEYS.accessToken, data.access_token);
      window.localStorage.setItem(PLAYER_STORAGE_KEYS.email, normalizedEmail);
      window.dispatchEvent(new Event(PLAYER_AUTH_EVENT));
      setStatus("Sign in completed.");
      router.push("/account");
      router.refresh();
    } catch (error) {
      setStatus(readErrorMessage(error, "Sign in failed."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleForgotPassword() {
    setBusyAction("forgot");
    setStatus(null);

    try {
      const data = await apiRequest<PasswordResetResponse>("/auth/password/forgot", {
        method: "POST",
        body: JSON.stringify({ email: resetEmail }),
      });

      setStatus(
        data.reset_token
          ? `Password reset token issued: ${data.reset_token}`
          : "Password reset request accepted.",
      );
    } catch (error) {
      setStatus(readErrorMessage(error, "Password reset request failed."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleResetPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("reset");
    setStatus(null);

    try {
      await apiRequest<{ password_reset: boolean }>("/auth/password/reset", {
        method: "POST",
        body: JSON.stringify({ token: resetToken, new_password: newPassword }),
      });
      setStatus("Password reset completed.");
    } catch (error) {
      setStatus(readErrorMessage(error, "Password reset failed."));
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section className="panel stack">
      <div>
        <p className="eyebrow">Player</p>
        <h2 style={{ marginBottom: 8 }}>Sign in</h2>
        <p style={{ margin: 0 }}>Dedicated player login flow outside the legacy monolith.</p>
      </div>

      {status ? <div className="status-line">{status}</div> : null}

      <form className="form-card stack" onSubmit={handleLogin}>
        <div className="field-grid player-form-fields">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
        </div>
        <div className="player-form-actions">
          <button className="button" type="submit" disabled={busyAction !== null}>
            {busyAction === "login" ? "Signing in..." : "Sign in"}
          </button>
          <Link className="button-secondary" href="/register">
            Register
          </Link>
        </div>
      </form>

      {!showReset ? (
        <button className="player-text-link" type="button" onClick={() => setShowReset(true)}>
          Hai dimenticato la password?
        </button>
      ) : (
        <section className="form-card stack">
          <h3 style={{ marginBottom: 0 }}>Password reset</h3>
          <div className="field-grid player-form-fields">
            <label>
              Reset email
              <input
                type="email"
                value={resetEmail}
                onChange={(event) => setResetEmail(event.target.value)}
                autoComplete="email"
              />
            </label>
            <div className="player-form-actions player-form-actions-inline-end">
              <button
                className="button-secondary"
                type="button"
                disabled={busyAction !== null || !resetEmail}
                onClick={() => void handleForgotPassword()}
              >
                {busyAction === "forgot" ? "Requesting..." : "Request reset token"}
              </button>
            </div>
          </div>

          <form className="field-grid player-form-fields" onSubmit={handleResetPassword}>
            <label>
              Reset token
              <input value={resetToken} onChange={(event) => setResetToken(event.target.value)} autoComplete="off" />
            </label>
            <label>
              New password
              <input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                autoComplete="new-password"
              />
            </label>
            <div className="player-form-actions player-form-actions-inline-end">
              <button className="button" type="submit" disabled={busyAction !== null || !resetToken || !newPassword}>
                {busyAction === "reset" ? "Updating..." : "Update password"}
              </button>
            </div>
          </form>
        </section>
      )}
    </section>
  );
}
