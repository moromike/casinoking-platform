"use client";

export const SITE_V3_SITE_CODE = "casinoking";
export const SITE_V3_DEFAULT_LOCALE = "it";
export const SITE_V3_PUBLIC_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export type SiteV3PageStatus = "draft" | "published" | "archived";
export type SiteV3ListStatusFilter = SiteV3PageStatus | "all";
export type SiteV3ValidationStatus = "valid" | "invalid" | "unknown";
export type SiteV3ValidationSeverity = "error" | "warning";

export type SiteV3AdminPage = {
  id: string;
  site_code: string;
  page_code: string;
  locale: string;
  title: string;
  status: SiteV3PageStatus;
  draft_version: number;
  published_version: number | null;
  created_by: string;
  updated_by: string;
  archived_by: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
};

export type SiteV3ModuleConfig = Record<string, unknown>;

export type SiteV3AdminModule = {
  id?: string;
  client_id?: string;
  page_id?: string;
  module_code: SiteV3ModuleCode;
  schema_version: number;
  slot_key: string;
  sort_order: number;
  config_json: SiteV3ModuleConfig;
  created_by?: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
};

export type SiteV3Version = {
  id: string;
  page_id: string;
  version: number;
  status: SiteV3PageStatus;
  validation_json: SiteV3ValidationResult;
  created_by: string;
  published_by: string | null;
  created_at: string;
  published_at: string | null;
  snapshot_json?: unknown;
};

export type SiteV3PublishedSummary = SiteV3Version | null;

export type SiteV3PagesResponse = {
  site_code: string;
  locale: string;
  pages: SiteV3AdminPage[];
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
};

export type SiteV3PageResponse = {
  page: SiteV3AdminPage;
  modules: SiteV3AdminModule[];
  published?: SiteV3PublishedSummary;
};

export type SiteV3VersionsResponse = {
  page: SiteV3AdminPage;
  versions: SiteV3Version[];
};

export type SiteV3PublishResponse = {
  page: SiteV3AdminPage;
  version: SiteV3Version;
};

export type SiteV3ValidationIssue = {
  severity: SiteV3ValidationSeverity;
  module_id: string | null;
  field: string;
  code: string;
  message: string;
};

export type SiteV3ValidationResult = {
  status: SiteV3ValidationStatus;
  issues: SiteV3ValidationIssue[];
};

export type SiteV3DraftPayload = {
  locale: string;
  title: string;
  expected_draft_version?: number | null;
  modules: SiteV3AdminModulePayload[];
};

export type SiteV3ValidatePayload = {
  locale: string;
  title: string;
  modules: SiteV3AdminModulePayload[];
};

export type SiteV3AdminModulePayload = {
  id?: string | null;
  client_id?: string | null;
  module_code: SiteV3ModuleCode;
  schema_version: number;
  slot_key: string;
  sort_order: number;
  config_json: SiteV3ModuleConfig;
};

export type SiteV3PublishPayload = {
  locale: string;
  expected_draft_version?: number | null;
};

export type SiteV3ArchivePayload = {
  locale: string;
};

export type SiteV3PageEditorState = {
  page_code: string;
  locale: string;
  title: string;
  modules: SiteV3AdminModule[];
};

export type SiteV3FieldType =
  | "asset_ref"
  | "boolean"
  | "html"
  | "nav_items"
  | "string"
  | "title_code"
  | "title_code_list";

export type SiteV3FieldGroup = "assets" | "catalog" | "content" | "links" | "rules";

export type SiteV3ModuleFieldDescriptor = {
  key: string;
  label: string;
  type: SiteV3FieldType;
  group?: SiteV3FieldGroup;
  required?: boolean;
  maxLength?: number;
  maxItems?: number;
  help: string;
};

export type SiteV3ModuleDescriptor = {
  moduleCode: SiteV3ModuleCode;
  label: string;
  category: SiteV3ModuleCategory;
  description: string;
  humanHint: string;
  schemaVersion: number;
  slotKeys: string[];
  fields: SiteV3ModuleFieldDescriptor[];
};

export type SiteV3ModuleCategory = "structure" | "hero" | "catalog" | "promo" | "text_legal";

export type SiteV3ModuleCode =
  | "global_header"
  | "hero_banner"
  | "game_grid"
  | "featured_game"
  | "promo_band"
  | "rich_text_safe"
  | "global_footer";

export type SiteV3TitleOption = {
  title_code: string;
  display_name: string;
  engine_code: string;
  is_master?: boolean;
  is_archived?: boolean;
  publication?: {
    lobby_visibility?: string;
    demo_enabled?: boolean;
    real_enabled?: boolean;
  };
};

export type SiteV3SiteAsset = {
  id: string;
  site_code: string;
  asset_kind: "homepage_banner" | string;
  file_path: string;
  public_url: string;
  mime: string;
  byte_size: number;
  checksum_sha256: string;
  uploaded_by_admin_user_id: string | null;
  created_at: string;
  status: "active" | "deleted" | string;
};

export type SiteV3AssetRef = {
  asset_id?: string;
  asset_kind?: string;
  public_url?: string;
};

export type SiteV3NavItem = {
  label: string;
  href?: string;
  title_code?: string;
};
