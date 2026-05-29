import { API_BASE_URL, ApiRequestError, readErrorMessage } from "@/app/lib/api";
import { SITE_V3_MODULE_CATEGORIES, SITE_V3_MODULE_DESCRIPTORS } from "./site-v3-admin-descriptors";
import {
  type SiteV3AdminModule,
  type SiteV3AdminModulePayload,
  type SiteV3AdminPage,
  type SiteV3AssetRef,
  type SiteV3FieldGroup,
  type SiteV3ModuleConfig,
  type SiteV3ModuleCategory,
  type SiteV3ModuleCode,
  type SiteV3ModuleDescriptor,
  type SiteV3ModuleFieldDescriptor,
  type SiteV3NavItem,
  type SiteV3PageEditorState,
  type SiteV3SiteAsset,
  type SiteV3TitleOption,
  type SiteV3ValidationResult,
} from "./site-v3-admin-types";

export type SiteV3AdminView =
  | { kind: "overview" }
  | { kind: "siteSettings" }
  | { kind: "pages" }
  | { kind: "pageDetail" }
  | { kind: "composition" }
  | { kind: "modules" }
  | { kind: "moduleStudio" }
  | { kind: "moduleCategory"; category: SiteV3ModuleCategory }
  | { kind: "moduleType"; moduleCode: SiteV3ModuleCode }
  | { kind: "moduleInstance"; moduleIndex: number }
  | { kind: "validation" }
  | { kind: "versions" };

export const EMPTY_VALIDATION: SiteV3ValidationResult = {
  status: "unknown",
  issues: [],
};

export const SITE_V3_FIELD_GROUP_ORDER: SiteV3FieldGroup[] = ["content", "catalog", "assets", "links", "rules"];

