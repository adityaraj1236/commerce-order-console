import type { IsoDateTime, MoneyString } from "./api";

/** Mirrors backend `OrderStatus`. The single list every page iterates over. */
export const ORDER_STATUSES = ["PLACED", "PACKED", "SHIPPED", "CANCELLED"] as const;

export type OrderStatus = (typeof ORDER_STATUSES)[number];

/** Narrows untrusted input (e.g. a URL parameter) to a valid status. */
export function isOrderStatus(value: string | null | undefined): value is OrderStatus {
  return ORDER_STATUSES.some((status) => status === value);
}

/** Mirrors backend `OrderItemCreate`. Prices are never sent: the backend decides them. */
export interface OrderItemCreate {
  product_id: string;
  quantity: number;
}

export interface OrderCreate {
  items: OrderItemCreate[];
}

/** Mirrors backend `OrderItemRead`. Name and unit price are snapshots from order time. */
export interface OrderItem {
  product_id: string;
  product_name: string;
  unit_price: MoneyString;
  quantity: number;
  line_total: MoneyString;
}

/** Mirrors backend `OrderRead`. */
export interface Order {
  id: string;
  order_reference: string;
  status: OrderStatus;
  total_amount: MoneyString;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
  items: OrderItem[];
  item_count: number;
  /** Statuses this order may move to next; the UI shows only these actions. */
  allowed_transitions: OrderStatus[];
}

/** Mirrors backend `OrderSummary`: one row of the order list. */
export interface OrderSummary {
  id: string;
  order_reference: string;
  status: OrderStatus;
  total_amount: MoneyString;
  item_count: number;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
}

export interface OrderListResponse {
  items: OrderSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OrderListParams {
  reference?: string;
  status?: OrderStatus;
  page?: number;
  pageSize?: number;
}
