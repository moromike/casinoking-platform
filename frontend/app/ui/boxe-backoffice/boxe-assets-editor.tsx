"use client";

import { useState } from "react";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset } from "@/app/lib/types";

export type BoxeAssetKind = "game_card" | "symbol_safe" | "symbol_mine";

type BoxeAssetField = {
  kind: BoxeAssetKind;
  label: string;
  description: string;
  accept: string;
  allowedMimeTypes: string[];
  maxBytes: number;
  guidance: string;
  emptyLabel: string;
};

type BoxeAssetsEditorProps = {
  assets: TitleAsset[];
  busyAction: string | null;
  onDeleteAsset: (kind: BoxeAssetKind) => void;
  onUploadAsset: (kind: BoxeAssetKind, file: File) => void;
};

const BOXE_ASSET_FIELDS: BoxeAssetField[] = [
  {
    kind: "game_card",
    label: "Lobby card",
    description: "Square card shown in the player lobby.",
    accept: "image/png,image/jpeg,image/webp",
    allowedMimeTypes: ["image/png", "image/jpeg", "image/webp"],
    maxBytes: 300 * 1024,
    guidance: "PNG, JPEG, or WebP. Max 300 KB. Recommended 512 x 512 px. Rendered cover/center.",
    emptyLabel: "Fallback lobby art",
  },
  {
    kind: "symbol_safe",
    label: "Safe symbol",
    description: "Diamond/safe icon rendered inside revealed safe boxes.",
    accept: "image/png,image/svg+xml",
    allowedMimeTypes: ["image/png", "image/svg+xml"],
    maxBytes: 150 * 1024,
    guidance: "PNG or SVG. Max 150 KB. Recommended 256 x 256 px. Rendered contained, no crop.",
    emptyLabel: "Default diamond",
  },
  {
    kind: "symbol_mine",
    label: "Mine symbol",
    description: "Mine icon rendered when the current row hits a mine.",
    accept: "image/png,image/svg+xml",
    allowedMimeTypes: ["image/png", "image/svg+xml"],
    maxBytes: 150 * 1024,
    guidance: "PNG or SVG. Max 150 KB. Recommended 256 x 256 px. Rendered contained, no crop.",
    emptyLabel: "Default mine",
  },
];

export function BoxeAssetsEditor({
  assets,
  busyAction,
  onDeleteAsset,
  onUploadAsset,
}: BoxeAssetsEditorProps) {
  const [inlineError, setInlineError] = useState<string | null>(null);
  const assetByKind = new Map(assets.map((asset) => [asset.asset_kind, asset]));

  function handleUpload(field: BoxeAssetField, file: File | null) {
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
    <article className="admin-card" data-testid="boxe-assets-editor">
      <div className="admin-card-heading">
        <div>
          <h3>Assets / Lobby card</h3>
          <p>BOXE uses Title asset registry kinds: game_card, symbol_safe, symbol_mine.</p>
        </div>
        <span className="status-inline info">registry</span>
      </div>

      {inlineError ? <p className="status-message error">{inlineError}</p> : null}

      <div className="stack">
        {BOXE_ASSET_FIELDS.map((field) => {
          const asset = assetByKind.get(field.kind) ?? null;
          return (
            <section className="board-asset-row" key={field.kind}>
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
                <p className="helper">{field.guidance}</p>
                <span className="meta-pill">
                  {asset ? `${asset.mime} - ${formatBytes(asset.byte_size)}` : "No uploaded asset"}
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
                  Remove
                </button>
              </div>
            </section>
          );
        })}
      </div>

      <div className="stack compact">
        <h4>Sounds</h4>
        <p className="helper">
          BOXE v1 keeps silent/default platform audio. The 3C audio hook remains ready
          for future sound assets without adding a Sounds tab in this WP.
        </p>
      </div>
    </article>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}
