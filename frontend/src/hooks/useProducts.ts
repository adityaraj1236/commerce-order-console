"use client";

import { useQuery } from "@tanstack/react-query";

import { listProducts } from "@/lib/api/productsApi";
import { queryKeys } from "@/lib/api/queryKeys";

/** The product catalogue with live stock. Shared by the Products and Create Order pages. */
export function useProducts() {
  return useQuery({ queryKey: queryKeys.products, queryFn: listProducts });
}
