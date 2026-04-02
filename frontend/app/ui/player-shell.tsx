"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { PLAYER_STORAGE_KEYS } from "@/app/lib/player-storage";

const PLAYER_AUTH_EVENT = "player-auth-changed";

const PLAYER_NAV_ITEMS = [
  { href: "/", label: "Lobby" },
  { href: "/mines", label: "Mines" },
  { href: "/account", label: "Account" },
  { href: "/login", label: "Login" },
  { href: "/register", label: "Register" },
] as const;

function readPlayerAuthState() {
  if (typeof window === "undefined") {
    return { isAuthenticated: false, avatarLabel: "C" };
  }

  const accessToken = window.localStorage.getItem(PLAYER_STORAGE_KEYS.accessToken) ?? "";
  const email = window.localStorage.getItem(PLAYER_STORAGE_KEYS.email) ?? "";
  const firstName = window.localStorage.getItem(PLAYER_STORAGE_KEYS.firstName) ?? "";
  const avatarSource = firstName || email || "CasinoKing";

  return {
    isAuthenticated: accessToken.length > 0,
    avatarLabel: avatarSource.charAt(0).toUpperCase() || "C",
  };
}

export function PlayerShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [authState, setAuthState] = useState(() => readPlayerAuthState());

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

  function handleLogout() {
    Object.values(PLAYER_STORAGE_KEYS).forEach((key) => {
      window.localStorage.removeItem(key);
    });

    const nextState = { isAuthenticated: false, avatarLabel: "C" };

    setAuthState(nextState);
    window.dispatchEvent(new Event(PLAYER_AUTH_EVENT));
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
                <button className="button-secondary" type="button" onClick={handleLogout}>
                  Esci
                </button>
              </>
            ) : (
              <>
                <Link className="button-secondary" href="/login">
                  Login
                </Link>
                <Link className="button" href="/register">
                  Register
                </Link>
              </>
            )}
          </div>
        </header>

        <div className="stack player-content">{children}</div>

        <div className="player-bottom-nav" data-player-bottom-nav-mobile>
          <nav aria-label="Player mobile navigation" className="player-bottom-nav-items">
            {PLAYER_NAV_ITEMS.map((item) => (
              <Link key={item.href} className="button-secondary" href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </main>
  );
}
