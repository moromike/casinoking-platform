import { type SiteV3ListStatusFilter, type SiteV3PagesResponse } from "../site-v3-admin-types";

export function SiteV3PagesScreen({
  locale,
  pagesData,
  pagesStatus,
  selectedPageCode,
  statusFilter,
  onLocaleChange,
  onNewPage,
  onOpenPage,
  onStatusFilterChange,
}: {
  locale: string;
  pagesData: SiteV3PagesResponse | null;
  pagesStatus: "idle" | "loading" | "error";
  selectedPageCode: string;
  statusFilter: SiteV3ListStatusFilter;
  onLocaleChange: (locale: string) => void;
  onNewPage: () => void;
  onOpenPage: (pageCode: string) => void;
  onStatusFilterChange: (status: SiteV3ListStatusFilter) => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Pages</span>
          <h3>Page list</h3>
          <p>Choose a page before editing identity, composition or versions.</p>
        </div>
        <button className="button" type="button" onClick={onNewPage}>
          New page
        </button>
      </div>
      <div className="site-v3-filter-row">
        <label className="site-v3-field">
          <span>Locale</span>
          <select value={locale} onChange={(event) => onLocaleChange(event.target.value)}>
            <option value="it">IT</option>
            <option value="en">EN</option>
            <option value="de">DE</option>
            <option value="es">ES</option>
          </select>
        </label>
        <label className="site-v3-field">
          <span>Status</span>
          <select
            value={statusFilter}
            onChange={(event) => onStatusFilterChange(event.target.value as SiteV3ListStatusFilter)}
          >
            <option value="all">All</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </div>
      {pagesStatus === "loading" ? <p className="empty-state">Loading pages...</p> : null}
      {pagesStatus === "error" ? <p className="empty-state">Page list unavailable.</p> : null}
      <div className="site-v3-page-table">
        {(pagesData?.pages ?? []).map((page) => (
          <button
            className={`site-v3-page-table-row ${page.page_code === selectedPageCode ? "is-selected" : ""}`}
            key={`${page.page_code}:${page.locale}`}
            type="button"
            onClick={() => onOpenPage(page.page_code)}
          >
            <span>
              <strong>{page.title}</strong>
              <small>{page.page_code} / {page.locale.toUpperCase()}</small>
            </span>
            <span className={`site-v3-status-pill is-${page.status}`}>{page.status}</span>
            <small>Draft v{page.draft_version} / Published {page.published_version ? `v${page.published_version}` : "none"}</small>
          </button>
        ))}
        {pagesData && pagesData.pages.length === 0 ? (
          <p className="empty-state">No Site V3 pages yet. Start with the Homepage draft.</p>
        ) : null}
      </div>
    </section>
  );
}
