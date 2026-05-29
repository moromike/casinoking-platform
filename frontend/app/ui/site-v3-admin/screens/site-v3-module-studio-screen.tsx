import { useMemo, useState } from "react";

import {
  type SiteV3CustomFieldType,
  type SiteV3FieldGroup,
  type SiteV3ModuleDefinition,
  type SiteV3ModuleDefinitionCategory,
  type SiteV3ModuleDefinitionField,
  type SiteV3ModuleDefinitionPayload,
  type SiteV3ModuleConfig,
  type SiteV3RendererTemplate,
} from "../site-v3-admin-types";
import { formatDate, getModuleCategoryLabel } from "../site-v3-admin-helpers";

const CUSTOM_DEFINITION_CATEGORIES: SiteV3ModuleDefinitionCategory[] = ["hero", "catalog", "promo", "text_legal"];
const FIELD_GROUPS: SiteV3FieldGroup[] = ["content", "catalog", "assets", "links", "rules"];
const FIELD_TYPES: Array<{ label: string; value: SiteV3CustomFieldType }> = [
  { label: "Text", value: "string" },
  { label: "Safe HTML", value: "html" },
  { label: "Boolean", value: "boolean" },
  { label: "Asset", value: "asset_ref" },
  { label: "Title", value: "title_code" },
  { label: "Title list", value: "title_code_list" },
  { label: "URL/path", value: "url" },
];
const RENDERER_TEMPLATES: Array<{ label: string; value: SiteV3RendererTemplate }> = [
  { label: "Image banner", value: "image_banner" },
  { label: "Game grid", value: "game_grid" },
  { label: "Editorial panel", value: "editorial_panel" },
  { label: "Rich text", value: "rich_text" },
  { label: "Feature card", value: "feature_card" },
];

const TEMPLATE_FIELD_PRESETS: Record<SiteV3RendererTemplate, SiteV3ModuleDefinitionField[]> = {
  image_banner: [
    { key: "headline", label: "Headline", type: "string", group: "content", required: true, max_length: 120 },
    { key: "media", label: "Media", type: "asset_ref", group: "assets" },
    { key: "cta_label", label: "CTA label", type: "string", group: "links", max_length: 60 },
    { key: "cta_url", label: "CTA URL", type: "url", group: "links", max_length: 300 },
    { key: "show_cta", label: "Show CTA", type: "boolean", group: "links" },
  ],
  game_grid: [
    { key: "heading", label: "Heading", type: "string", group: "content", required: true, max_length: 100 },
    { key: "title_codes", label: "Game titles", type: "title_code_list", group: "catalog", required: true, max_items: 24 },
  ],
  editorial_panel: [
    { key: "headline", label: "Headline", type: "string", group: "content", required: true, max_length: 120 },
    { key: "body", label: "Body", type: "string", group: "content", max_length: 500 },
    { key: "media", label: "Media", type: "asset_ref", group: "assets" },
    { key: "cta_label", label: "CTA label", type: "string", group: "links", max_length: 60 },
    { key: "cta_url", label: "CTA URL", type: "url", group: "links", max_length: 300 },
  ],
  rich_text: [
    { key: "html", label: "HTML", type: "html", group: "rules", required: true, max_length: 12000 },
  ],
  feature_card: [
    { key: "title_code", label: "Game title", type: "title_code", group: "catalog", required: true },
    { key: "headline", label: "Headline", type: "string", group: "content", max_length: 120 },
    { key: "body", label: "Body", type: "string", group: "content", max_length: 500 },
    { key: "media", label: "Media", type: "asset_ref", group: "assets" },
    { key: "cta_label", label: "CTA label", type: "string", group: "links", max_length: 60 },
  ],
};

type NewFieldDraft = {
  key: string;
  label: string;
  type: SiteV3CustomFieldType;
  group: SiteV3FieldGroup;
  required: boolean;
  max_length: string;
  max_items: string;
  help: string;
};

