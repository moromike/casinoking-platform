import { useEffect, useMemo, useState } from "react";
import { SITE_V3_MODULE_CATEGORIES, SITE_V3_MODULE_DESCRIPTORS } from "../site-v3-admin-descriptors";
import { type SiteV3AdminModule, type SiteV3ModuleCategory, type SiteV3ModuleCode } from "../site-v3-admin-types";
import { getModuleCategoryLabel, groupModuleFields, type SiteV3AdminView } from "../site-v3-admin-helpers";

export function SiteV3ModuleLibraryScreen({
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
          <p>Open a module category, then choose the module type to inspect or mount on the current page.</p>
        </div>
        <button className="button" type="button" onClick={() => onNavigate({ kind: "moduleWizard" })}>
          Add module
        </button>
      </div>
      <div className="site-v3-library-category-list">
        {SITE_V3_MODULE_CATEGORIES.map((category) => {
          const categoryModules = Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
            (descriptor) => descriptor.category === category.key,
          );
          const usedCount = modules.filter((module) => SITE_V3_MODULE_DESCRIPTORS[module.module_code].category === category.key).length;
          return (
            <button
              className="site-v3-library-category-row"
              key={category.key}
              onClick={() => onNavigate({ kind: "moduleCategory", category: category.key })}
              type="button"
            >
              <span>
                <strong>{category.label}</strong>
                <small>{category.description}</small>
              </span>
              <span>{categoryModules.length} types</span>
              <span>{usedCount} mounted</span>
              <em>Open</em>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function SiteV3NewModuleWizardScreen({
  modules,
  onAddModule,
  onNavigate,
}: {
  modules: SiteV3AdminModule[];
  onAddModule: (moduleCode: SiteV3ModuleCode) => void;
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  const [selectedCategory, setSelectedCategory] = useState<SiteV3ModuleCategory>("structure");
  const moduleOptions = useMemo(
    () => Object.values(SITE_V3_MODULE_DESCRIPTORS).filter(
      (descriptor) => descriptor.category === selectedCategory,
    ),
    [selectedCategory],
  );
  const [selectedModuleCode, setSelectedModuleCode] = useState<SiteV3ModuleCode>(
    moduleOptions[0]?.moduleCode ?? "global_header",
  );
  const selectedDescriptor = SITE_V3_MODULE_DESCRIPTORS[selectedModuleCode];

  useEffect(() => {
    if (selectedDescriptor.category !== selectedCategory) {
      const nextModuleCode = moduleOptions[0]?.moduleCode;
      if (nextModuleCode) {
        setSelectedModuleCode(nextModuleCode);
      }
    }
  }, [moduleOptions, selectedCategory, selectedDescriptor.category]);

  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Modules</span>
          <h3>Add module to page</h3>
          <p>Create a mounted module instance from an existing template. New module types are a platform development task, not a page editing task.</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "modules" })}>
          Back to library
        </button>
      </div>
      <div className="site-v3-module-wizard">
        <section className="site-v3-module-wizard-step">
          <span>1</span>
          <div>
            <strong>Choose module family</strong>
            <p>Pick the kind of page block you want to add.</p>
          </div>
          <div className="site-v3-module-wizard-options">
            {SITE_V3_MODULE_CATEGORIES.map((category) => (
              <button
                className={`site-v3-module-wizard-option ${category.key === selectedCategory ? "is-selected" : ""}`}
                key={category.key}
                type="button"
                onClick={() => setSelectedCategory(category.key)}
              >
                <strong>{category.label}</strong>
                <small>{category.description}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="site-v3-module-wizard-step">
          <span>2</span>
          <div>
            <strong>Choose template</strong>
            <p>Templates are fixed module types. You customize this page instance from Module settings after it is mounted.</p>
          </div>
          <div className="site-v3-module-wizard-options">
            {moduleOptions.map((descriptor) => {
              const mountedCount = modules.filter((module) => module.module_code === descriptor.moduleCode).length;
              return (
                <button
                  className={`site-v3-module-wizard-option ${descriptor.moduleCode === selectedModuleCode ? "is-selected" : ""}`}
                  key={descriptor.moduleCode}
                  type="button"
                  onClick={() => setSelectedModuleCode(descriptor.moduleCode)}
                >
                  <strong>{descriptor.label}</strong>
                  <small>{descriptor.humanHint}</small>
                  <em>{mountedCount} mounted</em>
                </button>
              );
            })}
          </div>
        </section>

        <section className="site-v3-module-wizard-step is-summary">
          <span>3</span>
          <div>
            <strong>Mount in page</strong>
            <p>The module will appear at the bottom of Composition. Save draft, then refresh preview to inspect it.</p>
          </div>
          <article className="site-v3-module-wizard-summary">
            <span className="site-v3-module-code">{selectedDescriptor.moduleCode}</span>
            <h4>{selectedDescriptor.label}</h4>
            <p>{selectedDescriptor.description}</p>
            <small>{selectedDescriptor.fields.length} editable fields / schema v{selectedDescriptor.schemaVersion}</small>
          </article>
          <div className="site-v3-command-actions">
            <button className="button" type="button" onClick={() => onAddModule(selectedModuleCode)}>
              Mount module
            </button>
            <button className="button-secondary" type="button" onClick={() => onNavigate({ kind: "composition" })}>
              Open composition
            </button>
          </div>
        </section>
      </div>
    </section>
  );
}

export function SiteV3ModuleCategoryScreen({
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

export function SiteV3ModuleTypeDetailScreen({
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
