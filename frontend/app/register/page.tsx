import { redirectToSiteV3 } from "../lib/site-v3-redirect";

export const dynamic = "force-dynamic";

type RegisterPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  redirectToSiteV3("/register", (await searchParams) ?? {});
}
