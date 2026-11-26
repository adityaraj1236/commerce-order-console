import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  /** e.g. a "Create order" or "Try again" button. */
  action?: ReactNode;
  /** Error states use the same layout with a danger-colored icon. */
  tone?: "neutral" | "error";
}

/** Used for "nothing here yet", "no search results" and "could not load" states. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  tone = "neutral",
}: EmptyStateProps) {
  return (
    <div
      className={cx("empty-state", tone === "error" && "empty-state-error")}
      role={tone === "error" ? "alert" : undefined}
    >
      <Icon className="empty-state-icon icon-lg" aria-hidden="true" />
      <p className="empty-state-title">{title}</p>
      {description ? <p className="empty-state-description">{description}</p> : null}
      {action ? <div className="empty-state-action">{action}</div> : null}
    </div>
  );
}
