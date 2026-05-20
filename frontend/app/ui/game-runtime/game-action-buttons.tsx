import { Button } from "../components/button";

type GameActionButtonsProps = {
  useMobileLayout?: boolean;
  betButtonLabel: string;
  collectButtonLabel: string;
  isBetDisabled: boolean;
  isCollectDisabled: boolean;
  isBetLoading: boolean;
  isCollectLoading: boolean;
  shouldPulseBetButton?: boolean;
  className?: string;
  desktopClassName?: string;
  mobileClassName?: string;
  betButtonClassName?: string;
  collectButtonClassName?: string;
  betButtonTestId?: string;
  collectButtonTestId?: string;
  onCollect: () => void;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function GameActionButtons({
  useMobileLayout = false,
  betButtonLabel,
  collectButtonLabel,
  isBetDisabled,
  isCollectDisabled,
  isBetLoading,
  isCollectLoading,
  shouldPulseBetButton = false,
  className,
  desktopClassName,
  mobileClassName,
  betButtonClassName,
  collectButtonClassName,
  betButtonTestId,
  collectButtonTestId,
  onCollect,
}: GameActionButtonsProps) {
  return (
    <div
      className={joinClassNames(
        "actions",
        "game-action-buttons",
        useMobileLayout ? "game-mobile-actions" : "game-desktop-actions",
        useMobileLayout ? mobileClassName : desktopClassName,
        className,
      )}
    >
      <Button
        type="submit"
        data-testid={betButtonTestId}
        disabled={isBetDisabled}
        isLoading={isBetLoading}
        className={joinClassNames(
          shouldPulseBetButton ? "game-bet-idle-pulse" : null,
          betButtonClassName,
        )}
      >
        {betButtonLabel}
      </Button>
      <Button
        type="button"
        data-testid={collectButtonTestId}
        disabled={isCollectDisabled}
        isLoading={isCollectLoading}
        variant="secondary"
        className={collectButtonClassName}
        onClick={onCollect}
      >
        {collectButtonLabel}
      </Button>
    </div>
  );
}
