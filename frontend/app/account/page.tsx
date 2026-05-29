import { redirectToSiteV3 } from "../lib/site-v3-redirect";

export const dynamic = "force-dynamic";

type AccountPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AccountPage({ searchParams }: AccountPageProps) {
  redirectToSiteV3("/account", (await searchParams) ?? {});
}
