"use client";

import { useState } from "react";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset } from "@/app/lib/types";

export type HiLoAssetKind =
  | "game_card"
  | "title_logo"
  | "game_area_background"
  | "cell_face_down_background";

type HiLoAssetField = {
  kind: HiLoAssetKind;
  label: string;
  description: string;
  accept: string;
  allowedMimeTypes: string[];
  maxBytes: number;
  guidance: string;
  emptyLabel: string;
};

type HiLoAssetsEditorProps = {
  assets: TitleAsset[];
  busyAction: string | null;
  onDeleteAsset: (kind: HiLoAssetKind) => void;
  onUploadAsset: (kind: HiLoAssetKind, file: File) => void;
};

const HI_LO_ASSET_FIELDS: HiLoAssetField[] = [
  {
    kind: "game_card",
    label: "Lobby card",
    description: "Square card shown in the player lobby.",
    accept: "image/png,image/jpeg,image/webp",
    allowedMimeTypes: ["image/png", "image/jpeg", "image/webp"],
    maxBytes: 300 * 1024,
    guidance: "PNG, JPEG, or WebP. Max 300 KB. Recommended 512 x 512 px.",
    emptyLabel: "Fallback lobby art",
  },
  {
    kind: "title_logo",
    label: "Title logo",
    description: "Optional logo used when theme title presentation is image.",
    accept: "image/png,image/webp",
    allowedMimeTypes: ["image/png", "image/webp"],
    maxBytes: 150 * 1024,
    guidance: "PNG or WebP. Max 150 KB. Recommended 720 x 180 px.",
    emptyLabel: "Text title",
  },
  {
    kind: "game_area_background",
    label: "Game area background",
    description: "Skinned background for the HI-LO card table area.",
    accept: "image/png,image/webp",
    allowedMimeTypes: ["image/png", "image/webp"],
    maxBytes: 400 * 1024,
    guidance: "PNG or WebP. Max 400 KB. Recommended 1280 x 720 px.",
    emptyLabel: "Default table gradient",
  },
  {
    kind: "cell_face_down_background",
    label: "Card back texture",
    description: "Texture shown on the closed/current card back.",
    accept: "image/png,image/webp,image/svg+xml",
    allowedMimeTypes: ["image/png", "image/webp", "image/svg+xml"],
    maxBytes: 256 * 1024,
    guidance: "PNG, WebP, or SVG. Max 256 KB. Recommended 256 x 384 px.",
    emptyLabel: "Default HI-LO card back",
  },
];

export function HiLoAssetsEditor({
  assets,
  busyAction,
  onDeleteAsset,
  onUploadAsset,
}: HiLoAssetsEditorProps) {
  const [inlineError, setInlineError] = useState<string | null>(null);
  const assetByKind = new Map(assets.map((asset) => [asset.asset_kind, asset]));

  function handleUpload(field: HiLoAssetField, file: File | null) {
    setInlineError(null);
    if (!file) {
      return;
    }
    if (!field.allowedMimeTypes.includes(file.type)) {
      setInlineError(`${field.label}: unsupported format. ${field.guidance}`);
      return;
    }
    if (file.size > field.maxBytes) {
      setInlineError(
        `${field.label}: file weighs ${formatBytes(file.size)}; maximum is ${formatBytes(field.maxBytes)}.`,
      );
      return;
    }
    onUploadAsset(field.kind, file);
  }

  return (
    <div className="stack" data-testid="hi-lo-assets-editor">
      {inlineError ? <p className="status-message error">{inlineError}</p> : null}
      <div className="board-assets-panel game-card-assets-panel">
        <div className="board-assets-toolbar">
          <div>
            <h3>HI-LO assets</h3>
            <p className="helper">
              Same asset management surface as Mines, with HI-LO card/table
              semantics.
            </p>
          </div>
          <span className="status-inline info">Lobby, logo, table, card back</span>
        </div>
        <div className="board-assets-grid">
          {HI_LO_ASSET_FIELDS.map((field) => {
            const asset = assetByKind.get(field.kind) ?? null;
            return (
              <article className="board-asset-row" key={field.kind}>
                <div className="board-asset-preview game-card-asset-preview">
                  {asset ? (
                    <img src={resolveBackendAssetUrl(asset.public_url)} alt="" aria-hidden="true" />
                  ) : (
                    <span>{field.emptyLabel}</span>
                  )}
                </div>
                <div className="board-asset-copy">
                  <h3>{field.label}</h3>
                  <p>{field.description}</p>
                  <span className="meta-pill">
                    {asset ? `${asset.mime} - ${formatBytes(asset.byte_size)}` : field.guidance}
                  </span>
                </div>
                <div className="board-asset-actions">
                  <label className="button-secondary admin-file-label">
                    Upload file
                    <input
                      type="file"
                      accept={field.accept}
                      className="admin-file-input"
                      disabled={busyAction !== null}
                      onChange={(event) => {
                        handleUpload(field, event.target.files?.[0] ?? null);
                        event.currentTarget.value = "";
                      }}
                    />
                  </label>
                  <button
                    className="button-ghost"
                    type="button"
                    disabled={!asset || busyAction !== null}
                    onClick={() => onDeleteAsset(field.kind)}
                  >
                    Restore default
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}
