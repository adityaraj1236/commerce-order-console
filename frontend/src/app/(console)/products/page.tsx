import type { Metadata } from "next";

import { ProductsPage } from "@/page_components/products_page/ProductsPage";

export const metadata: Metadata = { title: "Products · Commerce Order Console" };

export default function Page() {
  return <ProductsPage />;
}
