"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasStoredPlayerAccessToken,
} from "@/app/lib/auth-storage";

const PLACEHOLDER_GAMES = Array.from({ length: 11 }, (_, index) => ({
  id: `placeholder-${index + 1}`,
  title: `Coming Soon ${index + 1}`,
}));

export function PlayerLobbyPage() {
  const [hasAccessToken, setHasAccessToken] = useState(false);

  useEffect(() => {
    function syncAuthState() {
      setHasAccessToken(hasStoredPlayerAccessToken());
    }

    syncAuthState();
    window.addEventListener("storage", syncAuthState);
    window.addEventListener(PLAYER_AUTH_EVENT, syncAuthState);

    return () => {
      window.removeEventListener("storage", syncAuthState);
      window.removeEventListener(PLAYER_AUTH_EVENT, syncAuthState);
    };
  }, []);

  return (
    <>
      <section className="panel stack player-hero-banner">
        <div>
          <p className="eyebrow">CasinoKing</p>
          <h2 style={{ marginBottom: 8 }}>Lobby</h2>
          <p style={{ margin: 0 }}>
            Casino lobby with a dedicated entry point for Mines and scalable placeholders for the future catalogue.
          </p>
        </div>
        {!hasAccessToken ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            <Link className="button" href="/login">
              Login
            </Link>
            <Link className="button-secondary" href="/register">
              Register
            </Link>
          </div>
        ) : null}
      </section>

      <section className="panel stack">
        <div>
          <p className="eyebrow">Games</p>
          <h3 style={{ marginBottom: 8 }}>Lobby grid</h3>
          <p style={{ margin: 0 }}>Mines is the live original game. Placeholder cards preserve the future multi-game layout without inventing fake product logic.</p>
        </div>
        <div className="player-game-grid">
          <article className="player-game-card">
            <div className="player-game-art" aria-hidden="true">
              ♦
            </div>
            <div className="stack">
              <div>
                <p className="eyebrow">Original</p>
                <h4 style={{ margin: "0 0 6px" }}>Mines</h4>
                <p style={{ margin: 0 }}>Standalone game route with server-authoritative state, wallet integration, and fairness detail.</p>
              </div>
              <div>
                <Link className="button" href="/mines">
                  Open Mines
                </Link>
              </div>
            </div>
          </article>

          {PLACEHOLDER_GAMES.map((game) => (
            <article key={game.id} className="player-game-card player-game-card-placeholder">
              <div className="player-game-art" aria-hidden="true">
                ★
              </div>
              <div>
                <p className="eyebrow">Soon</p>
                <h4 style={{ margin: "0 0 6px" }}>{game.title}</h4>
                <p style={{ margin: 0 }}>Reserved slot for future onboarding.</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
