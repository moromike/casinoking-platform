"use client";

import { resolveBackendAssetUrl } from "@/app/lib/api";
import type { MinesPresentationConfig } from "@/app/lib/types";

export type MinesBoardAssetFieldKey = "safe_icon_data_url" | "mine_icon_data_url";

type MinesBoardAssetsEditorProps = {
  config: MinesPresentationConfig;
  onUpdateAsset: (key: MinesBoardAssetFieldKey, file: File | null) => void;
};

export function MinesBoardAssetsEditor({
  config,
  onUpdateAsset,
}: MinesBoardAssetsEditorProps) {
  const assetFields: Array<{
    key: MinesBoardAssetFieldKey;
    label: string;
  }> = [
    {
      key: "safe_icon_data_url",
      label: "Diamond asset",
    },
    {
      key: "mine_icon_data_url",
      label: "Mine asset",
    },
  ];

  return (
    <div className="board-assets-panel">
      <div className="board-assets-toolbar">
        <div>
          <h3>Board assets</h3>
          <p className="helper">SVG o PNG quadrato per diamante e mina.</p>
        </div>
        <span className="status-inline info">max 150 KB</span>
      </div>
      <div className="board-assets-grid">
        {assetFields.map((assetField) => (
          <article className="board-asset-row" key={assetField.key}>
            <div className="board-asset-preview">
              {config.board_assets?.[assetField.key] ? (
                <img
                  src={resolveBackendAssetUrl(
                    config.board_assets[assetField.key] ?? "",
                  )}
                  alt=""
                  aria-hidden="true"
                />
              ) : (
                <span>Default</span>
              )}
            </div>
            <div className="board-asset-copy">
              <h3>{assetField.label}</h3>
              <span className="meta-pill">
                {config.board_assets?.[assetField.key]
                  ? "Draft ready"
                  : "Default runtime"}
              </span>
            </div>
            <div className="board-asset-actions">
              <label className="button-secondary admin-file-label">
                Carica file
                <input
                  type="file"
                  accept="image/svg+xml,image/png"
                  className="admin-file-input"
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    onUpdateAsset(assetField.key, file);
                    event.currentTarget.value = "";
                  }}
                />
              </label>
              <button
                className="button-ghost"
                type="button"
                onClick={() => onUpdateAsset(assetField.key, null)}
              >
                Ripristina default
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
