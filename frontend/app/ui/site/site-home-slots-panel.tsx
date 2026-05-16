"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  ApiRequestError,
  apiDeleteRequest,
  apiFormRequest,
  apiRequest,
  readErrorMessage,
} from "@/app/lib/api";
import type { CatalogTitle } from "@/app/ui/platform-catalog-panel";

const SITE_CODE = "casinoking";
const HOMEPAGE_BANNER_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];
const HOMEPAGE_BANNER_MAX_BYTES = 2 * 1024 * 1024;

type HomeSlotTargetType = "none" | "title_demo" | "title_real";
type HomeSlotStatus = "draft" | "published" | "archived";

type SiteHomeSlot = {
  id: string;
  site_code: string;
  slot_key: string;
  title: string;
  subtitle: string | null;
  cta_label: string | null;
  cta_target_type: HomeSlotTargetType;
  cta_target_ref: string | null;
  media_asset_id: string | null;
  sort_order: number;
  status: HomeSlotStatus;
  starts_at: string | null;
  ends_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
  media_asset: SiteAsset | null;
};

type SiteAsset = {
  id: string;
  site_code: string;
  asset_kind: "homepage_banner";
  file_path?: string;
  public_url: string;
  mime: string;
  byte_size: number;
  checksum_sha256: string;
  uploaded_by_admin_user_id?: string | null;
  created_at: string;
  status: "active" | "deleted";
};

type SiteHomeSlotsResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  slots: SiteHomeSlot[];
};

type SiteTitlesResponse = {
  site: {
    site_code: string;
    display_name: string;
    status: string;
  };
  titles: CatalogTitle[];
};

type HomeSlotDraft = {
  slot_key: string;
  title: string;
  subtitle: string;
  cta_label: string;
  cta_target_type: HomeSlotTargetType;
  cta_target_ref: string;
  media_asset_id: string | null;
  sort_order: string;
  status: HomeSlotStatus;
  starts_at: string;
  ends_at: string;
};

type SiteHomeSlotsPanelProps = {
  accessToken: string;
  refreshKey?: number;
};

type PublishableTarget = {
  titleCode: string;
  label: string;
  demoEnabled: boolean;
  realEnabled: boolean;
};

const emptyDraft: HomeSlotDraft = {
  slot_key: "",
  title: "",
  subtitle: "",
  cta_label: "",
  cta_target_type: "none",
  cta_target_ref: "",
  media_asset_id: null,
  sort_order: "0",
  status: "draft",
  starts_at: "",
  ends_at: "",
};

