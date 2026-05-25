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
};

export type SiteV3PublicPageSnapshot = {
  site_code: string;
  page_code: string;
  locale: string;
  title: string;
  published_version: number;
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

export type SiteV3LoadResult = {
  page: SiteV3PublicPageSnapshot | null;
  navigation: SiteV3Navigation | null;
  gameLibrary: GameLibraryTitle[];
  error: string | null;
};
