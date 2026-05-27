"use client";

import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, ApiRequestError, apiRequest, readErrorMessage } from "@/app/lib/api";
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
  type SiteV3ModuleCategory,
  type SiteV3ModuleConfig,
  type SiteV3ModuleDescriptor,
  type SiteV3ModuleFieldDescriptor,
  type SiteV3FieldGroup,
  type SiteV3NavItem,
  type SiteV3PageEditorState,
  type SiteV3PageResponse,
  type SiteV3PagesResponse,
  type SiteV3SiteAsset,
  type SiteV3TitleOption,
  type SiteV3ValidationResult,
  type SiteV3Version,
} from "./site-v3-admin-types";
import {
  archiveSiteV3Page,
  getSiteV3Page,
  listSiteV3Assets,
  listSiteV3Pages,
  listSiteV3Versions,
  publishSiteV3Page,
  saveSiteV3Draft,
  validateSiteV3Draft,
} from "./site-v3-admin-api";
import { SiteV3DraftPreviewPanel } from "./site-v3-draft-preview-panel";

type SiteV3AdminBuilderProps = {
  accessToken: string;
};

type LocalMessage = {
  kind: "success" | "error" | "info";
  text: string;
};

type SiteV3AdminView =
  | { kind: "overview" }
  | { kind: "siteSettings" }
  | { kind: "pages" }
  | { kind: "pageDetail" }
  | { kind: "composition" }
  | { kind: "modules" }
  | { kind: "moduleCategory"; category: SiteV3ModuleCategory }
  | { kind: "moduleType"; moduleCode: SiteV3ModuleCode }
  | { kind: "moduleInstance"; moduleIndex: number }
  | { kind: "validation" }
  | { kind: "versions" };

type SiteTitlesResponse = {
  titles: SiteV3TitleOption[];
};

const SITE_V3_SLOT_ORDER = new Map<string, number>([
  ["header", 10],
  ["hero", 20],
  ["main", 30],
  ["content", 40],
  ["feature", 50],
  ["games", 60],
  ["promo", 70],
  ["footer", 90],
]);

const EMPTY_VALIDATION: SiteV3ValidationResult = {
  status: "unknown",
  issues: [],
};

const SITE_V3_FIELD_GROUP_ORDER: SiteV3FieldGroup[] = ["content", "catalog", "assets", "links", "rules"];

