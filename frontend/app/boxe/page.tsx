import { redirectToSiteV3 } from "../lib/site-v3-redirect";

export const dynamic = "force-dynamic";

type BoxePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function BoxePage({ searchParams }: BoxePageProps) {
  redirectToSiteV3("/boxe", (await searchParams) ?? {});
}
