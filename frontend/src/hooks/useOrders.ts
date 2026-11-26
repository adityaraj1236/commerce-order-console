"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getOrder, listOrders, updateOrderStatus } from "@/lib/api/ordersApi";
import { queryKeys } from "@/lib/api/queryKeys";
import type { OrderListParams, OrderStatus } from "@/types/order";

/** One page of the order list. The previous page stays visible while the next one loads. */
export function useOrders(params: OrderListParams) {
  return useQuery({
    queryKey: queryKeys.orders.list(params),
    queryFn: () => listOrders(params),
    placeholderData: keepPreviousData,
  });
}

export function useOrder(orderId: string) {
  return useQuery({
    queryKey: queryKeys.orders.detail(orderId),
    queryFn: () => getOrder(orderId),
  });
}

/**
 * Changes an order's status. The response is the updated order, shown immediately;
 * lists, stock (a cancellation restores it) and the dashboard are then refetched.
 */
export function useUpdateOrderStatus(orderId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: OrderStatus) => updateOrderStatus(orderId, status),
    onSuccess: (order) => queryClient.setQueryData(queryKeys.orders.detail(orderId), order),
    onSettled: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.orders.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.products }),
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard }),
      ]),
  });
}
