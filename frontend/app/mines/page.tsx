import { redirectToSiteV3 } from "../lib/site-v3-redirect";

export const dynamic = "force-dynamic";

type MinesPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function MinesPage({ searchParams }: MinesPageProps) {
  redirectToSiteV3("/mines", (await searchParams) ?? {});
}
