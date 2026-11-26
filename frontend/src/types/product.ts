import type { IsoDateTime, MoneyString } from "./api";

/** Mirrors backend `StockLevel`. The backend owns the low-stock threshold. */
export type StockLevel = "in_stock" | "low_stock" | "out_of_stock";

/** Mirrors backend `ProductRead`. */
export interface Product {
  id: string;
  name: string;
  sku: string;
  description: string;
  price: MoneyString;
  stock_quantity: number;
  is_in_stock: boolean;
  stock_level: StockLevel;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
}
