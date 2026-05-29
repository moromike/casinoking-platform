import type {
  GameLibraryTitle,
  SiteHomeSlot,
  SiteV3ModuleCode,
  SiteV3PublicModule,
  SiteV3PublicPageSnapshot,
} from "../../lib/types";
import { CustomModuleRenderer } from "./custom-module-renderer";
import { FeaturedGame } from "./featured-game";
import { GameGrid } from "./game-grid";
import { HeroBanner } from "./hero-banner";
import { PromoBand } from "./promo-band";
import { RichTextSafe } from "./rich-text-safe";

export function ModuleRenderer({
  gameLibrary,
  games,
  homeSlots,
  module,
  page,
}: {
  gameLibrary: GameLibraryTitle[];
  games: Map<string, GameLibraryTitle>;
  homeSlots: SiteHomeSlot[];
  module: SiteV3PublicModule;
  page: SiteV3PublicPageSnapshot;
}) {
  switch (module.module_code as SiteV3ModuleCode) {
    case "hero_banner":
      return <HeroBanner homeSlots={homeSlots} module={module} />;
    case "game_grid":
      return <GameGrid games={games} module={module} titles={gameLibrary} />;
    case "game_grid_4x":
      return <GameGrid games={games} module={module} titles={gameLibrary} variant="large4" />;
    case "featured_game":
      return <FeaturedGame games={games} module={module} />;
    case "promo_band":
      return <PromoBand module={module} />;
    case "rich_text_safe":
      return <RichTextSafe module={module} />;
    case "global_header":
    case "global_footer":
      return null;
    default:
      if (module.module_code.startsWith("custom_")) {
        return (
          <CustomModuleRenderer
            gameLibrary={gameLibrary}
            games={games}
            module={module}
            page={page}
          />
        );
      }
      if (process.env.NODE_ENV === "development") {
        console.warn(`Unknown Site V3 module on ${page.page_code}: ${module.module_code}`);
      }
      return null;
  }
}
