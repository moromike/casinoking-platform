"use client";

import { useEffect, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasStoredPlayerAccessToken,
} from "@/app/lib/auth-storage";
import { Button } from "@/app/ui/components/button";

const BANNER_SLIDES = [
  {
    id: "slide-1",
    eyebrow: "Benvenuto",
    headline: "Il casino che ti aspettava",
    body: "Giochi proprietari, wallet in tempo reale, fairness verificabile.",
    accent: "rgba(49, 123, 255, 0.28)",
  },
  {
    id: "slide-2",
    eyebrow: "Mines",
    headline: "Il primo gioco originale",
    body: "Server-authoritative, RTP certificato, payout runtime tabellare.",
    accent: "rgba(22, 163, 74, 0.28)",
  },
  {
    id: "slide-3",
    eyebrow: "Promo",
    headline: "Bonus di benvenuto",
    body: "Placeholder promozione. Il banner definitivo arriva con il lancio.",
    accent: "rgba(217, 119, 6, 0.28)",
  },
  {
    id: "slide-4",
    eyebrow: "Coming soon",
    headline: "Catalogo in espansione",
    body: "Nuovi giochi, nuove meccaniche. Torna presto a scoprire le novità.",
    accent: "rgba(139, 92, 246, 0.28)",
  },
] as const;

const PLACEHOLDER_GAMES = Array.from({ length: 5 }, (_, index) => ({
  id: `placeholder-${index + 1}`,
  title: `Coming Soon ${index + 1}`,
}));

const BANNER_INTERVAL_MS = 4500;

export function PlayerLobbyPage() {
  const [hasAccessToken, setHasAccessToken] = useState(false);
  const [activeSlide, setActiveSlide] = useState(0);

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

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((current) => (current + 1) % BANNER_SLIDES.length);
    }, BANNER_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  const slide = BANNER_SLIDES[activeSlide];

  return (
    <>
      <section
        className="player-hero-banner lobby-banner"
        style={{ background: `radial-gradient(circle at top right, ${slide.accent}, transparent 50%), radial-gradient(circle at 10% 80%, rgba(35, 205, 255, 0.12), transparent 30%), linear-gradient(135deg, #111827 0%, #18243d 100%)` }}
      >
        <div className="lobby-banner-content">
          <div className="lobby-banner-text">
            <p className="eyebrow">{slide.eyebrow}</p>
            <h2 style={{ margin: "4px 0 8px" }}>{slide.headline}</h2>
            <p style={{ margin: 0, color: "#c8d9f5" }}>{slide.body}</p>
          </div>

          {!hasAccessToken ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              <Button href="/login">Login</Button>
              <Button href="/register" variant="secondary">
                Register
              </Button>
            </div>
          ) : null}

          <div className="casino-hero-dots lobby-banner-dots" aria-label="Slide navigation">
            {BANNER_SLIDES.map((s, index) => (
              <button
                key={s.id}
                type="button"
                aria-label={`Slide ${index + 1}`}
                className={index === activeSlide ? "active" : ""}
                onClick={() => setActiveSlide(index)}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="panel stack">
        <div>
          <p className="eyebrow">Casino</p>
          <h3 style={{ marginBottom: 8 }}>Giochi</h3>
          <p style={{ margin: 0 }}>Mines è il gioco originale live. Gli slot riservati accoglieranno i titoli futuri.</p>
        </div>
        <div className="player-game-grid">
          <article className="player-game-card player-game-card-primary">
            <div className="player-game-art" aria-hidden="true">
              ♦
            </div>
            <div className="stack">
              <div>
                <p className="eyebrow">Originale · Live</p>
                <h4 style={{ margin: "0 0 6px" }}>Mines</h4>
                <p style={{ margin: 0 }}>Gioco standalone con stato server-authoritative, wallet integrato e fairness verificabile in tempo reale.</p>
              </div>
              <div>
                <Button href="/mines">Gioca ora</Button>
              </div>
            </div>
          </article>

          {PLACEHOLDER_GAMES.map((game) => (
            <article key={game.id} className="player-game-card player-game-card-placeholder">
              <div className="player-game-art" aria-hidden="true">
                ★
              </div>
              <div>
                <p className="eyebrow">Presto</p>
                <h4 style={{ margin: "0 0 6px" }}>{game.title}</h4>
                <p style={{ margin: 0 }}>Slot riservato al catalogo futuro.</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
