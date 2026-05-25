import type { GameLibraryTitle, SiteV3PublicModule } from "../../lib/types";
import { readString, readStringArray } from "../site-v3-render-helpers";
import { GameCard } from "./game-card";

export function GameGrid({
  games,
  module,
  titles,
}: {
  games: Map<string, GameLibraryTitle>;
  module: SiteV3PublicModule;
  titles: GameLibraryTitle[];
}) {
  const requestedCodes = readStringArray(module.config_json.title_codes);
  const selectedTitles =
    requestedCodes.length > 0
      ? requestedCodes.map((code) => games.get(code)).filter((title): title is GameLibraryTitle => Boolean(title))
      : titles;

  return (
    <section className="site-v3-section site-v3-game-section">
      <div className="site-v3-section-heading">
        <p className="site-v3-kicker">Giochi</p>
        <h2>{readString(module.config_json.heading, "Scegli il tuo gioco")}</h2>
      </div>
      {selectedTitles.length > 0 ? (
        <div className="site-v3-game-grid">
          {selectedTitles.map((title) => (
            <GameCard key={title.title_code} title={title} />
          ))}
        </div>
      ) : (
        <p className="site-v3-empty-section">Nessun gioco pubblicato disponibile per questa sezione.</p>
      )}
    </section>
  );
}
