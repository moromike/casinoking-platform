"use client";

import { useEffect, useMemo, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasPlayerAuthSnapshot,
  readPlayerAuthSnapshot,
  type PlayerAuthSnapshot,
} from "../../lib/player-auth";
import { resolvePlayerReturnHref, SITE_V3_BASE_URL } from "../site-v3-render-helpers";

export function SiteHeaderAuthActions({
  accountLabel,
  loginLabel,
}: {
  accountLabel: string;
  loginLabel: string;
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

  const loginHref = useMemo(() => resolvePlayerReturnHref("/login", returnTo), [returnTo]);
  const accountHref = useMemo(() => resolvePlayerReturnHref("/account", returnTo), [returnTo]);
  const isAuthenticated = hasPlayerAuthSnapshot(authSnapshot);

  if (isAuthenticated) {
    return (
      <a className="is-account" href={accountHref} title={authSnapshot.email}>
        {accountLabel}
      </a>
    );
  }

  return (
    <>
      <a className="is-login" href={loginHref}>
        {loginLabel}
      </a>
      <a className="is-account" href={accountHref}>
        {accountLabel}
      </a>
    </>
  );
}
