import { SiteV3PublicPage } from "./ui/site-v3-public-page";

export const dynamic = "force-dynamic";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = await searchParams;
  return <SiteV3PublicPage pageCode="home" searchParams={resolvedSearchParams ?? {}} />;
}
