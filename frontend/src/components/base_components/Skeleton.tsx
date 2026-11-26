import { cx } from "@/utils/classNames";

import "./base_components.css";

interface SkeletonProps {
  /** Matches the height of the text it stands in for. */
  variant?: "text" | "heading" | "display";
}

/** Placeholder shimmer while data loads. Hidden from screen readers. */
export function Skeleton({ variant = "text" }: SkeletonProps) {
  return (
    <span
      className={cx(
        "skeleton",
        variant === "heading" && "skeleton-heading",
        variant === "display" && "skeleton-display",
      )}
      aria-hidden="true"
    />
  );
}
