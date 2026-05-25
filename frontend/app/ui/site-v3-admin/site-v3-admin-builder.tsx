"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";
import {
  SITE_V3_MODULE_CATEGORIES,
  SITE_V3_MODULE_DESCRIPTORS,
} from "./site-v3-admin-descriptors";
import {
  SITE_V3_DEFAULT_LOCALE,
  SITE_V3_SITE_CODE,
  type SiteV3AdminModule,
  type SiteV3AdminModulePayload,
  type SiteV3AdminPage,
  type SiteV3AssetRef,
  type SiteV3ListStatusFilter,
  type SiteV3ModuleCode,
  type SiteV3ModuleConfig,
  type SiteV3ModuleDescriptor,
  type SiteV3ModuleFieldDescriptor,
  type SiteV3NavItem,
  type SiteV3PageEditorState,
  type SiteV3PageResponse,
  type SiteV3PagesResponse,
  type SiteV3TitleOption,
  type SiteV3ValidationResult,
  type SiteV3Version,
} from "./site-v3-admin-types";
import {
  archiveSiteV3Page,
  getSiteV3Page,
  listSiteV3Pages,
  listSiteV3Versions,
  publishSiteV3Page,
  saveSiteV3Draft,
  validateSiteV3Draft,
} from "./site-v3-admin-api";

type SiteV3AdminBuilderProps = {
  accessToken: string;
};

type LocalMessage = {
  kind: "success" | "error" | "info";
  text: string;
};

type SiteTitlesResponse = {
  titles: SiteV3TitleOption[];
};

const EMPTY_VALIDATION: SiteV3ValidationResult = {
  status: "unknown",
  issues: [],
};

