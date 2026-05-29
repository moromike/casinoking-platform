import { type SiteV3AdminModule, type SiteV3TitleOption } from "../site-v3-admin-types";
import { collectTitleCodes, previewBody, previewHeadline, type SiteV3ModuleDescriptorMap } from "../site-v3-admin-helpers";

export function SiteV3DraftPreview({
  descriptors,
  modules,
  pageTitle,
  titleOptions,
}: {
  descriptors: SiteV3ModuleDescriptorMap;
  modules: SiteV3AdminModule[];
  pageTitle: string;
  titleOptions: SiteV3TitleOption[];
}) {
  return (
    <section className="admin-card site-v3-preview-card">
      <div className="site-v3-card-heading">
        <div>
          <h4>Draft preview</h4>
          <p>Saved draft modules in page order.</p>
        </div>
      </div>
      <div className="site-v3-preview-surface">
        <h3>{pageTitle || "Untitled page"}</h3>
        {modules.map((module, index) => (
          <PreviewModule key={module.id ?? module.client_id ?? index} descriptors={descriptors} module={module} titleOptions={titleOptions} />
        ))}
        {modules.length === 0 ? <p className="empty-state">No modules to preview.</p> : null}
      </div>
    </section>
  );
}

export function PreviewModule({
  descriptors,
  module,
  titleOptions,
}: {
  descriptors: SiteV3ModuleDescriptorMap;
  module: SiteV3AdminModule;
  titleOptions: SiteV3TitleOption[];
}) {
  const descriptor = descriptors[module.module_code];
  const config = module.config_json;
  const titles = titleOptions.filter((title) =>
    collectTitleCodes(config).includes(title.title_code),
  );
  return (
    <article className={`site-v3-preview-module is-${module.module_code}`}>
      <span>{descriptor?.label ?? module.module_code}</span>
      <strong>{previewHeadline(module, descriptors)}</strong>
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
