"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { apiRequest, readErrorMessage } from "../lib/api";
import { sanitizeAuthReturnTo, withAuthReturnTo } from "../lib/auth-return";
import { dispatchPlayerAuthChanged, storePlayerAuthSession } from "../lib/player-auth";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

type WalletResponse = {
  wallet_type: string;
  balance_snapshot: string;
};

type PasswordResetResponse = {
  reset_requested: boolean;
  reset_token?: string | null;
};

export function PlayerLoginPage() {
  const router = useRouter();
  const [returnTo, setReturnTo] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showReset, setShowReset] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setReturnTo(sanitizeAuthReturnTo(params.get("return_to")));
  }, []);

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

      storePlayerAuthSession({
        accessToken: data.access_token,
        email: normalizedEmail,
      });
      dispatchPlayerAuthChanged();

      if (returnTo) {
        window.location.assign(returnTo);
        return;
      }

      let redirectTo = "/account";
      try {
        const wallet = await apiRequest<WalletResponse>("/wallets/cash", {}, data.access_token);
        if (Number.parseFloat(wallet.balance_snapshot ?? "0") > 0) {
          redirectTo = "/";
        }
      } catch {
        // Keep account as the safe fallback when the balance read is unavailable.
      }

      router.push(redirectTo);
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
    <section className="site-v3-player-panel">
      <div>
        <p className="site-v3-player-eyebrow">Player</p>
        <h1>Sign in</h1>
        <p>Accedi al tuo account CasinoKing.</p>
      </div>

      {status ? <div className="site-v3-player-status">{status}</div> : null}

      <form className="site-v3-player-form" onSubmit={(event) => void handleLogin(event)}>
        <div className="site-v3-player-field-grid">
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
        <div className="site-v3-player-form-actions">
          <button className="site-v3-button" disabled={busyAction !== null} type="submit">
            {busyAction === "login" ? "Signing in..." : "Sign in"}
          </button>
          <a className="site-v3-button is-secondary" href={withAuthReturnTo("/register", returnTo)}>
            Register
          </a>
        </div>
      </form>

      {!showReset ? (
        <button className="site-v3-text-link" type="button" onClick={() => setShowReset(true)}>
          Hai dimenticato la password?
        </button>
      ) : (
        <section className="site-v3-player-form">
          <h2>Password reset</h2>
          <div className="site-v3-player-field-grid">
            <label>
              Reset email
              <input type="email" value={resetEmail} onChange={(event) => setResetEmail(event.target.value)} />
            </label>
            <div className="site-v3-player-form-actions is-inline-end">
              <button
                className="site-v3-button is-secondary"
                type="button"
                disabled={busyAction !== null || !resetEmail}
                onClick={() => void handleForgotPassword()}
              >
                {busyAction === "forgot" ? "Requesting..." : "Request reset token"}
              </button>
            </div>
          </div>

          <form className="site-v3-player-field-grid" onSubmit={(event) => void handleResetPassword(event)}>
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
            <div className="site-v3-player-form-actions is-inline-end">
              <button
                className="site-v3-button"
                type="submit"
                disabled={busyAction !== null || !resetToken || !newPassword}
              >
                {busyAction === "reset" ? "Updating..." : "Update password"}
              </button>
            </div>
          </form>
        </section>
      )}
    </section>
  );
}
