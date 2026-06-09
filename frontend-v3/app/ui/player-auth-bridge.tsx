"use client";

import { useEffect } from "react";

import { consumePlayerAuthHandoff } from "../lib/player-auth";

export function PlayerAuthBridge() {
  useEffect(() => {
    consumePlayerAuthHandoff();
  }, []);

  return null;
}
