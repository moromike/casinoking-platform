"use client";

type TitleEditorCommandBarProps = {
  engineCode: string;
  accessToken: string | null;
  busyAction: string | null;
  canSaveDraft: boolean;
  canPublishLive: boolean;
  onLoadDraft: () => void;
  onLoadPublished: () => void;
  onSaveDraft: () => void;
  onPublishLive: () => void;
};

export type TitleEditorCommandAction =
  | "load-draft"
  | "load-published"
  | "save"
  | "publish";

export function buildTitleEditorBusyAction(
  engineCode: string,
  action: TitleEditorCommandAction,
) {
  return `admin-${engineCode}-backoffice-${action}`;
}

export function TitleEditorCommandBar({
  engineCode,
  accessToken,
  busyAction,
  canSaveDraft,
  canPublishLive,
  onLoadDraft,
  onLoadPublished,
  onSaveDraft,
  onPublishLive,
}: TitleEditorCommandBarProps) {
  const isLoadingDraft = busyAction === buildTitleEditorBusyAction(engineCode, "load-draft");
  const isLoadingPublished = busyAction === buildTitleEditorBusyAction(engineCode, "load-published");
  const isSavingDraft = busyAction === buildTitleEditorBusyAction(engineCode, "save");
  const isPublishingLive = busyAction === buildTitleEditorBusyAction(engineCode, "publish");
  const isTitleEditorBusy =
    isLoadingDraft || isLoadingPublished || isSavingDraft || isPublishingLive;

  return (
    <div className="editor-command-bar" aria-busy={isTitleEditorBusy || undefined}>
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
