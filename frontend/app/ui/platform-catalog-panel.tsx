"use client";

import { useEffect, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";

type CatalogTitle = {
  title_code: string;
  engine_code: string;
  display_name: string;
  status: string;
  site_title_status: string;
  engine: {
    engine_code: string;
    display_name: string;
    status: string;
  };
};

type SiteTitlesResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

export function PlatformCatalogPanel() {
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
            : "Catalogo giochi non disponibile",
        );
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Catalogo giochi</h3>
          <p>Engine, Title e pubblicazione Site correnti.</p>
        </div>
        <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
          {status === "loading" ? "loading" : catalog?.site.status ?? "n/a"}
        </span>
      </div>

      {message ? <p className="status-message error">{message}</p> : null}

      {catalog ? (
        <div className="admin-list admin-list-static">
          <div className="admin-metric-row">
            <span className="list-muted">Site</span>
            <span className="list-strong">{catalog.site.display_name}</span>
          </div>
          {catalog.titles.map((title) => (
            <article className="admin-list-card" key={title.title_code}>
              <div className="admin-card-heading">
                <div>
                  <h4>{title.display_name}</h4>
                  <p className="mono">{title.title_code}</p>
                </div>
                <span className={`status-inline ${title.site_title_status === "active" ? "success" : "warning"}`}>
                  {title.site_title_status}
                </span>
              </div>
              <div className="admin-metric-row">
                <span className="list-muted">Engine</span>
                <span className="list-strong">{title.engine.display_name}</span>
              </div>
              <div className="admin-metric-row">
                <span className="list-muted">Engine code</span>
                <span className="mono">{title.engine_code}</span>
              </div>
              <div className="admin-metric-row">
                <span className="list-muted">Title status</span>
                <span>{title.status}</span>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </article>
  );
}