const SITE_V3_FIELD_GROUP_META: Record<SiteV3FieldGroup, { label: string; description: string }> = {
  assets: {
    label: "Assets and media",
    description: "Images, banners or public media references used by this module.",
  },
  catalog: {
    label: "Game catalog",
    description: "Connections to existing published game titles.",
  },
  content: {
    label: "Content",
    description: "Text that appears directly in the public page.",
  },
  links: {
    label: "Links and actions",
    description: "Navigation, CTA and handoff fields.",
  },
  rules: {
    label: "Legal and safe HTML",
    description: "Long text, legal copy or allowlisted HTML.",
  },
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
  const [siteAssets, setSiteAssets] = useState<SiteV3SiteAsset[]>([]);
  const [assetsStatus, setAssetsStatus] = useState<"idle" | "loading" | "error">("idle");
  const [localMessage, setLocalMessage] = useState<LocalMessage | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [selectedModuleIndex, setSelectedModuleIndex] = useState<number | null>(null);
  const [currentView, setCurrentView] = useState<SiteV3AdminView>({ kind: "overview" });

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
    void loadSiteAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, locale, statusFilter]);

  useEffect(() => {
    setSelectedModuleIndex((current) => {
      if (editorState.modules.length === 0) {
        return null;
      }
      if (current === null) {
        return 0;
      }
      return Math.min(current, editorState.modules.length - 1);
    });
  }, [editorState.modules.length]);

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

  async function loadSiteAssets() {
    setAssetsStatus("loading");
    try {
      const assets = await listSiteV3Assets({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        assetKind: "homepage_banner",
      });
      setSiteAssets(assets);
      setAssetsStatus("idle");
    } catch {
      setSiteAssets([]);
      setAssetsStatus("error");
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
    setSelectedModuleIndex(nextState.modules.length > 0 ? 0 : null);
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
    setSelectedModuleIndex(null);
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

  function addModule(moduleCode: SiteV3ModuleCode): number {
    const descriptor = SITE_V3_MODULE_DESCRIPTORS[moduleCode];
    const nextIndex = editorState.modules.length;
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
    setSelectedModuleIndex(nextIndex);
    setValidation(EMPTY_VALIDATION);
    return nextIndex;
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
    setSelectedModuleIndex((current) => {
      if (editorState.modules.length <= 1) {
        return null;
      }
      if (current === null || current < index) {
        return current;
      }
      return Math.max(0, current - 1);
    });
    setValidation(EMPTY_VALIDATION);
    if (currentView.kind === "moduleInstance" && currentView.moduleIndex === index) {
      setCurrentView({ kind: "composition" });
    }
  }

  function duplicateModule(index: number) {
    const source = editorState.modules[index];
    if (!source) {
      return;
    }
    const nextIndex = index + 1;
    setEditorState((current) => {
      const sourceModule = current.modules[index];
      if (!sourceModule) {
        return current;
      }
      const duplicate: SiteV3AdminModule = {
        ...sourceModule,
        client_id: createClientId(sourceModule.module_code),
        id: undefined,
        sort_order: nextIndex,
        config_json: structuredCloneConfig(sourceModule.config_json),
      };
      const modules = [...current.modules];
      modules.splice(nextIndex, 0, duplicate);
      return { ...current, modules: normalizeModuleSortOrder(modules) };
    });
    setSelectedModuleIndex(nextIndex);
    setCurrentView({ kind: "moduleInstance", moduleIndex: nextIndex });
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
    setSelectedModuleIndex((current) => {
      if (current === index) {
        return nextIndex;
      }
      if (current === nextIndex) {
        return index;
      }
      return current;
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

  async function handleSaveDraft(): Promise<boolean> {
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
      return true;
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Save draft failed."),
      });
      return false;
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
  const selectedModule =
    selectedModuleIndex !== null ? editorState.modules[selectedModuleIndex] ?? null : null;

  async function openPageDetail(pageCode: string) {
    await loadPage(pageCode);
    setCurrentView({ kind: "pageDetail" });
  }

  function openNewPage() {
    startNewPage("home", "Homepage");
    setCurrentView({ kind: "pageDetail" });
  }

  function addModuleAndOpen(moduleCode: SiteV3ModuleCode) {
    const nextIndex = addModule(moduleCode);
    setCurrentView({ kind: "moduleInstance", moduleIndex: nextIndex });
  }

  function openModuleInstance(index: number) {
    setSelectedModuleIndex(index);
    setCurrentView({ kind: "moduleInstance", moduleIndex: index });
  }

  function addModuleFromComposition(moduleCode: SiteV3ModuleCode) {
    const nextIndex = addModule(moduleCode);
    setCurrentView({ kind: "moduleInstance", moduleIndex: nextIndex });
  }

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
            onClick={openNewPage}
            disabled={isBusy}
          >
            New page
          </button>
        </div>
      </section>

      <div className="site-v3-cms-shell">
        <SiteV3AdminNav
          activeView={currentView}
          pageTitle={editorState.title}
          pageCode={editorState.page_code}
          dirty={isDirty}
          moduleCount={editorState.modules.length}
          onNavigate={setCurrentView}
        />

        <main className="site-v3-cms-main">
          {localMessage ? (
            <div className={`site-v3-message is-${localMessage.kind}`} role={localMessage.kind === "error" ? "alert" : "status"}>
              {localMessage.text}
            </div>
          ) : null}

          {isPageActionBarView(currentView) ? (
            <SiteV3PageActionBar
              busyAction={busyAction}
              dirty={isDirty}
              isBusy={isBusy}
              pageMeta={pageMeta}
              validationErrors={validationErrors.length}
              onPublish={() => void handlePublish()}
              onSaveDraft={() => void handleSaveDraft()}
              onValidate={() => void handleValidate()}
            />
          ) : null}

          {currentView.kind === "overview" ? (
            <SiteV3OverviewScreen
              dirty={isDirty}
              editorState={editorState}
              pageMeta={pageMeta}
              pagesData={pagesData}
              publishedSummary={publishedSummary}
              validation={validation}
              versions={versions}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "siteSettings" ? (
            <SiteV3SiteSettingsScreen
              assetsStatus={assetsStatus}
              locale={locale}
              pagesData={pagesData}
              siteAssets={siteAssets}
              statusFilter={statusFilter}
            />
          ) : null}

          {currentView.kind === "pages" ? (
            <SiteV3PagesScreen
              locale={locale}
              pagesData={pagesData}
              pagesStatus={pagesStatus}
              selectedPageCode={editorState.page_code}
              statusFilter={statusFilter}
              onLocaleChange={setLocale}
              onNewPage={openNewPage}
              onOpenPage={(pageCode) => void openPageDetail(pageCode)}
              onStatusFilterChange={setStatusFilter}
            />
          ) : null}

          {currentView.kind === "pageDetail" ? (
            <SiteV3PageDetailScreen
              busyAction={busyAction}
              dirty={isDirty}
              editorState={editorState}
              isBusy={isBusy}
              pageMeta={pageMeta}
              publishedSummary={publishedSummary}
              validation={validation}
              validationErrors={validationErrors.length}
              onArchive={() => void handleArchive()}
              onLoadPage={() => void loadPage(editorState.page_code)}
              onPublish={() => void handlePublish()}
              onSaveDraft={() => void handleSaveDraft()}
              onUpdateEditorState={updateEditorState}
              onValidate={() => void handleValidate()}
            />
          ) : null}

          {currentView.kind === "composition" ? (
            <SiteV3CompositionScreen
              modules={editorState.modules}
              onDuplicateModule={duplicateModule}
              onAddModule={addModuleFromComposition}
              onMoveModule={moveModule}
              onNavigate={setCurrentView}
              onOpenModule={openModuleInstance}
              onRemoveModule={removeModule}
            />
          ) : null}

          {currentView.kind === "modules" ? (
            <SiteV3ModuleLibraryScreen
              modules={editorState.modules}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleCategory" ? (
            <SiteV3ModuleCategoryScreen
              category={currentView.category}
              modules={editorState.modules}
              onAddModule={addModuleAndOpen}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleType" ? (
            <SiteV3ModuleTypeDetailScreen
              moduleCode={currentView.moduleCode}
              modules={editorState.modules}
              onAddModule={addModuleAndOpen}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleInstance" ? (
            <SiteV3ModuleInstanceScreen
              assetsStatus={assetsStatus}
              module={editorState.modules[currentView.moduleIndex] ?? selectedModule}
              moduleIndex={currentView.moduleIndex}
              moduleCount={editorState.modules.length}
              siteAssets={siteAssets}
              titleOptions={titleOptions}
              onNavigate={setCurrentView}
              onUpdateModule={updateModule}
              onUpdateModuleConfig={updateModuleConfig}
            />
          ) : null}

          {currentView.kind === "validation" ? (
            <ValidationPanel
              validation={validation}
              errorCount={validationErrors.length}
              warningCount={validationWarnings.length}
            />
          ) : null}

          {currentView.kind === "versions" ? (
            <div className="site-v3-preview-history-grid">
              <SiteV3DraftPreview modules={editorState.modules} pageTitle={editorState.title} titleOptions={titleOptions} />
              <VersionHistory versions={versions} />
            </div>
          ) : null}

          {isPagePreviewView(currentView) ? (
            <SiteV3DraftPreviewPanel
              accessToken={accessToken}
              draftVersion={pageMeta?.draft_version ?? 0}
              isDirty={isDirty}
              isSaving={busyAction === "save-draft"}
              locale={locale}
              onSaveDraft={handleSaveDraft}
              pageCode={editorState.page_code}
              siteCode={SITE_V3_SITE_CODE}
            />
          ) : null}
        </main>
      </div>
    </div>
  );
}

function isPagePreviewView(view: SiteV3AdminView): boolean {
  return (
    view.kind === "pageDetail"
    || view.kind === "composition"
    || view.kind === "moduleInstance"
    || view.kind === "validation"
  );
}

function isPageActionBarView(view: SiteV3AdminView): boolean {
  return (
    view.kind === "composition"
    || view.kind === "moduleInstance"
    || view.kind === "validation"
  );
}

function SiteV3PageActionBar({
  busyAction,
  dirty,
  isBusy,
  pageMeta,
  validationErrors,
  onPublish,
  onSaveDraft,
  onValidate,
}: {
  busyAction: string | null;
  dirty: boolean;
  isBusy: boolean;
  pageMeta: SiteV3AdminPage | null;
  validationErrors: number;
  onPublish: () => void;
  onSaveDraft: () => void;
  onValidate: () => void;
}) {
  return (
    <section className="site-v3-page-action-bar" aria-label="Page draft actions">
      <div>
        <strong>{dirty ? "Unsaved draft changes" : "Draft saved"}</strong>
        <small>
          {dirty
            ? "Save draft to update Preview live. Publish remains blocked until the draft is saved."
            : `Draft v${pageMeta?.draft_version ?? 0} is ready for preview.`}
        </small>
      </div>
      <div className="site-v3-page-action-buttons">
        <button className="button" type="button" onClick={onSaveDraft} disabled={isBusy || !dirty}>
          {busyAction === "save-draft" ? "Saving..." : "Save draft"}
        </button>
        <button className="button-secondary" type="button" onClick={onValidate} disabled={isBusy}>
          {busyAction === "validate" ? "Validating..." : "Validate"}
        </button>
        <button className="button-secondary" type="button" onClick={onPublish} disabled={isBusy || dirty || validationErrors > 0}>
          {busyAction === "publish" ? "Publishing..." : "Publish live"}
        </button>
      </div>
    </section>
  );
}

function SiteV3AdminNav({
  activeView,
  dirty,
  moduleCount,
  pageCode,
  pageTitle,
  onNavigate,
}: {
  activeView: SiteV3AdminView;
  dirty: boolean;
  moduleCount: number;
  pageCode: string;
  pageTitle: string;
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  return (
    <aside className="site-v3-cms-nav" aria-label="Site V3 CMS navigation">
      <div className="site-v3-cms-nav-title">
        <span>CMS menu</span>
        <strong>{pageTitle || "Untitled page"}</strong>
        <small>{dirty ? "Unsaved changes" : "Draft aligned"}</small>
      </div>
      <nav className="site-v3-cms-nav-list">
        <div className="site-v3-cms-nav-group">
          <span>Site</span>
          <CmsNavButton
            active={isSameView(activeView, { kind: "overview" })}
            label="Dashboard"
            onClick={() => onNavigate({ kind: "overview" })}
          />
          <CmsNavButton
            active={isSameView(activeView, { kind: "siteSettings" })}
            label="Site settings"
            meta={SITE_V3_SITE_CODE}
            onClick={() => onNavigate({ kind: "siteSettings" })}
          />
        </div>

        <div className="site-v3-cms-nav-group">
          <span>Pages</span>
          <button
            className={`site-v3-cms-nav-item ${isSameView(activeView, { kind: "pages" }) ? "is-active" : ""}`}
            onClick={() => onNavigate({ kind: "pages" })}
            type="button"
          >
            <span>All pages</span>
          </button>
          <div className="site-v3-cms-subnav">
            <small>Selected page</small>
            <CmsNavButton
              active={isSameView(activeView, { kind: "pageDetail" })}
              label="Settings"
              meta={pageCode}
              onClick={() => onNavigate({ kind: "pageDetail" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "composition" })}
              label="Composition"
              meta={`${moduleCount} modules`}
              onClick={() => onNavigate({ kind: "composition" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "validation" })}
              label="Validation"
              onClick={() => onNavigate({ kind: "validation" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "versions" })}
              label="Versions"
              onClick={() => onNavigate({ kind: "versions" })}
            />
          </div>
        </div>

        <div className="site-v3-cms-nav-group">
          <span>Modules</span>
          <CmsNavButton
            active={isSameView(activeView, { kind: "modules" })}
            label="Module library"
            onClick={() => onNavigate({ kind: "modules" })}
          />
          <div className="site-v3-cms-subnav">
            <small>Categories</small>
            {SITE_V3_MODULE_CATEGORIES.map((category) => (
              <CmsNavButton
                active={activeView.kind === "moduleCategory" && activeView.category === category.key}
                key={category.key}
                label={category.label}
                onClick={() => onNavigate({ kind: "moduleCategory", category: category.key })}
              />
            ))}
          </div>
        </div>
      </nav>
      <a className="site-v3-cms-public-link" href="http://localhost:3001" rel="noreferrer" target="_blank">
        Open public Site V3
      </a>
    </aside>
  );
}

function CmsNavButton({
  active,
  label,
  meta,
  onClick,
}: {
  active: boolean;
  label: string;
  meta?: string;
  onClick: () => void;
}) {
  return (
    <button
      className={`site-v3-cms-nav-item ${active ? "is-active" : ""}`}
      onClick={onClick}
      type="button"
    >
      <span>{label}</span>
      {meta ? <small>{meta}</small> : null}
    </button>
  );
}

function SiteV3OverviewScreen({
  dirty,
  editorState,
  pageMeta,
  pagesData,
  publishedSummary,
  validation,
  versions,
  onNavigate,
}: {
  dirty: boolean;
  editorState: SiteV3PageEditorState;
  pageMeta: SiteV3AdminPage | null;
  pagesData: SiteV3PagesResponse | null;
  publishedSummary: SiteV3Version | null;
  validation: SiteV3ValidationResult;
  versions: SiteV3Version[];
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Site management</span>
          <h3>Site overview</h3>
          <p>Current page, publication state and next editing areas.</p>
        </div>
        <span className={`site-v3-status-pill is-${pageMeta?.status ?? "draft"}`}>
          {pageMeta?.status ?? "new draft"}
        </span>
      </div>
      <div className="site-v3-overview-grid">
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "pages" })}>
          <span>Pages</span>
          <strong>{pagesData?.pagination.total ?? 0}</strong>
          <small>Manage page list and filters.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "siteSettings" })}>
          <span>Site settings</span>
          <strong>{SITE_V3_SITE_CODE}</strong>
          <small>Global site scope, public renderer and handoff rules.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "pageDetail" })}>
          <span>Page settings</span>
          <strong>{editorState.title || "Untitled"}</strong>
          <small>{editorState.page_code} / {dirty ? "unsaved changes" : "saved draft"}</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "composition" })}>
          <span>Composition</span>
          <strong>{editorState.modules.length}</strong>
          <small>Mounted modules in page order.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "validation" })}>
          <span>Validation</span>
          <strong>{validation.status}</strong>
          <small>{validation.issues.length} issues.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "versions" })}>
          <span>Published version</span>
          <strong>{publishedSummary?.version ? `v${publishedSummary.version}` : "None"}</strong>
          <small>{versions.length} history entries.</small>
        </button>
      </div>
    </section>
  );
}

