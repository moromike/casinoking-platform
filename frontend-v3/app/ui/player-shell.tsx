"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { apiRequest } from "../lib/api";
import { sanitizeAuthReturnTo, withAuthReturnTo } from "../lib/auth-return";
import {
  PLAYER_AUTH_EVENT,
  clearPlayerAuthStorage,
  dispatchPlayerAuthChanged,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
} from "../lib/player-auth";

export function PlayerShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [returnTo, setReturnTo] = useState<string | null>(null);
  const [authSnapshot, setAuthSnapshot] = useState(readPlayerAuthSnapshot());
  const isAuthenticated = hasPlayerAuthSnapshot(authSnapshot);
  const avatarLabel = useMemo(() => {
    const source = authSnapshot.firstName || authSnapshot.email || "CasinoKing";
    return source.charAt(0).toUpperCase() || "C";
  }, [authSnapshot.email, authSnapshot.firstName]);

  useEffect(() => {
    function refreshSnapshot() {
      setAuthSnapshot(readPlayerAuthSnapshot());
    }

    const params = new URLSearchParams(window.location.search);
    setReturnTo(sanitizeAuthReturnTo(params.get("return_to")));
    refreshSnapshot();
    window.addEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
    window.addEventListener("storage", refreshSnapshot);
    return () => {
      window.removeEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
      window.removeEventListener("storage", refreshSnapshot);
    };
  }, []);

  async function handleLogout() {
    if (authSnapshot.accessToken) {
      try {
        await apiRequest("/auth/logout", { method: "POST" }, authSnapshot.accessToken);
      } catch {
        // Logout still clears the local player shell if the token is already stale.
      }
    }

    clearPlayerAuthStorage();
    dispatchPlayerAuthChanged();
    if (returnTo) {
      window.location.assign(returnTo);
      return;
    }
    router.push("/");
    router.refresh();
  }

  return (
    <main className="site-v3-player-shell">
      <div className="site-v3-player-frame">
        <header className="site-v3-player-topbar">
          <a className="site-v3-player-brand" href="/">
            CasinoKing
          </a>
          <div className="site-v3-player-actions">
            {isAuthenticated ? (
              <>
                <a className="site-v3-player-avatar" href={withAuthReturnTo("/account", returnTo)}>
                  {avatarLabel}
                </a>
                <button className="site-v3-button is-secondary" type="button" onClick={() => void handleLogout()}>
                  Esci
                </button>
              </>
            ) : (
              <>
                <a className="site-v3-button is-secondary" href={withAuthReturnTo("/login", returnTo)}>
                  Login
                </a>
                <a className="site-v3-button" href={withAuthReturnTo("/register", returnTo)}>
                  Register
                </a>
              </>
            )}
          </div>
        </header>

        <div className="site-v3-player-content">{children}</div>

        <nav className="site-v3-player-bottom-nav" aria-label="Player navigation">
          <a href="/">Lobby</a>
          <a href="/mines">Mines</a>
          <a href={withAuthReturnTo("/account", returnTo)}>Account</a>
          {!isAuthenticated ? <a href={withAuthReturnTo("/login", returnTo)}>Login</a> : null}
          {!isAuthenticated ? <a href={withAuthReturnTo("/register", returnTo)}>Register</a> : null}
        </nav>
      </div>
    </main>
  );
}