export function SiteHomeSlotsPanel({
  accessToken,
  refreshKey = 0,
}: SiteHomeSlotsPanelProps) {
  const [slotsData, setSlotsData] = useState<SiteHomeSlotsResponse | null>(null);
  const [slotsStatus, setSlotsStatus] = useState<"idle" | "loading" | "error">("idle");
  const [slotsMessage, setSlotsMessage] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<SiteTitlesResponse | null>(null);
  const [catalogStatus, setCatalogStatus] = useState<"idle" | "loading" | "error">("idle");
  const [catalogMessage, setCatalogMessage] = useState<string | null>(null);
  const [siteAssets, setSiteAssets] = useState<SiteAsset[]>([]);
  const [assetsStatus, setAssetsStatus] = useState<"idle" | "loading" | "error">("idle");
  const [assetsMessage, setAssetsMessage] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, HomeSlotDraft>>({});
  const [newDraft, setNewDraft] = useState<HomeSlotDraft>(emptyDraft);
  const [busySlotKey, setBusySlotKey] = useState<string | null>(null);
  const [busyAssetId, setBusyAssetId] = useState<string | null>(null);
  const [localMessage, setLocalMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!accessToken) {
      setSlotsData(null);
      setSlotsStatus("idle");
      setSlotsMessage("Admin login is required.");
      return;
    }

    let isMounted = true;
    setSlotsStatus("loading");
    setSlotsMessage(null);

    apiRequest<SiteHomeSlotsResponse>(
      `/admin/sites/${SITE_CODE}/home-slots`,
      {},
      accessToken,
    )
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setSlotsData(data);
        setSlotsStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setSlotsStatus("error");
        setSlotsMessage(readErrorMessage(error, "Homepage slots loading failed."));
      });

    return () => {
      isMounted = false;
    };
  }, [accessToken, refreshKey]);

  useEffect(() => {
    let isMounted = true;
    setCatalogStatus("loading");
    setCatalogMessage(null);

    apiRequest<SiteTitlesResponse>(`/catalog/sites/${SITE_CODE}/titles`)
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setCatalog(data);
        setCatalogStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setCatalogStatus("error");
        setCatalogMessage(
          error instanceof ApiRequestError ? error.message : "Title catalog is not available.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  useEffect(() => {
    if (!accessToken) {
      setSiteAssets([]);
      setAssetsStatus("idle");
      setAssetsMessage("Admin login is required.");
      return;
    }

    let isMounted = true;
    setAssetsStatus("loading");
    setAssetsMessage(null);

    apiRequest<SiteAsset[]>(
      `/admin/sites/${SITE_CODE}/assets?asset_kind=homepage_banner`,
      {},
      accessToken,
    )
      .then((assets) => {
        if (!isMounted) {
          return;
        }
        setSiteAssets(assets);
        setAssetsStatus("idle");
      })
      .catch((error: unknown) => {
        if (!isMounted) {
          return;
        }
        setAssetsStatus("error");
        setAssetsMessage(readErrorMessage(error, "Banner media loading failed."));
      });

    return () => {
      isMounted = false;
    };
  }, [accessToken, refreshKey]);

  useEffect(() => {
    if (!slotsData) {
      return;
    }
    setDrafts(
      Object.fromEntries(slotsData.slots.map((slot) => [slot.slot_key, slotToDraft(slot)])),
    );
  }, [slotsData]);

  const slots = slotsData?.slots ?? [];
  const publishableTargets = useMemo(
    () =>
      (catalog?.titles ?? [])
        .filter(isPublishableTargetTitle)
        .map((title) => ({
          titleCode: title.title_code,
          label: title.publication.lobby_display_name ?? title.display_name,
          demoEnabled: title.publication.demo_enabled,
          realEnabled: title.publication.real_enabled,
        }))
        .sort((left, right) => left.label.localeCompare(right.label, undefined, { sensitivity: "base" })),
    [catalog],
  );
  const publishedSlots = slots.filter((slot) => slot.status === "published");
  const isBusy = busySlotKey !== null || busyAssetId !== null;

  function updateDraft(slotKey: string, patch: Partial<HomeSlotDraft>) {
    setDrafts((current) => {
      const base = current[slotKey] ?? slotToDraft(slots.find((slot) => slot.slot_key === slotKey));
      return {
        ...current,
        [slotKey]: normalizeTargetPatch({ ...base, ...patch }, patch, publishableTargets),
      };
    });
  }

  function updateNewDraft(patch: Partial<HomeSlotDraft>) {
    setNewDraft((current) => normalizeTargetPatch({ ...current, ...patch }, patch, publishableTargets));
  }

  async function handleCreateSlot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isBusy) {
      return;
    }

    setBusySlotKey("__new__");
    setLocalMessage(null);
    try {
      const createdSlot = await apiRequest<SiteHomeSlot>(
        `/admin/sites/${SITE_CODE}/home-slots`,
        {
          method: "POST",
          body: JSON.stringify(draftToPayload(newDraft, true)),
        },
        accessToken,
      );
      setSlotsData((current) => mergeSlot(current, createdSlot));
      setNewDraft(emptyDraft);
      setLocalMessage({ kind: "success", text: `Slot ${createdSlot.slot_key} created.` });
    } catch (error) {
      setLocalMessage({ kind: "error", text: readErrorMessage(error, "Slot creation failed.") });
    } finally {
      setBusySlotKey(null);
    }
  }

  async function handleSaveSlot(event: FormEvent<HTMLFormElement>, slot: SiteHomeSlot) {
    event.preventDefault();
    if (!accessToken || isBusy) {
      return;
    }

    const draft = drafts[slot.slot_key] ?? slotToDraft(slot);
    setBusySlotKey(slot.slot_key);
    setLocalMessage(null);
    try {
      const updatedSlot = await apiRequest<SiteHomeSlot>(
        `/admin/sites/${SITE_CODE}/home-slots/${encodeURIComponent(slot.slot_key)}`,
        {
          method: "PATCH",
          body: JSON.stringify(draftToPayload(draft, false)),
        },
        accessToken,
      );
      setSlotsData((current) => mergeSlot(current, updatedSlot));
      setLocalMessage({ kind: "success", text: `Slot ${updatedSlot.slot_key} saved.` });
    } catch (error) {
      setLocalMessage({ kind: "error", text: readErrorMessage(error, "Slot save failed.") });
    } finally {
      setBusySlotKey(null);
    }
  }

  async function handleUploadAsset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isBusy) {
      return;
    }
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("file");
    if (!(fileInput instanceof HTMLInputElement) || !fileInput.files?.[0]) {
      setLocalMessage({ kind: "error", text: "Select a banner image before upload." });
      return;
    }

    const selectedFile = fileInput.files[0];
    if (!HOMEPAGE_BANNER_ALLOWED_MIME_TYPES.includes(selectedFile.type)) {
      setLocalMessage({
        kind: "error",
        text: "File not uploaded: homepage banners support PNG, JPEG, or WebP only.",
      });
      return;
    }
    if (selectedFile.size > HOMEPAGE_BANNER_MAX_BYTES) {
      setLocalMessage({
        kind: "error",
        text: `File not uploaded: it weighs ${formatBytes(selectedFile.size)}. The homepage banner limit is 2 MB.`,
      });
      return;
    }

    const formData = new FormData();
    formData.set("asset_kind", "homepage_banner");
    formData.set("file", selectedFile);

    setBusyAssetId("__upload__");
    setLocalMessage(null);
    try {
      const uploadedAsset = await apiFormRequest<SiteAsset>(
        `/admin/sites/${SITE_CODE}/assets`,
        formData,
        accessToken,
      );
      setSiteAssets((current) => mergeAsset(current, uploadedAsset));
      form.reset();
      setLocalMessage({ kind: "success", text: "Banner image uploaded." });
    } catch (error) {
      setLocalMessage({ kind: "error", text: readErrorMessage(error, "Banner upload failed.") });
    } finally {
      setBusyAssetId(null);
    }
  }

  async function handleDeleteAsset(asset: SiteAsset) {
    if (!accessToken || isBusy) {
      return;
    }

    setBusyAssetId(asset.id);
    setLocalMessage(null);
    try {
      await apiDeleteRequest<SiteAsset>(
        `/admin/sites/${SITE_CODE}/assets/${encodeURIComponent(asset.id)}`,
        accessToken,
      );
      setSiteAssets((current) => current.filter((item) => item.id !== asset.id));
      setDrafts((current) =>
        Object.fromEntries(
          Object.entries(current).map(([slotKey, draft]) => [
            slotKey,
            draft.media_asset_id === asset.id ? { ...draft, media_asset_id: null } : draft,
          ]),
        ),
      );
      setSlotsData((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          slots: current.slots.map((slot) =>
            slot.media_asset_id === asset.id
              ? { ...slot, media_asset_id: null, media_asset: null }
              : slot,
          ),
        };
      });
      setLocalMessage({ kind: "success", text: "Banner image deleted." });
    } catch (error) {
      setLocalMessage({ kind: "error", text: readErrorMessage(error, "Banner delete failed.") });
    } finally {
      setBusyAssetId(null);
    }
  }

  return (
    <article className="admin-card site-home-panel">
      <header className="site-home-header">
        <div>
          <p className="eyebrow">Site / Homepage</p>
          <h3>Homepage slots</h3>
          <p>Admin editor for CasinoKing site banners and spotlights.</p>
        </div>
        <div className="site-home-kpis" aria-label="Homepage slots summary">
          <span>{slotsStatus === "loading" ? "loading" : `${slots.length} slots`}</span>
          <span>{publishedSlots.length} published</span>
        </div>
      </header>

      {slotsMessage ? <p className="site-home-status error">{slotsMessage}</p> : null}
      {catalogMessage ? <p className="site-home-status error">{catalogMessage}</p> : null}
      {assetsMessage ? <p className="site-home-status error">{assetsMessage}</p> : null}
      {localMessage ? <p className={`site-home-status ${localMessage.kind}`}>{localMessage.text}</p> : null}

      <div className="site-home-workspace">
        <section className="site-home-zone" aria-labelledby="site-home-assets-title">
          <div className="site-home-zone-heading">
            <div>
              <h4 id="site-home-assets-title">Banner media</h4>
              <p>
                Homepage banner images. PNG, JPEG, or WebP. Max 2 MB. Recommended 1280 x
                720 px (16:9). Rendered as centered cover, so edges may crop; never
                stretched.
              </p>
            </div>
            <span>{assetsStatus === "loading" ? "media loading" : `${siteAssets.length} media`}</span>
          </div>
          <form className="site-home-asset-upload" onSubmit={handleUploadAsset}>
            <label className="site-home-field">
              <span>Upload image (PNG/JPEG/WebP, max 2 MB, 1280 x 720 px)</span>
              <input
                accept="image/png,image/jpeg,image/webp"
                disabled={isBusy}
                name="file"
                type="file"
              />
            </label>
            <button className="button-secondary" type="submit" disabled={isBusy || !accessToken}>
              {busyAssetId === "__upload__" ? "Uploading..." : "Upload"}
            </button>
          </form>
          {assetsStatus === "loading" && siteAssets.length === 0 ? (
            <div className="site-home-empty">Loading banner media...</div>
          ) : null}
          {assetsStatus === "error" && siteAssets.length === 0 ? (
            <div className="site-home-empty error">Banner media is not available.</div>
          ) : null}
          {siteAssets.length > 0 ? (
            <div className="site-home-asset-list">
              {siteAssets.map((asset) => (
                <article className="site-home-asset-card" key={asset.id}>
                  <img alt="" src={resolveSiteAssetUrl(asset.public_url)} />
                  <div>
                    <strong>{formatAssetLabel(asset)}</strong>
                    <span>{formatAssetMeta(asset)}</span>
                  </div>
                  <button
                    className="button-secondary"
                    disabled={isBusy}
                    type="button"
                    onClick={() => void handleDeleteAsset(asset)}
                  >
                    {busyAssetId === asset.id ? "Deleting..." : "Delete"}
                  </button>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        <section className="site-home-zone" aria-labelledby="site-home-create-title">
          <div className="site-home-zone-heading">
            <div>
              <h4 id="site-home-create-title">New slot</h4>
              <p>
                To publish: upload a banner, select it in Banner image, set Status to
                Published, then Create slot. Schedule is optional.
              </p>
            </div>
          </div>
          <form className="site-home-editor" onSubmit={handleCreateSlot}>
            <SlotFields
              draft={newDraft}
              publishableTargets={publishableTargets}
              siteAssets={siteAssets}
              isCreate
              disabled={isBusy}
              onDraftChange={updateNewDraft}
            />
            <div className="site-home-row-footer">
              <SlotPreview
                draft={newDraft}
                publishableTargets={publishableTargets}
                siteAssets={siteAssets}
              />
              <button className="button-secondary" type="submit" disabled={isBusy || !accessToken}>
                {busySlotKey === "__new__" ? "Creating..." : "Create slot"}
              </button>
            </div>
          </form>
        </section>

        <section className="site-home-zone" aria-labelledby="site-home-list-title">
          <div className="site-home-zone-heading">
            <div>
              <h4 id="site-home-list-title">Existing slots</h4>
              <p>Order, publication, and CTA targets are saved in the Site CMS.</p>
            </div>
            <span>{catalogStatus === "loading" ? "target loading" : `${publishableTargets.length} target`}</span>
          </div>

          {slotsStatus === "loading" && !slotsData ? (
            <div className="site-home-empty">Loading homepage slots...</div>
          ) : null}
          {slotsStatus === "error" && !slotsData ? (
            <div className="site-home-empty error">Homepage slots are not available.</div>
          ) : null}
          {slotsData && slots.length === 0 ? (
            <div className="site-home-empty">No homepage slots configured.</div>
          ) : null}
          {slots.length > 0 ? (
            <div className="site-home-slot-list">
              {slots.map((slot) => {
                const draft = drafts[slot.slot_key] ?? slotToDraft(slot);
                return (
                  <form
                    className="site-home-slot-row"
                    key={slot.slot_key}
                    onSubmit={(event) => void handleSaveSlot(event, slot)}
                  >
                    <div className="site-home-slot-meta">
                      <strong>{slot.slot_key}</strong>
                      <span>{slot.media_asset_id ? formatSelectedAsset(slot.media_asset_id, siteAssets) : "media fallback"}</span>
                      <span>updated {formatShortDate(slot.updated_at)}</span>
                    </div>
                    <SlotFields
                      draft={draft}
                      publishableTargets={publishableTargets}
                      siteAssets={siteAssets}
                      disabled={isBusy}
                      onDraftChange={(patch) => updateDraft(slot.slot_key, patch)}
                    />
                    <div className="site-home-row-footer">
                      <SlotPreview
                        draft={draft}
                        publishableTargets={publishableTargets}
                        siteAssets={siteAssets}
                      />
                      <button className="button-secondary" type="submit" disabled={isBusy || !accessToken}>
                        {busySlotKey === slot.slot_key ? "Saving..." : "Save"}
                      </button>
                    </div>
                  </form>
                );
              })}
            </div>
          ) : null}
        </section>
      </div>
    </article>
  );
}

function SlotFields({
  draft,
  publishableTargets,
  siteAssets,
  disabled,
  isCreate = false,
  onDraftChange,
}: {
  draft: HomeSlotDraft;
  publishableTargets: PublishableTarget[];
  siteAssets: SiteAsset[];
  disabled: boolean;
  isCreate?: boolean;
  onDraftChange: (patch: Partial<HomeSlotDraft>) => void;
}) {
  const targetOptions = getTargetsForType(draft.cta_target_type, publishableTargets);

  return (
    <div className="site-home-field-grid">
      {isCreate ? (
        <label className="site-home-field">
          <span>Slot key</span>
          <input
            value={draft.slot_key}
            disabled={disabled}
            onChange={(event) => onDraftChange({ slot_key: event.target.value })}
            placeholder="homepage-hero"
          />
        </label>
      ) : null}
      <label className="site-home-field">
        <span>Title</span>
        <input
          value={draft.title}
          disabled={disabled}
          onChange={(event) => onDraftChange({ title: event.target.value })}
        />
      </label>
      <label className="site-home-field">
        <span>Subtitle</span>
        <textarea
          value={draft.subtitle}
          disabled={disabled}
          onChange={(event) => onDraftChange({ subtitle: event.target.value })}
        />
      </label>
      <label className="site-home-field">
        <span>CTA label</span>
        <input
          value={draft.cta_label}
          disabled={disabled}
          onChange={(event) => onDraftChange({ cta_label: event.target.value })}
        />
      </label>
      <label className="site-home-field">
        <span>Target type</span>
        <select
          value={draft.cta_target_type}
          disabled={disabled}
          onChange={(event) => onDraftChange({ cta_target_type: event.target.value as HomeSlotTargetType })}
        >
          <option value="none">None</option>
          <option value="title_demo">Title demo</option>
          <option value="title_real">Title real</option>
        </select>
      </label>
      <label className="site-home-field">
        <span>Target ref</span>
        <select
          value={draft.cta_target_ref}
          disabled={disabled || draft.cta_target_type === "none"}
          onChange={(event) => onDraftChange({ cta_target_ref: event.target.value })}
        >
          <option value="">No title selected</option>
          {targetOptions.map((target) => (
            <option key={target.titleCode} value={target.titleCode}>
              {target.label} ({target.titleCode})
            </option>
          ))}
        </select>
      </label>
      <label className="site-home-field">
        <span>Banner image</span>
        <select
          value={draft.media_asset_id ?? ""}
          disabled={disabled}
          onChange={(event) => onDraftChange({ media_asset_id: event.target.value || null })}
        >
          <option value="">Fallback / no image</option>
          {siteAssets.map((asset) => (
            <option key={asset.id} value={asset.id}>
              {formatAssetLabel(asset)}
            </option>
          ))}
        </select>
      </label>
      <label className="site-home-field">
        <span>Sort order</span>
        <input
          type="number"
          min="0"
          value={draft.sort_order}
          disabled={disabled}
          onChange={(event) => onDraftChange({ sort_order: event.target.value })}
        />
      </label>
      <label className="site-home-field">
        <span>Status</span>
        <select
          value={draft.status}
          disabled={disabled}
          onChange={(event) => onDraftChange({ status: event.target.value as HomeSlotStatus })}
        >
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="archived">Archived</option>
        </select>
      </label>
      <label className="site-home-field">
        <span>Starts at</span>
        <input
          type="datetime-local"
          value={draft.starts_at}
          disabled={disabled}
          onChange={(event) => onDraftChange({ starts_at: event.target.value })}
        />
      </label>
      <label className="site-home-field">
        <span>Ends at</span>
        <input
          type="datetime-local"
          value={draft.ends_at}
          disabled={disabled}
          onChange={(event) => onDraftChange({ ends_at: event.target.value })}
        />
      </label>
    </div>
  );
}

function SlotPreview({
  draft,
  publishableTargets,
  siteAssets,
}: {
  draft: HomeSlotDraft;
  publishableTargets: PublishableTarget[];
  siteAssets: SiteAsset[];
}) {
  const target = publishableTargets.find((item) => item.titleCode === draft.cta_target_ref);
  const mediaAsset = siteAssets.find((asset) => asset.id === draft.media_asset_id) ?? null;
  const ctaMode =
    draft.cta_target_type === "title_demo"
      ? "demo"
      : draft.cta_target_type === "title_real"
        ? "real"
        : "none";

  return (
    <div className="site-home-preview" aria-label="Homepage slot compact preview">
      <div
        className={`site-home-preview-art ${mediaAsset ? "has-media" : ""}`}
        style={
          mediaAsset
            ? {
                backgroundImage: `linear-gradient(135deg, rgba(8, 47, 73, 0.82), rgba(30, 64, 175, 0.48)), url("${resolveSiteAssetUrl(mediaAsset.public_url)}")`,
              }
            : undefined
        }
      >
        <span>{draft.status}</span>
        <strong>{draft.title || "Untitled slot"}</strong>
      </div>
      <div className="site-home-preview-copy">
        <p>{draft.subtitle || "No subtitle"}</p>
        <div className="site-home-preview-meta">
          <span>{draft.cta_label || "No CTA label"}</span>
          <span>{ctaMode}</span>
          {target ? <span>{target.label}</span> : null}
        </div>
      </div>
    </div>
  );
}

function slotToDraft(slot?: SiteHomeSlot): HomeSlotDraft {
  if (!slot) {
    return emptyDraft;
  }
  return {
    slot_key: slot.slot_key,
    title: slot.title,
    subtitle: slot.subtitle ?? "",
    cta_label: slot.cta_label ?? "",
    cta_target_type: slot.cta_target_type,
    cta_target_ref: slot.cta_target_ref ?? "",
    media_asset_id: slot.media_asset_id,
    sort_order: String(slot.sort_order),
    status: slot.status,
    starts_at: isoToDatetimeLocal(slot.starts_at),
    ends_at: isoToDatetimeLocal(slot.ends_at),
  };
}

function draftToPayload(draft: HomeSlotDraft, includeSlotKey: boolean) {
  const payload = {
    title: draft.title,
    subtitle: draft.subtitle || null,
    cta_label: draft.cta_label || null,
    cta_target_type: draft.cta_target_type,
    cta_target_ref: draft.cta_target_type === "none" ? null : draft.cta_target_ref || null,
    media_asset_id: draft.media_asset_id,
    sort_order: parseSortOrder(draft.sort_order),
    status: draft.status,
    starts_at: datetimeLocalToIso(draft.starts_at),
    ends_at: datetimeLocalToIso(draft.ends_at),
  };

  if (!includeSlotKey) {
    return payload;
  }

  return {
    slot_key: draft.slot_key,
    ...payload,
  };
}

function isPublishableTargetTitle(title: CatalogTitle): boolean {
  return (
    !title.is_master &&
    title.status === "active" &&
    title.site_title_status === "active" &&
    title.publication.site_title_status === "active" &&
    title.publication.lobby_visibility === "visible" &&
    (title.publication.demo_enabled || title.publication.real_enabled)
  );
}

function getTargetsForType(targetType: HomeSlotTargetType, targets: PublishableTarget[]): PublishableTarget[] {
  if (targetType === "title_demo") {
    return targets.filter((target) => target.demoEnabled);
  }
  if (targetType === "title_real") {
    return targets.filter((target) => target.realEnabled);
  }
  return [];
}

function normalizeTargetPatch(
  draft: HomeSlotDraft,
  patch: Partial<HomeSlotDraft>,
  targets: PublishableTarget[],
): HomeSlotDraft {
  if (!("cta_target_type" in patch)) {
    return draft;
  }
  if (draft.cta_target_type === "none") {
    return { ...draft, cta_target_ref: "" };
  }
  const targetOptions = getTargetsForType(draft.cta_target_type, targets);
  if (targetOptions.some((target) => target.titleCode === draft.cta_target_ref)) {
    return draft;
  }
  return {
    ...draft,
    cta_target_ref: targetOptions[0]?.titleCode ?? "",
  };
}

function mergeSlot(current: SiteHomeSlotsResponse | null, slot: SiteHomeSlot): SiteHomeSlotsResponse {
  const site = current?.site ?? {
    site_code: slot.site_code,
    display_name: "CasinoKing",
    status: "active",
  };
  const nextSlots = [
    ...(current?.slots.filter((item) => item.slot_key !== slot.slot_key) ?? []),
    slot,
  ].sort((left, right) => {
    const sortDiff = left.sort_order - right.sort_order;
    if (sortDiff !== 0) {
      return sortDiff;
    }
    return left.slot_key.localeCompare(right.slot_key);
  });

  return {
    site,
    slots: nextSlots,
  };
}

function mergeAsset(current: SiteAsset[], asset: SiteAsset): SiteAsset[] {
  return [asset, ...current.filter((item) => item.id !== asset.id)].sort((left, right) => {
    const createdDiff = new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
    if (Number.isFinite(createdDiff) && createdDiff !== 0) {
      return createdDiff;
    }
    return left.id.localeCompare(right.id);
  });
}

function resolveSiteAssetUrl(assetUrl: string): string {
  if (!assetUrl.startsWith("/static/sites/")) {
    return assetUrl;
  }
  const apiBase = new URL(API_BASE_URL);
  return `${apiBase.origin}${assetUrl}`;
}

function formatAssetLabel(asset: SiteAsset): string {
  return `Banner ${asset.checksum_sha256.slice(0, 8)}`;
}

function formatSelectedAsset(assetId: string, assets: SiteAsset[]): string {
  const asset = assets.find((item) => item.id === assetId);
  return asset ? formatAssetLabel(asset) : "media selected";
}

function formatAssetMeta(asset: SiteAsset): string {
  return `${asset.mime} - ${formatBytes(asset.byte_size)} - ${formatShortDate(asset.created_at)}`;
}

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "0 KB";
  }
  if (value < 1024 * 1024) {
    return `${Math.ceil(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function isoToDatetimeLocal(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return offsetDate.toISOString().slice(0, 16);
}

function datetimeLocalToIso(value: string): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
}

function formatShortDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "n/a";
  }
  return date.toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function parseSortOrder(value: string): number {
  const parsed = Number.parseInt(value || "0", 10);
  if (Number.isNaN(parsed) || parsed < 0) {
    return 0;
  }
  return parsed;
}
