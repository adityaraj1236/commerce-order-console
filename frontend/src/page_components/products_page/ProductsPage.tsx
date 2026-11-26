"use client";

import { PackageOpen, Plus, ServerCrash } from "lucide-react";

import { StockBadge } from "@/components/base_components/Badge";
import { Button, ButtonLink } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import {
  Table,
  TableCell,
  TableHeaderCell,
  TableRow,
  TableSkeleton,
} from "@/components/base_components/Table";
import { PageHeader } from "@/components/global_components/PageHeader";
import { ProductIdentity } from "@/components/global_components/ProductIdentity";
import { ROUTES } from "@/components/global_components/navigation";
import { useProducts } from "@/hooks/useProducts";
import type { Product } from "@/types/product";
import { getErrorMessage } from "@/utils/apiErrors";
import { formatMoney } from "@/utils/money";

import "./products.css";

const COLUMN_COUNT = 5;
const SKELETON_ROWS = 6;

export function ProductsPage() {
  const { data, isPending, isError, error, refetch, isRefetching } = useProducts();

  return (
    <>
      <PageHeader
        title="Products"
        description={
          data ? `${data.total} products in the catalogue` : "Catalogue with prices and stock."
        }
        actions={
          <ButtonLink
            href={ROUTES.createOrder}
            icon={<Plus className="icon-sm" aria-hidden="true" />}
          >
            Create order
          </ButtonLink>
        }
      />

      <Card flush>
        {isError ? (
          <EmptyState
            icon={ServerCrash}
            tone="error"
            title="Could not load products"
            description={getErrorMessage(error)}
            action={
              <Button variant="secondary" onClick={() => refetch()} loading={isRefetching}>
                Try again
              </Button>
            }
          />
        ) : data && data.items.length === 0 ? (
          <EmptyState
            icon={PackageOpen}
            title="No products yet"
            description="Run the seed script to add the sample catalogue."
          />
        ) : (
          <Table caption="Product catalogue with prices and stock">
            <thead>
              <tr>
                <TableHeaderCell>Product</TableHeaderCell>
                <TableHeaderCell>Description</TableHeaderCell>
                <TableHeaderCell numeric>Price</TableHeaderCell>
                <TableHeaderCell numeric>Available</TableHeaderCell>
                <TableHeaderCell>Stock</TableHeaderCell>
              </tr>
            </thead>
            {isPending ? (
              <TableSkeleton rows={SKELETON_ROWS} columns={COLUMN_COUNT} />
            ) : (
              <tbody>
                {data.items.map((product) => (
                  <ProductRow key={product.id} product={product} />
                ))}
              </tbody>
            )}
          </Table>
        )}
      </Card>
    </>
  );
}

function ProductRow({ product }: { product: Product }) {
  return (
    <TableRow>
      <TableCell>
        <ProductIdentity name={product.name} sku={product.sku} />
      </TableCell>
      <TableCell muted className="products-description-cell">
        {product.description}
      </TableCell>
      <TableCell numeric>{formatMoney(product.price)}</TableCell>
      <TableCell numeric>{product.stock_quantity}</TableCell>
      <TableCell>
        <StockBadge level={product.stock_level} />
      </TableCell>
    </TableRow>
  );
}
