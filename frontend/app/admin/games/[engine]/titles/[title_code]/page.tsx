import { CasinoKingConsole } from "@/app/ui/casinoking-console";

type AdminGameTitlePageProps = {
  params: Promise<{
    engine: string;
    title_code: string;
  }>;
};

export default async function AdminGameTitlePage({
  params,
}: AdminGameTitlePageProps) {
  const { engine, title_code: titleCode } = await params;

  return (
    <CasinoKingConsole
      area="admin"
      adminGamesRoute={{ engineCode: engine, titleCode }}
    />
  );
}
