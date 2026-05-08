import type { FormEvent } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import {
  isPublicationDirty,
  normalizePositionInput,
  type PublicationDraft,
} from "./site-lobby-draft";

type SiteLobbyTitleRowProps = {
  title: CatalogTitle;
  draft: PublicationDraft;
  warnings: string[];
  isBusy: boolean;
  isSaving: boolean;
  onDraftChange: (titleCode: string, patch: Partial<PublicationDraft>) => void;
  onSave: (event: FormEvent<HTMLFormElement>, title: CatalogTitle) => void;
  onPreviewTitle?: (title: CatalogTitle) => void;
};

export function SiteLobbyTitleRow({
  title,
  draft,
  warnings,
  isBusy,
  isSaving,
  onDraftChange,
  onSave,
  onPreviewTitle,
}: SiteLobbyTitleRowProps) {
  if (title.is_master) {
    return (
      <div className="site-lobby-title-row is-master">
        <TitleIdentity title={title} label="Master" />
        <div className="site-lobby-master-panel">
          <button
            className="button-secondary"
            type="button"
            disabled={!onPreviewTitle}
            onClick={() => onPreviewTitle?.(title)}
          >
            Anteprima
          </button>
        </div>
        <WarningList warnings={warnings} />
      </div>
    );
  }

  const dirty = isPublicationDirty(title, draft);

  return (
    <form
      className={`site-lobby-title-row ${dirty ? "is-dirty" : ""}`}
      onSubmit={(event) => void onSave(event, title)}
    >
      <TitleIdentity title={title} draft={draft} label="Variante" />

      <div className="site-lobby-publication-controls">
        <div className="site-lobby-control-grid">
          <label className="site-lobby-field">
            <span>In lobby</span>
            <select
              value={draft.lobby_visibility}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, {
                  lobby_visibility: event.target.value as "hidden" | "visible",
                })
              }
            >
              <option value="hidden">Nascosto</option>
              <option value="visible">Visibile</option>
            </select>
          </label>

          <label className="site-lobby-field site-lobby-position-field">
            <span>Ordine</span>
            <input
              type="number"
              min={0}
              step={1}
              value={draft.position}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, {
                  position: normalizePositionInput(event.target.value),
                })
              }
            />
          </label>

          <label className="site-lobby-check">
            <input
              type="checkbox"
              checked={draft.demo_enabled}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, { demo_enabled: event.target.checked })
              }
            />
            <span>Demo</span>
          </label>

          <label className="site-lobby-check">
            <input
              type="checkbox"
              checked={draft.real_enabled}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, { real_enabled: event.target.checked })
              }
            />
            <span>Real</span>
          </label>

          <label className="site-lobby-check">
            <input
              type="checkbox"
              checked={draft.featured}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, { featured: event.target.checked })
              }
            />
            <span>In evidenza</span>
          </label>
        </div>

        <div className="site-lobby-editor-grid">
          <label className="site-lobby-field">
            <span>Titolo in lobby</span>
            <input
              type="text"
              maxLength={160}
              value={draft.lobby_display_name}
              placeholder={title.display_name}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, {
                  lobby_display_name: event.target.value,
                })
              }
            />
          </label>

          <label className="site-lobby-field">
            <span>Descrizione lobby</span>
            <textarea
              rows={2}
              maxLength={500}
              value={draft.lobby_description}
              placeholder="Descrizione opzionale per la card player"
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, {
                  lobby_description: event.target.value,
                })
              }
            />
          </label>
        </div>
      </div>

      <div className="site-lobby-row-footer">
        <span className={`site-lobby-save-state ${dirty ? "is-dirty" : "is-saved"}`}>
          {dirty ? "Modifiche non salvate" : "Allineato alla pubblicazione"}
        </span>
        <button className="button-secondary" type="submit" disabled={isBusy || !dirty}>
          {isSaving && dirty ? "Salvataggio..." : dirty ? "Salva modifiche" : "Salvato"}
        </button>
      </div>

      <WarningList warnings={warnings} />
    </form>
  );
}

function WarningList({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <ul className="site-lobby-warnings">
      {warnings.map((warning) => (
        <li key={warning}>{warning}</li>
      ))}
    </ul>
  );
}

function TitleIdentity({
  title,
  draft,
  label,
}: {
  title: CatalogTitle;
  draft?: PublicationDraft;
  label: string;
}) {
  const lobbyTitle = getLobbyTitle(title, draft);
  const visibilityLabel = title.is_master
    ? "Solo preview"
    : draft?.lobby_visibility === "visible"
      ? "Visibile"
      : "Nascosto";

  return (
    <div className="site-lobby-title-main">
      <div className="site-lobby-title-copy">
        <div className="site-lobby-title-name">
          <strong>{lobbyTitle}</strong>
          <span className={`status-inline ${title.is_master ? "warning" : "success"}`}>{label}</span>
          <span
            className={`status-inline ${
              !title.is_master && draft?.lobby_visibility === "visible" ? "success" : "warning"
            }`}
          >
            {visibilityLabel}
          </span>
        </div>
        <span className="site-lobby-catalog-name">{getCatalogLabel(title, draft)}</span>
      </div>
      <div className="site-lobby-title-meta">
        <span>title_code {title.title_code}</span>
        <span>engine {title.engine.display_name}</span>
        <span>title {title.status}</span>
        <span>site/title {title.site_title_status}</span>
      </div>
    </div>
  );
}

function getLobbyTitle(title: CatalogTitle, draft?: PublicationDraft): string {
  const draftName = draft?.lobby_display_name.trim();
  const publishedName = title.publication.lobby_display_name?.trim();
  return draftName || publishedName || title.display_name;
}

function getCatalogLabel(title: CatalogTitle, draft?: PublicationDraft): string {
  const lobbyTitle = getLobbyTitle(title, draft);
  if (lobbyTitle !== title.display_name) {
    return `Catalogo: ${title.display_name}`;
  }
  return "Catalogo allineato al titolo lobby";
}
