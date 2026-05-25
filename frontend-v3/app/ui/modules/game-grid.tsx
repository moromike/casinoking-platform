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
      ? uniqueTitles(requestedCodes.map((code) => games.get(code)).filter((title): title is GameLibraryTitle => Boolean(title)))
      : uniqueTitles(titles).filter((title) => title.demo_enabled || title.real_enabled);
  const heading = readString(module.config_json.heading, "Published games");

  return (
    <section className="site-v3-section site-v3-game-section" id="games">
      <div className="site-v3-section-heading">
        <div>
          <p className="site-v3-kicker">Games</p>
          <h2>{heading}</h2>
        </div>
        <span className="site-v3-section-count">{selectedTitles.length} available</span>
      </div>
      {selectedTitles.length > 0 ? (
        <div className="site-v3-game-grid">
          {selectedTitles.map((title) => (
            <GameCard key={title.title_code} title={title} />
          ))}
        </div>
      ) : (
        <p className="site-v3-empty-section">No published games are available for this section.</p>
      )}
    </section>
  );
}

function uniqueTitles(titles: GameLibraryTitle[]): GameLibraryTitle[] {
  const seen = new Set<string>();
  return titles.filter((title) => {
    if (seen.has(title.title_code)) {
      return false;
    }
    seen.add(title.title_code);
    return true;
  });
}
