import { SITE_V3_MODULE_CATEGORIES } from "../site-v3-admin-descriptors";
import { SITE_V3_SITE_CODE } from "../site-v3-admin-types";
import { isSameView, type SiteV3AdminView } from "../site-v3-admin-helpers";

export function SiteV3AdminNav({
  activeView,
  dirty,
  moduleCount,
  pageCode,
  pageTitle,
  onNavigate,
}: {
  activeView: SiteV3AdminView;
  dirty: boolean;
  moduleCount: number;
  pageCode: string;
  pageTitle: string;
  onNavigate: (view: SiteV3AdminView) => void;
}) {
  return (
    <aside className="site-v3-cms-nav" aria-label="Site V3 CMS navigation">
      <div className="site-v3-cms-nav-title">
        <span>CMS menu</span>
        <strong>{pageTitle || "Untitled page"}</strong>
        <small>{dirty ? "Unsaved changes" : "Draft aligned"}</small>
      </div>
      <nav className="site-v3-cms-nav-list">
        <div className="site-v3-cms-nav-group">
          <span>Site</span>
          <CmsNavButton
            active={isSameView(activeView, { kind: "overview" })}
            label="Dashboard"
            onClick={() => onNavigate({ kind: "overview" })}
          />
          <CmsNavButton
            active={isSameView(activeView, { kind: "siteSettings" })}
            label="Site settings"
            meta={SITE_V3_SITE_CODE}
            onClick={() => onNavigate({ kind: "siteSettings" })}
          />
        </div>

        <div className="site-v3-cms-nav-group">
          <span>Pages</span>
          <button
            className={`site-v3-cms-nav-item ${isSameView(activeView, { kind: "pages" }) ? "is-active" : ""}`}
            onClick={() => onNavigate({ kind: "pages" })}
            type="button"
          >
            <span>All pages</span>
          </button>
          <div className="site-v3-cms-subnav">
            <small>Selected page</small>
            <CmsNavButton
              active={isSameView(activeView, { kind: "pageDetail" })}
              label="Settings"
              meta={pageCode}
              onClick={() => onNavigate({ kind: "pageDetail" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "composition" })}
              label="Composition"
              meta={`${moduleCount} modules`}
              onClick={() => onNavigate({ kind: "composition" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "validation" })}
              label="Validation"
              onClick={() => onNavigate({ kind: "validation" })}
            />
            <CmsNavButton
              active={isSameView(activeView, { kind: "versions" })}
              label="Versions"
              onClick={() => onNavigate({ kind: "versions" })}
            />
          </div>
        </div>

        <div className="site-v3-cms-nav-group">
          <span>Modules</span>
          <CmsNavButton
            active={isSameView(activeView, { kind: "modules" })}
            label="Module library"
            onClick={() => onNavigate({ kind: "modules" })}
          />
          <div className="site-v3-cms-subnav">
            <small>Categories</small>
            <CmsNavButton
              active={isSameView(activeView, { kind: "moduleWizard" })}
              label="Add module"
              onClick={() => onNavigate({ kind: "moduleWizard" })}
            />
            {SITE_V3_MODULE_CATEGORIES.map((category) => (
              <CmsNavButton
                active={activeView.kind === "moduleCategory" && activeView.category === category.key}
                key={category.key}
                label={category.label}
                onClick={() => onNavigate({ kind: "moduleCategory", category: category.key })}
              />
            ))}
          </div>
        </div>
      </nav>
      <a className="site-v3-cms-public-link" href="http://localhost:3001" rel="noreferrer" target="_blank">
        Open public Site V3
      </a>
    </aside>
  );
}

export function CmsNavButton({
  active,
  label,
  meta,
  onClick,
}: {
  active: boolean;
  label: string;
  meta?: string;
  onClick: () => void;
}) {
  return (
    <button
      className={`site-v3-cms-nav-item ${active ? "is-active" : ""}`}
      onClick={onClick}
      type="button"
    >
      <span>{label}</span>
      {meta ? <small>{meta}</small> : null}
    </button>
  );
}
