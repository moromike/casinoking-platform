"use client";

import { useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GamePublicationBadges, GameStatusBadges } from "./game-status-badges";

type GameVariantListProps = {
  variants: CatalogTitle[];
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
};

export function GameVariantList({
  variants,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onUpdateTitleDisplayName,
  onPreviewTitle,
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
    return <div className="games-empty-state">No variants yet.</div>;
  }

  return (
    <div className="games-list-table-shell">
      <table className="games-list-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Title code</th>
            <th>Status</th>
            <th>Lobby</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {variants.map((title) => {
            const titleDraft = titleNameDrafts[title.title_code] ?? title.display_name;
            const hasNameChange = titleDraft.trim() !== title.display_name;

            return (
              <tr key={title.title_code}>
                <td>
                  {!onUpdateTitleDisplayName ? (
                    <span className="games-title-name">{title.display_name}</span>
                  ) : (
                    <input
                      aria-label={`Display name for ${title.title_code}`}
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
                  <GameStatusBadges title={title} />
                </td>
                <td>
                  <GamePublicationBadges title={title} />
                </td>
                <td>
                  <div className="games-row-actions">
                    <button
                      className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                      type="button"
                      onClick={() => onOpenTitle?.(title)}
                    >
                      {selectedTitleCode === title.title_code ? "Detail open" : "Open detail"}
                    </button>
                    {onUpdateTitleDisplayName ? (
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={
                          busyAction !== null ||
                          !titleDraft.trim() ||
                          !hasNameChange
                        }
                        onClick={() => void handleUpdateTitleName(title)}
                      >
                        Save name
                      </button>
                    ) : null}
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={!onPreviewTitle}
                      onClick={() => onPreviewTitle?.(title)}
                    >
                      Preview
                    </button>
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
