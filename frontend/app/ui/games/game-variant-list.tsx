"use client";

import { useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

type GameVariantListProps = {
  variants: CatalogTitle[];
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
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

export function GameVariantList({
  variants,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onUpdateTitleDisplayName,
  onUpdatePublication,
}: GameVariantListProps) {
  const [titleNameDrafts, setTitleNameDrafts] = useState<Record<string, string>>({});

  async function handleUpdateTitleName(title: CatalogTitle) {
    if (!onUpdateTitleDisplayName) {
      return;
    }
    await onUpdateTitleDisplayName(title, {
      display_name: (titleNameDrafts[title.title_code] ?? title.display_name).trim(),
    });
  }

  if (variants.length === 0) {
    return <p className="empty-state">Nessuna variante creata.</p>;
  }

  return (
    <div className="admin-list admin-list-static">
      {variants.map((title) => {
        const titleDraft = titleNameDrafts[title.title_code] ?? title.display_name;
        return (
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
              <span className="list-muted">Source</span>
              <span className="mono">{title.source_title_code ?? "n/a"}</span>
            </div>
            <div className="admin-metric-row">
              <span className="list-muted">Sito</span>
              <span>
                {title.publication.lobby_visibility === "visible" ? "visibile" : "nascosto"}
                {" / demo "}
                {title.publication.demo_enabled ? "on" : "off"}
                {" / real "}
                {title.publication.real_enabled ? "on" : "off"}
              </span>
            </div>
            {onUpdateTitleDisplayName ? (
              <div className="field-grid">
                <div className="field">
                  <label htmlFor={`title-name-${title.title_code}`}>Nome variante</label>
                  <input
                    id={`title-name-${title.title_code}`}
                    value={titleDraft}
                    onChange={(event) =>
                      setTitleNameDrafts((current) => ({
                        ...current,
                        [title.title_code]: event.target.value,
                      }))
                    }
                  />
                </div>
              </div>
            ) : null}
            <div className="actions">
              <button
                className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                type="button"
                onClick={() => onOpenTitle?.(title)}
              >
                {selectedTitleCode === title.title_code ? "Configurazione aperta" : "Personalizza"}
              </button>
              {onUpdateTitleDisplayName ? (
                <button
                  className="button-secondary"
                  type="button"
                  disabled={
                    busyAction !== null ||
                    !titleDraft.trim() ||
                    titleDraft.trim() === title.display_name
                  }
                  onClick={() => void handleUpdateTitleName(title)}
                >
                  Salva nome
                </button>
              ) : null}
              {onUpdatePublication ? (
                <>
                  <button
                    className="button-secondary"
                    type="button"
                    disabled={busyAction !== null}
                    onClick={() =>
                      void onUpdatePublication(title, {
                        lobby_visibility: "visible",
                        demo_enabled: true,
                        real_enabled: title.publication.real_enabled,
                        lobby_display_name: title.publication.lobby_display_name,
                        lobby_description: title.publication.lobby_description,
                        featured: title.publication.featured,
                        position: title.publication.position,
                      })
                    }
                  >
                    Pubblica demo
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
                        lobby_display_name: title.publication.lobby_display_name,
                        lobby_description: title.publication.lobby_description,
                        featured: title.publication.featured,
                        position: title.publication.position,
                      })
                    }
                  >
                    Pubblica demo + real
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
                        lobby_display_name: title.publication.lobby_display_name,
                        lobby_description: title.publication.lobby_description,
                        featured: title.publication.featured,
                        position: title.publication.position,
                      })
                    }
                  >
                    Nascondi
                  </button>
                </>
              ) : null}
              <a
                className="button-secondary"
                href={`/mines?title_code=${encodeURIComponent(title.title_code)}&mode=demo&preview=1`}
                target="_blank"
                rel="noreferrer"
              >
                Preview demo
              </a>
            </div>
          </article>
        );
      })}
    </div>
  );
}
