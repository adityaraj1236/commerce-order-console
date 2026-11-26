"use client";

import { useCallback, useState } from "react";

import type { Product } from "@/types/product";

/** productId -> quantity. Prices are not stored: they are always read from the live catalogue. */
export type CartQuantities = Record<string, number>;

/** Cart state for the Create Order page. Quantities stay whole numbers within the stock. */
export function useCart() {
  const [quantities, setQuantities] = useState<CartQuantities>({});

  const addProduct = useCallback((product: Product) => {
    setQuantities((current) => {
      const next = (current[product.id] ?? 0) + 1;
      return { ...current, [product.id]: Math.min(next, product.stock_quantity) };
    });
  }, []);

  const setQuantity = useCallback((productId: string, quantity: number) => {
    setQuantities((current) => ({ ...current, [productId]: quantity }));
  }, []);

  const removeProduct = useCallback((productId: string) => {
    setQuantities((current) =>
      Object.fromEntries(Object.entries(current).filter(([id]) => id !== productId)),
    );
  }, []);

  const clear = useCallback(() => setQuantities({}), []);

  return { quantities, addProduct, setQuantity, removeProduct, clear };
}
