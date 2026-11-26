import Link from "next/link";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/base_components/Skeleton";

interface MetricCardProps {
  /** Text, or a badge so status cards share the status colors. */
  label: ReactNode;
  value: number | undefined;
  hint: string;
  /** Where the card leads, e.g. the order list filtered by this status. */
  href: string;
}

/** One dashboard figure. Reuses the base `card` class for its surface. */
export function MetricCard({ label, value, hint, href }: MetricCardProps) {
  return (
    <Link href={href} className="card metric-card">
      <span className="metric-card-label">{label}</span>
      {value === undefined ? (
        <Skeleton variant="display" />
      ) : (
        <span className="metric-card-value">{value}</span>
      )}
      <span className="metric-card-hint">{hint}</span>
    </Link>
  );
}
