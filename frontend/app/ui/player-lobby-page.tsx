"use client";

import { useEffect, useState } from "react";

import {
  PLAYER_AUTH_EVENT,
  hasStoredPlayerAccessToken,
} from "@/app/lib/auth-storage";
import { ApiRequestError, apiRequest } from "@/app/lib/api";
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
    eyebrow: "Catalogo",
    headline: "Varianti pubblicate dal backoffice",
    body: "Le nuove skin Mines diventano giocabili quando vengono rese visibili sul sito.",
    accent: "rgba(139, 92, 246, 0.28)",
  },
] as const;

const BANNER_INTERVAL_MS = 4500;

type GameLibraryTitle = {
  title_code: string;
  engine_code: string;
  engine_display_name: string;
  display_name: string;
  catalog_display_name: string;
  description: string | null;
  demo_enabled: boolean;
  real_enabled: boolean;
  featured: boolean;
  position: number;
};

type GameLibraryResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: GameLibraryTitle[];
};

export function PlayerLobbyPage() {
  const [hasAccessToken, setHasAccessToken] = useState(false);
  const [activeSlide, setActiveSlide] = useState(0);
  const [gameLibrary, setGameLibrary] = useState<GameLibraryTitle[]>([]);
  const [libraryStatus, setLibraryStatus] = useState<"loading" | "idle" | "error">("loading");

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
    let isMounted = true;
    setLibraryStatus("loading");
    apiRequest<GameLibraryResponse>("/games/library")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setGameLibrary(data.titles);
        setLibraryStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setLibraryStatus("error");
        if (error instanceof ApiRequestError) {
          setGameLibrary([]);
        }
      });

    return () => {
      isMounted = false;
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
          <p style={{ margin: 0 }}>Titoli pubblicati dal backoffice per il sito corrente.</p>
        </div>
        <div className="player-game-grid">
          {gameLibrary.map((game) => (
            <article
              key={game.title_code}
              className={`player-game-card ${game.featured ? "player-game-card-primary" : ""}`}
            >
              <div className="player-game-art" aria-hidden="true">
                ♦
              </div>
              <div className="stack">
                <div>
                  <p className="eyebrow">{game.engine_display_name}</p>
                  <h4 style={{ margin: "0 0 6px" }}>{game.display_name}</h4>
                  <p style={{ margin: 0 }}>
                    {game.description ?? "Variante pubblicata del catalogo CasinoKing."}
                  </p>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                  {game.demo_enabled ? (
                    <Button href={`/mines?title_code=${game.title_code}&mode=demo`}>
                      Demo
                    </Button>
                  ) : null}
                  {game.real_enabled ? (
                    <Button
                      href={hasAccessToken ? `/mines?title_code=${game.title_code}` : "/login"}
                      variant={game.demo_enabled ? "secondary" : "primary"}
                    >
                      {hasAccessToken ? "Gioca" : "Login"}
                    </Button>
                  ) : null}
                </div>
              </div>
            </article>
          ))}

          {libraryStatus === "idle" && gameLibrary.length === 0 ? (
            <article className="player-game-card player-game-card-placeholder">
              <div className="player-game-art" aria-hidden="true">
                ♦
              </div>
              <div>
                <p className="eyebrow">Catalogo</p>
                <h4 style={{ margin: "0 0 6px" }}>Nessun gioco pubblicato</h4>
                <p style={{ margin: 0 }}>
                  Le varianti create in backoffice appariranno qui quando saranno pubblicate.
                </p>
              </div>
            </article>
          ) : null}

          {libraryStatus === "error" ? (
            <article className="player-game-card player-game-card-placeholder">
              <div className="player-game-art" aria-hidden="true">
                ♦
              </div>
              <div>
                <p className="eyebrow">Catalogo</p>
                <h4 style={{ margin: "0 0 6px" }}>Catalogo non disponibile</h4>
                <p style={{ margin: 0 }}>Riprova tra poco.</p>
              </div>
            </article>
          ) : null}
        </div>
      </section>
    </>
  );
}
