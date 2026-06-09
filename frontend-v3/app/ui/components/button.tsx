import Link, { type LinkProps } from "next/link";
import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  MouseEventHandler,
  ReactNode,
} from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type CommonButtonProps = {
  variant?: ButtonVariant;
  isLoading?: boolean;
  className?: string;
  children: ReactNode;
  disabled?: boolean;
};

type ButtonAsButtonProps = CommonButtonProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    href?: undefined;
  };

type ButtonAsLinkProps = CommonButtonProps &
  Omit<LinkProps, "href"> &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps | "href" | "className" | "children"> & {
    href: string;
  };

type ButtonProps = ButtonAsButtonProps | ButtonAsLinkProps;

const VARIANT_CLASS_NAME: Record<ButtonVariant, string> = {
  primary: "button",
  secondary: "button-secondary",
  ghost: "button-ghost",
};

function joinClassNames(...values: Array<string | null | undefined | false>) {
  return values.filter(Boolean).join(" ");
}

function renderButtonContent(children: ReactNode, isLoading: boolean) {
  return (
    <>
      <span className="button-content">{children}</span>
      {isLoading ? (
        <span aria-hidden="true" className="button-spinner">
          <svg fill="none" viewBox="0 0 24 24">
            <circle cx="12" cy="12" opacity="0.25" r="9" stroke="currentColor" strokeWidth="3" />
            <path
              d="M21 12a9 9 0 0 0-9-9"
              stroke="currentColor"
              strokeLinecap="round"
              strokeWidth="3"
            />
          </svg>
        </span>
      ) : null}
    </>
  );
}

export function Button(props: ButtonProps) {
  const variant = props.variant ?? "primary";
  const isLoading = props.isLoading ?? false;
  const resolvedClassName = joinClassNames(
    VARIANT_CLASS_NAME[variant],
    isLoading ? "is-loading" : null,
    props.className,
  );
  const content = renderButtonContent(props.children, isLoading);

  if ("href" in props && typeof props.href === "string") {
    const {
      href,
      variant: _variant,
      isLoading: _isLoading,
      className: _className,
      children: _children,
      disabled,
      onClick,
      ...linkProps
    } = props;
    const isDisabled = Boolean(disabled || isLoading);
    const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
      if (isDisabled) {
        event.preventDefault();
        return;
      }

      onClick?.(event);
    };

    return (
      <Link
        {...linkProps}
        aria-busy={isLoading || undefined}
        aria-disabled={isDisabled || undefined}
        className={resolvedClassName}
        href={href}
        onClick={handleClick}
        tabIndex={isDisabled ? -1 : linkProps.tabIndex}
      >
        {content}
      </Link>
    );
  }

  const {
    variant: _variant,
    isLoading: _isLoading,
    className: _className,
    children: _children,
    disabled,
    type,
    ...buttonProps
  } = props;

  return (
    <button
      {...buttonProps}
      aria-busy={isLoading || undefined}
      className={resolvedClassName}
      disabled={Boolean(disabled || isLoading)}
      type={type ?? "button"}
    >
      {content}
    </button>
  );
}
