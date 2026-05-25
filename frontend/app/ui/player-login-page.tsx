"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  dispatchPlayerAuthChanged,
  preparePlayerAuthReturnHandoff,
  storePlayerAuthSession,
} from "@/app/lib/auth-storage";
import { apiRequest, readErrorMessage } from "@/app/lib/api";
import { Button } from "@/app/ui/components/button";

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
    setReturnTo(sanitizeReturnTo(params.get("return_to")));
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
        preparePlayerAuthReturnHandoff({
          accessToken: data.access_token,
          email: normalizedEmail,
          returnTo,
        });
        window.location.assign(returnTo);
        return;
      }

      // Redirect intelligente: lobby se c'è saldo, account (ricarica) se saldo zero
      let redirectTo = "/account";
      try {
        const wallet = await apiRequest<WalletResponse>("/wallets/cash", {}, data.access_token);
        const balance = parseFloat(wallet.balance_snapshot ?? "0");
        if (balance > 0) redirectTo = "/";
      } catch {
        // fallback silenzioso: va ad account
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
          <Button disabled={busyAction !== null} isLoading={busyAction === "login"} type="submit">
            Sign in
          </Button>
          <Button href={returnTo ? `/register?return_to=${encodeURIComponent(returnTo)}` : "/register"} variant="secondary">
            Register
          </Button>
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
              <Button
                type="button"
                disabled={busyAction !== null || !resetEmail}
                isLoading={busyAction === "forgot"}
                variant="secondary"
                onClick={() => void handleForgotPassword()}
              >
                Request reset token
              </Button>
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
              <Button
                type="submit"
                disabled={busyAction !== null || !resetToken || !newPassword}
                isLoading={busyAction === "reset"}
              >
                Update password
              </Button>
            </div>
          </form>
        </section>
      )}
    </section>
  );
}

function sanitizeReturnTo(value: string | null): string | null {
  if (!value) {
    return null;
  }
  try {
    if (value.startsWith("/") && !value.startsWith("//")) {
      return value;
    }
    const url = new URL(value);
    const currentOrigin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const allowedOrigins = new Set([currentOrigin, "http://localhost:3001", "http://127.0.0.1:3001"]);
    return allowedOrigins.has(url.origin) ? url.toString() : null;
  } catch {
    return null;
  }
}
