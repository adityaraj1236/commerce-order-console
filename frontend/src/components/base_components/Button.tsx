import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cx } from "@/utils/classNames";

import { Spinner } from "./Spinner";
import "./base_components.css";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Icon shown before the label. */
  icon?: ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
  /** Square button holding only `icon`. Requires an aria-label. */
  iconOnly?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  fullWidth = false,
  iconOnly = false,
  disabled,
  type = "button",
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cx(
        "button",
        `button-${variant}`,
        `button-${size}`,
        fullWidth && "button-full-width",
        iconOnly && "button-icon-only",
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner /> : icon}
      {iconOnly ? null : children}
    </button>
  );
}

interface ButtonLinkProps {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  children: ReactNode;
}

/** A navigation link that looks exactly like a Button (same classes, no duplicate styles). */
export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  icon,
  children,
}: ButtonLinkProps) {
  return (
    <Link href={href} className={cx("button", `button-${variant}`, `button-${size}`)}>
      {icon}
      {children}
    </Link>
  );
}
