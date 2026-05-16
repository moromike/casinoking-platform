"use client";

type TitleEditorCommandBarProps = {
  accessToken: string | null;
  busyAction: string | null;
  canSaveDraft: boolean;
  canPublishLive: boolean;
  onLoadDraft: () => void;
  onLoadPublished: () => void;
  onSaveDraft: () => void;
  onPublishLive: () => void;
};

export function TitleEditorCommandBar({
  accessToken,
  busyAction,
  canSaveDraft,
  canPublishLive,
  onLoadDraft,
  onLoadPublished,
  onSaveDraft,
  onPublishLive,
}: TitleEditorCommandBarProps) {
  const isLoadingDraft = busyAction === "admin-mines-backoffice-load-draft";
  const isLoadingPublished = busyAction === "admin-mines-backoffice-load-published";
  const isSavingDraft = busyAction === "admin-mines-backoffice-save";
  const isPublishingLive = busyAction === "admin-mines-backoffice-publish";
  const isMinesBackofficeBusy =
    isLoadingDraft || isLoadingPublished || isSavingDraft || isPublishingLive;

  return (
    <div className="editor-command-bar" aria-busy={isMinesBackofficeBusy || undefined}>
      <button
        className="button-secondary"
        type="button"
        disabled={!accessToken || busyAction !== null}
        aria-busy={isLoadingDraft || undefined}
        onClick={onLoadDraft}
      >
        {isLoadingDraft ? "Loading saved draft..." : "Load saved draft"}
      </button>
      <button
        className="button-secondary"
        type="button"
        disabled={!accessToken || busyAction !== null}
        aria-busy={isLoadingPublished || undefined}
        onClick={onLoadPublished}
      >
        {isLoadingPublished ? "Loading published live..." : "Load published live"}
      </button>
      <button
        className="button"
        type="button"
        disabled={!canSaveDraft}
        aria-busy={isSavingDraft || undefined}
        onClick={onSaveDraft}
      >
        {isSavingDraft ? "Saving draft..." : "Save draft"}
      </button>
      <button
        className="button"
        type="button"
        disabled={!canPublishLive}
        aria-busy={isPublishingLive || undefined}
        onClick={onPublishLive}
      >
        {isPublishingLive ? "Publishing live..." : "Publish live"}
      </button>
    </div>
  );
}
