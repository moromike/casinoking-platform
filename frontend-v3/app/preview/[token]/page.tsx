import { SiteV3PublicPage } from "../../ui/site-v3-public-page";

export const dynamic = "force-dynamic";

type SiteV3PreviewPageProps = {
  params: Promise<{ token: string }>;
};

export default async function SiteV3PreviewPage({ params }: SiteV3PreviewPageProps) {
  const { token } = await params;
  return (
    <SiteV3PublicPage
      mode="preview"
      pageCode="preview"
      previewToken={token}
      searchParams={{}}
    />
  );
}
