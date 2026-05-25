import { resolvePublicAssetUrl } from "../../lib/api";
import type { GameLibraryTitle } from "../../lib/types";
import { resolveGameHref } from "../site-v3-render-helpers";

export function GameCard({ title }: { title: GameLibraryTitle }) {
  return (
    <article className="site-v3-game-card">
      <GameArtwork title={title} />
      <div className="site-v3-game-card-body">
        <p className="site-v3-game-engine">{title.engine_display_name}</p>
        <h3>{title.display_name}</h3>
        {title.description ? <span>{title.description}</span> : null}
        <div className="site-v3-mode-row">
          {title.demo_enabled ? <a href={resolveGameHref(title, "demo")}>Demo</a> : null}
          {title.real_enabled ? <a className="is-real" href={resolveGameHref(title, "real")}>Real</a> : null}
        </div>
      </div>
    </article>
  );
}

export function GameArtwork({ title }: { title: GameLibraryTitle }) {
  const assetUrl = resolvePublicAssetUrl(title.game_card_asset?.public_url);
  if (assetUrl) {
    return <img alt="" className="site-v3-game-art" src={assetUrl} />;
  }
  return (
    <div className="site-v3-game-art site-v3-game-art-fallback">
      <span>{title.display_name.slice(0, 2).toUpperCase()}</span>
    </div>
  );
}
