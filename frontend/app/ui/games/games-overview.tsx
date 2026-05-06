"use client";

import { FormEvent, useState } from "react";

import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";
import { GameVariantList } from "./game-variant-list";

type SiteCatalog = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type GamesOverviewProps = {
  catalog: SiteCatalog;
  selectedTitleCode?: string;
  busyAction?: string | null;
  onOpenTitle?: (title: CatalogTitle) => void;
  onDuplicateTitle?: (
    sourceTitle: CatalogTitle,
    payload: { title_code: string; display_name: string },
  ) => Promise<void>;
  onUpdateTitleDisplayName?: (
    title: CatalogTitle,
    payload: { display_name: string },
  ) => Promise<void>;
};

export function GamesOverview({
  catalog,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
}: GamesOverviewProps) {
  const [duplicateTitleCode, setDuplicateTitleCode] = useState("");
  const [duplicateTitleName, setDuplicateTitleName] = useState("");

  const minesTitles = catalog.titles.filter((title) => title.engine_code === "mines");
  const minesMaster = minesTitles.find((title) => title.is_master) ?? null;
  const minesVariants = minesTitles.filter((title) => !title.is_master);
  const otherTitles = catalog.titles.filter((title) => title.engine_code !== "mines");
  const isDuplicateBusy = busyAction === "duplicate-title";

  async function handleDuplicateMinesTitle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onDuplicateTitle || !minesMaster) {
      return;
    }

    await onDuplicateTitle(minesMaster, {
      title_code: duplicateTitleCode.trim().toLowerCase(),
      display_name: duplicateTitleName.trim(),
    });
    setDuplicateTitleCode("");
    setDuplicateTitleName("");
  }

  return (
    <div className="games-management-panel">
      {minesMaster ? (
        <section className="games-management-section">
          <div className="games-management-toolbar">
            <div>
              <h4>Mines</h4>
              <p>
                {minesVariants.length} varianti configurabili. Master bloccato.
              </p>
            </div>
            {onDuplicateTitle ? (
              <form className="games-create-inline" onSubmit={handleDuplicateMinesTitle}>
                <input
                  aria-label="Title code nuova variante"
                  value={duplicateTitleCode}
                  onChange={(event) => setDuplicateTitleCode(event.target.value)}
                  placeholder="mines_lagoon"
                />
                <input
                  aria-label="Nome nuova variante"
                  value={duplicateTitleName}
                  onChange={(event) => setDuplicateTitleName(event.target.value)}
                  placeholder="Mines Lagoon"
                />
                <button
                  className="button"
                  type="submit"
                  disabled={busyAction !== null || !duplicateTitleCode.trim() || !duplicateTitleName.trim()}
                >
                  {isDuplicateBusy ? "Creo..." : "Crea variante"}
                </button>
              </form>
            ) : null}
          </div>

          <GameVariantList
            master={minesMaster}
            variants={minesVariants}
            selectedTitleCode={selectedTitleCode}
            busyAction={busyAction}
            onOpenTitle={onOpenTitle}
            onUpdateTitleDisplayName={onUpdateTitleDisplayName}
          />
        </section>
      ) : null}

      {otherTitles.map((title) => (
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
            <span className="list-muted">Engine</span>
            <span className="list-strong">{title.engine.display_name}</span>
          </div>
          <div className="admin-metric-row">
            <span className="list-muted">Engine code</span>
            <span className="mono">{title.engine_code}</span>
          </div>
          <div className="admin-metric-row">
            <span className="list-muted">Title status</span>
            <span>{title.status}</span>
          </div>
          {onOpenTitle ? (
            <div className="actions">
              <button
                className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                type="button"
                onClick={() => onOpenTitle(title)}
              >
                {selectedTitleCode === title.title_code ? "Configurazione aperta" : "Configura"}
              </button>
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
