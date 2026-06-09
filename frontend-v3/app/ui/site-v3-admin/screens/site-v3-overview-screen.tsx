import { SITE_V3_SITE_CODE, type SiteV3AdminPage, type SiteV3PageEditorState, type SiteV3PagesResponse, type SiteV3ValidationResult, type SiteV3Version } from "../site-v3-admin-types";
import { type SiteV3AdminView } from "../site-v3-admin-helpers";

export function SiteV3OverviewScreen({
  dirty,
  editorState,
  pageMeta,
  pagesData,
  publishedSummary,
  validation,
  versions,
  onNavigate,
}: {
  dirty: boolean;
  editorState: SiteV3PageEditorState;
  pageMeta: SiteV3AdminPage | null;
  pagesData: SiteV3PagesResponse | null;
  publishedSummary: SiteV3Version | null;
  validation: SiteV3ValidationResult;
  versions: SiteV3Version[];
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Site management</span>
          <h3>Site overview</h3>
          <p>Current page, publication state and next editing areas.</p>
        </div>
        <span className={`site-v3-status-pill is-${pageMeta?.status ?? "draft"}`}>
          {pageMeta?.status ?? "new draft"}
        </span>
      </div>
      <div className="site-v3-overview-grid">
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "pages" })}>
          <span>Pages</span>
          <strong>{pagesData?.pagination.total ?? 0}</strong>
          <small>Manage page list and filters.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "siteSettings" })}>
          <span>Site settings</span>
          <strong>{SITE_V3_SITE_CODE}</strong>
          <small>Global site scope, public renderer and handoff rules.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "pageDetail" })}>
          <span>Page settings</span>
          <strong>{editorState.title || "Untitled"}</strong>
          <small>{editorState.page_code} / {dirty ? "unsaved changes" : "saved draft"}</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "composition" })}>
          <span>Composition</span>
          <strong>{editorState.modules.length}</strong>
          <small>Mounted modules in page order.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "validation" })}>
          <span>Validation</span>
          <strong>{validation.status}</strong>
          <small>{validation.issues.length} issues.</small>
        </button>
        <button className="site-v3-overview-card" type="button" onClick={() => onNavigate({ kind: "versions" })}>
          <span>Published version</span>
          <strong>{publishedSummary?.version ? `v${publishedSummary.version}` : "None"}</strong>
          <small>{versions.length} history entries.</small>
        </button>
      </div>
    </section>
  );
}
