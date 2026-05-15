"use client";

import { useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GamePublicationBadges, GameStatusBadges } from "./game-status-badges";

type GameVariantListProps = {
  variants: CatalogTitle[];
  emptyMessage?: string;
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
  onArchiveTitle?: (title: CatalogTitle) => Promise<void>;
  onRestoreTitle?: (title: CatalogTitle) => Promise<void>;
};

export function GameVariantList({
  variants,
  emptyMessage = "No variants yet.",
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onUpdateTitleDisplayName,
  onPreviewTitle,
  onArchiveTitle,
  onRestoreTitle,
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

  async function handleArchiveTitle(title: CatalogTitle) {
    if (!onArchiveTitle) {
      return;
    }
    const confirmed = window.confirm(
      `Archive ${title.display_name}? The title will disappear from player launch surfaces but financial history stays intact.`,
    );
    if (!confirmed) {
      return;
    }
    await onArchiveTitle(title);
  }

  async function handleRestoreTitle(title: CatalogTitle) {
    if (!onRestoreTitle) {
      return;
    }
    await onRestoreTitle(title);
  }

  if (variants.length === 0) {
    return <div className="games-empty-state">{emptyMessage}</div>;
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
            const isArchived = title.is_archived === true;

            return (
              <tr className={isArchived ? "games-row-archived" : undefined} key={title.title_code}>
                <td>
                  {!onUpdateTitleDisplayName ? (
                    <span className="games-title-name">{title.display_name}</span>
                  ) : (
                    <input
                      aria-label={`Display name for ${title.title_code}`}
                      disabled={isArchived}
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
                      Open detail
                    </button>
                    {onUpdateTitleDisplayName ? (
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={
                          busyAction !== null ||
                          isArchived ||
                          !titleDraft.trim() ||
                          !hasNameChange
                        }
                        onClick={() => void handleUpdateTitleName(title)}
                      >
                        Save
                      </button>
                    ) : null}
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={!onPreviewTitle || isArchived}
                      onClick={() => onPreviewTitle?.(title)}
                    >
                      Preview
                    </button>
                    {isArchived ? (
                      <button
                        className="button-secondary"
                        type="button"
                        disabled={!onRestoreTitle || busyAction !== null}
                        onClick={() => void handleRestoreTitle(title)}
                      >
                        {busyAction === `restore-title:${title.title_code}` ? "Restoring..." : "Restore"}
                      </button>
                    ) : (
                      <button
                        className="button-secondary danger"
                        type="button"
                        disabled={!onArchiveTitle || busyAction !== null}
                        onClick={() => void handleArchiveTitle(title)}
                      >
                        {busyAction === `archive-title:${title.title_code}` ? "Archiving..." : "Archive"}
                      </button>
                    )}
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
