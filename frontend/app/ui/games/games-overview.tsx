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

export function GamesOverview({
  catalog,
  selectedTitleCode,
  busyAction = null,
  onOpenTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onUpdatePublication,
}: GamesOverviewProps) {
  const [duplicateTitleCode, setDuplicateTitleCode] = useState("");
  const [duplicateTitleName, setDuplicateTitleName] = useState("");

  const minesTitles = catalog.titles.filter((title) => title.engine_code === "mines");
  const minesMaster = minesTitles.find((title) => title.is_master) ?? null;
  const minesVariants = minesTitles.filter((title) => !title.is_master);
  const visibleMinesVariants = minesVariants.filter(
    (title) => title.publication.lobby_visibility === "visible",
  ).length;
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
    <div className="stack">
      {minesMaster ? (
        <section className="admin-surface admin-surface-section">
          <div className="admin-card-heading">
            <div>
              <h4>Mines</h4>
              <p>Master bloccato, varianti modificabili e stato sito in sintesi.</p>
            </div>
            <span className="status-inline info">{catalog.site.display_name}</span>
          </div>

          <div className="field-grid">
            <article className="admin-list-card">
              <div className="admin-card-heading">
                <div>
                  <h4>{minesMaster.display_name}</h4>
                  <p className="mono">{minesMaster.title_code}</p>
                </div>
                <span className="status-inline warning">master bloccato</span>
              </div>
              <div className="admin-metric-row">
                <span className="list-muted">Engine</span>
                <span className="list-strong">{minesMaster.engine.display_name}</span>
              </div>
              <div className="admin-metric-row">
                <span className="list-muted">Varianti</span>
                <span className="list-strong">
                  {minesVariants.length} totali / {visibleMinesVariants} visibili
                </span>
              </div>
              <div className="actions">
                <button
                  className={selectedTitleCode === minesMaster.title_code ? "button" : "button-secondary"}
                  type="button"
                  onClick={() => onOpenTitle?.(minesMaster)}
                >
                  {selectedTitleCode === minesMaster.title_code ? "Master aperto" : "Apri master"}
                </button>
                <a
                  className="button-secondary"
                  href={`/mines?title_code=${encodeURIComponent(minesMaster.title_code)}&mode=demo&preview=1`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Preview master
                </a>
              </div>
            </article>

            {onDuplicateTitle ? (
              <form className="admin-list-card" onSubmit={handleDuplicateMinesTitle}>
                <div className="admin-card-heading">
                  <div>
                    <h4>Nuova variante</h4>
                    <p>Duplica il master e poi personalizza la copia.</p>
                  </div>
                  <span className="status-inline success">azione principale</span>
                </div>
                <div className="field-grid">
                  <div className="field">
                    <label htmlFor="duplicate-title-code">Title code</label>
                    <input
                      id="duplicate-title-code"
                      value={duplicateTitleCode}
                      onChange={(event) => setDuplicateTitleCode(event.target.value)}
                      placeholder="mines_lagoon"
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="duplicate-title-name">Nome variante</label>
                    <input
                      id="duplicate-title-name"
                      value={duplicateTitleName}
                      onChange={(event) => setDuplicateTitleName(event.target.value)}
                      placeholder="Mines Lagoon"
                    />
                  </div>
                </div>
                <div className="actions">
                  <button
                    className="button"
                    type="submit"
                    disabled={busyAction !== null || !duplicateTitleCode.trim() || !duplicateTitleName.trim()}
                  >
                    {isDuplicateBusy ? "Creo variante..." : "Crea variante"}
                  </button>
                </div>
              </form>
            ) : null}
          </div>
        </section>
      ) : null}

      {minesMaster ? (
        <section className="admin-surface admin-surface-section">
          <div className="admin-card-heading">
            <div>
              <h4>Varianti Mines</h4>
              <p>Apri una variante per configurarla o provarla in demo.</p>
            </div>
            <span className="status-inline info">{minesVariants.length}</span>
          </div>
          <GameVariantList
            variants={minesVariants}
            selectedTitleCode={selectedTitleCode}
            busyAction={busyAction}
            onOpenTitle={onOpenTitle}
            onUpdateTitleDisplayName={onUpdateTitleDisplayName}
            onUpdatePublication={onUpdatePublication}
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
