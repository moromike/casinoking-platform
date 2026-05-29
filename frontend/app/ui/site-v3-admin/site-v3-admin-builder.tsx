"use client";

import { useEffect, useMemo, useState } from "react";

import { apiRequest, readErrorMessage } from "@/app/lib/api";
import {
  buildSiteV3ModuleDescriptors,
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
  type SiteV3ModuleDefinition,
  type SiteV3ModuleDefinitionPayload,
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
  archiveSiteV3ModuleDefinition,
  archiveSiteV3Page,
  createSiteV3ModuleDefinition,
  getSiteV3Page,
  listSiteV3Assets,
  listSiteV3ModuleDefinitions,
  listSiteV3Pages,
  listSiteV3Versions,
  publishSiteV3ModuleDefinition,
  publishSiteV3Page,
  saveSiteV3Draft,
  uploadSiteV3Asset,
  validateSiteV3Draft,
} from "./site-v3-admin-api";
import { SiteV3DraftPreviewPanel } from "./site-v3-draft-preview-panel";
import {
  buildDraftPayload,
  buildModulePayloads,
  createClientId,
  createDefaultConfig,
  createEmptyEditorState,
  EMPTY_VALIDATION,
  formatApiError,
  isPageActionBarView,
  isPagePreviewView,
  normalizeModuleSortOrder,
  normalizePageCode,
  serializeEditorState,
  sortModules,
  structuredCloneConfig,
  type SiteV3AdminView,
} from "./site-v3-admin-helpers";
import { SiteV3AdminNav } from "./screens/site-v3-admin-nav";
import { SiteV3PageActionBar } from "./screens/site-v3-page-action-bar";
import { SiteV3OverviewScreen } from "./screens/site-v3-overview-screen";
import { SiteV3SiteSettingsScreen } from "./screens/site-v3-site-settings-screen";
import { SiteV3PagesScreen } from "./screens/site-v3-pages-screen";
import { SiteV3PageDetailScreen } from "./screens/site-v3-page-detail-screen";
import { SiteV3CompositionScreen } from "./screens/site-v3-composition-screen";
import { SiteV3ModuleLibraryScreen, SiteV3ModuleCategoryScreen, SiteV3ModuleTypeDetailScreen } from "./screens/site-v3-module-library-screen";
import { SiteV3ModuleStudioScreen } from "./screens/site-v3-module-studio-screen";
import { SiteV3ModuleInstanceScreen } from "./screens/site-v3-module-instance-screen";
import { ValidationPanel } from "./screens/site-v3-validation-panel";
import { SiteV3DraftPreview } from "./screens/site-v3-draft-preview";
import { VersionHistory } from "./screens/site-v3-version-history";

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

