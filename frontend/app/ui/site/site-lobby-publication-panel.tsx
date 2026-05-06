"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";
import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

const SITE_CODE = "casinoking";

type SiteTitlesResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type GameLibraryTitle = {
  title_code: string;
  engine_code: string;
  engine_display_name: string;
  display_name: string;
  catalog_display_name: string;
  description: string | null;
  demo_enabled: boolean;
  real_enabled: boolean;
  featured: boolean;
  position: number;
};

type GameLibraryResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: GameLibraryTitle[];
};

type PublicationPayload = {
  lobby_visibility: "hidden" | "visible";
  demo_enabled: boolean;
  real_enabled: boolean;
  lobby_display_name?: string | null;
  lobby_description?: string | null;
  featured?: boolean;
  position?: number;
};

type PublicationDraft = {
  lobby_visibility: "hidden" | "visible";
  demo_enabled: boolean;
  real_enabled: boolean;
  lobby_display_name: string;
  lobby_description: string;
  featured: boolean;
  position: number;
};

type SiteLobbyPublicationPanelProps = {
  refreshKey?: number;
  busyAction?: string | null;
  onUpdatePublication: (title: CatalogTitle, payload: PublicationPayload) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
};

type LaunchHintRecord = Record<string, unknown>;

export function SiteLobbyPublicationPanel({
  refreshKey = 0,
  busyAction = null,
  onUpdatePublication,
  onPreviewTitle,
}: SiteLobbyPublicationPanelProps) {
  const [catalog, setCatalog] = useState<SiteTitlesResponse | null>(null);
  const [catalogStatus, setCatalogStatus] = useState<"idle" | "loading" | "error">("idle");
  const [catalogMessage, setCatalogMessage] = useState<string | null>(null);
  const [library, setLibrary] = useState<GameLibraryResponse | null>(null);
  const [libraryStatus, setLibraryStatus] = useState<"idle" | "loading" | "error">("idle");
  const [libraryMessage, setLibraryMessage] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, PublicationDraft>>({});

  useEffect(() => {
    let isMounted = true;
    setCatalogStatus("loading");
    setCatalogMessage(null);

    apiRequest<SiteTitlesResponse>(`/catalog/sites/${SITE_CODE}/titles`)
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setCatalog(data);
        setCatalogStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setCatalogStatus("error");
        setCatalogMessage(
          error instanceof ApiRequestError
            ? error.message
            : "Lobby publication is unavailable.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  useEffect(() => {
    let isMounted = true;
    setLibraryStatus("loading");
    setLibraryMessage(null);

    apiRequest<GameLibraryResponse>("/games/library")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setLibrary(data);
        setLibraryStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setLibraryStatus("error");
        setLibraryMessage(
          error instanceof ApiRequestError ? error.message : "Player lobby preview is unavailable.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  useEffect(() => {
    if (!catalog) {
      return;
    }
    setDrafts(
      Object.fromEntries(
        catalog.titles.map((title) => [title.title_code, createPublicationDraft(title)]),
      ),
    );
  }, [catalog]);

  const titles = catalog?.titles ?? [];
  const variants = titles.filter((title) => !title.is_master);
  const visibleVariants = variants.filter(
    (title) => title.publication.lobby_visibility === "visible",
  );
  const demoEnabled = visibleVariants.filter((title) => title.publication.demo_enabled);
  const realEnabled = visibleVariants.filter((title) => title.publication.real_enabled);
  const libraryTitles = library?.titles ?? [];

  const sortedTitles = useMemo(
    () =>
      [...titles].sort((left, right) => {
        if (left.is_master !== right.is_master) {
          return left.is_master ? -1 : 1;
        }
        return left.display_name.localeCompare(right.display_name, undefined, {
          sensitivity: "base",
        });
      }),
    [titles],
  );

  const isSaving = busyAction === "update-title-publication";
  const isBusy = busyAction !== null;

  function updateDraft(titleCode: string, patch: Partial<PublicationDraft>) {
    setDrafts((current) => ({
      ...current,
      [titleCode]: {
        ...(current[titleCode] ?? createPublicationDraftByCode(titles, titleCode)),
        ...patch,
      },
    }));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>, title: CatalogTitle) {
    event.preventDefault();
    if (title.is_master) {
      return;
    }
    const draft = drafts[title.title_code];
    if (!draft) {
      return;
    }
    await onUpdatePublication(title, draftToPayload(draft));
  }

  return (
    <article className="admin-card site-lobby-panel">
      <header className="site-lobby-header">
        <div className="site-lobby-heading">
          <p className="eyebrow">Site / Lobby</p>
          <h3>Lobby publication</h3>
          <p>Manage the titles that appear on the CasinoKing player site.</p>
        </div>
        <div className="site-lobby-site-status" aria-label="Current site">
          <span>Site</span>
          <strong>{catalog?.site.display_name ?? "CasinoKing"}</strong>
          <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
            {catalogStatus === "loading" ? "Loading" : catalog?.site.status ?? "n/a"}
          </span>
        </div>
      </header>

      {catalogMessage ? <p className="site-lobby-status error">{catalogMessage}</p> : null}

      <dl className="site-lobby-kpis">
        <div>
          <dt>Visible settings</dt>
          <dd>{visibleVariants.length}</dd>
        </div>
        <div>
          <dt>Demo enabled</dt>
          <dd>{demoEnabled.length}</dd>
        </div>
        <div>
          <dt>Real enabled</dt>
          <dd>{realEnabled.length}</dd>
        </div>
        <div>
          <dt>Variants</dt>
          <dd>{variants.length}</dd>
        </div>
      </dl>

      <div className="site-lobby-workspace">
        <section className="site-lobby-zone site-lobby-management-zone" aria-labelledby="site-lobby-management-title">
          <div className="site-lobby-zone-heading">
            <div>
              <h4 id="site-lobby-management-title">Available titles</h4>
              <p>Publication management</p>
            </div>
            <span className="site-lobby-count">{titles.length} total</span>
          </div>

          {catalogStatus === "loading" && !catalog ? (
            <div className="site-lobby-empty">Loading title catalog...</div>
          ) : null}

          {catalogStatus === "error" && !catalog ? (
            <div className="site-lobby-empty error">Title catalog could not be loaded.</div>
          ) : null}

          {catalog && titles.length === 0 ? (
            <div className="site-lobby-empty">No titles are assigned to this site.</div>
          ) : null}

          {catalog && titles.length > 0 ? (
            <div className="site-lobby-title-list">
              {sortedTitles.map((title) => {
                const draft = drafts[title.title_code] ?? createPublicationDraft(title);
                const warnings = getPublicationWarnings(title, draft);

                if (title.is_master) {
                  return (
                    <div className="site-lobby-title-row is-master" key={title.title_code}>
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
                    key={title.title_code}
                    onSubmit={(event) => void handleSave(event, title)}
                  >
                    <TitleIdentity title={title} label="Variant" />

                    <div className="site-lobby-control-grid">
                      <label className="site-lobby-field">
                        <span>Visibility</span>
                        <select
                          value={draft.lobby_visibility}
                          disabled={isBusy}
                          onChange={(event) =>
                            updateDraft(title.title_code, {
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
                            updateDraft(title.title_code, {
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
                            updateDraft(title.title_code, { demo_enabled: event.target.checked })
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
                            updateDraft(title.title_code, { real_enabled: event.target.checked })
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
                            updateDraft(title.title_code, { featured: event.target.checked })
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
                            updateDraft(title.title_code, {
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
                            updateDraft(title.title_code, {
                              lobby_description: event.target.value,
                            })
                          }
                        />
                      </label>
                    </div>

                    <div className="site-lobby-row-footer">
                      <WarningList warnings={warnings} />
                      <button
                        className="button-secondary"
                        type="submit"
                        disabled={isBusy || !dirty}
                      >
                        {isSaving ? "Saving..." : "Save"}
                      </button>
                    </div>
                  </form>
                );
              })}
            </div>
          ) : null}
        </section>

        <aside className="site-lobby-zone site-lobby-preview-zone" aria-labelledby="site-lobby-preview-title">
          <div className="site-lobby-zone-heading">
            <div>
              <h4 id="site-lobby-preview-title">Lobby preview / order</h4>
              <p>Player library source</p>
            </div>
            <span className="site-lobby-source">GET /games/library</span>
          </div>

          {libraryMessage ? <p className="site-lobby-status error">{libraryMessage}</p> : null}

          {libraryStatus === "loading" && !library ? (
            <div className="site-lobby-empty">Loading player lobby preview...</div>
          ) : null}

          {libraryStatus === "error" && !library ? (
            <div className="site-lobby-empty error">Player lobby preview could not be loaded.</div>
          ) : null}

          {library && libraryTitles.length === 0 ? (
            <div className="site-lobby-empty">No variants are returned by the player library.</div>
          ) : null}

          {library && libraryTitles.length > 0 ? (
            <ol className="site-lobby-preview-list">
              {libraryTitles.map((title, index) => (
                <li className="site-lobby-preview-item" key={title.title_code}>
                  <span className="site-lobby-preview-rank">{index + 1}</span>
                  <div className="site-lobby-preview-copy">
                    <div className="site-lobby-preview-title">
                      <strong>{title.display_name}</strong>
                      {title.featured ? <span className="status-inline success">Featured</span> : null}
                    </div>
                    <span className="mono">{title.title_code}</span>
                    <p>{title.description ?? "No lobby description."}</p>
                    <div className="site-lobby-preview-meta">
                      <span>{title.engine_display_name}</span>
                      <span>Position {title.position}</span>
                      <span>{formatModes(title)}</span>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          ) : null}
        </aside>
      </div>
    </article>
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

function createPublicationDraft(title: CatalogTitle): PublicationDraft {
  return {
    lobby_visibility: title.publication.lobby_visibility,
    demo_enabled: title.publication.demo_enabled,
    real_enabled: title.publication.real_enabled,
    lobby_display_name: title.publication.lobby_display_name ?? "",
    lobby_description: title.publication.lobby_description ?? "",
    featured: title.publication.featured,
    position: title.publication.position,
  };
}

function createPublicationDraftByCode(titles: CatalogTitle[], titleCode: string): PublicationDraft {
  const title = titles.find((candidate) => candidate.title_code === titleCode);
  if (title) {
    return createPublicationDraft(title);
  }

  return {
    lobby_visibility: "hidden",
    demo_enabled: false,
    real_enabled: false,
    lobby_display_name: "",
    lobby_description: "",
    featured: false,
    position: 0,
  };
}

function draftToPayload(draft: PublicationDraft): PublicationPayload {
  return {
    lobby_visibility: draft.lobby_visibility,
    demo_enabled: draft.demo_enabled,
    real_enabled: draft.real_enabled,
    lobby_display_name: normalizeOptionalText(draft.lobby_display_name),
    lobby_description: normalizeOptionalText(draft.lobby_description),
    featured: draft.featured,
    position: draft.position,
  };
}

function isPublicationDirty(title: CatalogTitle, draft: PublicationDraft): boolean {
  const current = createPublicationDraft(title);
  return (
    current.lobby_visibility !== draft.lobby_visibility ||
    current.demo_enabled !== draft.demo_enabled ||
    current.real_enabled !== draft.real_enabled ||
    current.lobby_display_name !== draft.lobby_display_name ||
    current.lobby_description !== draft.lobby_description ||
    current.featured !== draft.featured ||
    current.position !== draft.position
  );
}

function normalizeOptionalText(value: string): string | null {
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function normalizePositionInput(value: string): number {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return Math.max(0, parsed);
}

function getPublicationWarnings(title: CatalogTitle, draft: PublicationDraft): string[] {
  const warnings: string[] = [];

  if (title.is_master) {
    warnings.push("Master titles are preview-only and cannot be published as lobby items.");
  }

  if (
    draft.lobby_visibility === "visible" &&
    !draft.demo_enabled &&
    !draft.real_enabled &&
    !title.is_master
  ) {
    warnings.push("Visible titles need demo or real enabled to appear in the player library.");
  }

  if (draft.lobby_visibility === "visible" && hasInactiveCatalogStatus(title)) {
    warnings.push("Launch may be rejected until the title, site title, and engine are active.");
  }

  warnings.push(...getLaunchConfigWarnings(title, draft));

  return warnings;
}

function hasInactiveCatalogStatus(title: CatalogTitle): boolean {
  return (
    title.status !== "active" ||
    title.site_title_status !== "active" ||
    title.engine.status !== "active"
  );
}

function getLaunchConfigWarnings(title: CatalogTitle, draft: PublicationDraft): string[] {
  if (draft.lobby_visibility !== "visible") {
    return [];
  }

  const record = title as unknown as LaunchHintRecord;
  const warnings: string[] = [];

  if (hasExplicitFalse(record, ["has_live_config", "has_published_config", "has_launch_config"])) {
    warnings.push("No live launch config is reported for this title.");
  }

  if (hasExplicitFalse(record, ["launch_enabled"])) {
    warnings.push("Launch is reported as disabled for this title.");
  }

  if (draft.demo_enabled && hasExplicitFalse(record, ["demo_launch_enabled", "demo_playable"])) {
    warnings.push("Demo launch is reported as unavailable for this title.");
  }

  if (draft.real_enabled && hasExplicitFalse(record, ["real_launch_enabled", "real_playable"])) {
    warnings.push("Real launch is reported as unavailable for this title.");
  }

  const liveStatus = record.live_config_status ?? record.launch_config_status;
  if (
    typeof liveStatus === "string" &&
    !["active", "live", "published", "ready"].includes(liveStatus.toLowerCase())
  ) {
    warnings.push("Live config status is not reported as ready.");
  }

  return warnings;
}

function hasExplicitFalse(record: LaunchHintRecord, keys: string[]): boolean {
  return keys.some(
    (key) => Object.prototype.hasOwnProperty.call(record, key) && record[key] === false,
  );
}

function formatModes(title: Pick<GameLibraryTitle, "demo_enabled" | "real_enabled">): string {
  if (title.demo_enabled && title.real_enabled) {
    return "Demo + real";
  }
  if (title.demo_enabled) {
    return "Demo";
  }
  if (title.real_enabled) {
    return "Real";
  }
  return "No modes";
}
