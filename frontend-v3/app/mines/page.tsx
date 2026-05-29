import { loadGameLibraryTitles } from "../lib/api";
import { GameFramePage } from "../ui/game-frame-page";

export const dynamic = "force-dynamic";

type MinesPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function MinesPage({ searchParams }: MinesPageProps) {
  const resolvedSearchParams = await searchParams;
  const titles = await loadGameLibraryTitles("casinoking");
  return (
    <GameFramePage
      config={{
        displayName: "Mines",
        engineCode: "mines",
        gameCode: "mines",
        routePath: "mines",
      }}
      searchParams={resolvedSearchParams ?? {}}
      titles={titles}
    />
  );
}
