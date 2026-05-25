import { SiteV3PublicPage } from "../../ui/site-v3-public-page";

export const dynamic = "force-dynamic";

type SiteV3DynamicPageProps = {
  params: Promise<{ page_code: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SiteV3DynamicPage({
  params,
  searchParams,
}: SiteV3DynamicPageProps) {
  const { page_code: pageCode } = await params;
  const resolvedSearchParams = await searchParams;
  return <SiteV3PublicPage pageCode={pageCode} searchParams={resolvedSearchParams ?? {}} />;
}
