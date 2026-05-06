"use client";

import { useEffect, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";
import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

type SiteTitlesResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type SiteLobbyPublicationPanelProps = {
  refreshKey?: number;
  busyAction?: string | null;
  onUpdatePublication: (
    title: CatalogTitle,
    payload: {
      lobby_visibility: "hidden" | "visible";
      demo_enabled: boolean;
      real_enabled: boolean;
      lobby_display_name?: string | null;
      lobby_description?: string | null;
      featured?: boolean;
      position?: number;
    },
  ) => Promise<void>;
};

export function SiteLobbyPublicationPanel({
  refreshKey = 0,
  busyAction = null,
  onUpdatePublication,
}: SiteLobbyPublicationPanelProps) {
  const [catalog, setCatalog] = useState<SiteTitlesResponse | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setStatus("loading");
    setMessage(null);

    apiRequest<SiteTitlesResponse>("/catalog/sites/casinoking/titles")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setCatalog(data);
        setStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setStatus("error");
        setMessage(
          error instanceof ApiRequestError
            ? error.message
            : "Pubblicazione lobby non disponibile",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  const titles = catalog?.titles ?? [];
  const variants = titles.filter((title) => !title.is_master);
  const visibleVariants = variants.filter(
    (title) => title.publication.lobby_visibility === "visible",
  );

  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Lobby giochi</h3>
          <p>Gestione leggera dei Title pubblicati sul sito corrente.</p>
        </div>
        <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
          {status === "loading" ? "loading" : catalog?.site.display_name ?? "CasinoKing"}
        </span>
      </div>

      {message ? <p className="status-message error">{message}</p> : null}

      {catalog ? (
        <div className="stack">
          <section className="admin-surface admin-surface-section">
            <div className="admin-card-heading">
              <div>
                <h4>Stato lobby</h4>
                <p>Visibilita', demo e real senza configurare il gioco.</p>
              </div>
              <span className="status-inline info">
                {visibleVariants.length} visibili / {variants.length} varianti
              </span>
            </div>
          </section>

          <section className="admin-surface admin-surface-section">
            <div className="admin-card-heading">
              <div>
                <h4>Title disponibili</h4>
                <p>Il master resta consultabile ma non pubblicabile come item lobby.</p>
              </div>
            </div>

            {titles.length > 0 ? (
              <div className="admin-list admin-list-static">
                {titles.map((title) => {
                  const publication = title.publication;
                  const isVisible = publication.lobby_visibility === "visible";
                  return (
                    <article className="admin-list-card" key={title.title_code}>
                      <div className="admin-card-heading">
                        <div>
                          <h4>{publication.lobby_display_name ?? title.display_name}</h4>
                          <p className="mono">{title.title_code}</p>
                        </div>
                        <span className={`status-inline ${title.is_master ? "warning" : isVisible ? "success" : "info"}`}>
                          {title.is_master ? "master" : isVisible ? "visible" : "hidden"}
                        </span>
                      </div>
                      <div className="admin-metric-row">
                        <span className="list-muted">Engine</span>
                        <span>{title.engine.display_name}</span>
                      </div>
                      <div className="admin-metric-row">
                        <span className="list-muted">Modalita'</span>
                        <span>
                          demo {publication.demo_enabled ? "on" : "off"} / real{" "}
                          {publication.real_enabled ? "on" : "off"}
                        </span>
                      </div>
                      <div className="admin-metric-row">
                        <span className="list-muted">Ordine</span>
                        <span>{publication.position}</span>
                      </div>
                      <div className="actions">
                        {title.is_master ? (
                          <a
                            className="button-secondary"
                            href={`/mines?title_code=${encodeURIComponent(title.title_code)}&mode=demo&preview=1`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Preview demo
                          </a>
                        ) : (
                          <>
                            <button
                              className="button-secondary"
                              type="button"
                              disabled={busyAction !== null}
                              onClick={() =>
                                void onUpdatePublication(title, {
                                  lobby_visibility: "visible",
                                  demo_enabled: true,
                                  real_enabled: publication.real_enabled,
                                  lobby_display_name: publication.lobby_display_name,
                                  lobby_description: publication.lobby_description,
                                  featured: publication.featured,
                                  position: publication.position,
                                })
                              }
                            >
                              Demo
                            </button>
                            <button
                              className="button-secondary"
                              type="button"
                              disabled={busyAction !== null}
                              onClick={() =>
                                void onUpdatePublication(title, {
                                  lobby_visibility: "visible",
                                  demo_enabled: true,
                                  real_enabled: true,
                                  lobby_display_name: publication.lobby_display_name,
                                  lobby_description: publication.lobby_description,
                                  featured: publication.featured,
                                  position: publication.position,
                                })
                              }
                            >
                              Demo + real
                            </button>
                            <button
                              className="button-ghost"
                              type="button"
                              disabled={busyAction !== null}
                              onClick={() =>
                                void onUpdatePublication(title, {
                                  lobby_visibility: "hidden",
                                  demo_enabled: false,
                                  real_enabled: false,
                                  lobby_display_name: publication.lobby_display_name,
                                  lobby_description: publication.lobby_description,
                                  featured: publication.featured,
                                  position: publication.position,
                                })
                              }
                            >
                              Nascondi
                            </button>
                          </>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <p className="empty-state">Nessun Title disponibile.</p>
            )}
          </section>
        </div>
      ) : null}
    </article>
  );
}
