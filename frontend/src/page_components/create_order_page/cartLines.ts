import type { CartQuantities } from "@/hooks/useCart";
import type { ApiErrorDetail } from "@/types/api";
import type { OrderCreate } from "@/types/order";
import type { Product } from "@/types/product";
import { multiplyPaise } from "@/utils/money";

export interface CartLine {
  product: Product;
  quantity: number;
  /** Paise, for the preview only; the backend calculates the real total. */
  lineTotalPaise: number;
  /** Why this line cannot be ordered as it is, based on the latest stock. */
  issue: string | null;
  /** Every available unit is already in the cart; nothing more can be added. */
  atStockLimit: boolean;
}

function findIssue(product: Product, quantity: number): string | null {
  if (product.stock_quantity === 0) {
    return "Out of stock now. Remove it to place the order.";
  }
  if (quantity > product.stock_quantity) {
    return `Only ${product.stock_quantity} available. Reduce the quantity.`;
  }
  return null;
}

/** Joins cart quantities with the live catalogue, so prices and stock are always current. */
export function buildCartLines(quantities: CartQuantities, products: Product[]): CartLine[] {
  const productsById = new Map(products.map((product) => [product.id, product]));
  return Object.entries(quantities).flatMap(([productId, quantity]) => {
    const product = productsById.get(productId);
    if (!product) return [];
    return [
      {
        product,
        quantity,
        lineTotalPaise: multiplyPaise(product.price, quantity),
        issue: findIssue(product, quantity),
        atStockLimit: product.stock_quantity > 0 && quantity === product.stock_quantity,
      },
    ];
  });
}

function pluralizeUnits(count: number): string {
  return count === 1 ? "unit is" : "units are";
}

/** "27" QHD Monitor: all 1 available unit is in this order." for each line at its limit. */
export function describeStockLimits(lines: CartLine[]): string[] {
  return lines
    .filter((line) => line.atStockLimit)
    .map(
      ({ product }) =>
        `${product.name}: all ${product.stock_quantity} available ${pluralizeUnits(product.stock_quantity)} in this order.`,
    );
}

export function toOrderPayload(lines: CartLine[]): OrderCreate {
  return {
    items: lines.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
  };
}

const ITEM_FIELD_PATTERN = /^items\.(\d+)\./;

/**
 * Maps backend error details ("items.1.quantity") back to product ids using the
 * payload that was sent, so each cart line can show its own server message.
 */
export function mapLineErrors(
  details: ApiErrorDetail[],
  payload: OrderCreate | undefined,
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const detail of details) {
    const index = ITEM_FIELD_PATTERN.exec(detail.field)?.[1];
    const productId = index === undefined ? undefined : payload?.items[Number(index)]?.product_id;
    if (productId) {
      errors[productId] = detail.message;
    }
  }
  return errors;
}
