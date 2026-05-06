"use client";

import { useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

type GameVariantListProps = {
  master: CatalogTitle;
  variants: CatalogTitle[];
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
};

export function GameVariantList({
  master,
  variants,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onUpdateTitleDisplayName,
}: GameVariantListProps) {
  const [titleNameDrafts, setTitleNameDrafts] = useState<Record<string, string>>({});
  const rows = [master, ...variants];

  async function handleUpdateTitleName(title: CatalogTitle) {
    if (!onUpdateTitleDisplayName) {
      return;
    }
    await onUpdateTitleDisplayName(title, {
      display_name: (titleNameDrafts[title.title_code] ?? title.display_name).trim(),
    });
  }

  return (
    <div className="games-list-table-shell">
      <table className="games-list-table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Title code</th>
            <th>Tipo</th>
            <th>Stato sito</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((title) => {
            const titleDraft = titleNameDrafts[title.title_code] ?? title.display_name;
            const publicationLabel =
              title.publication.lobby_visibility === "visible"
                ? `visibile / demo ${title.publication.demo_enabled ? "on" : "off"} / real ${
                    title.publication.real_enabled ? "on" : "off"
                  }`
                : "nascosto";

            return (
              <tr key={title.title_code}>
                <td>
                  {title.is_master || !onUpdateTitleDisplayName ? (
                    <strong>{title.display_name}</strong>
                  ) : (
                    <input
                      aria-label={`Nome variante ${title.title_code}`}
                      value={titleDraft}
                      onChange={(event) =>
                        setTitleNameDrafts((current) => ({
                          ...current,
                          [title.title_code]: event.target.value,
                        }))
                      }
                    />
                  )}
                </td>
                <td className="mono">{title.title_code}</td>
                <td>
                  <span className={`status-inline ${title.is_master ? "warning" : "success"}`}>
                    {title.is_master ? "master" : "variante"}
                  </span>
                </td>
                <td>{title.is_master ? "-" : publicationLabel}</td>
                <td>
                  <div className="games-row-actions">
                    <button
                      className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                      type="button"
                      onClick={() => onOpenTitle?.(title)}
                    >
                      {title.is_master ? "Apri master" : "Dettaglio"}
                    </button>
                    {!title.is_master && onUpdateTitleDisplayName ? (
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
                    <a
                      className="button-secondary"
                      href={`/mines?title_code=${encodeURIComponent(title.title_code)}&mode=demo&preview=1`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Preview
                    </a>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
