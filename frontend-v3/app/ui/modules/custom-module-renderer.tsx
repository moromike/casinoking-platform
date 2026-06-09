import type {
  GameLibraryTitle,
  SiteV3CustomDefinitionSnapshot,
  SiteV3CustomFieldSnapshot,
  SiteV3PublicModule,
  SiteV3PublicPageSnapshot,
} from "../../lib/types";
import {
  readBoolean,
  readString,
  readStringArray,
  resolveAssetRef,
  resolveLink,
} from "../site-v3-render-helpers";
import { AccountAwareLink } from "./account-aware-link";
import { FeaturedGame } from "./featured-game";
import { GameGrid } from "./game-grid";
import { RichTextSafe } from "./rich-text-safe";

type CustomModuleRendererProps = {
  gameLibrary: GameLibraryTitle[];
  games: Map<string, GameLibraryTitle>;
  module: SiteV3PublicModule;
  page: SiteV3PublicPageSnapshot;
};

type CustomCta = {
  href: string;
  label: string;
};

export function CustomModuleRenderer({
  gameLibrary,
  games,
  module,
  page,
}: CustomModuleRendererProps) {
  const definition = module.definition_snapshot;
  if (!isUsableDefinition(definition, module, page)) {
    return null;
  }

  switch (definition.renderer_template) {
    case "image_banner":
      return renderImageBanner(definition, module);
    case "game_grid":
      return renderGameGrid(definition, module, gameLibrary, games);
    case "editorial_panel":
      return renderEditorialPanel(definition, module);
    case "rich_text":
      return renderRichText(definition, module);
    case "feature_card":
      return renderFeatureCard(definition, module, games);
    default:
      warnCustomRenderer(
        `Unsupported custom Site V3 renderer template on ${page.page_code}: ${definition.renderer_template}`,
      );
      return null;
  }
}

function isUsableDefinition(
  definition: SiteV3CustomDefinitionSnapshot | undefined,
  module: SiteV3PublicModule,
  page: SiteV3PublicPageSnapshot,
): definition is SiteV3CustomDefinitionSnapshot {
  if (!definition) {
    warnCustomRenderer(`Custom Site V3 module without definition_snapshot on ${page.page_code}: ${module.module_code}`);
    return false;
  }
  if (definition.module_code !== module.module_code) {
    warnCustomRenderer(
      `Custom Site V3 definition_snapshot mismatch on ${page.page_code}: ${module.module_code}`,
    );
    return false;
  }
  if (!Array.isArray(definition.field_schema_json)) {
    warnCustomRenderer(`Custom Site V3 definition_snapshot has no fields on ${page.page_code}: ${module.module_code}`);
    return false;
  }
  return true;
}

function renderImageBanner(
  definition: SiteV3CustomDefinitionSnapshot,
  module: SiteV3PublicModule,
) {
  const mediaUrl = firstAssetUrl(definition.field_schema_json, module.config_json);
  if (!mediaUrl) {
    return null;
  }
  const cta = firstCta(definition.field_schema_json, module.config_json);
  return (
    <section className="site-v3-custom-image-banner">
      <img alt="" src={mediaUrl} />
      {cta ? (
        <AccountAwareLink className="site-v3-primary-link site-v3-custom-image-cta" href={cta.href} label={cta.label} />
      ) : null}
    </section>
  );
}

function renderGameGrid(
  definition: SiteV3CustomDefinitionSnapshot,
  module: SiteV3PublicModule,
  gameLibrary: GameLibraryTitle[],
  games: Map<string, GameLibraryTitle>,
) {
  const titleCodes = firstTitleCodeList(definition.field_schema_json, module.config_json);
  const heading = firstText(definition.field_schema_json, module.config_json, ["heading", "headline", "title"]);
  return (
    <GameGrid
      games={games}
      module={{
        ...module,
        module_code: "game_grid",
        config_json: {
          ...module.config_json,
          ...(heading ? { heading } : {}),
          title_codes: titleCodes,
        },
      }}
      titles={gameLibrary}
    />
  );
}

function renderEditorialPanel(
  definition: SiteV3CustomDefinitionSnapshot,
  module: SiteV3PublicModule,
  variant: "standard" | "feature" = "standard",
) {
  const mediaUrl = firstAssetUrl(definition.field_schema_json, module.config_json);
  const heading = firstText(definition.field_schema_json, module.config_json, ["headline", "heading", "title"]);
  const bodyHtml = firstHtml(definition.field_schema_json, module.config_json);
  const bodyText = bodyHtml
    ? ""
    : firstText(definition.field_schema_json, module.config_json, ["body", "subtitle", "summary", "text"]);
  const cta = firstCta(definition.field_schema_json, module.config_json);

  if (!mediaUrl && !heading && !bodyHtml && !bodyText && !cta) {
    return null;
  }

  return (
    <section
      className={`site-v3-custom-editorial ${mediaUrl ? "has-media" : "is-text-only"} ${variant === "feature" ? "is-feature" : ""}`}
    >
      {mediaUrl ? <img alt="" src={mediaUrl} /> : null}
      <div>
        {heading ? <h2>{heading}</h2> : null}
        {bodyHtml ? (
          <div className="site-v3-custom-rich" dangerouslySetInnerHTML={{ __html: bodyHtml }} />
        ) : null}
        {bodyText ? <p>{bodyText}</p> : null}
        {cta ? <AccountAwareLink className="site-v3-secondary-link" href={cta.href} label={cta.label} /> : null}
      </div>
    </section>
  );
}

