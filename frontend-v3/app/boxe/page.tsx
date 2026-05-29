import { loadGameLibraryTitles } from "../lib/api";
import { GameFramePage } from "../ui/game-frame-page";

export const dynamic = "force-dynamic";

type BoxePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function BoxePage({ searchParams }: BoxePageProps) {
  const resolvedSearchParams = await searchParams;
  const titles = await loadGameLibraryTitles("casinoking");
  return (
    <GameFramePage
      config={{
        displayName: "BOXE",
        engineCode: "boxe",
        gameCode: "boxe",
        routePath: "boxe",
      }}
      searchParams={resolvedSearchParams ?? {}}
      titles={titles}
    />
  );
}
