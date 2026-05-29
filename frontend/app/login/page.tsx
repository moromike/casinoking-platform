import { redirectToSiteV3 } from "../lib/site-v3-redirect";

export const dynamic = "force-dynamic";

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  redirectToSiteV3("/login", (await searchParams) ?? {});
}
