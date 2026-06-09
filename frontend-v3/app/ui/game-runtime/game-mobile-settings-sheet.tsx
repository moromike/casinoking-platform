import type { ReactNode } from "react";

type GameMobileSettingsSheetProps = {
  isDemoPlayer: boolean;
  title: string;
  doneLabel: string;
  demoBadgeLabel: string;
  onClose: () => void;
  children: ReactNode;
  overlayClassName?: string;
  sheetClassName?: string;
  headerClassName?: string;
  closeButtonClassName?: string;
  demoBadgeClassName?: string;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameMobileSettingsSheet({
  isDemoPlayer,
  title,
  doneLabel,
  demoBadgeLabel,
  onClose,
  children,
  overlayClassName,
  sheetClassName,
  headerClassName,
  closeButtonClassName,
  demoBadgeClassName,
}: GameMobileSettingsSheetProps) {
  return (
    <div
      className={joinClassNames("game-mobile-settings-overlay", overlayClassName)}
      role="presentation"
      onClick={onClose}
    >
      <section
        className={joinClassNames(
          "session-actions",
          "game-control-rail",
          "game-mobile-settings-sheet",
          sheetClassName,
        )}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <div className={joinClassNames("game-mobile-settings-header", headerClassName)}>
          <div>
            <h3>{title}</h3>
            {isDemoPlayer ? (
              <span className={joinClassNames("status-badge", "info", demoBadgeClassName)}>
                {demoBadgeLabel}
              </span>
            ) : null}
          </div>
          <button
            className={joinClassNames("button-ghost", closeButtonClassName)}
            type="button"
            onClick={onClose}
          >
            {doneLabel}
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
