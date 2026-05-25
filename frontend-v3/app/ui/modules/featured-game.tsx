import type { GameLibraryTitle, SiteV3PublicModule } from "../../lib/types";
import { readString, resolveGameHref } from "../site-v3-render-helpers";
import { GameArtwork } from "./game-card";

export function FeaturedGame({
  games,
  module,
}: {
  games: Map<string, GameLibraryTitle>;
  module: SiteV3PublicModule;
}) {
  const titleCode = readString(module.config_json.title_code, "");
  const game = titleCode ? games.get(titleCode) : undefined;
  if (!game) {
    return null;
  }

  return (
    <section className="site-v3-featured">
      <GameArtwork title={game} />
      <div>
        <p className="site-v3-kicker">{game.engine_display_name}</p>
        <h2>{readString(module.config_json.headline, game.display_name)}</h2>
        <p>{readString(module.config_json.body, game.description ?? "Apri il gioco dalla lobby CasinoKing.")}</p>
        <a className="site-v3-primary-link" href={resolveGameHref(game, "demo")}>
          {readString(module.config_json.cta_label, "Prova in demo")}
        </a>
      </div>
    </section>
  );
}
