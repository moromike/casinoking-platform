"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import {
  PLAYER_AUTH_EVENT,
  clearPlayerAuthStorage,
  dispatchPlayerAuthChanged,
  readStoredPlayerAuthSnapshot,
} from "@/app/lib/auth-storage";
import { apiRequest } from "@/app/lib/api";
import { Button } from "@/app/ui/components/button";

const PLAYER_NAV_ITEMS = [
  { href: "/", label: "Lobby" },
  { href: "/mines", label: "Mines" },
  { href: "/account", label: "Account" },
  { href: "/login", label: "Login" },
  { href: "/register", label: "Register" },
] as const;

const PLAYER_GUEST_ONLY_NAV_ITEMS = new Set(["/login", "/register"]);

function readPlayerAuthState() {
  const { accessToken, email, firstName } = readStoredPlayerAuthSnapshot();
  const avatarSource = firstName || email || "CasinoKing";

  return {
    isAuthenticated: accessToken.length > 0,
    avatarLabel: avatarSource.charAt(0).toUpperCase() || "C",
  };
}

export function PlayerShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [authState, setAuthState] = useState({
    isAuthenticated: false,
    avatarLabel: "C",
  });
  const bottomNavItems = PLAYER_NAV_ITEMS.filter(
    (item) => !authState.isAuthenticated || !PLAYER_GUEST_ONLY_NAV_ITEMS.has(item.href),
  );

  useEffect(() => {
    function syncAuthState() {
      setAuthState(readPlayerAuthState());
    }

    syncAuthState();
    window.addEventListener("storage", syncAuthState);
    window.addEventListener(PLAYER_AUTH_EVENT, syncAuthState);

    return () => {
      window.removeEventListener("storage", syncAuthState);
      window.removeEventListener(PLAYER_AUTH_EVENT, syncAuthState);
    };
  }, []);

  async function handleLogout() {
    const { accessToken } = readStoredPlayerAuthSnapshot();
    if (accessToken.length > 0) {
      try {
        await apiRequest("/auth/logout", { method: "POST" }, accessToken);
      } catch {
        // Logout proceeds locally even if the backend call fails.
      }
    }

    clearPlayerAuthStorage();

    const nextState = { isAuthenticated: false, avatarLabel: "C" };

    setAuthState(nextState);
    dispatchPlayerAuthChanged();
    router.push("/");
    router.refresh();
  }

  return (
    <main className="page-shell player-shell">
      <div className="player-shell-frame">
        <header className="player-shell-topbar">
          <Link className="player-shell-brand" href="/">
            CasinoKing
          </Link>

          <div className="player-shell-header-actions">
            {authState.isAuthenticated ? (
              <>
                <Link aria-label="Account" className="player-shell-avatar" href="/account">
                  {authState.avatarLabel}
                </Link>
                <Button type="button" variant="secondary" onClick={handleLogout}>
                  Esci
                </Button>
              </>
            ) : (
              <>
                <Button href="/login" variant="secondary">
                  Login
                </Button>
                <Button href="/register">Register</Button>
              </>
            )}
          </div>
        </header>

        <div className="stack player-content">{children}</div>

        <div className="player-bottom-nav" data-player-bottom-nav-mobile>
          <nav aria-label="Player mobile navigation" className="player-bottom-nav-items">
            {bottomNavItems.map((item) => (
              <Button key={item.href} href={item.href} variant="secondary">
                {item.label}
              </Button>
            ))}
          </nav>
        </div>
      </div>
    </main>
  );
}
