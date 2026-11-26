import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "./Button";
import "./base_components.css";

interface PaginationProps {
  page: number;
  totalPages: number;
  totalItems: number;
  /** e.g. "orders" -> "Page 1 of 3 · 24 orders" */
  itemLabel: string;
  onPageChange: (page: number) => void;
  /** Disable buttons while the next page loads. */
  busy?: boolean;
}

export function Pagination({
  page,
  totalPages,
  totalItems,
  itemLabel,
  onPageChange,
  busy = false,
}: PaginationProps) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <p className="pagination-summary">
        Page {page} of {Math.max(totalPages, 1)} · {totalItems} {itemLabel}
      </p>
      <div className="pagination-buttons">
        <Button
          variant="secondary"
          size="sm"
          icon={<ChevronLeft className="icon-sm" aria-hidden="true" />}
          disabled={busy || page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={busy || page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
          <ChevronRight className="icon-sm" aria-hidden="true" />
        </Button>
      </div>
    </nav>
  );
}
