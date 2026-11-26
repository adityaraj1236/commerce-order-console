import type { ReactNode } from "react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

export interface SummaryItem {
  label: string;
  value: ReactNode;
  /** Larger, bold row with a divider above: grand totals. */
  emphasis?: boolean;
}

/** Label / value rows, e.g. an order summary or a cart total. */
export function SummaryList({ items }: { items: SummaryItem[] }) {
  return (
    <dl className="summary-list">
      {items.map((item) => (
        <div
          key={item.label}
          className={cx("summary-list-row", item.emphasis && "summary-list-row-emphasis")}
        >
          <dt>{item.label}</dt>
          <dd className="summary-list-value">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