export function SiteV3AdminBuilder({ accessToken }: SiteV3AdminBuilderProps) {
  const [pagesData, setPagesData] = useState<SiteV3PagesResponse | null>(null);
  const [pagesStatus, setPagesStatus] = useState<"idle" | "loading" | "error">("idle");
  const [statusFilter, setStatusFilter] = useState<SiteV3ListStatusFilter>("all");
  const [locale, setLocale] = useState(SITE_V3_DEFAULT_LOCALE);
  const [pageMeta, setPageMeta] = useState<SiteV3AdminPage | null>(null);
  const [editorState, setEditorState] = useState<SiteV3PageEditorState>(
    createEmptyEditorState("home", "Homepage", locale),
  );
  const [lastSavedSnapshot, setLastSavedSnapshot] = useState("");
  const [validation, setValidation] = useState<SiteV3ValidationResult>(EMPTY_VALIDATION);
  const [versions, setVersions] = useState<SiteV3Version[]>([]);
  const [publishedSummary, setPublishedSummary] = useState<SiteV3Version | null>(null);
  const [titleOptions, setTitleOptions] = useState<SiteV3TitleOption[]>([]);
  const [localMessage, setLocalMessage] = useState<LocalMessage | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const currentSnapshot = useMemo(() => serializeEditorState(editorState), [editorState]);
  const isDirty = currentSnapshot !== lastSavedSnapshot;
  const validationErrors = validation.issues.filter((issue) => issue.severity === "error");
  const validationWarnings = validation.issues.filter((issue) => issue.severity === "warning");

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void loadPages();
    void loadTitleOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, locale, statusFilter]);

  async function loadPages(preferredPageCode?: string) {
    setPagesStatus("loading");
    setLocalMessage(null);
    try {
      const data = await listSiteV3Pages({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        locale,
        status: statusFilter,
      });
      setPagesData(data);
      setPagesStatus("idle");

      const nextPageCode = preferredPageCode ?? pageMeta?.page_code ?? data.pages[0]?.page_code;
      if (nextPageCode) {
        await loadPage(nextPageCode, { preserveDirty: false });
      } else {
        startNewPage("home", "Homepage");
      }
    } catch (error) {
      setPagesStatus("error");
      setLocalMessage({
        kind: "error",
        text: readErrorMessage(error, "Site V3 pages could not be loaded."),
      });
    }
  }

  async function loadTitleOptions() {
    try {
      const data = await apiRequest<SiteTitlesResponse>(`/catalog/sites/${SITE_V3_SITE_CODE}/titles`);
      setTitleOptions(
        data.titles
          .filter((title) => title.is_archived !== true && title.is_master !== true)
          .sort((left, right) => left.display_name.localeCompare(right.display_name)),
      );
    } catch {
      setTitleOptions([]);
    }
  }

  async function loadPage(pageCode: string, options: { preserveDirty: boolean } = { preserveDirty: true }) {
    if (options.preserveDirty && isDirty && !window.confirm("Unsaved Site V3 changes will be discarded. Reload page?")) {
      return;
    }

    setBusyAction("load-page");
    setLocalMessage(null);
    try {
      const data = await getSiteV3Page({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode,
        locale,
      });
      applyPageResponse(data);
      await loadVersions(data.page.page_code);
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: readErrorMessage(error, "Site V3 page loading failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function loadVersions(pageCode: string) {
    try {
      const data = await listSiteV3Versions({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode,
        locale,
      });
      setVersions(data.versions);
    } catch {
      setVersions([]);
    }
  }

  function applyPageResponse(data: SiteV3PageResponse) {
    const nextState: SiteV3PageEditorState = {
      page_code: data.page.page_code,
      locale: data.page.locale,
      title: data.page.title,
      modules: sortModules(data.modules),
    };
    setPageMeta(data.page);
    setEditorState(nextState);
    setPublishedSummary(data.published ?? null);
    setValidation(EMPTY_VALIDATION);
    setLastSavedSnapshot(serializeEditorState(nextState));
  }

  function startNewPage(pageCode: string, title: string) {
    const nextState = createEmptyEditorState(normalizePageCode(pageCode), title, locale);
    setPageMeta(null);
    setPublishedSummary(null);
    setVersions([]);
    setValidation(EMPTY_VALIDATION);
    setEditorState(nextState);
    setLastSavedSnapshot("");
    setLocalMessage({
      kind: "info",
      text: "New Site V3 page draft. Save draft to create it in the backend.",
    });
  }

  function updateEditorState(patch: Partial<SiteV3PageEditorState>) {
    setEditorState((current) => ({
      ...current,
      ...patch,
    }));
    setValidation(EMPTY_VALIDATION);
  }

  function addModule(moduleCode: SiteV3ModuleCode) {
    const descriptor = SITE_V3_MODULE_DESCRIPTORS[moduleCode];
    setEditorState((current) => ({
      ...current,
      modules: [
        ...current.modules,
        {
          client_id: createClientId(moduleCode),
          module_code: moduleCode,
          schema_version: descriptor.schemaVersion,
          slot_key: descriptor.slotKeys[0],
          sort_order: current.modules.length,
          config_json: createDefaultConfig(descriptor),
        },
      ],
    }));
    setValidation(EMPTY_VALIDATION);
  }

  function removeModule(index: number) {
    const module = editorState.modules[index];
    const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
    if (!window.confirm(`Remove ${descriptor.label}?`)) {
      return;
    }
    setEditorState((current) => ({
      ...current,
      modules: current.modules.filter((_, moduleIndex) => moduleIndex !== index),
    }));
    setValidation(EMPTY_VALIDATION);
  }

  function moveModule(index: number, delta: number) {
    const nextIndex = index + delta;
    if (nextIndex < 0 || nextIndex >= editorState.modules.length) {
      return;
    }
    setEditorState((current) => {
      const modules = [...current.modules];
      const [module] = modules.splice(index, 1);
      modules.splice(nextIndex, 0, module);
      return { ...current, modules };
    });
    setValidation(EMPTY_VALIDATION);
  }

  function updateModule(index: number, patch: Partial<SiteV3AdminModule>) {
    setEditorState((current) => ({
      ...current,
      modules: current.modules.map((module, moduleIndex) =>
        moduleIndex === index ? { ...module, ...patch } : module,
      ),
    }));
    setValidation(EMPTY_VALIDATION);
  }

  function updateModuleConfig(index: number, key: string, value: unknown) {
    setEditorState((current) => ({
      ...current,
      modules: current.modules.map((module, moduleIndex) =>
        moduleIndex === index
          ? {
              ...module,
              config_json: {
                ...module.config_json,
                [key]: value,
              },
            }
          : module,
      ),
    }));
    setValidation(EMPTY_VALIDATION);
  }

  async function handleSaveDraft() {
    const payload = buildDraftPayload(editorState, pageMeta?.draft_version ?? null);
    setBusyAction("save-draft");
    setLocalMessage(null);
    try {
      const data = await saveSiteV3Draft({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode: editorState.page_code,
        payload,
      });
      applyPageResponse(data);
      await loadPages(data.page.page_code);
      setLocalMessage({
        kind: "success",
        text: "Draft saved. Public Site V3 output is still unchanged until publish.",
      });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Save draft failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleValidate() {
    setBusyAction("validate");
    setLocalMessage(null);
    try {
      const result = await validateSiteV3Draft({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode: editorState.page_code,
        payload: {
          locale: editorState.locale,
          title: editorState.title,
          modules: buildModulePayloads(editorState.modules),
        },
      });
      setValidation(result);
      setLocalMessage({
        kind: result.status === "valid" ? "success" : "error",
        text:
          result.status === "valid"
            ? "Validation green. This draft can be published after it is saved."
            : "Validation found blocking issues. Fix them before publishing.",
      });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Validation failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublish() {
    if (!pageMeta) {
      setLocalMessage({ kind: "error", text: "Save the draft once before publishing." });
      return;
    }
    if (isDirty) {
      setLocalMessage({ kind: "error", text: "Save draft before publishing. Unsaved changes are not published." });
      return;
    }

    setBusyAction("publish");
    setLocalMessage(null);
    try {
      const data = await publishSiteV3Page({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode: editorState.page_code,
        payload: {
          locale: editorState.locale,
          expected_draft_version: pageMeta.draft_version,
        },
      });
      await loadPage(data.page.page_code, { preserveDirty: false });
      await loadPages(data.page.page_code);
      setLocalMessage({
        kind: "success",
        text: `Published version ${data.page.published_version}. Public renderer will read the snapshot only.`,
      });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Publish failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleArchive() {
    if (!pageMeta) {
      setLocalMessage({ kind: "error", text: "This page does not exist yet." });
      return;
    }
    if (!window.confirm(`Archive ${editorState.page_code}? Public Site V3 will stop serving it.`)) {
      return;
    }
    setBusyAction("archive");
    setLocalMessage(null);
    try {
      await archiveSiteV3Page({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        pageCode: editorState.page_code,
        payload: { locale: editorState.locale },
      });
      await loadPages();
      setLocalMessage({ kind: "success", text: "Page archived." });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Archive failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  const isBusy = busyAction !== null;

  return (
    <div className="site-v3-admin" data-testid="site-v3-admin-builder">
      <section className="admin-card site-v3-admin-hero">
        <div>
          <span className="status-badge info">Site V3 Lab</span>
          <h3>Site V3 Builder</h3>
          <p>
            Build draft pages inside the real backoffice. Public Site V3 reads only
            published snapshots.
          </p>
        </div>
        <div className="site-v3-admin-hero-actions">
          <button
            className="button-secondary"
            type="button"
            onClick={() => void loadPages()}
            disabled={isBusy}
          >
            Reload
          </button>
          <button
            className="button-secondary"
            type="button"
            onClick={() => startNewPage("home", "Homepage")}
            disabled={isBusy}
          >
            New page
          </button>
        </div>
      </section>

      {localMessage ? (
        <div className={`site-v3-message is-${localMessage.kind}`} role={localMessage.kind === "error" ? "alert" : "status"}>
          {localMessage.text}
        </div>
      ) : null}

      <div className="site-v3-admin-layout">
        <aside className="admin-card site-v3-page-list" aria-label="Site V3 pages">
          <div className="site-v3-card-heading">
            <div>
              <h4>Pages</h4>
              <p>Locale {locale.toUpperCase()} - {pagesData?.pagination.total ?? 0} records</p>
            </div>
          </div>
          <div className="site-v3-filter-row">
            <label className="site-v3-field">
              <span>Locale</span>
              <select value={locale} onChange={(event) => setLocale(event.target.value)}>
                <option value="it">IT</option>
                <option value="en">EN</option>
                <option value="de">DE</option>
                <option value="es">ES</option>
              </select>
            </label>
            <label className="site-v3-field">
              <span>Status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as SiteV3ListStatusFilter)}
              >
                <option value="all">All</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </label>
          </div>
          {pagesStatus === "loading" ? <p className="empty-state">Loading pages...</p> : null}
          {pagesStatus === "error" ? <p className="empty-state">Page list unavailable.</p> : null}
          <div className="site-v3-page-list-items">
            {(pagesData?.pages ?? []).map((page) => (
              <button
                className={`site-v3-page-button ${page.page_code === editorState.page_code ? "is-selected" : ""}`}
                key={`${page.page_code}:${page.locale}`}
                type="button"
                onClick={() => void loadPage(page.page_code)}
              >
                <span>
                  <strong>{page.title}</strong>
                  <small>{page.page_code}</small>
                </span>
                <span className={`site-v3-status-pill is-${page.status}`}>{page.status}</span>
              </button>
            ))}
            {pagesData && pagesData.pages.length === 0 ? (
              <p className="empty-state">No Site V3 pages yet. Start with the Homepage draft.</p>
            ) : null}
          </div>
        </aside>

        <main className="site-v3-editor-stack">
          <section className="admin-card site-v3-command-card">
            <div className="site-v3-editor-header">
              <div>
                <span className={`site-v3-status-pill is-${pageMeta?.status ?? "draft"}`}>
                  {pageMeta?.status ?? "new draft"}
                </span>
                <h3>{editorState.title || "Untitled page"}</h3>
                <p>
                  Draft v{pageMeta?.draft_version ?? 0}
                  {publishedSummary ? ` - published v${publishedSummary.version}` : " - not published"}
                </p>
              </div>
              <div className="site-v3-command-actions">
                <button className="button-secondary" type="button" onClick={() => void loadPage(editorState.page_code)} disabled={isBusy || !pageMeta}>
                  Load saved draft
                </button>
                <button className="button" type="button" onClick={() => void handleSaveDraft()} disabled={isBusy || !isDirty}>
                  {busyAction === "save-draft" ? "Saving..." : "Save draft"}
                </button>
                <button className="button-secondary" type="button" onClick={() => void handleValidate()} disabled={isBusy}>
                  {busyAction === "validate" ? "Validating..." : "Validate"}
                </button>
                <button className="button" type="button" onClick={() => void handlePublish()} disabled={isBusy || isDirty || validationErrors.length > 0}>
                  {busyAction === "publish" ? "Publishing..." : "Publish live"}
                </button>
                <button className="button-secondary danger" type="button" onClick={() => void handleArchive()} disabled={isBusy || !pageMeta}>
                  Archive
                </button>
              </div>
            </div>
            <div className="site-v3-draft-state">
              <span className={isDirty ? "is-dirty" : "is-saved"}>
                {isDirty ? "Unsaved changes" : "Aligned with saved draft"}
              </span>
              <span>{validation.status === "valid" ? "Validation green" : validation.status === "invalid" ? "Validation has issues" : "Validation not run"}</span>
            </div>
          </section>

          <section className="admin-card">
            <div className="site-v3-card-heading">
              <div>
                <h4>Page identity</h4>
                <p>These fields define the editable draft identity. Page code is immutable after first save.</p>
              </div>
            </div>
            <div className="site-v3-form-grid">
              <label className="site-v3-field">
                <span>Page code</span>
                <input
                  value={editorState.page_code}
                  onChange={(event) =>
                    updateEditorState({
                      page_code: normalizePageCode(event.target.value),
                    })
                  }
                  disabled={Boolean(pageMeta)}
                />
              </label>
              <label className="site-v3-field">
                <span>Title</span>
                <input
                  value={editorState.title}
                  onChange={(event) => updateEditorState({ title: event.target.value })}
                  maxLength={160}
                />
              </label>
            </div>
          </section>

          <ModuleComposer
            modules={editorState.modules}
            titleOptions={titleOptions}
            onAddModule={addModule}
            onMoveModule={moveModule}
            onRemoveModule={removeModule}
            onUpdateModule={updateModule}
            onUpdateModuleConfig={updateModuleConfig}
          />

          <ValidationPanel
            validation={validation}
            errorCount={validationErrors.length}
            warningCount={validationWarnings.length}
          />

          <div className="site-v3-preview-history-grid">
            <SiteV3DraftPreview modules={editorState.modules} pageTitle={editorState.title} titleOptions={titleOptions} />
            <VersionHistory versions={versions} />
          </div>
        </main>
      </div>
    </div>
  );
}

function ModuleComposer({
  modules,
  titleOptions,
  onAddModule,
  onMoveModule,
  onRemoveModule,
  onUpdateModule,
  onUpdateModuleConfig,
}: {
  modules: SiteV3AdminModule[];
  titleOptions: SiteV3TitleOption[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onMoveModule: (index: number, delta: number) => void;
  onRemoveModule: (index: number) => void;
  onUpdateModule: (index: number, patch: Partial<SiteV3AdminModule>) => void;
  onUpdateModuleConfig: (index: number, key: string, value: unknown) => void;
}) {
  return (
    <section className="admin-card site-v3-module-composer">
      <div className="site-v3-card-heading">
        <div>
          <h4>Module library</h4>
          <p>Scegli i blocchi della pagina per tipologia, poi ordinali e compilali sotto.</p>
        </div>
        <span className="site-v3-status-pill is-draft">{modules.length} modules</span>
      </div>
      <div className="site-v3-module-picker" aria-label="Site V3 module picker">
        {SITE_V3_MODULE_CATEGORIES.map((category) => {
          const categoryModules = Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
            (descriptor) => descriptor.category === category.key,
          );
          return (
            <section className="site-v3-module-picker-group" key={category.key}>
              <div className="site-v3-module-picker-heading">
                <strong>{category.label}</strong>
                <p>{category.description}</p>
              </div>
              <div className="site-v3-module-picker-grid">
                {categoryModules.map((descriptor) => {
                  const count = modules.filter((module) => module.module_code === descriptor.moduleCode).length;
                  return (
                    <button
                      aria-label={`Add ${descriptor.label} module`}
                      className="site-v3-module-picker-card"
                      key={descriptor.moduleCode}
                      onClick={() => onAddModule(descriptor.moduleCode)}
                      type="button"
                    >
                      <span>{descriptor.label}</span>
                      <strong>{descriptor.moduleCode}</strong>
                      <p>{descriptor.humanHint}</p>
                      {count > 0 ? <small>{count} gia' in pagina</small> : <small>Aggiungi modulo</small>}
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
      <div className="site-v3-module-list">
        {modules.map((module, index) => {
          const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
          return (
            <article className="site-v3-module-card" key={module.id ?? module.client_id ?? `${module.module_code}-${index}`}>
              <header className="site-v3-module-card-header">
                <div>
                  <span className="site-v3-module-code">{module.module_code}</span>
                  <h5>{descriptor.label}</h5>
                  <p>{descriptor.humanHint}</p>
                </div>
                <div className="site-v3-module-actions">
                  <button className="button-secondary" type="button" onClick={() => onMoveModule(index, -1)} disabled={index === 0}>
                    Up
                  </button>
                  <button className="button-secondary" type="button" onClick={() => onMoveModule(index, 1)} disabled={index === modules.length - 1}>
                    Down
                  </button>
                  <button className="button-secondary danger" type="button" onClick={() => onRemoveModule(index)}>
                    Remove
                  </button>
                </div>
              </header>
              <div className="site-v3-module-meta">
                <label className="site-v3-field">
                  <span>Slot</span>
                  <select value={module.slot_key} onChange={(event) => onUpdateModule(index, { slot_key: event.target.value })}>
                    {descriptor.slotKeys.map((slotKey) => (
                      <option key={slotKey} value={slotKey}>
                        {slotKey}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="site-v3-module-order">
                  <span>Sort</span>
                  <strong>{index}</strong>
                </div>
              </div>
              <div className="site-v3-module-fields">
                {descriptor.fields.map((field) => (
                  <ModuleField
                    key={field.key}
                    field={field}
                    module={module}
                    titleOptions={titleOptions}
                    onChange={(value) => onUpdateModuleConfig(index, field.key, value)}
                  />
                ))}
              </div>
            </article>
          );
        })}
        {modules.length === 0 ? (
          <p className="empty-state">No modules yet. Add a hero, game grid or footer to start composing the page.</p>
        ) : null}
      </div>
    </section>
  );
}

function ModuleField({
  field,
  module,
  titleOptions,
  onChange,
}: {
  field: SiteV3ModuleFieldDescriptor;
  module: SiteV3AdminModule;
  titleOptions: SiteV3TitleOption[];
  onChange: (value: unknown) => void;
}) {
  const value = module.config_json[field.key];
  const commonLabel = (
    <>
      <span>
        {field.label}
        {field.required ? <strong aria-label="required"> *</strong> : null}
      </span>
      <small>{field.help}</small>
    </>
  );

  if (field.type === "html") {
    return (
      <label className="site-v3-field site-v3-field-wide">
        {commonLabel}
        <textarea value={toText(value)} onChange={(event) => onChange(event.target.value)} rows={7} maxLength={field.maxLength} />
      </label>
    );
  }

  if (field.type === "title_code") {
    return (
      <label className="site-v3-field">
        {commonLabel}
        <select value={toText(value)} onChange={(event) => onChange(event.target.value)}>
          <option value="">Select title</option>
          {titleOptions.map((title) => (
            <option key={title.title_code} value={title.title_code}>
              {title.display_name} ({title.title_code})
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "title_code_list") {
    const selected = Array.isArray(value) ? value.map(String) : [];
    return (
      <fieldset className="site-v3-fieldset site-v3-field-wide">
        <legend>{field.label}{field.required ? " *" : ""}</legend>
        <p>{field.help}</p>
        <div className="site-v3-title-checks">
          {titleOptions.map((title) => (
            <label key={title.title_code} className="site-v3-check">
              <input
                type="checkbox"
                checked={selected.includes(title.title_code)}
                onChange={(event) => {
                  const next = event.target.checked
                    ? [...selected, title.title_code]
                    : selected.filter((titleCode) => titleCode !== title.title_code);
                  onChange(next);
                }}
              />
              <span>{title.display_name}</span>
            </label>
          ))}
          {titleOptions.length === 0 ? <span className="empty-state">No title options available.</span> : null}
        </div>
      </fieldset>
    );
  }

  if (field.type === "nav_items") {
    return (
      <label className="site-v3-field site-v3-field-wide">
        {commonLabel}
        <textarea
          value={navItemsToLines(value)}
          onChange={(event) => onChange(linesToNavItems(event.target.value))}
          rows={5}
        />
      </label>
    );
  }

  if (field.type === "asset_ref") {
    const assetRef = toAssetRef(value);
    return (
      <div className="site-v3-fieldset site-v3-field-wide">
        <strong>{field.label}</strong>
        <p>{field.help}</p>
        <div className="site-v3-form-grid">
          <label className="site-v3-field">
            <span>Asset ID</span>
            <input value={assetRef.asset_id ?? ""} onChange={(event) => onChange({ ...assetRef, asset_id: event.target.value })} />
          </label>
          <label className="site-v3-field">
            <span>Asset kind</span>
            <input value={assetRef.asset_kind ?? ""} onChange={(event) => onChange({ ...assetRef, asset_kind: event.target.value })} />
          </label>
          <label className="site-v3-field site-v3-field-wide">
            <span>Public URL</span>
            <input value={assetRef.public_url ?? ""} onChange={(event) => onChange({ ...assetRef, public_url: event.target.value })} />
          </label>
        </div>
        <span className="site-v3-warning-note">Upload is not part of WP3. Missing assets remain visible as warnings.</span>
      </div>
    );
  }

  if (field.type === "boolean") {
    return (
      <label className="site-v3-check">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        <span>{field.label}</span>
      </label>
    );
  }

  const useTextarea = (field.maxLength ?? 0) > 180 || field.key === "body" || field.key === "legal_text";
  return (
    <label className={`site-v3-field ${useTextarea ? "site-v3-field-wide" : ""}`}>
      {commonLabel}
      {useTextarea ? (
        <textarea value={toText(value)} onChange={(event) => onChange(event.target.value)} rows={4} maxLength={field.maxLength} />
      ) : (
        <input value={toText(value)} onChange={(event) => onChange(event.target.value)} maxLength={field.maxLength} />
      )}
    </label>
  );
}

function ValidationPanel({
  validation,
  errorCount,
  warningCount,
}: {
  validation: SiteV3ValidationResult;
  errorCount: number;
  warningCount: number;
}) {
  return (
    <section className="admin-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>Validation</h4>
          <p>Publish is blocked by error severity issues. Codes stay visible for support.</p>
        </div>
        <span className={`site-v3-status-pill is-${validation.status}`}>
          {validation.status}
        </span>
      </div>
      <div className="site-v3-validation-summary">
        <span>{errorCount} errors</span>
        <span>{warningCount} warnings</span>
      </div>
      {validation.issues.length > 0 ? (
        <ul className="site-v3-issue-list">
          {validation.issues.map((issue, index) => (
            <li className={`is-${issue.severity}`} key={`${issue.code}-${issue.field}-${index}`}>
              <strong>{issue.message}</strong>
              <span>{issue.code}</span>
              <small>
                {issue.module_id ?? "page"} / {issue.field}
              </small>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">Run validation to see readiness for publish.</p>
      )}
    </section>
  );
}

function SiteV3DraftPreview({
  modules,
  pageTitle,
  titleOptions,
}: {
  modules: SiteV3AdminModule[];
  pageTitle: string;
  titleOptions: SiteV3TitleOption[];
}) {
  return (
    <section className="admin-card site-v3-preview-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>Draft preview</h4>
          <p>Composition preview. Final pixel rendering belongs to WP4 public renderer.</p>
        </div>
      </div>
      <div className="site-v3-preview-surface">
        <h3>{pageTitle || "Untitled page"}</h3>
        {modules.map((module, index) => (
          <PreviewModule key={module.id ?? module.client_id ?? index} module={module} titleOptions={titleOptions} />
        ))}
        {modules.length === 0 ? <p className="empty-state">No modules to preview.</p> : null}
      </div>
    </section>
  );
}

function PreviewModule({
  module,
  titleOptions,
}: {
  module: SiteV3AdminModule;
  titleOptions: SiteV3TitleOption[];
}) {
  const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
  const config = module.config_json;
  const titles = titleOptions.filter((title) =>
    collectTitleCodes(config).includes(title.title_code),
  );
  return (
    <article className={`site-v3-preview-module is-${module.module_code}`}>
      <span>{descriptor.label}</span>
      <strong>{previewHeadline(module)}</strong>
      {previewBody(module) ? <p>{previewBody(module)}</p> : null}
      {titles.length > 0 ? (
        <div className="site-v3-preview-games">
          {titles.map((title) => (
            <span key={title.title_code}>{title.display_name}</span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function VersionHistory({ versions }: { versions: SiteV3Version[] }) {
  return (
    <section className="admin-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>History</h4>
          <p>Read-only for MVP. Revert UI is Phase 2.</p>
        </div>
      </div>
      {versions.length > 0 ? (
        <ol className="site-v3-version-list">
          {versions.map((version) => (
            <li key={version.id}>
              <strong>v{version.version}</strong>
              <span className={`site-v3-status-pill is-${version.status}`}>{version.status}</span>
              <small>{formatDate(version.published_at ?? version.created_at)}</small>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-state">No versions yet. Publish once to create history.</p>
      )}
    </section>
  );
}

function createEmptyEditorState(pageCode: string, title: string, locale: string): SiteV3PageEditorState {
  return {
    page_code: pageCode,
    locale,
    title,
    modules: [],
  };
}

function createDefaultConfig(descriptor: SiteV3ModuleDescriptor): SiteV3ModuleConfig {
  return Object.fromEntries(
    descriptor.fields.map((field) => {
      if (field.type === "title_code_list" || field.type === "nav_items") {
        return [field.key, []];
      }
      if (field.type === "asset_ref") {
        return [field.key, {}];
      }
      if (field.type === "boolean") {
        return [field.key, false];
      }
      return [field.key, ""];
    }),
  );
}

function buildDraftPayload(editorState: SiteV3PageEditorState, expectedDraftVersion: number | null) {
  return {
    locale: editorState.locale,
    title: editorState.title,
    expected_draft_version: expectedDraftVersion,
    modules: buildModulePayloads(editorState.modules),
  };
}

function buildModulePayloads(modules: SiteV3AdminModule[]): SiteV3AdminModulePayload[] {
  return modules.map((module, index) => ({
    id: module.id ?? null,
    client_id: module.client_id ?? null,
    module_code: module.module_code,
    schema_version: module.schema_version,
    slot_key: module.slot_key,
    sort_order: index,
    config_json: module.config_json,
  }));
}

function serializeEditorState(editorState: SiteV3PageEditorState): string {
  return JSON.stringify(stableValue({
    ...editorState,
    page_code: normalizePageCode(editorState.page_code),
    modules: buildModulePayloads(editorState.modules),
  }));
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(stableValue);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, entryValue]) => entryValue !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entryValue]) => [key, stableValue(entryValue)]),
    );
  }
  return value;
}

function sortModules(modules: SiteV3AdminModule[]): SiteV3AdminModule[] {
  return [...modules].sort((left, right) => {
    const slotCompare = left.slot_key.localeCompare(right.slot_key);
    if (slotCompare !== 0) {
      return slotCompare;
    }
    return left.sort_order - right.sort_order;
  });
}

function normalizePageCode(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]/g, "")
    .slice(0, 64);
}

function createClientId(moduleCode: string): string {
  return `${moduleCode}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function toText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function toAssetRef(value: unknown): SiteV3AssetRef {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as SiteV3AssetRef) : {};
}

function navItemsToLines(value: unknown): string {
  if (!Array.isArray(value)) {
    return "";
  }
  return value
    .map((item) => {
      if (!item || typeof item !== "object") {
        return "";
      }
      const navItem = item as SiteV3NavItem;
      return [navItem.label, navItem.href ?? navItem.title_code ?? ""].filter(Boolean).join(" | ");
    })
    .join("\n");
}

function linesToNavItems(value: string): SiteV3NavItem[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, target] = line.split("|").map((part) => part.trim());
      if (!target) {
        return { label };
      }
      if (target.startsWith("/") || target.startsWith("http")) {
        return { label, href: target };
      }
      return { label, title_code: target };
    });
}

function collectTitleCodes(config: SiteV3ModuleConfig): string[] {
  const values = Object.values(config);
  return values.flatMap((value) => {
    if (typeof value === "string") {
      return value ? [value] : [];
    }
    if (Array.isArray(value)) {
      return value.filter((item): item is string => typeof item === "string");
    }
    return [];
  });
}

function previewHeadline(module: SiteV3AdminModule): string {
  const config = module.config_json;
  return toText(config.headline) || toText(config.heading) || toText(config.brand_label) || toText(config.legal_text) || SITE_V3_MODULE_DESCRIPTORS[module.module_code].label;
}

function previewBody(module: SiteV3AdminModule): string {
  const config = module.config_json;
  if (typeof config.html === "string") {
    return config.html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }
  return toText(config.body);
}

function formatDate(value: string | null): string {
  if (!value) {
    return "not published";
  }
  return new Date(value).toLocaleString("it-IT", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function formatApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    const suffix = [error.code, error.supportId ? `support ${error.supportId}` : null]
      .filter(Boolean)
      .join(" - ");
    return `${fallback} ${error.message}${suffix ? ` (${suffix})` : ""}`;
  }
  return readErrorMessage(error, fallback);
}
