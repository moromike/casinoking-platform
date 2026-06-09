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
  const lobbyField = BOXE_ASSET_FIELDS[0];
  const boardAssetFields = BOXE_ASSET_FIELDS.slice(1);

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
    <div className="stack" data-testid="boxe-assets-editor">
      <div className="board-assets-panel game-card-assets-panel">
        <div className="board-assets-toolbar">
          <div>
            <h3>Lobby card</h3>
            <p className="helper">{lobbyField.guidance}</p>
          </div>
        </div>

        <article className="board-asset-row game-card-asset-row">
          <div className="board-asset-preview game-card-asset-preview">
            {assetByKind.get(lobbyField.kind) ? (
              <img
                src={resolveBackendAssetUrl(assetByKind.get(lobbyField.kind)?.public_url ?? "")}
                alt=""
                aria-hidden="true"
              />
            ) : (
              <span>No card</span>
            )}
          </div>
          <div className="board-asset-copy">
            <h3>Game card</h3>
            <p>
              {assetByKind.get(lobbyField.kind)
                ? `${assetByKind.get(lobbyField.kind)?.mime} - ${formatBytes(
                    assetByKind.get(lobbyField.kind)?.byte_size ?? 0,
                  )}`
                : "When missing, the lobby uses the BOXE fallback art."}
            </p>
            {inlineError ? <p className="status-message error">{inlineError}</p> : null}
          </div>
          <div className="board-asset-actions">
            <label className="button-secondary admin-file-label">
              Upload file
              <input
                type="file"
                accept={lobbyField.accept}
                className="admin-file-input"
                disabled={busyAction !== null}
                onChange={(event) => {
                  handleUpload(lobbyField, event.target.files?.[0] ?? null);
                  event.currentTarget.value = "";
                }}
              />
            </label>
            <button
              className="button-ghost"
              type="button"
              disabled={!assetByKind.get(lobbyField.kind) || busyAction !== null}
              onClick={() => onDeleteAsset(lobbyField.kind)}
            >
              Remove card
            </button>
          </div>
        </article>
      </div>

      <div className="board-assets-panel">
        <div className="board-assets-toolbar">
          <div>
            <h3>Board assets</h3>
            <p className="helper">
              Safe and mine icons. SVG or PNG only. Max 150 KB each. Recommended
              256 x 256 px square art. Rendered contained in the box, without
              crop or stretch.
            </p>
          </div>
          <span className="status-inline info">SVG/PNG - 256 x 256 px - max 150 KB</span>
        </div>
        <div className="board-assets-grid">
          {boardAssetFields.map((field) => {
            const asset = assetByKind.get(field.kind) ?? null;
            return (
              <article className="board-asset-row" key={field.kind}>
                <div className="board-asset-preview">
                  {asset ? (
                    <img src={resolveBackendAssetUrl(asset.public_url)} alt="" aria-hidden="true" />
                  ) : (
                    <span>Default</span>
                  )}
                </div>
                <div className="board-asset-copy">
                  <h3>{field.label}</h3>
                  <span className="meta-pill">
                    {asset ? `${asset.mime} - ${formatBytes(asset.byte_size)}` : field.emptyLabel}
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
