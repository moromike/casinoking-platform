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
  const demoEnabled = visibleVariants.filter((title) => title.publication.demo_enabled);
  const realEnabled = visibleVariants.filter((title) => title.publication.real_enabled);

  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Lobby giochi</h3>
          <p>Pubblicazione dei Title sul sito corrente.</p>
        </div>
        <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
          {status === "loading" ? "loading" : catalog?.site.display_name ?? "CasinoKing"}
        </span>
      </div>

      {message ? <p className="status-message error">{message}</p> : null}

      {catalog ? (
        <div className="site-lobby-manager">
          <div className="site-lobby-kpis">
            <div>
              <span className="list-muted">Visibili</span>
              <strong>{visibleVariants.length}</strong>
            </div>
            <div>
              <span className="list-muted">Demo</span>
              <strong>{demoEnabled.length}</strong>
            </div>
            <div>
              <span className="list-muted">Real</span>
              <strong>{realEnabled.length}</strong>
            </div>
            <div>
              <span className="list-muted">Varianti</span>
              <strong>{variants.length}</strong>
            </div>
          </div>

          {titles.length > 0 ? (
            <div className="site-lobby-table-shell">
              <table className="site-lobby-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Tipo</th>
                    <th>Visibilita'</th>
                    <th>Modalita'</th>
                    <th>Ordine</th>
                    <th>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {titles.map((title) => {
                    const publication = title.publication;
                    const isVisible = publication.lobby_visibility === "visible";
                    return (
                      <tr key={title.title_code}>
                        <td>
                          <strong>{publication.lobby_display_name ?? title.display_name}</strong>
                          <span className="mono">{title.title_code}</span>
                        </td>
                        <td>
                          <span className={`status-inline ${title.is_master ? "warning" : "success"}`}>
                            {title.is_master ? "master" : "variante"}
                          </span>
                        </td>
                        <td>
                          <span className={`status-inline ${isVisible ? "success" : "info"}`}>
                            {isVisible ? "visible" : "hidden"}
                          </span>
                        </td>
                        <td>
                          demo {publication.demo_enabled ? "on" : "off"} / real{" "}
                          {publication.real_enabled ? "on" : "off"}
                        </td>
                        <td>{publication.position}</td>
                        <td>
                          <div className="site-lobby-actions">
                            {title.is_master ? (
                              <a
                                className="button-secondary"
                                href={`/mines?title_code=${encodeURIComponent(title.title_code)}&mode=demo&preview=1`}
                                target="_blank"
                                rel="noreferrer"
                              >
                                Preview
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
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-state">Nessun Title disponibile.</p>
          )}
        </div>
      ) : null}
    </article>
  );
}
