"use client";

import { resolvePublicAssetUrl } from "../../lib/api";
import type { GameLibraryTitle } from "../../lib/types";
import { useState } from "react";
import { LaunchCashier } from "./launch-cashier";

export function GameCard({ title }: { title: GameLibraryTitle }) {
  const [cashierOpen, setCashierOpen] = useState(false);

  return (
    <>
      <button
        aria-label={`Open launch cashier for ${title.display_name}`}
        className="site-v3-game-card player-lobby-card"
        onClick={() => setCashierOpen(true)}
        type="button"
      >
        <GameArtwork title={title} />
        <span className="site-v3-game-card-overlay">
          <small>{title.engine_display_name}</small>
          <strong>{title.display_name}</strong>
        </span>
      </button>
      {cashierOpen ? (
        <LaunchCashier title={title} onClose={() => setCashierOpen(false)} />
      ) : null}
    </>
  );
}

export function GameArtwork({ title }: { title: GameLibraryTitle }) {
  const assetUrl = resolvePublicAssetUrl(title.game_card_asset?.public_url);
  if (assetUrl) {
    return <img alt="" className="site-v3-game-art" src={assetUrl} />;
  }
  return (
    <div className="site-v3-game-art site-v3-game-art-fallback">
      <span>{fallbackGlyph(title)}</span>
      <strong>{title.display_name}</strong>
    </div>
  );
}

function fallbackGlyph(title: GameLibraryTitle): string {
  if (title.engine_code === "hi_lo") {
    return "A";
  }
  if (title.engine_code === "boxe") {
    return "BX";
  }
  return "M";
}
