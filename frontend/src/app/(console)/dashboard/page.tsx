import type { Metadata } from "next";

import { DashboardPage } from "@/page_components/dashboard_page/DashboardPage";

export const metadata: Metadata = { title: "Dashboard · Commerce Order Console" };

export default function Page() {
  return <DashboardPage />;
}