function SiteV3SiteSettingsScreen({
  assetsStatus,
  locale,
  pagesData,
  siteAssets,
  statusFilter,
}: {
  assetsStatus: "idle" | "loading" | "error";
  locale: string;
  pagesData: SiteV3PagesResponse | null;
  siteAssets: SiteV3SiteAsset[];
  statusFilter: SiteV3ListStatusFilter;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Site</span>
          <h3>Site settings</h3>
          <p>Global Site V3 settings that are not owned by a single page.</p>
        </div>
        <span className="site-v3-status-pill is-published">read only MVP</span>
      </div>
      <div className="site-v3-settings-grid">
        <article className="site-v3-setting-card">
          <span>Site code</span>
          <strong>{SITE_V3_SITE_CODE}</strong>
          <p>Canonical scope for public Site V3 pages and navigation.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Public renderer</span>
          <strong>localhost:3001</strong>
          <p>The public Site V3 app reads published snapshots only.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Admin route</span>
          <strong>/admin/site-v3</strong>
          <p>The builder lives in the existing backoffice shell on port 3000.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Locale context</span>
          <strong>{locale.toUpperCase()}</strong>
          <p>Current page-list locale filter. MVP content is Italian-first with the locale model ready.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Page filter</span>
          <strong>{statusFilter}</strong>
          <p>Current list filter for all pages. Draft, published and archived pages stay separate.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Assets</span>
          <strong>{assetsStatus === "error" ? "unavailable" : `${siteAssets.length} loaded`}</strong>
          <p>Site V3 currently reuses the platform asset catalog; the dedicated picker remains a later WP.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Account and cashier</span>
          <strong>V1 handoff</strong>
          <p>Login, account and cashier flows remain owned by the existing V1 application.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Published pages</span>
          <strong>{pagesData?.pages.filter((page) => page.status === "published").length ?? 0}</strong>
          <p>Only published snapshots are visible to the public renderer.</p>
        </article>
      </div>
    </section>
  );
}

