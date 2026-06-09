import { type SiteV3PagesResponse } from "../site-v3-admin-types";

export function SiteV3SystemPagesScreen({
  pagesData,
  selectedPageCode,
  onOpenRegistrationPage,
}: {
  pagesData: SiteV3PagesResponse | null;
  selectedPageCode: string;
  onOpenRegistrationPage: () => void;
}) {
  const registrationPage = pagesData?.pages.find((page) => page.page_code === "register") ?? null;

  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className="site-v3-screen-kicker">Pages</span>
          <h3>System pages</h3>
          <p>Manage fixed player routes whose runtime is owned by Site V3.</p>
        </div>
      </div>

      <div className="site-v3-page-table">
        <button
          className={`site-v3-page-table-row ${selectedPageCode === "register" ? "is-selected" : ""}`}
          onClick={onOpenRegistrationPage}
          type="button"
        >
          <span>
            <strong>Registration</strong>
            <small>register / system_registration_form</small>
          </span>
          <span className={`site-v3-status-pill is-${registrationPage?.status ?? "draft"}`}>
            {registrationPage?.status ?? "not created"}
          </span>
          <small>
            {registrationPage
              ? `Draft v${registrationPage.draft_version} / Published ${registrationPage.published_version ? `v${registrationPage.published_version}` : "none"}`
              : "Create the managed registration page with the built-in system module"}
          </small>
        </button>
      </div>
    </section>
  );
}