export const SITE_V3_FIELD_GROUP_META: Record<SiteV3FieldGroup, { label: string; description: string }> = {
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

export type SiteV3ModuleDescriptorMap = Record<string, SiteV3ModuleDescriptor>;

export function isPagePreviewView(view: SiteV3AdminView): boolean {
  return (
    view.kind === "pageDetail"
    || view.kind === "composition"
    || view.kind === "moduleInstance"
    || view.kind === "validation"
  );
}

export function isPageActionBarView(view: SiteV3AdminView): boolean {
  return (
    view.kind === "composition"
    || view.kind === "moduleInstance"
    || view.kind === "validation"
  );
}

export function isSameView(left: SiteV3AdminView, right: SiteV3AdminView): boolean {
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

export function groupModuleFields(fields: SiteV3ModuleFieldDescriptor[]): Array<{
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

export function getFieldGroup(field: SiteV3ModuleFieldDescriptor): SiteV3FieldGroup {
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

export function createEmptyEditorState(pageCode: string, title: string, locale: string): SiteV3PageEditorState {
  return {
    page_code: pageCode,
    locale,
    title,
    modules: [],
  };
}

export function createDefaultConfig(descriptor: SiteV3ModuleDescriptor): SiteV3ModuleConfig {
  const typedDefaults = Object.fromEntries(
    descriptor.fields.map((field) => {
      if (field.type === "title_code_list" || field.type === "nav_items") {
        return [field.key, []];
      }
      if (field.type === "asset_ref") {
        return [field.key, {}];
      }
      if (field.type === "boolean") {
        return [field.key, field.key.startsWith("show_")];
      }
      return [field.key, ""];
    }),
  );
  return {
    ...typedDefaults,
    ...(descriptor.defaultConfig ?? {}),
  };
}

export function buildDraftPayload(editorState: SiteV3PageEditorState, expectedDraftVersion: number | null) {
  return {
    locale: editorState.locale,
    title: editorState.title,
    expected_draft_version: expectedDraftVersion,
    modules: buildModulePayloads(editorState.modules),
  };
}

export function buildModulePayloads(modules: SiteV3AdminModule[]): SiteV3AdminModulePayload[] {
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

export function serializeEditorState(editorState: SiteV3PageEditorState): string {
  return JSON.stringify(stableValue({
    ...editorState,
    page_code: normalizePageCode(editorState.page_code),
    modules: buildModulePayloads(editorState.modules),
  }));
}

export function stableValue(value: unknown): unknown {
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

export function sortModules(modules: SiteV3AdminModule[]): SiteV3AdminModule[] {
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

export function pinnedSlotOrder(slotKey: string): number {
  if (slotKey === "header") {
    return 0;
  }
  if (slotKey === "footer") {
    return 100;
  }
  return 50;
}

export function normalizeModuleSortOrder(modules: SiteV3AdminModule[]): SiteV3AdminModule[] {
  return modules.map((module, index) => ({ ...module, sort_order: index }));
}

export function structuredCloneConfig(config: SiteV3ModuleConfig): SiteV3ModuleConfig {
  return JSON.parse(JSON.stringify(config)) as SiteV3ModuleConfig;
}

export function normalizePageCode(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]/g, "")
    .slice(0, 64);
}

export function createClientId(moduleCode: string): string {
  return `${moduleCode}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function toText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function toAssetRef(value: unknown): SiteV3AssetRef {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as SiteV3AssetRef) : {};
}

export function resolveSiteAssetUrl(assetUrl: string): string {
  if (!assetUrl.startsWith("/static/sites/")) {
    return assetUrl;
  }
  const apiBase = new URL(API_BASE_URL);
  return `${apiBase.origin}${assetUrl}`;
}

export function formatSiteAssetLabel(asset: SiteV3SiteAsset): string {
  return `Banner ${asset.checksum_sha256.slice(0, 8)}`;
}

export function formatSiteAssetMeta(asset: SiteV3SiteAsset): string {
  return `${asset.mime} - ${formatBytes(asset.byte_size)} - ${formatShortDate(asset.created_at)}`;
}

export function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "0 KB";
  }
  if (value < 1024 * 1024) {
    return `${Math.ceil(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatShortDate(value: string): string {
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

export function normalizeNavItems(value: unknown): SiteV3NavItem[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is SiteV3NavItem => Boolean(item) && typeof item === "object")
    .map((item) => ({
      label: toText(item.label),
      ...(item.href ? { href: toText(item.href) } : {}),
      ...(item.title_code ? { title_code: toText(item.title_code) } : {}),
    }));
}

export function cleanNavItems(items: SiteV3NavItem[]): SiteV3NavItem[] {
  return items
    .map((item) => ({
      label: item.label.trim(),
      ...(item.href?.trim() ? { href: item.href.trim() } : {}),
      ...(item.title_code?.trim() ? { title_code: item.title_code.trim() } : {}),
    }))
    .filter((item) => item.label || item.href || item.title_code);
}

export function navTargetPatch(value: string): Pick<SiteV3NavItem, "href" | "title_code"> {
  const target = value.trim();
  if (!target) {
    return { href: "", title_code: "" };
  }
  if (target.startsWith("/") || target.startsWith("http")) {
    return { href: target, title_code: "" };
  }
  return { href: "", title_code: target };
}

export function collectTitleCodes(config: SiteV3ModuleConfig): string[] {
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

export function groupTitlesByEngine(titleOptions: SiteV3TitleOption[]): Array<{ engineCode: string; titles: SiteV3TitleOption[] }> {
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

export function formatEngineLabel(engineCode: string): string {
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

export function formatTitlePublication(title: SiteV3TitleOption): string {
  const publication = title.publication;
  const lobby = publication?.lobby_visibility === "visible" ? "visible" : "hidden";
  const demo = publication?.demo_enabled ? "demo on" : "demo off";
  const real = publication?.real_enabled ? "real on" : "real off";
  return `${lobby}, ${demo}, ${real}`;
}

export function previewHeadline(module: SiteV3AdminModule, descriptors: SiteV3ModuleDescriptorMap = SITE_V3_MODULE_DESCRIPTORS): string {
  const config = module.config_json;
  return (
    toText(config.headline)
    || toText(config.heading)
    || toText(config.brand_label)
    || toText(config.legal_text)
    || descriptors[module.module_code]?.label
    || module.module_code
  );
}

export function getMissingRequiredFields(module: SiteV3AdminModule, descriptors: SiteV3ModuleDescriptorMap = SITE_V3_MODULE_DESCRIPTORS): SiteV3ModuleFieldDescriptor[] {
  const descriptor = descriptors[module.module_code];
  if (!descriptor) {
    return [];
  }
  return descriptor.fields.filter((field) => field.required && isEmptyConfigValue(module.config_json[field.key]));
}

export function isEmptyConfigValue(value: unknown): boolean {
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

export function previewBody(module: SiteV3AdminModule): string {
  const config = module.config_json;
  if (typeof config.html === "string") {
    return config.html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }
  return toText(config.body);
}

export function getModuleCategoryLabel(category: string): string {
  return SITE_V3_MODULE_CATEGORIES.find((entry) => entry.key === category)?.label ?? category;
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "not published";
  }
  return new Date(value).toLocaleString("en-US", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function formatApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    const suffix = [error.code, error.supportId ? `support ${error.supportId}` : null]
      .filter(Boolean)
      .join(" - ");
    return `${fallback} ${error.message}${suffix ? ` (${suffix})` : ""}`;
  }
  return readErrorMessage(error, fallback);
}
