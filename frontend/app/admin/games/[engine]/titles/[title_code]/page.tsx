import { redirect } from "next/navigation";

const SITE_V3_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export const dynamic = "force-dynamic";

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

  redirect(
    `${SITE_V3_BASE_URL}/admin/games/${encodeURIComponent(engine)}/titles/${encodeURIComponent(titleCode)}`,
  );
}
