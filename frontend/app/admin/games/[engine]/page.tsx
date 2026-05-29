import { redirect } from "next/navigation";

const SITE_V3_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export const dynamic = "force-dynamic";

type AdminGameEnginePageProps = {
  params: Promise<{
    engine: string;
  }>;
};

export default async function AdminGameEnginePage({
  params,
}: AdminGameEnginePageProps) {
  const { engine } = await params;

  redirect(`${SITE_V3_BASE_URL}/admin/games/${encodeURIComponent(engine)}`);
}
