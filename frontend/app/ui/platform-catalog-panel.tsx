"use client";

import { FormEvent, useEffect, useState } from "react";

import { ApiRequestError, apiRequest } from "@/app/lib/api";

export type CatalogTitle = {
  title_code: string;
  engine_code: string;
  display_name: string;
  status: string;
  is_master: boolean;
  source_title_code: string | null;
  site_title_status: string;
  publication: {
    site_title_status: string;
    lobby_visibility: "hidden" | "visible";
    demo_enabled: boolean;
    real_enabled: boolean;
    lobby_display_name: string | null;
    lobby_description: string | null;
    featured: boolean;
    position: number;
  };
  engine: {
    engine_code: string;
    display_name: string;
    status: string;
  };
};

type SiteTitlesResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type PlatformCatalogPanelProps = {
  selectedTitleCode?: string;
  refreshKey?: number;
  busyAction?: string | null;
  onConfigureTitle?: (title: CatalogTitle) => void;
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

export function PlatformCatalogPanel({
  selectedTitleCode,
  refreshKey = 0,
  busyAction = null,
  onConfigureTitle,
  onDuplicateTitle,
  onUpdateTitleDisplayName,
  onUpdatePublication,
}: PlatformCatalogPanelProps) {
  const [catalog, setCatalog] = useState<SiteTitlesResponse | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [duplicateTitleCode, setDuplicateTitleCode] = useState("");
  const [duplicateTitleName, setDuplicateTitleName] = useState("");
  const [titleNameDrafts, setTitleNameDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    let isMounted = true;
    setStatus("loading");
    setMessage(null);

    apiRequest<SiteTitlesResponse>("/catalog/sites/casinoking/titles")
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setCatalog(data);
        setStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setStatus("error");
        setMessage(
          error instanceof ApiRequestError
            ? error.message
            : "Catalogo giochi non disponibile",
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
    setTitleNameDrafts((current) => {
      const next = { ...current };
      for (const title of catalog.titles) {
        if (next[title.title_code] === undefined) {
          next[title.title_code] = title.display_name;
        }
      }
      return next;
    });
  }, [catalog]);

  const minesTitles = catalog?.titles.filter((title) => title.engine_code === "mines") ?? [];
  const minesMaster = minesTitles.find((title) => title.is_master) ?? null;
  const minesVariants = minesTitles.filter((title) => !title.is_master);
  const isDuplicateBusy = busyAction === "duplicate-title";
  const visibleMinesVariants = minesVariants.filter(
    (title) => title.publication.lobby_visibility === "visible",
  ).length;

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

  async function handleUpdateTitleName(title: CatalogTitle) {
    if (!onUpdateTitleDisplayName) {
      return;
    }
    await onUpdateTitleDisplayName(title, {
      display_name: (titleNameDrafts[title.title_code] ?? title.display_name).trim(),
    });
  }

  return (
    <article className="admin-card">
      <div className="admin-card-heading">
        <div>
          <h3>Catalogo giochi</h3>
          <p>Engine, master e varianti pubblicate sul Site corrente.</p>
        </div>
        <span className={`status-inline ${catalog?.site.status === "active" ? "success" : "warning"}`}>
          {status === "loading" ? "loading" : catalog?.site.status ?? "n/a"}
        </span>
      </div>

      {message ? <p className="status-message error">{message}</p> : null}

      {catalog ? (
        <div className="stack">
          {minesMaster ? (
            <section className="admin-surface admin-surface-section">
              <div className="admin-card-heading">
                <div>
                  <h4>Mines</h4>
                  <p>Master bloccato, varianti modificabili e pubblicazione sul sito.</p>
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
                      onClick={() => onConfigureTitle?.(minesMaster)}
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
                  <p>Apri una variante per configurarla, pubblicarla in demo o provarla.</p>
                </div>
                <span className="status-inline info">{minesVariants.length}</span>
              </div>

              {minesVariants.length > 0 ? (
                <div className="admin-list admin-list-static">
                {minesVariants.map((title) => (
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
                      <span className="list-muted">Source</span>
                      <span className="mono">{title.source_title_code ?? "n/a"}</span>
                    </div>
                    <div className="admin-metric-row">
                      <span className="list-muted">Sito</span>
                      <span>
                        {title.publication.lobby_visibility === "visible"
                          ? "visibile"
                          : "nascosto"}
                        {" / demo "}
                        {title.publication.demo_enabled ? "on" : "off"}
                        {" / real "}
                        {title.publication.real_enabled ? "on" : "off"}
                      </span>
                    </div>
                    {onUpdateTitleDisplayName ? (
                      <div className="field-grid">
                        <div className="field">
                          <label htmlFor={`title-name-${title.title_code}`}>Nome variante</label>
                          <input
                            id={`title-name-${title.title_code}`}
                            value={titleNameDrafts[title.title_code] ?? title.display_name}
                            onChange={(event) =>
                              setTitleNameDrafts((current) => ({
                                ...current,
                                [title.title_code]: event.target.value,
                              }))
                            }
                          />
                        </div>
                      </div>
                    ) : null}
                    <div className="actions">
                      <button
                        className={selectedTitleCode === title.title_code ? "button" : "button-secondary"}
                        type="button"
                        onClick={() => onConfigureTitle?.(title)}
                      >
                        {selectedTitleCode === title.title_code ? "Configurazione aperta" : "Personalizza"}
                      </button>
                      {onUpdateTitleDisplayName ? (
                        <button
                          className="button-secondary"
                          type="button"
                          disabled={
                            busyAction !== null ||
                            !(titleNameDrafts[title.title_code] ?? title.display_name).trim() ||
                            (titleNameDrafts[title.title_code] ?? title.display_name).trim() === title.display_name
                          }
                          onClick={() => void handleUpdateTitleName(title)}
                        >
                          Salva nome
                        </button>
                      ) : null}
                      {onUpdatePublication ? (
                        <>
                          <button
                            className="button-secondary"
                            type="button"
                            disabled={busyAction !== null}
                            onClick={() =>
                              void onUpdatePublication(title, {
                                lobby_visibility: "visible",
                                demo_enabled: true,
                                real_enabled: title.publication.real_enabled,
                                lobby_display_name: title.publication.lobby_display_name,
                                lobby_description: title.publication.lobby_description,
                                featured: title.publication.featured,
                                position: title.publication.position,
                              })
                            }
                          >
                            Pubblica demo
                          </button>
                          <button
                            className="button-secondary"
                            type="button"
                            disabled={busyAction !== null}
                            onClick={() =>
                              void onUpdatePublication(title, {
                                lobby_visibility: "visible",
                                demo_enabled: true,
                                real_enabled: true,
                                lobby_display_name: title.publication.lobby_display_name,
                                lobby_description: title.publication.lobby_description,
                                featured: title.publication.featured,
                                position: title.publication.position,
                              })
                            }
                          >
                            Pubblica demo + real
                          </button>
                          <button
                            className="button-ghost"
                            type="button"
                            disabled={busyAction !== null}
                            onClick={() =>
                              void onUpdatePublication(title, {
                                lobby_visibility: "hidden",
                                demo_enabled: false,
                                real_enabled: false,
                                lobby_display_name: title.publication.lobby_display_name,
                                lobby_description: title.publication.lobby_description,
                                featured: title.publication.featured,
                                position: title.publication.position,
                              })
                            }
                          >
                            Nascondi
                          </button>
                        </>
                      ) : null}
                      <a
                        className="button-secondary"
                        href={`/mines?title_code=${encodeURIComponent(title.title_code)}&mode=demo&preview=1`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Preview demo
                      </a>
                    </div>
                  </article>
                ))}
                </div>
              ) : (
                <p className="empty-state">Nessuna variante creata.</p>
              )}
            </section>
          ) : null}

          {catalog.titles.filter((title) => title.engine_code !== "mines").map((title) => (
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
              {onConfigureTitle ? (
                <div className="actions">
                  <button
                    className={
                      selectedTitleCode === title.title_code
                        ? "button"
                        : "button-secondary"
                    }
                    type="button"
                    onClick={() => onConfigureTitle(title)}
                  >
                    {selectedTitleCode === title.title_code
                      ? "Configurazione aperta"
                      : "Configura"}
                  </button>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}
    </article>
  );
}
