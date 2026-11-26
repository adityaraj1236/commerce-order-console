import type { OrderStatus } from "./order";

/** Mirrors backend `DashboardSummary`. */
export interface DashboardSummary {
  orders: {
    total: number;
    by_status: Record<OrderStatus, number>;
  };
  products: {
    total: number;
    low_stock: number;
    out_of_stock: number;
    low_stock_threshold: number;
  };
}
