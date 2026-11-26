import type { DashboardSummary } from "@/types/dashboard";

import { apiRequest } from "./apiClient";

export function getDashboardSummary(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>("/dashboard/summary");
}
