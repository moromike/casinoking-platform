import { useState } from "react";
import { readErrorMessage } from "@/app/lib/api";
import { type SiteV3AdminModule, type SiteV3ModuleFieldDescriptor, type SiteV3NavItem, type SiteV3SiteAsset, type SiteV3TitleOption } from "../site-v3-admin-types";
import { cleanNavItems, formatBytes, formatEngineLabel, formatSiteAssetLabel, formatSiteAssetMeta, formatTitlePublication, groupTitlesByEngine, navTargetPatch, normalizeNavItems, resolveSiteAssetUrl, toAssetRef, toText } from "../site-v3-admin-helpers";

const SITE_V3_BANNER_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];
const SITE_V3_BANNER_MAX_BYTES = 2 * 1024 * 1024;

export function ModuleField({
  assetsStatus,
  field,
  module,
  siteAssets,
  titleOptions,
  onUploadSiteAsset,
  onChange,
}: {
  assetsStatus: "idle" | "loading" | "error";
  field: SiteV3ModuleFieldDescriptor;
  module: SiteV3AdminModule;
  siteAssets: SiteV3SiteAsset[];
  titleOptions: SiteV3TitleOption[];
  onUploadSiteAsset?: (file: File) => Promise<SiteV3SiteAsset>;
  onChange: (value: unknown) => void;
}) {
  const value = module.config_json[field.key];
  const [gameFilter, setGameFilter] = useState("");
  const [assetUploadStatus, setAssetUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [assetUploadMessage, setAssetUploadMessage] = useState<string | null>(null);
  const commonLabel = (
    <>
      <span>
        {field.label}
        {field.required ? <strong aria-label="required"> *</strong> : null}
      </span>
      <small>{field.help}</small>
    </>
  );

  if (field.type === "html") {
    const textValue = toText(value);
    return (
      <label className="site-v3-field site-v3-field-wide">
        {commonLabel}
        <textarea value={textValue} onChange={(event) => onChange(event.target.value)} rows={7} maxLength={field.maxLength} />
        {field.maxLength ? <small className="site-v3-field-counter">{textValue.length}/{field.maxLength}</small> : null}
      </label>
    );
  }

  if (field.type === "title_code") {
    return (
      <label className="site-v3-field">
        {commonLabel}
        <select value={toText(value)} onChange={(event) => onChange(event.target.value)}>
          <option value="">Select title</option>
          {titleOptions.map((title) => (
            <option key={title.title_code} value={title.title_code}>
              {title.display_name} ({title.title_code})
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "title_code_list") {
    const selected = Array.isArray(value) ? value.map(String) : [];
    const selectedSet = new Set(selected);
    const titlesByCode = new Map(titleOptions.map((title) => [title.title_code, title]));
    const normalizedFilter = gameFilter.trim().toLowerCase();
    const filteredTitleOptions = normalizedFilter
      ? titleOptions.filter((title) =>
        [
          title.display_name,
          title.title_code,
          title.engine_code,
          formatTitlePublication(title),
        ].join(" ").toLowerCase().includes(normalizedFilter),
      )
      : titleOptions;
    const selectedItems = selected.map((titleCode) => ({
      titleCode,
      title: titlesByCode.get(titleCode) ?? null,
    }));
    const maxItems = field.maxItems ?? Number.POSITIVE_INFINITY;

    function updateSelected(titleCode: string, checked: boolean) {
      if (checked) {
        if (selectedSet.has(titleCode) || selected.length >= maxItems) {
          return;
        }
        onChange([...selected, titleCode]);
        return;
      }
      onChange(selected.filter((entry) => entry !== titleCode));
    }

    function moveSelected(titleCode: string, delta: number) {
      const currentIndex = selected.indexOf(titleCode);
      const nextIndex = currentIndex + delta;
      if (currentIndex < 0 || nextIndex < 0 || nextIndex >= selected.length) {
        return;
      }
      const next = [...selected];
      const [item] = next.splice(currentIndex, 1);
      next.splice(nextIndex, 0, item);
      onChange(next);
    }

    return (
      <fieldset className="site-v3-fieldset site-v3-field-wide">
        <legend>{field.label}{field.required ? " *" : ""}</legend>
        <p>{field.help}</p>
        <div className="site-v3-game-picker">
          <section className="site-v3-game-selection" aria-label="Selected game titles">
            <div className="site-v3-game-picker-heading">
              <span>Selected game titles</span>
              <strong>{selected.length}{Number.isFinite(maxItems) ? `/${maxItems}` : ""}</strong>
            </div>
            <p className="site-v3-game-picker-note">
              These titles render in the exact order shown on the public page.
            </p>
            {selected.length > 0 ? (
              <button className="button-secondary danger" type="button" onClick={() => onChange([])}>
                Clear selected games
              </button>
            ) : null}
            {selectedItems.length > 0 ? (
              <ol className="site-v3-game-selection-list">
                {selectedItems.map(({ titleCode, title }, index) => (
                  <li className="site-v3-game-selected-row" key={titleCode}>
                    <span className="site-v3-module-order-index">{index + 1}</span>
                    <span>
                      <strong>{title?.display_name ?? titleCode}</strong>
                      <small>{titleCode}{title ? ` / ${formatEngineLabel(title.engine_code)} / ${formatTitlePublication(title)}` : " / unavailable in catalog"}</small>
                    </span>
                    <div className="site-v3-game-selected-actions">
                      <button className="button-secondary" type="button" onClick={() => moveSelected(titleCode, -1)} disabled={index === 0}>
                        Up
                      </button>
                      <button className="button-secondary" type="button" onClick={() => moveSelected(titleCode, 1)} disabled={index === selectedItems.length - 1}>
                        Down
                      </button>
                      <button className="button-secondary danger" type="button" onClick={() => updateSelected(titleCode, false)}>
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="empty-state">No games selected yet. Add titles from Available title library below.</p>
            )}
          </section>

          <section className="site-v3-game-library" aria-label="Available title library">
            <div className="site-v3-game-picker-heading">
              <span>Available title library</span>
              <strong>{filteredTitleOptions.length}/{titleOptions.length} titles</strong>
            </div>
            <p className="site-v3-game-picker-note">
              Selecting a title adds it to the public Game Grid order above.
            </p>
            <label className="site-v3-field site-v3-game-filter">
              <span>Search available games</span>
              <input
                value={gameFilter}
                onChange={(event) => setGameFilter(event.target.value)}
                placeholder="Search by name, title code, engine or publication state"
              />
            </label>
            {groupTitlesByEngine(filteredTitleOptions).map((group) => (
              <section className="site-v3-game-library-group" key={group.engineCode}>
                <div className="site-v3-game-library-heading">
                  <strong>{formatEngineLabel(group.engineCode)}</strong>
                  <small>{group.titles.length} titles</small>
                </div>
                <div className="site-v3-game-option-grid">
                  {group.titles.map((title) => {
                    const checked = selectedSet.has(title.title_code);
                    return (
                      <label className={`site-v3-game-option ${checked ? "is-selected" : ""}`} key={title.title_code}>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={!checked && selected.length >= maxItems}
                          onChange={(event) => updateSelected(title.title_code, event.target.checked)}
                        />
                        <span>
                          <strong>{title.display_name}</strong>
                          <small>{title.title_code} / {formatTitlePublication(title)}</small>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </section>
            ))}
            {titleOptions.length === 0 ? <span className="empty-state">No title options available.</span> : null}
            {titleOptions.length > 0 && filteredTitleOptions.length === 0 ? (
              <span className="empty-state">No games match this search.</span>
            ) : null}
          </section>
        </div>
      </fieldset>
    );
  }

  if (field.type === "nav_items") {
    const navItems = normalizeNavItems(value);

    function updateNavItem(index: number, patch: Partial<SiteV3NavItem>) {
      const next = navItems.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item));
      onChange(cleanNavItems(next));
    }

    function addNavItem() {
      onChange([...cleanNavItems(navItems), { label: "", href: "/" }]);
    }

    function removeNavItem(index: number) {
      onChange(navItems.filter((_, itemIndex) => itemIndex !== index));
    }

    return (
      <div className="site-v3-fieldset site-v3-field-wide">
        <strong>{field.label}{field.required ? " *" : ""}</strong>
        <p>{field.help}</p>
        <div className="site-v3-nav-editor">
          {navItems.map((item, index) => (
            <div className="site-v3-nav-row" key={`nav-${index}`}>
              <label className="site-v3-field">
                <span>Label</span>
                <input
                  value={item.label}
                  maxLength={60}
                  onChange={(event) => updateNavItem(index, { label: event.target.value })}
                />
              </label>
              <label className="site-v3-field">
                <span>Target</span>
                <input
                  value={item.href ?? item.title_code ?? ""}
                  placeholder="/games or title_code"
                  onChange={(event) => updateNavItem(index, navTargetPatch(event.target.value))}
                />
              </label>
              <button className="button-secondary danger" type="button" onClick={() => removeNavItem(index)}>
                Remove
              </button>
            </div>
          ))}
          {navItems.length === 0 ? (
            <p className="empty-state">No navigation links yet. Add one link for each header button.</p>
          ) : null}
          <button className="button-secondary" type="button" onClick={addNavItem}>
            Add navigation item
          </button>
        </div>
      </div>
    );
  }

  if (field.type === "asset_ref") {
    const assetRef = toAssetRef(value);
    const selectedAsset = siteAssets.find(
      (asset) => asset.id === assetRef.asset_id || asset.public_url === assetRef.public_url,
    );

    async function uploadAsset(file: File) {
      if (!onUploadSiteAsset) {
        setAssetUploadStatus("error");
        setAssetUploadMessage("Banner upload is unavailable right now.");
        return;
      }
      if (!SITE_V3_BANNER_ALLOWED_MIME_TYPES.includes(file.type)) {
        setAssetUploadStatus("error");
        setAssetUploadMessage("Upload supports PNG, JPEG, or WebP images only.");
        return;
      }
      if (file.size > SITE_V3_BANNER_MAX_BYTES) {
        setAssetUploadStatus("error");
        setAssetUploadMessage(`Upload blocked: ${formatBytes(file.size)} exceeds the 2 MB banner limit.`);
        return;
      }

      setAssetUploadStatus("uploading");
      setAssetUploadMessage("Uploading banner...");
      try {
        const uploadedAsset = await onUploadSiteAsset(file);
        onChange({
          asset_id: uploadedAsset.id,
          asset_kind: uploadedAsset.asset_kind,
          public_url: uploadedAsset.public_url,
        });
        setAssetUploadStatus("success");
        setAssetUploadMessage("Banner uploaded and selected for this module.");
      } catch (error) {
        setAssetUploadStatus("error");
        setAssetUploadMessage(readErrorMessage(error, "Banner upload failed."));
      }
    }

    return (
      <div className="site-v3-fieldset site-v3-field-wide">
        <strong>{field.label}</strong>
        <p>{field.help}</p>
        <div className="site-v3-asset-picker" aria-label={`${field.label} asset picker`}>
          <div className="site-v3-asset-picker-heading">
            <span>{assetsStatus === "loading" ? "Loading assets..." : `${siteAssets.length} banners available`}</span>
            {selectedAsset ? <strong>{formatSiteAssetLabel(selectedAsset)} selected</strong> : <strong>No asset selected</strong>}
          </div>
          {assetsStatus === "error" ? (
            <p className="site-v3-message is-error">Assets are unavailable right now. You can still use the manual public URL field.</p>
          ) : null}
          <div className="site-v3-asset-upload">
            <div>
              <strong>Upload banner image</strong>
              <small>Accepted formats: PNG, JPEG, WebP. Max size: 2 MB. Recommended dimensions: 1600x900 or larger, 16:9. Hero media renders as cover/crop with no stretch.</small>
            </div>
            <label className="button-secondary admin-file-label">
              {assetUploadStatus === "uploading" ? "Uploading..." : "Choose image"}
              <input
                accept="image/png,image/jpeg,image/webp"
                className="admin-file-input"
                disabled={assetUploadStatus === "uploading"}
                type="file"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  event.target.value = "";
                  if (file) {
                    void uploadAsset(file);
                  }
                }}
              />
            </label>
          </div>
          {assetUploadMessage ? (
            <p className={`site-v3-message is-${assetUploadStatus === "error" ? "error" : "success"}`} role={assetUploadStatus === "error" ? "alert" : "status"}>
              {assetUploadMessage}
            </p>
          ) : null}
          {siteAssets.length > 0 ? (
            <div className="site-v3-asset-picker-grid">
              {siteAssets.map((asset) => {
                const selected = selectedAsset?.id === asset.id;
                return (
                  <button
                    aria-label={`Use ${formatSiteAssetLabel(asset)}`}
                    aria-pressed={selected}
                    className={`site-v3-asset-option ${selected ? "is-selected" : ""}`}
                    key={asset.id}
                    onClick={() =>
                      onChange({
                        asset_id: asset.id,
                        asset_kind: asset.asset_kind,
                        public_url: asset.public_url,
                      })
                    }
                    type="button"
                  >
                    <img alt="" src={resolveSiteAssetUrl(asset.public_url)} />
                    <span>{formatSiteAssetLabel(asset)}</span>
                    <small>{formatSiteAssetMeta(asset)}</small>
                  </button>
                );
              })}
            </div>
          ) : assetsStatus === "idle" ? (
            <p className="site-v3-message">No banner assets uploaded yet. Choose an image here to add one to the Site V3 picker.</p>
          ) : null}
          {selectedAsset ? (
            <button className="button-secondary" type="button" onClick={() => onChange({})}>
              Clear selected asset
            </button>
          ) : null}
        </div>
        <div className="site-v3-manual-asset-url">
          <label className="site-v3-field site-v3-field-wide">
            <span>Manual public URL</span>
            <input
              value={assetRef.public_url ?? ""}
              placeholder="https://... or /static/..."
              onChange={(event) =>
                onChange({
                  public_url: event.target.value,
                })
              }
            />
            <small>Use this only when the banner is not available in the asset picker yet. Hero media renders as cover/crop with no stretch.</small>
          </label>
          {assetRef.public_url ? (
            <button className="button-secondary" type="button" onClick={() => onChange({})}>
              Clear URL
            </button>
          ) : null}
        </div>
        <span className="site-v3-warning-note">Select an uploaded site banner or paste a public image URL. Hero media renders as cover/crop with no stretch.</span>
      </div>
    );
  }

  if (field.type === "boolean") {
    return (
      <label className="site-v3-check">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        <span>{field.label}</span>
      </label>
    );
  }

  const useTextarea = (field.maxLength ?? 0) > 180 || field.key === "body" || field.key === "legal_text";
  const textValue = toText(value);
  return (
    <label className={`site-v3-field ${useTextarea ? "site-v3-field-wide" : ""}`}>
      {commonLabel}
      {useTextarea ? (
        <textarea value={textValue} onChange={(event) => onChange(event.target.value)} rows={4} maxLength={field.maxLength} />
      ) : (
        <input value={textValue} onChange={(event) => onChange(event.target.value)} maxLength={field.maxLength} />
      )}
      {field.maxLength ? <small className="site-v3-field-counter">{textValue.length}/{field.maxLength}</small> : null}
    </label>
  );
}
