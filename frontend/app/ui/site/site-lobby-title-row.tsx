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
          <span className="status-inline warning">Preview only</span>
          <button
            className="button-secondary"
            type="button"
            disabled={!onPreviewTitle}
            onClick={() => onPreviewTitle?.(title)}
          >
            Preview
          </button>
        </div>
        <WarningList warnings={warnings} />
      </div>
    );
  }

  const dirty = isPublicationDirty(title, draft);

  return (
    <form
      className="site-lobby-title-row"
      onSubmit={(event) => void onSave(event, title)}
    >
      <TitleIdentity title={title} label="Variant" />

      <div className="site-lobby-publication-controls">
        <div className="site-lobby-control-grid">
          <label className="site-lobby-field">
            <span>Visibility</span>
            <select
              value={draft.lobby_visibility}
              disabled={isBusy}
              onChange={(event) =>
                onDraftChange(title.title_code, {
                  lobby_visibility: event.target.value as "hidden" | "visible",
                })
              }
            >
              <option value="hidden">Hidden</option>
              <option value="visible">Visible</option>
            </select>
          </label>

          <label className="site-lobby-field site-lobby-position-field">
            <span>Position</span>
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
            <span>Featured</span>
          </label>
        </div>

        <div className="site-lobby-editor-grid">
          <label className="site-lobby-field">
            <span>Lobby display name</span>
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
            <span>Description</span>
            <textarea
              rows={2}
              maxLength={500}
              value={draft.lobby_description}
              placeholder="Optional lobby description"
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
        <button className="button-secondary" type="submit" disabled={isBusy || !dirty}>
          {isSaving ? "Saving..." : "Save"}
        </button>
      </div>

      <WarningList warnings={warnings} />
    </form>
  );
}

function TitleIdentity({ title, label }: { title: CatalogTitle; label: string }) {
  return (
    <div className="site-lobby-title-main">
      <div className="site-lobby-title-copy">
        <div className="site-lobby-title-name">
          <strong>{title.display_name}</strong>
          <span className={`status-inline ${title.is_master ? "warning" : "success"}`}>{label}</span>
        </div>
        <span className="mono">{title.title_code}</span>
      </div>
      <div className="site-lobby-title-meta">
        <span>{title.engine.display_name}</span>
        <span>{title.status}</span>
        <span>{title.site_title_status}</span>
      </div>
    </div>
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

