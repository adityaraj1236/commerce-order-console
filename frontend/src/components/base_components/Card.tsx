import type { ReactNode } from "react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

interface CardProps {
  title?: string;
  /** Rendered on the right of the header, e.g. a button or count. */
  actions?: ReactNode;
  /** Remove body padding, for tables that run edge to edge. */
  flush?: boolean;
  className?: string;
  children: ReactNode;
}

export function Card({ title, actions, flush = false, className, children }: CardProps) {
  return (
    <section className={cx("card", className)}>
      {title || actions ? (
        <header className="card-header">
          {title ? <h2 className="card-title">{title}</h2> : <span />}
          {actions}
        </header>
      ) : null}
      <div className={cx("card-body", flush && "card-body-flush")}>{children}</div>
    </section>
  );
}
