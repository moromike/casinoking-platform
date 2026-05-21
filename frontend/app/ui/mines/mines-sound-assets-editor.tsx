"use client";

import type { TitleAsset } from "@/app/lib/types";
import {
  TitleSoundAssetsEditor,
  type TitleSoundAssetField,
  type TitleSoundAssetKind,
} from "@/app/ui/title-editor/title-sound-assets-editor";

type MinesSoundAssetsEditorProps = {
  assets: TitleAsset[];
  busyAction: string | null;
  onDeleteAsset: (kind: TitleSoundAssetKind) => void;
  onUploadAsset: (kind: TitleSoundAssetKind, file: File | null) => void;
};

const SOUND_FIELDS: TitleSoundAssetField[] = [
  {
    kind: "audio_safe_reveal",
    label: "Safe reveal",
    description: "When the player finds a diamond.",
  },
  {
    kind: "audio_mine_hit",
    label: "Mine hit",
    description: "When the player finds a mine.",
  },
  {
    kind: "audio_collect",
    label: "Collect",
    description: "When cashout completes successfully.",
  },
  {
    kind: "audio_win",
    label: "Win",
    description: "When the hand closes with an automatic win.",
  },
];

export function MinesSoundAssetsEditor({
  assets,
  busyAction,
  onDeleteAsset,
  onUploadAsset,
}: MinesSoundAssetsEditorProps) {
  return (
    <TitleSoundAssetsEditor
      assets={assets}
      busyAction={busyAction}
      fields={SOUND_FIELDS}
      onDeleteAsset={onDeleteAsset}
      onUploadAsset={onUploadAsset}
    />
  );
}
