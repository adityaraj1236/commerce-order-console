import type {
  Order,
  OrderCreate,
  OrderListParams,
  OrderListResponse,
  OrderStatus,
} from "@/types/order";

import { apiRequest } from "./apiClient";

export function listOrders({
  reference,
  status,
  page,
  pageSize,
}: OrderListParams = {}): Promise<OrderListResponse> {
  return apiRequest<OrderListResponse>("/orders", {
    query: { reference: reference?.trim(), status, page, page_size: pageSize },
  });
}

export function getOrder(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${encodeURIComponent(orderId)}`);
}

export function getOrderByReference(orderReference: string): Promise<Order> {
  return apiRequest<Order>(`/orders/reference/${encodeURIComponent(orderReference.trim())}`);
}

export function createOrder(payload: OrderCreate): Promise<Order> {
  return apiRequest<Order>("/orders", { method: "POST", body: payload });
}

export function updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
  return apiRequest<Order>(`/orders/${encodeURIComponent(orderId)}/status`, {
    method: "PATCH",
    body: { status },
  });
}
