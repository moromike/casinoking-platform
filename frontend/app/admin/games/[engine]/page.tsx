import { CasinoKingConsole } from "@/app/ui/casinoking-console";

type AdminGameEnginePageProps = {
  params: Promise<{
    engine: string;
  }>;
};

export default async function AdminGameEnginePage({
  params,
}: AdminGameEnginePageProps) {
  const { engine } = await params;

  return (
    <CasinoKingConsole
      area="admin"
      adminGamesRoute={{ engineCode: engine }}
    />
  );
}
