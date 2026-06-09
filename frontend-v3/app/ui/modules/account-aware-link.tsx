"use client";

import { useEffect, useMemo, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
  type PlayerAuthSnapshot,
} from "../../lib/player-auth";
import { resolvePlayerReturnHref, SITE_V3_BASE_URL } from "../site-v3-render-helpers";

export function AccountAwareLink({
  className,
  href,
  label,
}: {
  className: string;
  href: string;
  label: string;
}) {
  const [returnTo, setReturnTo] = useState(SITE_V3_BASE_URL);
  const [authSnapshot, setAuthSnapshot] = useState<PlayerAuthSnapshot>({
    accessToken: "",
    email: "",
  });

  useEffect(() => {
    function refreshSnapshot() {
      setAuthSnapshot(readPlayerAuthSnapshot());
    }

    setReturnTo(window.location.href);
    refreshSnapshot();
    window.addEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
    window.addEventListener("storage", refreshSnapshot);
    return () => {
      window.removeEventListener(PLAYER_AUTH_EVENT, refreshSnapshot);
      window.removeEventListener("storage", refreshSnapshot);
    };
  }, []);

  const isAccountHref = pointsToAccount(href);
  const accountHref = useMemo(() => resolvePlayerReturnHref("/account", returnTo), [returnTo]);
  const isAuthenticated = hasPlayerAuthSnapshot(authSnapshot);

  if (isAccountHref && isAuthenticated) {
    return (
      <a className={className} href={accountHref} title={authSnapshot.email}>
        Account
      </a>
    );
  }

  return (
    <a className={className} href={isAccountHref ? accountHref : href}>
      {label}
    </a>
  );
}

function pointsToAccount(href: string): boolean {
  if (href === "/account" || href.startsWith("/account?")) {
    return true;
  }
  try {
    const url = new URL(href, SITE_V3_BASE_URL);
    return url.pathname === "/account";
  } catch {
    return false;
  }
}
