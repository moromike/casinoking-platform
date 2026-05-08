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
  return (
    <div className="editor-command-bar">
      <button
        className="button-secondary"
        type="button"
        disabled={!accessToken || busyAction !== null}
        onClick={onLoadDraft}
      >
        {busyAction === "admin-mines-backoffice-load-draft"
          ? "Carico bozza salvata..."
          : "Carica bozza salvata"}
      </button>
      <button
        className="button-secondary"
        type="button"
        disabled={!accessToken || busyAction !== null}
        onClick={onLoadPublished}
      >
        {busyAction === "admin-mines-backoffice-load-published"
          ? "Carico live pubblicato..."
          : "Carica live pubblicato"}
      </button>
      <button
        className="button"
        type="button"
        disabled={!canSaveDraft}
        onClick={onSaveDraft}
      >
        {busyAction === "admin-mines-backoffice-save" ? "Salvo bozza..." : "Salva bozza"}
      </button>
      <button
        className="button"
        type="button"
        disabled={!canPublishLive}
        onClick={onPublishLive}
      >
        {busyAction === "admin-mines-backoffice-publish" ? "Pubblico live..." : "Pubblica live"}
      </button>
    </div>
  );
}
