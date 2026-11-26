import type { OrderStatus } from "@/types/order";
import type { StockLevel } from "@/types/product";
import { ORDER_STATUS_LABEL, STOCK_LEVEL_LABEL } from "@/utils/labels";

import "./base_components.css";

/** Every tone maps to one class in base_components.css, colored from theme.css. */
type BadgeTone =
  | "status-placed"
  | "status-packed"
  | "status-shipped"
  | "status-cancelled"
  | "stock-in"
  | "stock-low"
  | "stock-out";

interface BadgeProps {
  tone: BadgeTone;
  label: string;
}

export function Badge({ tone, label }: BadgeProps) {
  return (
    <span className={`badge badge-${tone}`}>
      <span className="badge-dot" aria-hidden="true" />
      {label}
    </span>
  );
}

const STATUS_TONE: Record<OrderStatus, BadgeTone> = {
  PLACED: "status-placed",
  PACKED: "status-packed",
  SHIPPED: "status-shipped",
  CANCELLED: "status-cancelled",
};

/** The only way an order status is shown anywhere in the app. */
export function StatusBadge({ status }: { status: OrderStatus }) {
  return <Badge tone={STATUS_TONE[status]} label={ORDER_STATUS_LABEL[status]} />;
}

const STOCK_TONE: Record<StockLevel, BadgeTone> = {
  in_stock: "stock-in",
  low_stock: "stock-low",
  out_of_stock: "stock-out",
};

/** The only way a stock level is shown. The level itself comes from the backend. */
export function StockBadge({ level }: { level: StockLevel }) {
  return <Badge tone={STOCK_TONE[level]} label={STOCK_LEVEL_LABEL[level]} />;
}
