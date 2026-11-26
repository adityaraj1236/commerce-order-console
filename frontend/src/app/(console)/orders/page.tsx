import type { Metadata } from "next";
import { Suspense } from "react";

import { OrdersPage } from "@/page_components/orders_page/OrdersPage";

export const metadata: Metadata = { title: "Orders · Commerce Order Console" };

export default function Page() {
  // The page reads its filters from the URL, which Next.js requires inside Suspense.
  return (
    <Suspense>
      <OrdersPage />
    </Suspense>
  );
}
