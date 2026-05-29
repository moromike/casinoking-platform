import { redirectToSiteV3 } from "@/app/lib/site-v3-redirect";

type HiLoPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HiLoPage({ searchParams }: HiLoPageProps) {
  redirectToSiteV3("/hi-lo", (await searchParams) ?? {});
}
