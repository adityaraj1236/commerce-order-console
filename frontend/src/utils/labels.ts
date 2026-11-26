import type { OrderStatus } from "@/types/order";
import type { StockLevel } from "@/types/product";

/** Human-readable labels: the one place enum values become UI text. */

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  PLACED: "Placed",
  PACKED: "Packed",
  SHIPPED: "Shipped",
  CANCELLED: "Cancelled",
};

/** Button text for moving an order to each status. */
export const STATUS_ACTION_LABEL: Record<OrderStatus, string> = {
  PLACED: "Mark as placed",
  PACKED: "Mark as packed",
  SHIPPED: "Mark as shipped",
  CANCELLED: "Cancel order",
};

export const STOCK_LEVEL_LABEL: Record<StockLevel, string> = {
  in_stock: "In stock",
  low_stock: "Low stock",
  out_of_stock: "Out of stock",
};
