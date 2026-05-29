import { type SiteV3AdminPage, type SiteV3PageEditorState, type SiteV3ValidationResult, type SiteV3Version } from "../site-v3-admin-types";
import { normalizePageCode } from "../site-v3-admin-helpers";

export function SiteV3PageDetailScreen({
  busyAction,
  dirty,
  editorState,
  isBusy,
  pageMeta,
  publishedSummary,
  validation,
  validationErrors,
  onArchive,
  onLoadPage,
  onPublish,
  onSaveDraft,
  onUpdateEditorState,
  onValidate,
}: {
  busyAction: string | null;
  dirty: boolean;
  editorState: SiteV3PageEditorState;
  isBusy: boolean;
  pageMeta: SiteV3AdminPage | null;
  publishedSummary: SiteV3Version | null;
  validation: SiteV3ValidationResult;
  validationErrors: number;
  onArchive: () => void;
  onLoadPage: () => void;
  onPublish: () => void;
  onSaveDraft: () => void;
  onUpdateEditorState: (patch: Partial<SiteV3PageEditorState>) => void;
  onValidate: () => void;
}) {
  return (
    <section className="admin-card site-v3-cms-screen">
      <div className="site-v3-screen-heading">
        <div>
          <span className={`site-v3-status-pill is-${pageMeta?.status ?? "draft"}`}>
            {pageMeta?.status ?? "new draft"}
          </span>
          <h3>{editorState.title || "Untitled page"}</h3>
          <p>
            Draft v{pageMeta?.draft_version ?? 0}
            {publishedSummary ? ` - published v${publishedSummary.version}` : " - not published"}
          </p>
        </div>
        <div className="site-v3-command-actions">
          <button className="button-secondary" type="button" onClick={onLoadPage} disabled={isBusy || !pageMeta}>
            Load saved draft
          </button>
          <button className="button" type="button" onClick={onSaveDraft} disabled={isBusy || !dirty}>
            {busyAction === "save-draft" ? "Saving..." : "Save draft"}
          </button>
          <button className="button-secondary" type="button" onClick={onValidate} disabled={isBusy}>
            {busyAction === "validate" ? "Validating..." : "Validate"}
          </button>
          <button className="button" type="button" onClick={onPublish} disabled={isBusy || dirty || validation.status !== "valid" || validationErrors > 0}>
            {busyAction === "publish" ? "Publishing..." : "Publish live"}
          </button>
          <button className="button-secondary danger" type="button" onClick={onArchive} disabled={isBusy || !pageMeta}>
            Archive
          </button>
        </div>
      </div>
      <div className="site-v3-draft-state">
        <span className={dirty ? "is-dirty" : "is-saved"}>
          {dirty ? "Unsaved changes" : "Aligned with saved draft"}
        </span>
        <span>{validation.status === "valid" ? "Validation green" : validation.status === "invalid" ? "Validation has issues" : "Validation not run"}</span>
      </div>
      <div className="site-v3-form-grid">
        <label className="site-v3-field">
          <span>Page code</span>
          <input
            value={editorState.page_code}
            onChange={(event) =>
              onUpdateEditorState({
                page_code: normalizePageCode(event.target.value),
              })
            }
            disabled={Boolean(pageMeta)}
          />
        </label>
        <label className="site-v3-field">
          <span>Title</span>
          <input
            value={editorState.title}
            onChange={(event) => onUpdateEditorState({ title: event.target.value })}
            maxLength={160}
          />
        </label>
      </div>
    </section>
  );
}