function SiteV3PagesScreen({
  locale,
  pagesData,
  pagesStatus,
  selectedPageCode,
  statusFilter,
  onLocaleChange,
  onNewPage,
  onOpenPage,
  onStatusFilterChange,
}: {
  locale: string;
  pagesData: SiteV3PagesResponse | null;
  pagesStatus: "idle" | "loading" | "error";
  selectedPageCode: string;
  statusFilter: SiteV3ListStatusFilter;
  onLocaleChange: (locale: string) => void;
  onNewPage: () => void;
  onOpenPage: (pageCode: string) => void;
  onStatusFilterChange: (status: SiteV3ListStatusFilter) => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Pages</span>
          <h3>Page list</h3>
          <p>Choose a page before editing identity, composition or versions.</p>
        </div>
        <button className="button" type="button" onClick={onNewPage}>
          New page
        </button>
      </div>
      <div className="site-v3-filter-row">
        <label className="site-v3-field">
          <span>Locale</span>
          <select value={locale} onChange={(event) => onLocaleChange(event.target.value)}>
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
            onChange={(event) => onStatusFilterChange(event.target.value as SiteV3ListStatusFilter)}
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
      <div className="site-v3-page-table">
        {(pagesData?.pages ?? []).map((page) => (
          <button
            className={`site-v3-page-table-row ${page.page_code === selectedPageCode ? "is-selected" : ""}`}
            key={`${page.page_code}:${page.locale}`}
            type="button"
            onClick={() => onOpenPage(page.page_code)}
          >
            <span>
              <strong>{page.title}</strong>
              <small>{page.page_code} / {page.locale.toUpperCase()}</small>
            </span>
            <span className={`site-v3-status-pill is-${page.status}`}>{page.status}</span>
            <small>Draft v{page.draft_version} / Published {page.published_version ? `v${page.published_version}` : "none"}</small>
          </button>
        ))}
        {pagesData && pagesData.pages.length === 0 ? (
          <p className="empty-state">No Site V3 pages yet. Start with the Homepage draft.</p>
        ) : null}
      </div>
    </section>
  );
}

