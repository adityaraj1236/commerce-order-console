import type { OrderListParams } from "@/types/order";

/**
 * Every TanStack Query cache key in one place. Mutations invalidate by prefix,
 * e.g. invalidating `queryKeys.orders.all` refreshes every order list and detail.
 */
export const queryKeys = {
  products: ["products"] as const,
  orders: {
    all: ["orders"] as const,
    list: (params: OrderListParams) => ["orders", "list", params] as const,
    detail: (orderId: string) => ["orders", "detail", orderId] as const,
  },
  dashboard: ["dashboard"] as const,
};
