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
            : "La pubblicazione lobby non e' disponibile.",
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
          error instanceof ApiRequestError ? error.message : "L'anteprima lobby player non e' disponibile.",
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
              <h4 id="site-lobby-management-title">Gestione editoriale</h4>
              <p>Lobby visibile e catalogo disponibile restano separati</p>
            </div>
          <span className="site-lobby-count">{siteLobbyTitles.length} titoli</span>
          </div>

          {catalogStatus === "loading" && !catalog ? (
            <div className="site-lobby-empty">Caricamento catalogo titoli...</div>
          ) : null}

          {catalogStatus === "error" && !catalog ? (
            <div className="site-lobby-empty error">Il catalogo titoli non e' disponibile.</div>
          ) : null}

          {catalog && siteLobbyTitles.length === 0 ? (
            <div className="site-lobby-empty">Nessun titolo assegnato a questo sito.</div>
          ) : null}

          {catalog && siteLobbyTitles.length > 0 ? (
            <div className="site-lobby-title-list">
              <section className="site-lobby-title-group" aria-labelledby="site-lobby-visible-title">
                <div className="site-lobby-title-group-heading">
                  <div>
                    <h5 id="site-lobby-visible-title">Lobby visibile</h5>
                    <p>Titoli che oggi entrano nella libreria player.</p>
                  </div>
                  <span>{visibleLobbyTitles.length} visibili</span>
                </div>
                {visibleLobbyTitles.length > 0 ? (
                  visibleLobbyTitles.map(renderTitleRow)
                ) : (
                  <div className="site-lobby-empty">Nessun titolo visibile nella lobby player.</div>
                )}
              </section>

              <section className="site-lobby-title-group" aria-labelledby="site-lobby-catalog-title">
                <div className="site-lobby-title-group-heading">
                  <div>
                    <h5 id="site-lobby-catalog-title">Catalogo disponibile</h5>
                    <p>Varianti nascoste e master di riferimento.</p>
                  </div>
                  <span>{availableCatalogTitles.length} nel catalogo</span>
                </div>
                {availableCatalogTitles.length > 0 ? (
                  availableCatalogTitles.map(renderTitleRow)
                ) : (
                  <div className="site-lobby-empty">Nessun altro titolo disponibile.</div>
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