const EMPTY_FIELD_DRAFT: NewFieldDraft = {
  key: "",
  label: "",
  type: "string",
  group: "content",
  required: false,
  max_length: "",
  max_items: "",
  help: "",
};

export function SiteV3ModuleStudioScreen({
  busyAction,
  moduleDefinitions,
  moduleDefinitionsStatus,
  onArchiveDefinition,
  onCreateDefinition,
  onPublishDefinition,
  onReloadDefinitions,
  onUpdateDefinition,
}: {
  busyAction: string | null;
  moduleDefinitions: SiteV3ModuleDefinition[];
  moduleDefinitionsStatus: "idle" | "loading" | "error";
  onArchiveDefinition: (moduleCode: string) => Promise<void>;
  onCreateDefinition: (payload: SiteV3ModuleDefinitionPayload) => Promise<boolean>;
  onPublishDefinition: (moduleCode: string) => Promise<void>;
  onReloadDefinitions: () => Promise<void>;
  onUpdateDefinition: (moduleCode: string, payload: SiteV3ModuleDefinitionPayload) => Promise<boolean>;
}) {
  const [label, setLabel] = useState("");
  const [moduleCode, setModuleCode] = useState("custom_");
  const [category, setCategory] = useState<SiteV3ModuleDefinitionCategory>("hero");
  const [rendererTemplate, setRendererTemplate] = useState<SiteV3RendererTemplate>("image_banner");
  const [fieldDraft, setFieldDraft] = useState<NewFieldDraft>(EMPTY_FIELD_DRAFT);
  const [fieldKeyTouched, setFieldKeyTouched] = useState(false);
  const [fields, setFields] = useState<SiteV3ModuleDefinitionField[]>([]);
  const [defaultConfig, setDefaultConfig] = useState<SiteV3ModuleConfig>({});
  const [editingModuleCode, setEditingModuleCode] = useState<string | null>(null);
  const [formError, setFormError] = useState("");
  const isSaving =
    busyAction === "module-definition-create" ||
    (editingModuleCode !== null && busyAction === `module-definition-update:${editingModuleCode}`);
  const saveDisabled = isSaving || fields.length === 0;

  const sortedDefinitions = useMemo(
    () => [...moduleDefinitions].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [moduleDefinitions],
  );

  function handleLabelChange(value: string) {
    setLabel(value);
    if (moduleCode === "custom_" || moduleCode === normalizeCustomModuleCode(label)) {
      setModuleCode(normalizeCustomModuleCode(value));
    }
  }

  function addField() {
    const normalizedKey = normalizeFieldKey(fieldDraft.key || fieldDraft.label);
    const normalizedLabel = fieldDraft.label.trim();
    if (!normalizedKey || !normalizedLabel) {
      setFormError("Field key and label are required.");
      return;
    }
    if (fields.some((field) => field.key === normalizedKey)) {
      setFormError("Field key already exists.");
      return;
    }
    setFields((current) => [
      ...current,
      {
        key: normalizedKey,
        label: normalizedLabel,
        type: fieldDraft.type,
        group: fieldDraft.group,
        required: fieldDraft.required,
        ...(fieldDraft.max_length ? { max_length: Number(fieldDraft.max_length) } : {}),
        ...(fieldDraft.max_items ? { max_items: Number(fieldDraft.max_items) } : {}),
        ...(fieldDraft.help.trim() ? { help: fieldDraft.help.trim() } : {}),
      },
    ]);
    setFieldDraft(EMPTY_FIELD_DRAFT);
    setFieldKeyTouched(false);
    setFormError("");
  }

  function handleRendererTemplateChange(nextTemplate: SiteV3RendererTemplate) {
    setRendererTemplate(nextTemplate);
    if (fields.length === 0) {
      applyTemplatePreset(nextTemplate);
    }
  }

  function applyTemplatePreset(template = rendererTemplate) {
    const presetFields = cloneFields(TEMPLATE_FIELD_PRESETS[template]);
    setFields(presetFields);
    setDefaultConfig(buildDefaultConfig(presetFields));
    setFormError("");
  }

  function resetForm() {
    setLabel("");
    setModuleCode("custom_");
    setCategory("hero");
    setRendererTemplate("image_banner");
    setFields([]);
    setDefaultConfig({});
    setFieldDraft(EMPTY_FIELD_DRAFT);
    setFieldKeyTouched(false);
    setEditingModuleCode(null);
    setFormError("");
  }

  function loadDefinitionForEdit(definition: SiteV3ModuleDefinition) {
    setLabel(definition.label);
    setModuleCode(definition.module_code);
    setCategory(definition.category);
    setRendererTemplate(definition.renderer_template);
    setFields(cloneFields(definition.field_schema_json));
    setDefaultConfig(definition.default_config_json);
    setEditingModuleCode(definition.module_code);
    setFieldDraft(EMPTY_FIELD_DRAFT);
    setFieldKeyTouched(false);
    setFormError("");
  }

  function cloneDefinition(definition: SiteV3ModuleDefinition) {
    setLabel(`${definition.label} copy`);
    setModuleCode(nextCloneModuleCode(definition.module_code));
    setCategory(definition.category);
    setRendererTemplate(definition.renderer_template);
    setFields(cloneFields(definition.field_schema_json));
    setDefaultConfig(definition.default_config_json);
    setEditingModuleCode(null);
    setFieldDraft(EMPTY_FIELD_DRAFT);
    setFieldKeyTouched(false);
    setFormError("");
  }

  async function handleSave() {
    const normalizedModuleCode = normalizeCustomModuleCode(moduleCode);
    if (!label.trim() || normalizedModuleCode === "custom_") {
      setFormError("Module label and code are required.");
      return;
    }
    if (fields.length === 0) {
      setFormError("Add at least one field.");
      return;
    }
    const payload: SiteV3ModuleDefinitionPayload = {
      module_code: normalizedModuleCode,
      label: label.trim(),
      category,
      renderer_template: rendererTemplate,
      field_schema_json: fields,
      default_config_json: buildDefaultConfig(fields, defaultConfig),
    };
    const saved =
      editingModuleCode === null
        ? await onCreateDefinition(payload)
        : await onUpdateDefinition(editingModuleCode, { ...payload, module_code: editingModuleCode });
    if (saved) {
      resetForm();
    }
  }

  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Modules</span>
          <h3>Module Studio</h3>
          <p>Design custom module definitions from approved renderer templates.</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => void onReloadDefinitions()}>
          Reload
        </button>
      </div>

      {formError ? (
        <div className="site-v3-message is-error" role="alert">
          {formError}
        </div>
      ) : null}

      <div className="site-v3-studio-grid">
        <section className="site-v3-studio-panel">
          <div className="site-v3-studio-panel-heading">
            <strong>{editingModuleCode ? "Edit draft definition" : "New definition"}</strong>
            {editingModuleCode ? (
              <button className="button-secondary" type="button" onClick={resetForm}>
                New definition
              </button>
            ) : null}
          </div>
          <div className="site-v3-form-grid">
            <label className="site-v3-field">
              <span>Module label</span>
              <input value={label} onChange={(event) => handleLabelChange(event.target.value)} placeholder="Landing banner" />
            </label>
            <label className="site-v3-field">
              <span>Module code</span>
              <input
                disabled={editingModuleCode !== null}
                value={moduleCode}
                onChange={(event) => setModuleCode(normalizeCustomModuleCode(event.target.value))}
              />
            </label>
            <label className="site-v3-field">
              <span>Category</span>
              <select value={category} onChange={(event) => setCategory(event.target.value as SiteV3ModuleDefinitionCategory)}>
                {CUSTOM_DEFINITION_CATEGORIES.map((entry) => (
                  <option key={entry} value={entry}>
                    {getModuleCategoryLabel(entry)}
                  </option>
                ))}
              </select>
            </label>
            <label className="site-v3-field">
              <span>Renderer template</span>
              <select value={rendererTemplate} onChange={(event) => handleRendererTemplateChange(event.target.value as SiteV3RendererTemplate)}>
                {RENDERER_TEMPLATES.map((entry) => (
                  <option key={entry.value} value={entry.value}>
                    {entry.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="site-v3-command-actions">
            <button className="button-secondary" type="button" onClick={() => applyTemplatePreset()}>
              Use template fields
            </button>
          </div>

          <div className="site-v3-fieldset site-v3-field-wide">
            <strong>Field schema</strong>
            <div className="site-v3-studio-field-builder">
              <label className="site-v3-field">
                <span>Field label</span>
                <input
                  value={fieldDraft.label}
                  onChange={(event) =>
                    setFieldDraft((current) => ({
                      ...current,
                      label: event.target.value,
                      key: fieldKeyTouched ? current.key : normalizeFieldKey(event.target.value),
                    }))
                  }
                  placeholder="Headline"
                />
              </label>
              <label className="site-v3-field">
                <span>Field key</span>
                <input
                  value={fieldDraft.key}
                  onChange={(event) => {
                    setFieldKeyTouched(true);
                    setFieldDraft((current) => ({ ...current, key: normalizeFieldKey(event.target.value) }));
                  }}
                  placeholder="headline"
                />
              </label>
              <label className="site-v3-field">
                <span>Type</span>
                <select
                  value={fieldDraft.type}
                  onChange={(event) =>
                    setFieldDraft((current) => ({
                      ...current,
                      type: event.target.value as SiteV3CustomFieldType,
                      group: defaultGroupForFieldType(event.target.value as SiteV3CustomFieldType),
                    }))
                  }
                >
                  {FIELD_TYPES.map((entry) => (
                    <option key={entry.value} value={entry.value}>
                      {entry.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="site-v3-field">
                <span>Group</span>
                <select value={fieldDraft.group} onChange={(event) => setFieldDraft((current) => ({ ...current, group: event.target.value as SiteV3FieldGroup }))}>
                  {FIELD_GROUPS.map((entry) => (
                    <option key={entry} value={entry}>
                      {entry}
                    </option>
                  ))}
                </select>
              </label>
              <label className="site-v3-field">
                <span>Max length</span>
                <input
                  inputMode="numeric"
                  value={fieldDraft.max_length}
                  onChange={(event) => setFieldDraft((current) => ({ ...current, max_length: event.target.value.replace(/\D/g, "").slice(0, 5) }))}
                />
              </label>
              <label className="site-v3-field">
                <span>Max items</span>
                <input
                  inputMode="numeric"
                  value={fieldDraft.max_items}
                  onChange={(event) => setFieldDraft((current) => ({ ...current, max_items: event.target.value.replace(/\D/g, "").slice(0, 2) }))}
                />
              </label>
              <label className="site-v3-field site-v3-field-wide">
                <span>Help</span>
                <input value={fieldDraft.help} onChange={(event) => setFieldDraft((current) => ({ ...current, help: event.target.value }))} />
              </label>
              <label className="site-v3-checkbox-row">
                <input
                  checked={fieldDraft.required}
                  type="checkbox"
                  onChange={(event) => setFieldDraft((current) => ({ ...current, required: event.target.checked }))}
                />
                <span>Required</span>
              </label>
              <button className="button-secondary" type="button" onClick={addField}>
                Add field
              </button>
            </div>
            {fields.length > 0 ? (
              <div className="site-v3-studio-field-list">
                {fields.map((field) => (
                  <article key={field.key}>
                    <span>
                      <strong>{field.label}</strong>
                      <small>{field.key} - {field.type}{field.required ? " - required" : ""}</small>
                    </span>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => setFields((current) => current.filter((entry) => entry.key !== field.key))}
                    >
                      Remove
                    </button>
                  </article>
                ))}
              </div>
            ) : null}
          </div>

          <div className="site-v3-command-actions">
            <button className="button" disabled={saveDisabled} type="button" onClick={() => void handleSave()}>
              {editingModuleCode ? "Update draft" : "Create definition"}
            </button>
          </div>
        </section>

        <section className="site-v3-studio-panel">
          <div className="site-v3-studio-panel-heading">
            <strong>Custom definitions</strong>
            <small>{moduleDefinitionsStatus === "loading" ? "Loading" : `${sortedDefinitions.length} definitions`}</small>
          </div>
          <div className="site-v3-studio-definition-list">
            {sortedDefinitions.map((definition) => (
              <article className="site-v3-studio-definition-card" key={definition.id}>
                <div>
                  <span className="site-v3-module-code">{definition.module_code}</span>
                  <h4>{definition.label}</h4>
                  <p>{getModuleCategoryLabel(definition.category)} - {definition.renderer_template} - {definition.field_schema_json.length} fields</p>
                  <small>
                    {definition.status} - draft schema v{definition.draft_schema_version} - published {definition.published_version ?? "none"} - {formatDate(definition.updated_at)}
                  </small>
                </div>
                <div className="site-v3-command-actions">
                  <button
                    className="button-secondary"
                    disabled={definition.status === "archived"}
                    type="button"
                    onClick={() => loadDefinitionForEdit(definition)}
                  >
                    Edit draft
                  </button>
                  <button className="button-secondary" type="button" onClick={() => cloneDefinition(definition)}>
                    Clone
                  </button>
                  <button
                    className="button-secondary"
                    disabled={busyAction === `module-definition-publish:${definition.module_code}` || definition.status === "archived"}
                    type="button"
                    onClick={() => void onPublishDefinition(definition.module_code)}
                  >
                    Publish
                  </button>
                  <button
                    className="button-secondary"
                    disabled={busyAction === `module-definition-archive:${definition.module_code}` || definition.status === "archived"}
                    type="button"
                    onClick={() => void onArchiveDefinition(definition.module_code)}
                  >
                    Archive
                  </button>
                </div>
              </article>
            ))}
            {sortedDefinitions.length === 0 ? (
              <div className="site-v3-empty-state">
                <strong>No custom definitions yet.</strong>
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </section>
  );
}

function normalizeCustomModuleCode(value: string): string {
  const suffix = value
    .trim()
    .toLowerCase()
    .replace(/^custom[_-]?/, "")
    .replace(/[^a-z0-9_ -]/g, "")
    .replace(/[\s-]+/g, "_")
    .replace(/_+/g, "_")
    .slice(0, 56);
  return `custom_${suffix}`;
}

function nextCloneModuleCode(moduleCode: string): string {
  const base = moduleCode.replace(/^custom_/, "").replace(/_copy(?:_\d+)?$/, "");
  const suffix = `${base}_copy`;
  return normalizeCustomModuleCode(suffix);
}

function normalizeFieldKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_ -]/g, "")
    .replace(/[\s-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^[^a-z]+/, "")
    .slice(0, 64);
}

function cloneFields(fields: SiteV3ModuleDefinitionField[]): SiteV3ModuleDefinitionField[] {
  return fields.map((field) => ({ ...field }));
}

function buildDefaultConfig(
  fields: SiteV3ModuleDefinitionField[],
  existingDefaults: SiteV3ModuleConfig = {},
): SiteV3ModuleConfig {
  return Object.fromEntries(
    fields.map((field) => [
      field.key,
      Object.prototype.hasOwnProperty.call(existingDefaults, field.key)
        ? existingDefaults[field.key]
        : defaultValueForField(field.type),
    ]),
  );
}

function defaultGroupForFieldType(fieldType: SiteV3CustomFieldType): SiteV3FieldGroup {
  if (fieldType === "asset_ref") {
    return "assets";
  }
  if (fieldType === "title_code" || fieldType === "title_code_list") {
    return "catalog";
  }
  if (fieldType === "url") {
    return "links";
  }
  if (fieldType === "html") {
    return "rules";
  }
  return "content";
}

function defaultValueForField(fieldType: SiteV3CustomFieldType): unknown {
  if (fieldType === "boolean") {
    return false;
  }
  if (fieldType === "asset_ref") {
    return {};
  }
  if (fieldType === "title_code_list") {
    return [];
  }
  return "";
}
