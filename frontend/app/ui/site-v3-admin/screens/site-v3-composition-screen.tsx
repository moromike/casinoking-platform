import { useMemo, useState } from "react";
import { SITE_V3_MODULE_CATEGORIES, SITE_V3_MODULE_DESCRIPTORS } from "../site-v3-admin-descriptors";
import { type SiteV3AdminModule, type SiteV3ModuleCode } from "../site-v3-admin-types";
import { getMissingRequiredFields, getModuleCategoryLabel, previewHeadline } from "../site-v3-admin-helpers";

export function SiteV3CompositionScreen({
  modules,
  onAddModule,
  onDuplicateModule,
  onMoveModule,
  onOpenModule,
  onRemoveModule,
}: {
  modules: SiteV3AdminModule[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onDuplicateModule: (index: number) => void;
  onMoveModule: (index: number, delta: number) => void;
  onOpenModule: (index: number) => void;
  onRemoveModule: (index: number) => void;
}) {
  const [isAddPickerOpen, setIsAddPickerOpen] = useState(false);
  const moduleOptions = useMemo(() => Object.values(SITE_V3_MODULE_DESCRIPTORS), []);
  const [moduleCodeToAdd, setModuleCodeToAdd] = useState<SiteV3ModuleCode>(
    moduleOptions[0]?.moduleCode ?? "global_header",
  );
  const selectedDescriptor = SITE_V3_MODULE_DESCRIPTORS[moduleCodeToAdd];

  function addSelectedModule() {
    onAddModule(moduleCodeToAdd);
    setIsAddPickerOpen(false);
  }

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
        <div className="site-v3-inline-module-picker is-compact">
          <div className="site-v3-inline-module-picker-heading">
            <strong>Add module to this page</strong>
            <small>Select one module type. It will be mounted at the end of the page; you stay here in Composition.</small>
          </div>
          <div className="site-v3-inline-module-select-row">
            <label className="site-v3-field">
              <span>Module type</span>
              <select
                value={moduleCodeToAdd}
                onChange={(event) => setModuleCodeToAdd(event.target.value as SiteV3ModuleCode)}
              >
                {SITE_V3_MODULE_CATEGORIES.map((category) => (
                  <optgroup key={category.key} label={category.label}>
                    {moduleOptions
                      .filter((descriptor) => descriptor.category === category.key)
                      .map((descriptor) => (
                        <option key={descriptor.moduleCode} value={descriptor.moduleCode}>
                          {descriptor.label}
                        </option>
                      ))}
                  </optgroup>
                ))}
              </select>
            </label>
            <button className="button" type="button" onClick={addSelectedModule}>
              Add selected module
            </button>
            <button className="button-secondary" type="button" onClick={() => setIsAddPickerOpen(false)}>
              Cancel
            </button>
          </div>
          <div className="site-v3-inline-module-selected">
            <strong>{selectedDescriptor.label}</strong>
            <small>
              {getModuleCategoryLabel(selectedDescriptor.category)} / {selectedDescriptor.moduleCode}
            </small>
            <p>{selectedDescriptor.humanHint}</p>
          </div>
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
