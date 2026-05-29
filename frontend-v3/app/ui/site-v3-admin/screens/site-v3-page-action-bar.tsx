import { type SiteV3AdminPage } from "../site-v3-admin-types";

export function SiteV3PageActionBar({
  busyAction,
  dirty,
  isBusy,
  pageMeta,
  validationErrors,
  validationStatus,
  onPublish,
  onSaveDraft,
  onValidate,
}: {
  busyAction: string | null;
  dirty: boolean;
  isBusy: boolean;
  pageMeta: SiteV3AdminPage | null;
  validationErrors: number;
  validationStatus: "valid" | "invalid" | "unknown";
  onPublish: () => void;
  onSaveDraft: () => void;
  onValidate: () => void;
}) {
  return (
    <section className="site-v3-page-action-bar" aria-label="Page draft actions">
      <div>
        <strong>{dirty ? "Unsaved draft changes" : "Draft saved"}</strong>
        <small>
          {dirty
            ? "Save draft to update Preview live. Publish stays unavailable until the draft is saved."
            : validationStatus === "valid"
              ? `Draft v${pageMeta?.draft_version ?? 0} is validated and ready for publish.`
              : `Draft v${pageMeta?.draft_version ?? 0} is ready for preview. Run validation before publish.`}
        </small>
      </div>
      <div className="site-v3-page-action-buttons">
        <button className="button" type="button" onClick={onSaveDraft} disabled={isBusy || !dirty}>
          {busyAction === "save-draft" ? "Saving..." : "Save draft"}
        </button>
        <button className="button-secondary" type="button" onClick={onValidate} disabled={isBusy}>
          {busyAction === "validate" ? "Validating..." : "Validate"}
        </button>
        <button className="button-secondary" type="button" onClick={onPublish} disabled={isBusy || dirty || validationStatus !== "valid" || validationErrors > 0}>
          {busyAction === "publish" ? "Publishing..." : "Publish live"}
        </button>
      </div>
    </section>
  );
}
