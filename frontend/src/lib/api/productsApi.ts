import type { Product, ProductListResponse } from "@/types/product";

import { apiRequest } from "./apiClient";

export function listProducts(): Promise<ProductListResponse> {
  return apiRequest<ProductListResponse>("/products");
}

export function getProduct(productId: string): Promise<Product> {
  return apiRequest<Product>(`/products/${encodeURIComponent(productId)}`);
}
