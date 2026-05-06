"use client";

import { useEffect, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";
import { GamesOverview } from "@/app/ui/games/games-overview";

export type CatalogTitle = {
  title_code: string;
  engine_code: string;
  display_name: string;
  status: string;
  is_master: boolean;
  source_title_code: string | null;
  site_title_status: string;
  publication: {
    site_title_status: string;
    lobby_visibility: "hidden" | "visible";
    demo_enabled: boolean;
    real_enabled: boolean;
    lobby_display_name: string | null;
    lobby_description: string | null;
    featured: boolean;
    position: number;
  };
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

type PlatformCatalogPanelProps = {
  selectedTitleCode?: string;
  refreshKey?: number;
  busyAction?: string | null;
  onConfigureTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string },
  ) => Promise<void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onUpdatePublication?: (
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

export function PlatformCatalogPanel({
  selectedTitleCode,
  refreshKey = 0,
  busyAction = null,
  onConfigureTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onUpdatePublication,
}: PlatformCatalogPanelProps) {
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
  }, [refreshKey]);

  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Catalogo giochi</h3>
          <p>Engine, master e varianti del Site corrente.</p>
        </div>
        <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
          {status === "loading" ? "loading" : catalog?.site.status ?? "n/a"}
        </span>
      </div>

      {message ? <p className="status-message error">{message}</p> : null}

      {catalog ? (
        <GamesOverview
          catalog={catalog}
          selectedTitleCode={selectedTitleCode}
          busyAction={busyAction}
          onOpenTitle={onConfigureTitle}
          onDuplicateTitle={onDuplicateTitle}
          onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          onUpdatePublication={onUpdatePublication}
        />
      ) : null}
    </article>
  );
}
