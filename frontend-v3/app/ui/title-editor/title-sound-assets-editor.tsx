"use client";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset } from "@/app/lib/types";

export type TitleSoundAssetKind =
  | "audio_safe_reveal"
  | "audio_mine_hit"
  | "audio_collect"
  | "audio_win";

export type TitleSoundAssetField = {
  kind: TitleSoundAssetKind;
  label: string;
  description: string;
};

type TitleSoundAssetsEditorProps = {
  assets: TitleAsset[];
  busyAction: string | null;
  fields: TitleSoundAssetField[];
  onDeleteAsset: (kind: TitleSoundAssetKind) => void;
  onUploadAsset: (kind: TitleSoundAssetKind, file: File | null) => void;
};

export const TITLE_SOUND_ASSET_ACCEPT = "audio/mpeg,audio/ogg,audio/wav,audio/webm";
export const TITLE_SOUND_ASSET_MIME_TYPES = [
  "audio/mpeg",
  "audio/ogg",
  "audio/wav",
  "audio/webm",
] as const;
export const TITLE_SOUND_ASSET_MAX_BYTES = 1024 * 1024;

export function TitleSoundAssetsEditor({
  assets,
  busyAction,
  fields,
  onDeleteAsset,
  onUploadAsset,
}: TitleSoundAssetsEditorProps) {
  const assetByKind = new Map(assets.map((asset) => [asset.asset_kind, asset]));

  return (
    <div className="board-assets-panel mines-sound-assets-panel">
      <div className="board-assets-toolbar">
        <div>
          <h3>Sounds</h3>
          <p className="helper">
            Very short MP3, OGG, WAV, or WebM audio. Max 1 MB each. No pixel
            dimensions. If an asset is missing, the runtime stays silent.
          </p>
        </div>
        <span className="status-inline info">runtime audio</span>
      </div>
      <div className="board-assets-grid mines-sound-assets-grid">
        {fields.map((field) => {
          const asset = assetByKind.get(field.kind);
          return (
            <article className="board-asset-row mines-sound-asset-row" key={field.kind}>
              <div className="board-asset-copy">
                <h3>{field.label}</h3>
                <p className="helper">{field.description}</p>
                <span className="meta-pill">
                  {asset ? `${asset.mime} - ${Math.round(asset.byte_size / 1024)} KB` : "No asset"}
                </span>
              </div>
              <div className="board-asset-actions">
                {asset ? (
                  <audio controls preload="none" src={resolveBackendAssetUrl(asset.public_url)} />
                ) : null}
                <label className="button-secondary admin-file-label">
                  Upload file
                  <input
                    type="file"
                    accept={TITLE_SOUND_ASSET_ACCEPT}
                    className="admin-file-input"
                    disabled={busyAction !== null}
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      onUploadAsset(field.kind, file);
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
            </article>
          );
        })}
      </div>
    </div>
  );
}
