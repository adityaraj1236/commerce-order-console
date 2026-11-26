import type { Metadata } from "next";

import { OrderDetailPage } from "@/page_components/order_detail_page/OrderDetailPage";

export const metadata: Metadata = { title: "Order · Commerce Order Console" };

export default async function Page({ params }: { params: Promise<{ orderId: string }> }) {
  const { orderId } = await params;
  return <OrderDetailPage orderId={orderId} />;
}