function SiteV3PageDetailScreen({
  busyAction,
  dirty,
  editorState,
  isBusy,
  pageMeta,
  publishedSummary,
  validation,
  validationErrors,
  onArchive,
  onLoadPage,
  onPublish,
  onSaveDraft,
  onUpdateEditorState,
  onValidate,
}: {
  busyAction: string | null;
  dirty: boolean;
  editorState: SiteV3PageEditorState;
  isBusy: boolean;
  pageMeta: SiteV3AdminPage | null;
  publishedSummary: SiteV3Version | null;
  validation: SiteV3ValidationResult;
  validationErrors: number;
  onArchive: () => void;
  onLoadPage: () => void;
  onPublish: () => void;
  onSaveDraft: () => void;
  onUpdateEditorState: (patch: Partial<SiteV3PageEditorState>) => void;
  onValidate: () => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
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
          <button className="button-secondary" type="button" onClick={onLoadPage} disabled={isBusy || !pageMeta}>
            Load saved draft
          </button>
          <button className="button" type="button" onClick={onSaveDraft} disabled={isBusy || !dirty}>
            {busyAction === "save-draft" ? "Saving..." : "Save draft"}
          </button>
          <button className="button-secondary" type="button" onClick={onValidate} disabled={isBusy}>
            {busyAction === "validate" ? "Validating..." : "Validate"}
          </button>
          <button className="button" type="button" onClick={onPublish} disabled={isBusy || dirty || validationErrors > 0}>
            {busyAction === "publish" ? "Publishing..." : "Publish live"}
          </button>
          <button className="button-secondary danger" type="button" onClick={onArchive} disabled={isBusy || !pageMeta}>
            Archive
          </button>
        </div>
      </div>
      <div className="site-v3-draft-state">
        <span className={dirty ? "is-dirty" : "is-saved"}>
          {dirty ? "Unsaved changes" : "Aligned with saved draft"}
        </span>
        <span>{validation.status === "valid" ? "Validation green" : validation.status === "invalid" ? "Validation has issues" : "Validation not run"}</span>
      </div>
      <div className="site-v3-form-grid">
        <label className="site-v3-field">
          <span>Page code</span>
          <input
            value={editorState.page_code}
            onChange={(event) =>
              onUpdateEditorState({
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
            onChange={(event) => onUpdateEditorState({ title: event.target.value })}
            maxLength={160}
          />
        </label>
      </div>
    </section>
  );
}

function SiteV3CompositionScreen({
  modules,
  onAddModule,
  onDuplicateModule,
  onMoveModule,
  onNavigate,
  onOpenModule,
  onRemoveModule,
}: {
  modules: SiteV3AdminModule[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onDuplicateModule: (index: number) => void;
  onMoveModule: (index: number, delta: number) => void;
  onNavigate: (view: SiteV3AdminView) => void;
  onOpenModule: (index: number) => void;
  onRemoveModule: (index: number) => void;
}) {
  const [isAddPickerOpen, setIsAddPickerOpen] = useState(false);
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Pages</span>
          <h3>Page composition</h3>
          <p>Modules render top-to-bottom in this order.</p>
        </div>
        <button className="button" type="button" onClick={() => setIsAddPickerOpen((current) => !current)}>
          Add module
        </button>
      </div>
      {isAddPickerOpen ? (
        <div className="site-v3-inline-module-picker">
          <div className="site-v3-inline-module-picker-heading">
            <strong>Add module to this page</strong>
            <small>Choose a module type. It will be mounted at the end of the current page and opened for editing.</small>
          </div>
          {SITE_V3_MODULE_CATEGORIES.map((category) => {
            const categoryModules = Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
              (descriptor) => descriptor.category === category.key,
            );
            return (
              <section className="site-v3-inline-module-group" key={category.key}>
                <div>
                  <strong>{category.label}</strong>
                  <small>{category.description}</small>
                </div>
                <div className="site-v3-inline-module-options">
                  {categoryModules.map((descriptor) => (
                    <button
                      className="site-v3-inline-module-option"
                      key={descriptor.moduleCode}
                      onClick={() => {
                        onAddModule(descriptor.moduleCode);
                        setIsAddPickerOpen(false);
                      }}
                      type="button"
                    >
                      <strong>{descriptor.label}</strong>
                      <small>{descriptor.humanHint}</small>
                    </button>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      ) : null}
      <div className="site-v3-page-hierarchy-note">
        <span>Parent page</span>
        <strong>Root / Homepage</strong>
        <small>Hierarchy is modeled in the CMS UI; backend parent-page routing remains a future WP.</small>
      </div>
      <div className="site-v3-module-list is-full-page">
        {modules.map((module, index) => {
          const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
          const missingRequiredFields = getMissingRequiredFields(module);
          const isReady = missingRequiredFields.length === 0;
          return (
            <article className="site-v3-module-row" key={module.id ?? module.client_id ?? `${module.module_code}-${index}`}>
              <button
                aria-label={`Edit ${descriptor.label}`}
                className="site-v3-module-row-main"
                onClick={() => onOpenModule(index)}
                type="button"
              >
                <span className="site-v3-module-order-index">{index + 1}</span>
                <span>
                  <strong>{descriptor.label}</strong>
                  <small>{getModuleCategoryLabel(descriptor.category)} / {module.module_code} / slot {module.slot_key}</small>
                  <em>{previewHeadline(module)}</em>
                  <span className="site-v3-module-row-status">
                    <span className={`site-v3-status-pill ${isReady ? "is-valid" : "is-invalid"}`}>
                      {isReady ? "Ready" : `${missingRequiredFields.length} required missing`}
                    </span>
                    {!isReady ? <small>{missingRequiredFields.map((field) => field.label).join(", ")}</small> : null}
                  </span>
                </span>
              </button>
              <div className="site-v3-module-actions">
                <button className="button-secondary" type="button" onClick={() => onMoveModule(index, -1)} disabled={index === 0}>
                  Up
                </button>
                <button className="button-secondary" type="button" onClick={() => onMoveModule(index, 1)} disabled={index === modules.length - 1}>
                  Down
                </button>
                <button className="button-secondary" type="button" onClick={() => onDuplicateModule(index)}>
                  Duplicate
                </button>
                <button className="button-secondary danger" type="button" onClick={() => onRemoveModule(index)}>
                  Remove
                </button>
              </div>
            </article>
          );
        })}
        {modules.length === 0 ? (
          <p className="empty-state">No modules yet. Open Modules and add a header, banner, game grid or footer.</p>
        ) : null}
      </div>
    </section>
  );
}

function SiteV3ModuleLibraryScreen({
  modules,
  onNavigate,
}: {
  modules: SiteV3AdminModule[];
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Modules</span>
          <h3>Module library</h3>
          <p>Pick a category, then open a module type or add it to the current page.</p>
        </div>
      </div>
      <div className="site-v3-category-grid">
        {SITE_V3_MODULE_CATEGORIES.map((category) => {
          const categoryModules = Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
            (descriptor) => descriptor.category === category.key,
          );
          const usedCount = modules.filter((module) => SITE_V3_MODULE_DESCRIPTORS[module.module_code].category === category.key).length;
          return (
            <button
              className="site-v3-category-card"
              key={category.key}
              onClick={() => onNavigate({ kind: "moduleCategory", category: category.key })}
              type="button"
            >
              <span>{category.label}</span>
              <strong>{categoryModules.length} module types</strong>
              <small>{usedCount} mounted on current page</small>
              <p>{category.description}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function SiteV3ModuleCategoryScreen({
  category,
  modules,
  onAddModule,
  onNavigate,
}: {
  category: SiteV3ModuleCategory;
  modules: SiteV3AdminModule[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  const categoryConfig = SITE_V3_MODULE_CATEGORIES.find((entry) => entry.key === category);
  const categoryModules = Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
    (descriptor) => descriptor.category === category,
  );
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Modules</span>
          <h3>{categoryConfig?.label ?? category}</h3>
          <p>{categoryConfig?.description}</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "modules" })}>
          Back to categories
        </button>
      </div>
      <div className="site-v3-module-type-list">
        {categoryModules.map((descriptor) => {
          const count = modules.filter((module) => module.module_code === descriptor.moduleCode).length;
          return (
            <article className="site-v3-module-type-card" key={descriptor.moduleCode}>
              <div>
                <span className="site-v3-module-code">{descriptor.moduleCode}</span>
                <h4>{descriptor.label}</h4>
                <p>{descriptor.humanHint}</p>
                <small>{count} mounted on current page</small>
              </div>
              <div className="site-v3-module-actions">
                <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "moduleType", moduleCode: descriptor.moduleCode })}>
                  Open detail
                </button>
                <button className="button" type="button" onClick={() => onAddModule(descriptor.moduleCode)}>
                  Add to page
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function SiteV3ModuleTypeDetailScreen({
  moduleCode,
  modules,
  onAddModule,
  onNavigate,
}: {
  moduleCode: SiteV3ModuleCode;
  modules: SiteV3AdminModule[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  const descriptor = SITE_V3_MODULE_DESCRIPTORS[moduleCode];
  const count = modules.filter((module) => module.module_code === moduleCode).length;
  const groupedFields = groupModuleFields(descriptor.fields);
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">{getModuleCategoryLabel(descriptor.category)}</span>
          <h3>{descriptor.label}</h3>
          <p>{descriptor.description}</p>
        </div>
        <div className="site-v3-command-actions">
          <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "moduleCategory", category: descriptor.category })}>
            Back
          </button>
          <button className="button" type="button" onClick={() => onAddModule(moduleCode)}>
            Add to page
          </button>
        </div>
      </div>
      <div className="site-v3-module-detail-summary is-full-page">
        <span className="site-v3-module-code">{moduleCode}</span>
        <span className="site-v3-module-category">{getModuleCategoryLabel(descriptor.category)}</span>
        <p>{descriptor.humanHint}</p>
        <small>Schema v{descriptor.schemaVersion}. {count} mounted on current page.</small>
      </div>
      <div className="site-v3-fieldset site-v3-field-wide">
        <strong>Editable fields</strong>
        <div className="site-v3-module-field-groups">
          {groupedFields.map(({ fields, group, meta }) => (
            <section className="site-v3-module-field-group" key={group}>
              <div className="site-v3-module-field-group-heading">
                <strong>{meta.label}</strong>
                <small>{meta.description}</small>
              </div>
              <div className="site-v3-module-field-list">
                {fields.map((field) => (
                  <article key={field.key}>
                    <strong>{field.label}{field.required ? " *" : ""}</strong>
                    <span>{field.type}</span>
                    <p>{field.help}</p>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </section>
  );
}

function SiteV3ModuleInstanceScreen({
  assetsStatus,
  module,
  moduleIndex,
  moduleCount,
  siteAssets,
  titleOptions,
  onNavigate,
  onUpdateModule,
  onUpdateModuleConfig,
}: {
  assetsStatus: "idle" | "loading" | "error";
  module: SiteV3AdminModule | null;
  moduleIndex: number;
  moduleCount: number;
  siteAssets: SiteV3SiteAsset[];
  titleOptions: SiteV3TitleOption[];
  onNavigate: (view: SiteV3AdminView) => void;
  onUpdateModule: (index: number, patch: Partial<SiteV3AdminModule>) => void;
  onUpdateModuleConfig: (index: number, key: string, value: unknown) => void;
}) {
  if (module === null) {
    return (
      <section className="admin-card site-v3-cms-screen">
        <div className="site-v3-screen-heading">
          <div>
            <span className="site-v3-screen-kicker">Module instance</span>
            <h3>No module selected</h3>
            <p>Open Composition and choose a mounted module.</p>
          </div>
          <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "composition" })}>
            Open composition
          </button>
        </div>
      </section>
    );
  }

  const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
  const groupedFields = groupModuleFields(descriptor.fields);
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Module instance</span>
          <h3>{descriptor.label}</h3>
          <p>{descriptor.humanHint}</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "composition" })}>
          Back to composition
        </button>
      </div>
      <div className="site-v3-module-detail-summary is-full-page">
        <span className="site-v3-module-code">{module.module_code}</span>
        <span className="site-v3-module-category">{getModuleCategoryLabel(descriptor.category)}</span>
        <small>Module {moduleIndex + 1} of {moduleCount}. These settings control this single mounted block.</small>
      </div>
      <div className="site-v3-module-meta">
        <label className="site-v3-field">
          <span>Slot / role</span>
          <select value={module.slot_key} onChange={(event) => onUpdateModule(moduleIndex, { slot_key: event.target.value })}>
            {descriptor.slotKeys.map((slotKey) => (
              <option key={slotKey} value={slotKey}>
                {slotKey}
              </option>
            ))}
          </select>
        </label>
        <div className="site-v3-module-order">
          <span>Position</span>
          <strong>{moduleIndex + 1}</strong>
        </div>
      </div>
      <div className="site-v3-module-field-groups is-editor">
        {groupedFields.map(({ fields, group, meta }) => (
          <section className="site-v3-module-field-group" key={group}>
            <div className="site-v3-module-field-group-heading">
              <strong>{meta.label}</strong>
              <small>{meta.description}</small>
            </div>
            <div className="site-v3-module-fields is-full-page">
              {fields.map((field) => (
                <ModuleField
                  assetsStatus={assetsStatus}
                  key={field.key}
                  field={field}
                  module={module}
                  siteAssets={siteAssets}
                  titleOptions={titleOptions}
                  onChange={(value) => onUpdateModuleConfig(moduleIndex, field.key, value)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

function isSameView(left: SiteV3AdminView, right: SiteV3AdminView): boolean {
  if (left.kind !== right.kind) {
    return false;
  }
  if (left.kind === "moduleCategory" && right.kind === "moduleCategory") {
    return left.category === right.category;
  }
  if (left.kind === "moduleType" && right.kind === "moduleType") {
    return left.moduleCode === right.moduleCode;
  }
  if (left.kind === "moduleInstance" && right.kind === "moduleInstance") {
    return left.moduleIndex === right.moduleIndex;
  }
  return true;
}

function groupModuleFields(fields: SiteV3ModuleFieldDescriptor[]): Array<{
  fields: SiteV3ModuleFieldDescriptor[];
  group: SiteV3FieldGroup;
  meta: { label: string; description: string };
}> {
  return SITE_V3_FIELD_GROUP_ORDER.map((group) => ({
    fields: fields.filter((field) => getFieldGroup(field) === group),
    group,
    meta: SITE_V3_FIELD_GROUP_META[group],
  })).filter((entry) => entry.fields.length > 0);
}

function getFieldGroup(field: SiteV3ModuleFieldDescriptor): SiteV3FieldGroup {
  if (field.group) {
    return field.group;
  }
  if (field.type === "asset_ref") {
    return "assets";
  }
  if (field.type === "title_code" || field.type === "title_code_list") {
    return "catalog";
  }
  if (field.type === "html") {
    return "rules";
  }
  if (field.key.includes("cta") || field.key.includes("link") || field.type === "nav_items") {
    return "links";
  }
  return "content";
}

function ModuleField({
  assetsStatus,
  field,
  module,
  siteAssets,
  titleOptions,
  onChange,
}: {
  assetsStatus: "idle" | "loading" | "error";
  field: SiteV3ModuleFieldDescriptor;
  module: SiteV3AdminModule;
  siteAssets: SiteV3SiteAsset[];
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
    const selectedSet = new Set(selected);
    const titlesByCode = new Map(titleOptions.map((title) => [title.title_code, title]));
    const selectedItems = selected.map((titleCode) => ({
      titleCode,
      title: titlesByCode.get(titleCode) ?? null,
    }));
    const maxItems = field.maxItems ?? Number.POSITIVE_INFINITY;

    function updateSelected(titleCode: string, checked: boolean) {
      if (checked) {
        if (selectedSet.has(titleCode) || selected.length >= maxItems) {
          return;
        }
        onChange([...selected, titleCode]);
        return;
      }
      onChange(selected.filter((entry) => entry !== titleCode));
    }

    function moveSelected(titleCode: string, delta: number) {
      const currentIndex = selected.indexOf(titleCode);
      const nextIndex = currentIndex + delta;
      if (currentIndex < 0 || nextIndex < 0 || nextIndex >= selected.length) {
        return;
      }
      const next = [...selected];
      const [item] = next.splice(currentIndex, 1);
      next.splice(nextIndex, 0, item);
      onChange(next);
    }

    return (
      <fieldset className="site-v3-fieldset site-v3-field-wide">
        <legend>{field.label}{field.required ? " *" : ""}</legend>
        <p>{field.help}</p>
        <div className="site-v3-game-picker">
          <section className="site-v3-game-selection" aria-label="Selected game icon modules">
            <div className="site-v3-game-picker-heading">
              <span>Selected game icons</span>
              <strong>{selected.length}{Number.isFinite(maxItems) ? `/${maxItems}` : ""}</strong>
            </div>
            {selectedItems.length > 0 ? (
              <ol className="site-v3-game-selection-list">
                {selectedItems.map(({ titleCode, title }, index) => (
                  <li className="site-v3-game-selected-row" key={titleCode}>
                    <span className="site-v3-module-order-index">{index + 1}</span>
                    <span>
                      <strong>{title?.display_name ?? titleCode}</strong>
                      <small>{titleCode}{title ? ` / ${formatEngineLabel(title.engine_code)} / ${formatTitlePublication(title)}` : " / unavailable in catalog"}</small>
                    </span>
                    <div className="site-v3-game-selected-actions">
                      <button className="button-secondary" type="button" onClick={() => moveSelected(titleCode, -1)} disabled={index === 0}>
                        Up
                      </button>
                      <button className="button-secondary" type="button" onClick={() => moveSelected(titleCode, 1)} disabled={index === selectedItems.length - 1}>
                        Down
                      </button>
                      <button className="button-secondary danger" type="button" onClick={() => updateSelected(titleCode, false)}>
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="empty-state">No game icons selected. Add games from the grouped library below.</p>
            )}
          </section>

          <section className="site-v3-game-library" aria-label="Game icon library">
            <div className="site-v3-game-picker-heading">
              <span>Library by engine</span>
              <strong>{titleOptions.length} titles</strong>
            </div>
            {groupTitlesByEngine(titleOptions).map((group) => (
              <section className="site-v3-game-library-group" key={group.engineCode}>
                <div className="site-v3-game-library-heading">
                  <strong>{formatEngineLabel(group.engineCode)}</strong>
                  <small>{group.titles.length} titles</small>
                </div>
                <div className="site-v3-game-option-grid">
                  {group.titles.map((title) => {
                    const checked = selectedSet.has(title.title_code);
                    return (
                      <label className={`site-v3-game-option ${checked ? "is-selected" : ""}`} key={title.title_code}>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={!checked && selected.length >= maxItems}
                          onChange={(event) => updateSelected(title.title_code, event.target.checked)}
                        />
                        <span>
                          <strong>{title.display_name}</strong>
                          <small>{title.title_code} / {formatTitlePublication(title)}</small>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </section>
            ))}
            {titleOptions.length === 0 ? <span className="empty-state">No title options available.</span> : null}
          </section>
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
    const selectedAsset = siteAssets.find(
      (asset) => asset.id === assetRef.asset_id || asset.public_url === assetRef.public_url,
    );
    return (
      <div className="site-v3-fieldset site-v3-field-wide">
        <strong>{field.label}</strong>
        <p>{field.help}</p>
        <div className="site-v3-asset-picker" aria-label={`${field.label} asset picker`}>
          <div className="site-v3-asset-picker-heading">
            <span>{assetsStatus === "loading" ? "Loading assets..." : `${siteAssets.length} banners available`}</span>
            {selectedAsset ? <strong>{formatSiteAssetLabel(selectedAsset)} selected</strong> : <strong>No asset selected</strong>}
          </div>
          {assetsStatus === "error" ? (
            <p className="site-v3-message is-error">Assets are unavailable right now. You can still use the manual Public URL field.</p>
          ) : null}
          {siteAssets.length > 0 ? (
            <div className="site-v3-asset-picker-grid">
              {siteAssets.map((asset) => {
                const selected = selectedAsset?.id === asset.id;
                return (
                  <button
                    aria-label={`Use ${formatSiteAssetLabel(asset)}`}
                    aria-pressed={selected}
                    className={`site-v3-asset-option ${selected ? "is-selected" : ""}`}
                    key={asset.id}
                    onClick={() =>
                      onChange({
                        asset_id: asset.id,
                        asset_kind: asset.asset_kind,
                        public_url: asset.public_url,
                      })
                    }
                    type="button"
                  >
                    <img alt="" src={resolveSiteAssetUrl(asset.public_url)} />
                    <span>{formatSiteAssetLabel(asset)}</span>
                    <small>{formatSiteAssetMeta(asset)}</small>
                  </button>
                );
              })}
            </div>
          ) : assetsStatus === "idle" ? (
            <p className="site-v3-message">No banner assets uploaded yet. Upload one in the V1 Site home media area, then return here.</p>
          ) : null}
          {selectedAsset ? (
            <button className="button-secondary" type="button" onClick={() => onChange({})}>
              Clear selected asset
            </button>
          ) : null}
        </div>
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
    const leftPinned = pinnedSlotOrder(left.slot_key);
    const rightPinned = pinnedSlotOrder(right.slot_key);
    if (leftPinned !== rightPinned) {
      return leftPinned - rightPinned;
    }
    if (left.sort_order !== right.sort_order) {
      return left.sort_order - right.sort_order;
    }
    return left.slot_key.localeCompare(right.slot_key);
  });
}

function pinnedSlotOrder(slotKey: string): number {
  if (slotKey === "header") {
    return 0;
  }
  if (slotKey === "footer") {
    return 100;
  }
  return 50;
}

function normalizeModuleSortOrder(modules: SiteV3AdminModule[]): SiteV3AdminModule[] {
  return modules.map((module, index) => ({ ...module, sort_order: index }));
}

function structuredCloneConfig(config: SiteV3ModuleConfig): SiteV3ModuleConfig {
  return JSON.parse(JSON.stringify(config)) as SiteV3ModuleConfig;
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

function resolveSiteAssetUrl(assetUrl: string): string {
  if (!assetUrl.startsWith("/static/sites/")) {
    return assetUrl;
  }
  const apiBase = new URL(API_BASE_URL);
  return `${apiBase.origin}${assetUrl}`;
}

function formatSiteAssetLabel(asset: SiteV3SiteAsset): string {
  return `Banner ${asset.checksum_sha256.slice(0, 8)}`;
}

function formatSiteAssetMeta(asset: SiteV3SiteAsset): string {
  return `${asset.mime} - ${formatBytes(asset.byte_size)} - ${formatShortDate(asset.created_at)}`;
}

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "0 KB";
  }
  if (value < 1024 * 1024) {
    return `${Math.ceil(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatShortDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("en-US", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });
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

function groupTitlesByEngine(titleOptions: SiteV3TitleOption[]): Array<{ engineCode: string; titles: SiteV3TitleOption[] }> {
  const groups = new Map<string, SiteV3TitleOption[]>();
  titleOptions.forEach((title) => {
    const engineCode = title.engine_code || "unknown";
    groups.set(engineCode, [...(groups.get(engineCode) ?? []), title]);
  });

  return Array.from(groups.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([engineCode, titles]) => ({
      engineCode,
      titles: [...titles].sort((left, right) => left.display_name.localeCompare(right.display_name)),
    }));
}

function formatEngineLabel(engineCode: string): string {
  if (engineCode === "hi_lo" || engineCode === "hi-lo") {
    return "HI-LO";
  }
  if (engineCode === "boxe") {
    return "BOXE";
  }
  if (engineCode === "mines") {
    return "Mines";
  }
  return engineCode.replace(/[_-]/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function formatTitlePublication(title: SiteV3TitleOption): string {
  const publication = title.publication;
  const lobby = publication?.lobby_visibility === "visible" ? "visible" : "hidden";
  const demo = publication?.demo_enabled ? "demo on" : "demo off";
  const real = publication?.real_enabled ? "real on" : "real off";
  return `${lobby}, ${demo}, ${real}`;
}

function previewHeadline(module: SiteV3AdminModule): string {
  const config = module.config_json;
  return toText(config.headline) || toText(config.heading) || toText(config.brand_label) || toText(config.legal_text) || SITE_V3_MODULE_DESCRIPTORS[module.module_code].label;
}

function getMissingRequiredFields(module: SiteV3AdminModule): SiteV3ModuleFieldDescriptor[] {
  const descriptor = SITE_V3_MODULE_DESCRIPTORS[module.module_code];
  return descriptor.fields.filter((field) => field.required && isEmptyConfigValue(module.config_json[field.key]));
}

function isEmptyConfigValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return true;
  }
  if (typeof value === "string") {
    return value.trim().length === 0;
  }
  if (Array.isArray(value)) {
    return value.length === 0;
  }
  if (typeof value === "object") {
    return Object.values(value as Record<string, unknown>).every(isEmptyConfigValue);
  }
  return false;
}

function previewBody(module: SiteV3AdminModule): string {
  const config = module.config_json;
  if (typeof config.html === "string") {
    return config.html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }
  return toText(config.body);
}

function getModuleCategoryLabel(category: string): string {
  return SITE_V3_MODULE_CATEGORIES.find((entry) => entry.key === category)?.label ?? category;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "not published";
  }
  return new Date(value).toLocaleString("en-US", {
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
