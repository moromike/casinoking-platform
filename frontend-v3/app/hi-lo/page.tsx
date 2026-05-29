import { loadGameLibraryTitles } from "../lib/api";
import { GameFramePage } from "../ui/game-frame-page";

export const dynamic = "force-dynamic";

type HiLoPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HiLoPage({ searchParams }: HiLoPageProps) {
  const resolvedSearchParams = await searchParams;
  const titles = await loadGameLibraryTitles("casinoking");
  return (
    <GameFramePage
      config={{
        displayName: "HI-LO",
        engineCode: "hi_lo",
        gameCode: "hi_lo",
        routePath: "hi-lo",
        runtimePath: "/runtime/hi-lo",
      }}
      searchParams={resolvedSearchParams ?? {}}
      titles={titles}
    />
  );
}
