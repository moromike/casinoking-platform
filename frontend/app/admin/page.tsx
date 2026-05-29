import { redirect } from "next/navigation";

const SITE_V3_BASE_URL =
  process.env.NEXT_PUBLIC_SITE_V3_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:3000";

export const dynamic = "force-dynamic";

export default function AdminPage() {
  redirect(`${SITE_V3_BASE_URL}/admin`);
}
