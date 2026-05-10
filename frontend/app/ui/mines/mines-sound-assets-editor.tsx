"use client";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { TitleAsset } from "@/app/lib/types";
import type { MinesSoundKind } from "./use-mines-sounds";

type MinesSoundAssetsEditorProps = {
  assets: TitleAsset[];
  busyAction: string | null;
  onDeleteAsset: (kind: MinesSoundKind) => void;
  onUploadAsset: (kind: MinesSoundKind, file: File | null) => void;
};

const SOUND_FIELDS: Array<{
  kind: MinesSoundKind;
  label: string;
  description: string;
}> = [
  {
    kind: "audio_safe_reveal",
    label: "Safe reveal",
    description: "Quando il player trova un diamante.",
  },
  {
    kind: "audio_mine_hit",
    label: "Mine hit",
    description: "Quando il player trova una mina.",
  },
  {
    kind: "audio_collect",
    label: "Collect",
    description: "Quando il cashout va a buon fine.",
  },
  {
    kind: "audio_win",
    label: "Win",
    description: "Quando la mano chiude in vincita automatica.",
  },
];

export function MinesSoundAssetsEditor({
  assets,
  busyAction,
  onDeleteAsset,
  onUploadAsset,
}: MinesSoundAssetsEditorProps) {
  const assetByKind = new Map(assets.map((asset) => [asset.asset_kind, asset]));

  return (
    <div className="board-assets-panel mines-sound-assets-panel">
      <div className="board-assets-toolbar">
        <div>
          <h3>Sounds</h3>
          <p className="helper">
            MP3, OGG o WAV cortissimo. Max 1 MB. Se manca un asset, il runtime resta silenzioso.
          </p>
        </div>
        <span className="status-inline info">runtime audio</span>
      </div>
      <div className="board-assets-grid mines-sound-assets-grid">
        {SOUND_FIELDS.map((field) => {
          const asset = assetByKind.get(field.kind);
          return (
            <article className="board-asset-row mines-sound-asset-row" key={field.kind}>
              <div className="board-asset-copy">
                <h3>{field.label}</h3>
                <p className="helper">{field.description}</p>
                <span className="meta-pill">
                  {asset ? `${asset.mime} - ${Math.round(asset.byte_size / 1024)} KB` : "Nessun asset"}
                </span>
              </div>
              <div className="board-asset-actions">
                {asset ? (
                  <audio controls preload="none" src={resolveBackendAssetUrl(asset.public_url)} />
                ) : null}
                <label className="button-secondary admin-file-label">
                  Carica file
                  <input
                    type="file"
                    accept="audio/mpeg,audio/ogg,audio/wav,audio/webm"
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
                  Rimuovi
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
