"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { isOrderStatus, type OrderStatus } from "@/types/order";

export const ORDERS_PAGE_SIZE = 10;

interface FilterChanges {
  reference?: string;
  status?: OrderStatus | null;
  page?: number;
}

/**
 * Order list filters live in the URL (?reference=&status=&page=), so they survive
 * opening an order and coming back, and the dashboard can link to a filtered list.
 * Invalid values in the URL are ignored rather than sent to the API.
 */
export function useOrderFilters() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const reference = searchParams.get("reference") ?? "";
  const statusParam = searchParams.get("status");
  const status = isOrderStatus(statusParam) ? statusParam : undefined;
  const page = Math.max(1, Math.trunc(Number(searchParams.get("page"))) || 1);

  const update = (changes: FilterChanges) => {
    const next = new URLSearchParams(searchParams);
    const set = (key: string, value: string | undefined) =>
      value ? next.set(key, value) : next.delete(key);

    if (changes.reference !== undefined) set("reference", changes.reference.trim());
    if (changes.status !== undefined) set("status", changes.status ?? undefined);
    if (changes.page !== undefined)
      set("page", changes.page > 1 ? String(changes.page) : undefined);

    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  return {
    reference,
    status,
    page,
    hasFilters: reference !== "" || status !== undefined,
    update,
  };
}
