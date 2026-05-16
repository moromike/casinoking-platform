"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";
import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import {
  createPublicationDraft,
  createPublicationDraftByCode,
  draftToPayload,
  getPublicationWarnings,
  type PublicationDraft,
  type PublicationPayload,
} from "./site-lobby-draft";
import { SiteLobbyPreview, type GameLibraryResponse } from "./site-lobby-preview";
import { SiteLobbySummary } from "./site-lobby-summary";
import { SiteLobbyTitleRow } from "./site-lobby-title-row";

const SITE_CODE = "casinoking";

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
  onUpdatePublication: (title: CatalogTitle, payload: PublicationPayload) => Promise<void>;
  onPreviewTitle?: (title: CatalogTitle) => void;
};

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
            : "Lobby publication is not available.",
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
          error instanceof ApiRequestError ? error.message : "Player lobby preview is not available.",
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
  const siteLobbyTitles = titles.filter((title) => title.is_archived !== true);
  const variants = siteLobbyTitles.filter((title) => !title.is_master);
  const visibleVariants = variants.filter(
    (title) => title.publication.lobby_visibility === "visible",
  );
  const demoEnabled = visibleVariants.filter((title) => title.publication.demo_enabled);
  const realEnabled = visibleVariants.filter((title) => title.publication.real_enabled);
  const libraryTitles = library?.titles ?? [];

  const visibleLobbyTitles = useMemo(
    () =>
      variants
        .filter((title) => title.publication.lobby_visibility === "visible")
        .sort((left, right) => {
          const positionDiff = left.publication.position - right.publication.position;
          if (positionDiff !== 0) {
            return positionDiff;
          }
          return left.display_name.localeCompare(right.display_name, undefined, {
            sensitivity: "base",
          });
        }),
    [variants],
  );

  const availableCatalogTitles = useMemo(
    () =>
      [...siteLobbyTitles].sort((left, right) => {
        if (left.is_master !== right.is_master) {
          return left.is_master ? -1 : 1;
        }
        return left.display_name.localeCompare(right.display_name, undefined, {
          sensitivity: "base",
        });
      }).filter((title) => title.is_master || title.publication.lobby_visibility !== "visible"),
    [siteLobbyTitles],
  );

  const isSaving = busyAction === "update-title-publication";
  const isBusy = busyAction !== null;

  function updateDraft(titleCode: string, patch: Partial<PublicationDraft>) {
    setDrafts((current) => ({
      ...current,
      [titleCode]: {
        ...(current[titleCode] ?? createPublicationDraftByCode(siteLobbyTitles, titleCode)),
        ...patch,
      },
    }));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>, title: CatalogTitle) {
    event.preventDefault();
    if (title.is_master || title.is_archived === true) {
      return;
    }
    const draft = drafts[title.title_code];
    if (!draft) {
      return;
    }
    await onUpdatePublication(title, draftToPayload(draft));
  }

  function renderTitleRow(title: CatalogTitle) {
    const draft = drafts[title.title_code] ?? createPublicationDraft(title);
    const warnings = getPublicationWarnings(title, draft);

    return (
      <SiteLobbyTitleRow
        key={title.title_code}
        title={title}
        draft={draft}
        warnings={warnings}
        isBusy={isBusy}
        isSaving={isSaving}
        onDraftChange={updateDraft}
        onSave={handleSave}
        onPreviewTitle={onPreviewTitle}
      />
    );
  }

  return (
    <article className="admin-card site-lobby-panel">
      <SiteLobbySummary
        catalogStatus={catalogStatus}
        siteDisplayName={catalog?.site.display_name ?? "CasinoKing"}
        siteStatus={catalog?.site.status ?? null}
        visibleCount={visibleVariants.length}
        demoEnabledCount={demoEnabled.length}
        realEnabledCount={realEnabled.length}
        variantsCount={variants.length}
      />

      {catalogMessage ? <p className="site-lobby-status error">{catalogMessage}</p> : null}

      <div className="site-lobby-workspace">
        <section className="site-lobby-zone site-lobby-management-zone" aria-labelledby="site-lobby-management-title">
          <div className="site-lobby-zone-heading">
            <div>
              <h4 id="site-lobby-management-title">Editorial management</h4>
              <p>Visible lobby and available catalog stay separate</p>
            </div>
          <span className="site-lobby-count">{siteLobbyTitles.length} titles</span>
          </div>

          {catalogStatus === "loading" && !catalog ? (
            <div className="site-lobby-empty">Loading title catalog...</div>
          ) : null}

          {catalogStatus === "error" && !catalog ? (
            <div className="site-lobby-empty error">Title catalog is not available.</div>
          ) : null}

          {catalog && siteLobbyTitles.length === 0 ? (
            <div className="site-lobby-empty">No titles assigned to this site.</div>
          ) : null}

          {catalog && siteLobbyTitles.length > 0 ? (
            <div className="site-lobby-title-list">
              <section className="site-lobby-title-group" aria-labelledby="site-lobby-visible-title">
                <div className="site-lobby-title-group-heading">
                  <div>
                    <h5 id="site-lobby-visible-title">Visible lobby</h5>
                    <p>Titles currently entering the player library.</p>
                  </div>
                  <span>{visibleLobbyTitles.length} visible</span>
                </div>
                {visibleLobbyTitles.length > 0 ? (
                  visibleLobbyTitles.map(renderTitleRow)
                ) : (
                  <div className="site-lobby-empty">No visible titles in the player lobby.</div>
                )}
              </section>

              <section className="site-lobby-title-group" aria-labelledby="site-lobby-catalog-title">
                <div className="site-lobby-title-group-heading">
                  <div>
                    <h5 id="site-lobby-catalog-title">Available catalog</h5>
                    <p>Hidden variants and reference masters.</p>
                  </div>
                  <span>{availableCatalogTitles.length} in catalog</span>
                </div>
                {availableCatalogTitles.length > 0 ? (
                  availableCatalogTitles.map(renderTitleRow)
                ) : (
                  <div className="site-lobby-empty">No other titles available.</div>
                )}
              </section>
            </div>
          ) : null}
        </section>

        <SiteLobbyPreview
          libraryStatus={libraryStatus}
          libraryMessage={libraryMessage}
          libraryTitles={libraryTitles}
          hasLibrary={library !== null}
        />
      </div>
    </article>
  );
}