function mergeSiteAsset(current: SiteV3SiteAsset[], asset: SiteV3SiteAsset): SiteV3SiteAsset[] {
  return [asset, ...current.filter((item) => item.id !== asset.id)];
}

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
  const [moduleDefinitions, setModuleDefinitions] = useState<SiteV3ModuleDefinition[]>([]);
  const [moduleDefinitionsStatus, setModuleDefinitionsStatus] = useState<"idle" | "loading" | "error">("idle");
  const [titleOptions, setTitleOptions] = useState<SiteV3TitleOption[]>([]);
  const [siteAssets, setSiteAssets] = useState<SiteV3SiteAsset[]>([]);
  const [assetsStatus, setAssetsStatus] = useState<"idle" | "loading" | "error">("idle");
  const [localMessage, setLocalMessage] = useState<LocalMessage | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [selectedModuleIndex, setSelectedModuleIndex] = useState<number | null>(null);
  const [currentView, setCurrentView] = useState<SiteV3AdminView>({ kind: "overview" });

  const currentSnapshot = useMemo(() => serializeEditorState(editorState), [editorState]);
  const resolvedModuleDescriptors = useMemo(
    () => buildSiteV3ModuleDescriptors(moduleDefinitions),
    [moduleDefinitions],
  );
  const isDirty = currentSnapshot !== lastSavedSnapshot;
  const validationErrors = validation.issues.filter((issue) => issue.severity === "error");
  const validationWarnings = validation.issues.filter((issue) => issue.severity === "warning");

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void loadPages(undefined, { preserveDirty: false });
    void loadTitleOptions();
    void loadSiteAssets();
    void loadModuleDefinitions();
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

  function confirmDiscardUnsavedChanges(actionLabel: string): boolean {
    return !isDirty || window.confirm(`Unsaved Site V3 changes will be discarded. ${actionLabel}?`);
  }

  async function loadPages(
    preferredPageCode?: string | null,
    options: { preserveDirty?: boolean } = { preserveDirty: true },
  ) {
    if (options.preserveDirty !== false && !confirmDiscardUnsavedChanges("Continue")) {
      return;
    }
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

      const nextPageCode =
        preferredPageCode === null
          ? data.pages[0]?.page_code
          : preferredPageCode ?? pageMeta?.page_code ?? data.pages[0]?.page_code;
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

  async function handleUploadSiteAsset(file: File): Promise<SiteV3SiteAsset> {
    const uploadedAsset = await uploadSiteV3Asset({
      accessToken,
      siteCode: SITE_V3_SITE_CODE,
      file,
      assetKind: "homepage_banner",
    });
    setSiteAssets((current) => mergeSiteAsset(current, uploadedAsset));
    setAssetsStatus("idle");
    setLocalMessage({
      kind: "success",
      text: "Banner uploaded and added to the Site V3 asset picker.",
    });
    return uploadedAsset;
  }

  async function loadPage(pageCode: string, options: { preserveDirty: boolean } = { preserveDirty: true }): Promise<boolean> {
    if (options.preserveDirty && !confirmDiscardUnsavedChanges("Load saved draft")) {
      return false;
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
      return true;
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: readErrorMessage(error, "Site V3 page loading failed."),
      });
      return false;
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
    const descriptor = resolvedModuleDescriptors[moduleCode];
    if (!descriptor) {
      setLocalMessage({ kind: "error", text: `Module type ${moduleCode} is unavailable.` });
      return editorState.modules.length;
    }
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
    const descriptor = resolvedModuleDescriptors[module.module_code];
    if (!window.confirm(`Remove ${descriptor?.label ?? module.module_code}?`)) {
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
    setCurrentView({ kind: "composition" });
    setValidation(EMPTY_VALIDATION);
    setLocalMessage({
      kind: "info",
      text: "Module duplicated in Composition. Open it only if you need to edit its settings.",
    });
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
      await loadPages(data.page.page_code, { preserveDirty: false });
      if (currentView.kind === "moduleInstance") {
        setCurrentView({ kind: "composition" });
      }
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
      setCurrentView({ kind: "validation" });
      setLocalMessage({
        kind: result.status === "valid" ? "success" : "error",
        text:
          result.status === "valid"
            ? "Validation green. This draft can be published after it is saved."
            : "Validation found publish-stopping issues. Fix them before publishing.",
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
    if (validation.status !== "valid" || validationErrors.length > 0) {
      setLocalMessage({ kind: "error", text: "Run validation and fix any issues before publishing." });
      setCurrentView({ kind: "validation" });
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
      await loadPages(data.page.page_code, { preserveDirty: false });
      if (currentView.kind === "moduleInstance") {
        setCurrentView({ kind: "composition" });
      }
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
      setCurrentView({ kind: "pages" });
      await loadPages(null, { preserveDirty: false });
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
    const loaded = await loadPage(pageCode);
    if (loaded) {
      setCurrentView({ kind: "pageDetail" });
    }
  }

  async function loadModuleDefinitions() {
    setModuleDefinitionsStatus("loading");
    try {
      const data = await listSiteV3ModuleDefinitions({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        status: "all",
      });
      setModuleDefinitions(data.definitions);
      setModuleDefinitionsStatus("idle");
    } catch {
      setModuleDefinitions([]);
      setModuleDefinitionsStatus("error");
    }
  }

  function openNewPage() {
    if (!confirmDiscardUnsavedChanges("Create a new page")) {
      return;
    }
    startNewPage("home", "Homepage");
    setCurrentView({ kind: "pageDetail" });
  }

  function changeLocale(nextLocale: string) {
    if (!confirmDiscardUnsavedChanges("Change locale")) {
      return;
    }
    setLocale(nextLocale);
  }

  function changeStatusFilter(nextStatusFilter: SiteV3ListStatusFilter) {
    if (!confirmDiscardUnsavedChanges("Change status filter")) {
      return;
    }
    setStatusFilter(nextStatusFilter);
  }

  function addModuleAndShowComposition(moduleCode: SiteV3ModuleCode) {
    const descriptor = resolvedModuleDescriptors[moduleCode];
    addModule(moduleCode);
    setCurrentView({ kind: "composition" });
    setLocalMessage({
      kind: "info",
      text: `${descriptor?.label ?? moduleCode} mounted in Composition. Open the module instance from its row only when you need to edit it.`,
    });
  }

  function openModuleInstance(index: number) {
    setSelectedModuleIndex(index);
    setCurrentView({ kind: "moduleInstance", moduleIndex: index });
  }

  function addModuleFromComposition(moduleCode: SiteV3ModuleCode) {
    const descriptor = resolvedModuleDescriptors[moduleCode];
    addModule(moduleCode);
    setCurrentView({ kind: "composition" });
    setLocalMessage({
      kind: "info",
      text: `${descriptor?.label ?? moduleCode} added. Save draft, then refresh preview to inspect it.`,
    });
  }

  async function handleCreateModuleDefinition(payload: SiteV3ModuleDefinitionPayload): Promise<boolean> {
    setBusyAction("module-definition-create");
    setLocalMessage(null);
    try {
      const data = await createSiteV3ModuleDefinition({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        payload,
      });
      setModuleDefinitions((current) => [data.definition, ...current.filter((definition) => definition.id !== data.definition.id)]);
      setLocalMessage({
        kind: "success",
        text: `${data.definition.label} definition created as draft.`,
      });
      return true;
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Create module definition failed."),
      });
      return false;
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublishModuleDefinition(moduleCode: string): Promise<void> {
    setBusyAction(`module-definition-publish:${moduleCode}`);
    setLocalMessage(null);
    try {
      const data = await publishSiteV3ModuleDefinition({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        moduleCode,
      });
      setModuleDefinitions((current) => current.map((definition) => definition.module_code === moduleCode ? data.definition : definition));
      setLocalMessage({
        kind: "success",
        text: `${data.definition.label} published as definition version ${data.definition.published_version}.`,
      });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Publish module definition failed."),
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleArchiveModuleDefinition(moduleCode: string): Promise<void> {
    if (!window.confirm(`Archive ${moduleCode}?`)) {
      return;
    }
    setBusyAction(`module-definition-archive:${moduleCode}`);
    setLocalMessage(null);
    try {
      const data = await archiveSiteV3ModuleDefinition({
        accessToken,
        siteCode: SITE_V3_SITE_CODE,
        moduleCode,
      });
      setModuleDefinitions((current) => current.map((definition) => definition.module_code === moduleCode ? data.definition : definition));
      setLocalMessage({
        kind: "success",
        text: `${data.definition.label} archived.`,
      });
    } catch (error) {
      setLocalMessage({
        kind: "error",
        text: formatApiError(error, "Archive module definition failed."),
      });
    } finally {
      setBusyAction(null);
    }
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
              validationStatus={validation.status}
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
              onLocaleChange={changeLocale}
              onNewPage={openNewPage}
              onOpenPage={(pageCode) => void openPageDetail(pageCode)}
              onStatusFilterChange={changeStatusFilter}
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
              descriptors={resolvedModuleDescriptors}
              modules={editorState.modules}
              pageCode={editorState.page_code}
              pageTitle={editorState.title}
              onDuplicateModule={duplicateModule}
              onAddModule={addModuleFromComposition}
              onMoveModule={moveModule}
              onOpenModule={openModuleInstance}
              onRemoveModule={removeModule}
            />
          ) : null}

          {currentView.kind === "modules" ? (
            <SiteV3ModuleLibraryScreen
              descriptors={resolvedModuleDescriptors}
              modules={editorState.modules}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleCategory" ? (
            <SiteV3ModuleCategoryScreen
              category={currentView.category}
              descriptors={resolvedModuleDescriptors}
              modules={editorState.modules}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleType" ? (
            <SiteV3ModuleTypeDetailScreen
              descriptors={resolvedModuleDescriptors}
              moduleCode={currentView.moduleCode}
              modules={editorState.modules}
              onAddModule={addModuleAndShowComposition}
              onNavigate={setCurrentView}
            />
          ) : null}

          {currentView.kind === "moduleStudio" ? (
            <SiteV3ModuleStudioScreen
              busyAction={busyAction}
              moduleDefinitions={moduleDefinitions}
              moduleDefinitionsStatus={moduleDefinitionsStatus}
              onArchiveDefinition={handleArchiveModuleDefinition}
              onCreateDefinition={handleCreateModuleDefinition}
              onPublishDefinition={handlePublishModuleDefinition}
              onReloadDefinitions={loadModuleDefinitions}
            />
          ) : null}

          {currentView.kind === "moduleInstance" ? (
            <SiteV3ModuleInstanceScreen
              assetsStatus={assetsStatus}
              descriptors={resolvedModuleDescriptors}
              module={editorState.modules[currentView.moduleIndex] ?? null}
              moduleIndex={currentView.moduleIndex}
              moduleCount={editorState.modules.length}
              siteAssets={siteAssets}
              titleOptions={titleOptions}
              onNavigate={setCurrentView}
              onUploadSiteAsset={handleUploadSiteAsset}
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
              <SiteV3DraftPreview descriptors={resolvedModuleDescriptors} modules={editorState.modules} pageTitle={editorState.title} titleOptions={titleOptions} />
              <VersionHistory versions={versions} />
            </div>
          ) : null}

          {isPagePreviewView(currentView) ? (
            <SiteV3DraftPreviewPanel
              accessToken={accessToken}
              draftVersion={pageMeta?.draft_version ?? 0}
              isDirty={isDirty}
              locale={locale}
              pageCode={editorState.page_code}
              siteCode={SITE_V3_SITE_CODE}
            />
          ) : null}
        </main>
      </div>
    </div>
  );
}
