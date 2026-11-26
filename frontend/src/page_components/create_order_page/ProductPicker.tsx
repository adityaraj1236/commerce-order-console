"use client";

import { Plus, Search, SearchX } from "lucide-react";
import { useState } from "react";

import { StockBadge } from "@/components/base_components/Badge";
import { Button } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { Input } from "@/components/base_components/Input";
import {
  Table,
  TableCell,
  TableHeaderCell,
  TableRow,
  TableSkeleton,
} from "@/components/base_components/Table";
import { ProductIdentity } from "@/components/global_components/ProductIdentity";
import type { CartQuantities } from "@/hooks/useCart";
import type { Product } from "@/types/product";
import { cx } from "@/utils/classNames";
import { formatMoney } from "@/utils/money";

const COLUMN_COUNT = 4;
const SKELETON_ROWS = 6;

interface ProductPickerProps {
  products: Product[] | undefined;
  quantities: CartQuantities;
  onAdd: (product: Product) => void;
}

function matchesSearch(product: Product, search: string): boolean {
  const term = search.trim().toLowerCase();
  return (
    term === "" ||
    product.name.toLowerCase().includes(term) ||
    product.sku.toLowerCase().includes(term)
  );
}

export function ProductPicker({ products, quantities, onAdd }: ProductPickerProps) {
  const [search, setSearch] = useState("");
  const visibleProducts = products?.filter((product) => matchesSearch(product, search));

  return (
    <Card
      title="Catalogue"
      flush
      actions={
        <div className="product-picker-search">
          <label htmlFor="product-search" className="visually-hidden">
            Search products by name or SKU
          </label>
          <Input
            id="product-search"
            type="search"
            placeholder="Search name or SKU"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            icon={<Search className="icon-sm" />}
          />
        </div>
      }
    >
      {visibleProducts && visibleProducts.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="No products match"
          description={`Nothing matches "${search.trim()}". Try another name or SKU.`}
        />
      ) : (
        <Table caption="Products available to add to the order">
          <thead>
            <tr>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell numeric>Price</TableHeaderCell>
              <TableHeaderCell>Stock</TableHeaderCell>
              <TableHeaderCell numeric>
                <span className="visually-hidden">Add to order</span>
              </TableHeaderCell>
            </tr>
          </thead>
          {visibleProducts ? (
            <tbody>
              {visibleProducts.map((product) => (
                <PickerRow
                  key={product.id}
                  product={product}
                  inCart={quantities[product.id] ?? 0}
                  onAdd={onAdd}
                />
              ))}
            </tbody>
          ) : (
            <TableSkeleton rows={SKELETON_ROWS} columns={COLUMN_COUNT} />
          )}
        </Table>
      )}
    </Card>
  );
}

interface PickerRowProps {
  product: Product;
  inCart: number;
  onAdd: (product: Product) => void;
}

function PickerRow({ product, inCart, onAdd }: PickerRowProps) {
  const outOfStock = product.stock_quantity === 0;
  const allStockInCart = inCart >= product.stock_quantity;
  const label = outOfStock ? "Unavailable" : inCart > 0 ? `In cart (${inCart})` : "Add";

  return (
    <TableRow>
      <TableCell>
        <ProductIdentity name={product.name} sku={product.sku} />
      </TableCell>
      <TableCell numeric>{formatMoney(product.price)}</TableCell>
      <TableCell>
        <div className="product-picker-stock">
          <StockBadge level={product.stock_level} />
          <span
            className={cx(
              "product-picker-available",
              product.stock_level === "low_stock" && "product-picker-available-low",
            )}
          >
            {product.stock_level === "low_stock"
              ? `Only ${product.stock_quantity} left`
              : `${product.stock_quantity} available`}
          </span>
        </div>
      </TableCell>
      <TableCell numeric>
        <Button
          size="sm"
          variant={inCart > 0 ? "secondary" : "primary"}
          icon={outOfStock ? undefined : <Plus className="icon-sm" aria-hidden="true" />}
          disabled={outOfStock || allStockInCart}
          onClick={() => onAdd(product)}
          aria-label={`Add ${product.name} to the order`}
          title={allStockInCart && !outOfStock ? "All available stock is in the cart" : undefined}
        >
          {label}
        </Button>
      </TableCell>
    </TableRow>
  );
}