function renderRichText(
  definition: SiteV3CustomDefinitionSnapshot,
  module: SiteV3PublicModule,
) {
  const html =
    firstHtml(definition.field_schema_json, module.config_json) ||
    firstText(definition.field_schema_json, module.config_json, ["html", "body", "content", "text"]);
  if (!html) {
    return null;
  }
  return (
    <RichTextSafe
      module={{
        ...module,
        module_code: "rich_text_safe",
        config_json: { html },
      }}
    />
  );
}

function renderFeatureCard(
  definition: SiteV3CustomDefinitionSnapshot,
  module: SiteV3PublicModule,
  games: Map<string, GameLibraryTitle>,
) {
  const titleCode = firstTitleCode(definition.field_schema_json, module.config_json);
  if (titleCode && games.has(titleCode)) {
    const headline = firstText(definition.field_schema_json, module.config_json, ["headline", "heading", "title"]);
    const body = firstText(definition.field_schema_json, module.config_json, ["body", "subtitle", "summary", "text"]);
    const ctaLabel = firstText(definition.field_schema_json, module.config_json, ["cta_label", "button_label", "link_label"]);
    return (
      <FeaturedGame
        games={games}
        module={{
          ...module,
          module_code: "featured_game",
          config_json: {
            title_code: titleCode,
            ...(headline ? { headline } : {}),
            ...(body ? { body } : {}),
            ...(ctaLabel ? { cta_label: ctaLabel } : {}),
          },
        }}
      />
    );
  }
  return renderEditorialPanel(definition, module, "feature");
}

function firstAssetUrl(fields: SiteV3CustomFieldSnapshot[], config: Record<string, unknown>): string | null {
  const assetFields = fields.filter((field) => field.type === "asset_ref");
  const preferred = assetFields.find((field) =>
    ["media", "image", "banner", "background", "artwork"].some((part) => field.key.includes(part)),
  );
  const orderedFields = preferred ? [preferred, ...assetFields.filter((field) => field !== preferred)] : assetFields;
  for (const field of orderedFields) {
    const assetUrl = resolveAssetRef(config[field.key]);
    if (assetUrl) {
      return assetUrl;
    }
  }
  return null;
}

function firstTitleCode(fields: SiteV3CustomFieldSnapshot[], config: Record<string, unknown>): string {
  return firstFieldString(fields, config, (field) => field.type === "title_code") || readString(config.title_code, "");
}

function firstTitleCodeList(fields: SiteV3CustomFieldSnapshot[], config: Record<string, unknown>): string[] {
  const field = fields.find((entry) => entry.type === "title_code_list");
  const value = field ? readStringArray(config[field.key]) : [];
  return value.length > 0 ? value : readStringArray(config.title_codes);
}

function firstHtml(fields: SiteV3CustomFieldSnapshot[], config: Record<string, unknown>): string {
  return firstFieldString(fields, config, (field) => field.type === "html");
}

function firstText(
  fields: SiteV3CustomFieldSnapshot[],
  config: Record<string, unknown>,
  preferredKeys: string[],
): string {
  for (const key of preferredKeys) {
    const value = readString(config[key], "");
    if (value) {
      return value;
    }
  }
  return firstFieldString(
    fields,
    config,
    (field) => field.type === "string" && preferredKeys.some((key) => field.key.includes(key)),
  );
}

function firstCta(fields: SiteV3CustomFieldSnapshot[], config: Record<string, unknown>): CustomCta | null {
  if (!readBoolean(config.show_cta, true)) {
    return null;
  }
  const label = firstText(fields, config, ["cta_label", "button_label", "link_label"]);
  const rawHref =
    firstText(fields, config, ["cta_url", "button_url", "link_url", "url", "href"]) ||
    firstFieldString(fields, config, (field) => field.type === "url");
  if (!label || !rawHref) {
    return null;
  }
  return {
    href: resolveLink(rawHref),
    label,
  };
}

function firstFieldString(
  fields: SiteV3CustomFieldSnapshot[],
  config: Record<string, unknown>,
  predicate: (field: SiteV3CustomFieldSnapshot) => boolean,
): string {
  const field = fields.find(predicate);
  return field ? readString(config[field.key], "") : "";
}

function warnCustomRenderer(message: string): void {
  if (process.env.NODE_ENV === "development") {
    console.warn(message);
  }
}
