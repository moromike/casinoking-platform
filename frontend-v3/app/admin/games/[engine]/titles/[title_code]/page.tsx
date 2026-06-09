import { AdminGamesPage } from "../../../../../ui/admin-games-page";

type AdminGameTitlePageProps = {
  params: Promise<{
    engine: string;
    title_code: string;
  }>;
};

export const dynamic = "force-dynamic";

export default async function AdminGameTitleRoute({ params }: AdminGameTitlePageProps) {
  const { engine, title_code: titleCode } = await params;
  return <AdminGamesPage routeIntent={{ engineCode: engine, titleCode }} />;
}
