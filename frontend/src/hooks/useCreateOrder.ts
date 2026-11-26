"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createOrder } from "@/lib/api/ordersApi";
import { queryKeys } from "@/lib/api/queryKeys";

/**
 * Places an order. Whether it succeeds or fails, stock may have changed on the
 * server (ours or someone else's order), so products, orders and the dashboard
 * are refetched to keep the UI in step with the database.
 */
export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createOrder,
    onSettled: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.products }),
        queryClient.invalidateQueries({ queryKey: queryKeys.orders.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard }),
      ]),
  });
}
