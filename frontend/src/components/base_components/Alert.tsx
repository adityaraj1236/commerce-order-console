import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import "./base_components.css";

type AlertTone = "error" | "warning" | "success" | "info";

const ALERT_ICON = {
  error: CircleAlert,
  warning: TriangleAlert,
  success: CircleCheck,
  info: Info,
} as const;

interface AlertProps {
  tone: AlertTone;
  title: string;
  /** Extra lines, e.g. each short cart line from a 409 response. */
  items?: string[];
  children?: ReactNode;
}

export function Alert({ tone, title, items = [], children }: AlertProps) {
  const Icon = ALERT_ICON[tone];
  return (
    <div className={`alert alert-${tone}`} role={tone === "error" ? "alert" : "status"}>
      <Icon className="icon-md" aria-hidden="true" />
      <div className="alert-content">
        <p className="alert-title">{title}</p>
        {items.length > 0 ? (
          <ul className="alert-list">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
        {children}
      </div>
    </div>
  );
}
