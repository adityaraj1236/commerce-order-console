"use client";

import { useQuery } from "@tanstack/react-query";

import { getDashboardSummary } from "@/lib/api/dashboardApi";
import { queryKeys } from "@/lib/api/queryKeys";

export function useDashboardSummary() {
  return useQuery({ queryKey: queryKeys.dashboard, queryFn: getDashboardSummary });
}
