import { AdminGamesPage } from "../../../ui/admin-games-page";

type AdminGameEnginePageProps = {
  params: Promise<{
    engine: string;
  }>;
};

export const dynamic = "force-dynamic";

export default async function AdminGameEngineRoute({ params }: AdminGameEnginePageProps) {
  const { engine } = await params;
  return <AdminGamesPage routeIntent={{ engineCode: engine }} />;
}
