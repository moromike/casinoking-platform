import { SITE_V3_SITE_CODE, type SiteV3ListStatusFilter, type SiteV3PagesResponse, type SiteV3SiteAsset } from "../site-v3-admin-types";

export function SiteV3SiteSettingsScreen({
  assetsStatus,
  locale,
  pagesData,
  siteAssets,
  statusFilter,
}: {
  assetsStatus: "idle" | "loading" | "error";
  locale: string;
  pagesData: SiteV3PagesResponse | null;
  siteAssets: SiteV3SiteAsset[];
  statusFilter: SiteV3ListStatusFilter;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Site</span>
          <h3>Site settings</h3>
          <p>Global Site V3 settings that are not owned by a single page.</p>
        </div>
        <span className="site-v3-status-pill is-published">read only MVP</span>
      </div>
      <div className="site-v3-settings-grid">
        <article className="site-v3-setting-card">
          <span>Site code</span>
          <strong>{SITE_V3_SITE_CODE}</strong>
          <p>Canonical scope for public Site V3 pages and navigation.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Public renderer</span>
          <strong>localhost:3001</strong>
          <p>The public Site V3 app reads published snapshots only.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Admin route</span>
          <strong>/admin/site-v3</strong>
          <p>The builder lives in the existing backoffice shell on port 3000.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Locale context</span>
          <strong>{locale.toUpperCase()}</strong>
          <p>Current page-list locale filter. MVP content is Italian-first with the locale model ready.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Page filter</span>
          <strong>{statusFilter}</strong>
          <p>Current list filter for all pages. Draft, published and archived pages stay separate.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Assets</span>
          <strong>{assetsStatus === "error" ? "unavailable" : `${siteAssets.length} loaded`}</strong>
          <p>Site V3 currently reuses the platform asset catalog; the dedicated picker remains a later WP.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Account and cashier</span>
          <strong>V1 handoff</strong>
          <p>Login, account and cashier flows remain owned by the existing V1 application.</p>
        </article>
        <article className="site-v3-setting-card">
          <span>Published pages</span>
          <strong>{pagesData?.pages.filter((page) => page.status === "published").length ?? 0}</strong>
          <p>Only published snapshots are visible to the public renderer.</p>
        </article>
      </div>
    </section>
  );
}
