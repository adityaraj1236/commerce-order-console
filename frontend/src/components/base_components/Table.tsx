import type { HTMLAttributes, ReactNode, TdHTMLAttributes, ThHTMLAttributes } from "react";

import { cx } from "@/utils/classNames";

import { Skeleton } from "./Skeleton";
import "./base_components.css";

interface TableProps {
  /** Describes the table for screen readers. */
  caption: string;
  children: ReactNode;
}

/** Horizontally scrollable on small screens; never overflows the page. */
export function Table({ caption, children }: TableProps) {
  return (
    <div className="table-scroll">
      <table className="table">
        <caption className="visually-hidden">{caption}</caption>
        {children}
      </table>
    </div>
  );
}

interface TableHeaderCellProps extends ThHTMLAttributes<HTMLTableCellElement> {
  numeric?: boolean;
}

export function TableHeaderCell({ numeric = false, className, ...rest }: TableHeaderCellProps) {
  return (
    <th
      scope="col"
      className={cx("table-header-cell", numeric && "table-cell-numeric", className)}
      {...rest}
    />
  );
}

interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
  /** Highlight on hover and show a pointer: the row opens something. */
  interactive?: boolean;
}

export function TableRow({ interactive = false, className, ...rest }: TableRowProps) {
  return (
    <tr className={cx("table-row", interactive && "table-row-interactive", className)} {...rest} />
  );
}

interface TableSkeletonProps {
  rows: number;
  columns: number;
}

/** Loading placeholder rows with the same shape as the real table body. */
export function TableSkeleton({ rows, columns }: TableSkeletonProps) {
  return (
    <tbody aria-busy="true">
      {Array.from({ length: rows }, (_, row) => (
        <TableRow key={row}>
          {Array.from({ length: columns }, (_, column) => (
            <TableCell key={column}>
              <Skeleton />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </tbody>
  );
}

interface TableCellProps extends TdHTMLAttributes<HTMLTableCellElement> {
  numeric?: boolean;
  muted?: boolean;
}

export function TableCell({ numeric = false, muted = false, className, ...rest }: TableCellProps) {
  return (
    <td
      className={cx(
        "table-cell",
        numeric && "table-cell-numeric",
        muted && "table-cell-muted",
        className,
      )}
      {...rest}
    />
  );
}
