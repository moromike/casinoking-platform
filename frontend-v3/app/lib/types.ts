export type ApiEnvelope<T> =
  | {
      success: true;
      data: T;
    }
  | {
      success: false;
      error?: {
        code?: string;
        message?: string;
        request_id?: string;
        support_id?: string;
      };
    };

export type SiteV3ModuleCode =
  | "global_header"
  | "hero_banner"
  | "game_grid"
  | "game_grid_4x"
  | "featured_game"
  | "promo_band"
  | "rich_text_safe"
  | "global_footer";

export type SiteV3PublicModule = {
  id: string;
  module_code: SiteV3ModuleCode | string;
  schema_version: number;
  slot_key: string;
  sort_order: number;
  config_json: Record<string, unknown>;
  definition_snapshot?: SiteV3CustomDefinitionSnapshot;
};

export type SiteV3CustomDefinitionSnapshot = {
  module_code: string;
  label: string;
  category: "hero" | "catalog" | "promo" | "text_legal" | string;
  renderer_template: "image_banner" | "game_grid" | "editorial_panel" | "rich_text" | "feature_card" | string;
  definition_version: number;
  definition_version_id: string;
  schema_version: number;
  field_schema_json: SiteV3CustomFieldSnapshot[];
  default_config_json?: Record<string, unknown>;
  published_at?: string | null;
};

export type SiteV3CustomFieldSnapshot = {
  key: string;
  label: string;
  type: "asset_ref" | "boolean" | "html" | "string" | "title_code" | "title_code_list" | "url" | string;
  group?: "assets" | "catalog" | "content" | "links" | "rules" | string;
  required?: boolean;
  max_length?: number;
  max_items?: number;
  help?: string;
};

export type SiteV3PublicPageSnapshot = {
  site_code: string;
  page_code: string;
  locale: string;
  title: string;
  published_version?: number;
  draft_version?: number;
  is_preview?: boolean;
  version_id?: string;
  published_at?: string | null;
  modules: SiteV3PublicModule[];
};

export type SiteV3Navigation = {
  site_code: string;
  locale: string;
  status: "ready" | "partial";
  header: SiteV3PublicModule | null;
  footer: SiteV3PublicModule | null;
};

export type GameLibraryTitle = {
  title_code: string;
  engine_code: string;
  engine_display_name: string;
  display_name: string;
  catalog_display_name: string;
  description: string | null;
  demo_enabled: boolean;
  real_enabled: boolean;
  featured: boolean;
  position: number;
  game_card_asset: {
    id: string;
    asset_kind: "game_card";
    public_url: string;
    mime: string;
    byte_size: number;
    created_at: string;
  } | null;
};

export type GameLibrary = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: GameLibraryTitle[];
};

export type SiteHomeTargetType = "none" | "title_demo" | "title_real" | string;

export type SiteHomeAsset = {
  id: string;
  site_code: string;
  asset_kind: "homepage_banner" | string;
  public_url: string;
  mime: string;
  byte_size: number;
  checksum_sha256: string;
  created_at: string;
  status: "active" | "deleted" | string;
};

export type SiteHomeSlot = {
  id: string;
  site_code: string;
  slot_key: string;
  title: string;
  subtitle: string | null;
  cta_label: string | null;
  cta_target_type: SiteHomeTargetType;
  cta_target_ref: string | null;
  media_asset_id: string | null;
  media_asset: SiteHomeAsset | null;
  sort_order: number;
};

export type SiteHomeResponse = {
  site: GameLibrary["site"] & {
    created_at?: string;
    updated_at?: string;
  };
  slots: SiteHomeSlot[];
};

export type SiteV3LoadResult = {
  page: SiteV3PublicPageSnapshot | null;
  navigation: SiteV3Navigation | null;
  gameLibrary: GameLibraryTitle[];
  homeSlots: SiteHomeSlot[];
  error: string | null;
};
