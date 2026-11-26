import type { Metadata } from "next";

import { CreateOrderPage } from "@/page_components/create_order_page/CreateOrderPage";

export const metadata: Metadata = { title: "Create Order · Commerce Order Console" };

export default function Page() {
  return <CreateOrderPage />;
}
