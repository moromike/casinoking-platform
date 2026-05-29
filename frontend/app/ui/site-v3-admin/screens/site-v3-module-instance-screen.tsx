import { SITE_V3_MODULE_DESCRIPTORS } from "../site-v3-admin-descriptors";
import { type SiteV3AdminModule, type SiteV3SiteAsset, type SiteV3TitleOption } from "../site-v3-admin-types";
import { getMissingRequiredFields, getModuleCategoryLabel, groupModuleFields, type SiteV3AdminView } from "../site-v3-admin-helpers";
import { ModuleField } from "../fields/module-field";

export function SiteV3ModuleInstanceScreen({
  assetsStatus,
  module,
  moduleIndex,
  moduleCount,
  siteAssets,
  titleOptions,
  onNavigate,
  onUploadSiteAsset,
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
  onUploadSiteAsset: (file: File) => Promise<SiteV3SiteAsset>;
  onUpdateModule: (index: number, patch: Partial<SiteV3AdminModule>) => void;
  onUpdateModuleConfig: (index: number, key: string, value: unknown) => void;
}) {
  if (module === null) {
    return (
      <section className="admin-card site-v3-cms-screen">
        <div className="site-v3-screen-heading">
          <div>
            <span className="site-v3-screen-kicker">Mounted module instance</span>
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
  const missingRequiredFields = getMissingRequiredFields(module);
  const isReady = missingRequiredFields.length === 0;
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Mounted module instance</span>
          <h3>Editing {descriptor.label} instance</h3>
          <p>{descriptor.humanHint}</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "composition" })}>
          Back to composition
        </button>
      </div>
      <div className="site-v3-module-detail-summary is-full-page">
        <span className="site-v3-module-code">{module.module_code}</span>
        <span className="site-v3-module-category">{getModuleCategoryLabel(descriptor.category)}</span>
        <small>Module {moduleIndex + 1} of {moduleCount}. These settings control this single mounted module instance.</small>
      </div>
      <div className={`site-v3-module-readiness ${isReady ? "is-ready" : "is-incomplete"}`}>
        <span>{isReady ? "Ready to save" : "Needs attention"}</span>
        {isReady ? (
          <p>All required fields for this module are filled.</p>
        ) : (
          <p>Required fields missing: {missingRequiredFields.map((field) => field.label).join(", ")}.</p>
        )}
      </div>
      <div className="site-v3-module-meta">
        <label className="site-v3-field">
          <span>Placement area</span>
          <small>Where this module belongs in the page layout. Most modules only need the default value.</small>
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
                  onUploadSiteAsset={onUploadSiteAsset}
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
