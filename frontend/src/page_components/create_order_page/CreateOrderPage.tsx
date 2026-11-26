"use client";

import { ServerCrash } from "lucide-react";
import { useState } from "react";

import { Alert } from "@/components/base_components/Alert";
import { Button, ButtonLink } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { useToast } from "@/components/base_components/Toast";
import { PageHeader } from "@/components/global_components/PageHeader";
import { ROUTES } from "@/components/global_components/navigation";
import { useCart } from "@/hooks/useCart";
import { useCreateOrder } from "@/hooks/useCreateOrder";
import { useProducts } from "@/hooks/useProducts";
import type { Order } from "@/types/order";
import type { Product } from "@/types/product";
import { getErrorDetails, getErrorMessage } from "@/utils/apiErrors";
import { formatMoney } from "@/utils/money";

import { CartPanel } from "./CartPanel";
import { ProductPicker } from "./ProductPicker";
import { buildCartLines, describeStockLimits, mapLineErrors, toOrderPayload } from "./cartLines";
import "./create_order.css";

export function CreateOrderPage() {
  const products = useProducts();
  const cart = useCart();
  const createOrder = useCreateOrder();
  const { showToast } = useToast();
  const [placedOrder, setPlacedOrder] = useState<Order | null>(null);

  const lines = buildCartLines(cart.quantities, products.data?.items ?? []);
  const lineErrors = mapLineErrors(getErrorDetails(createOrder.error), createOrder.variables);
  const stockLimitMessages = describeStockLimits(lines);

  // Any cart edit clears the previous result: old errors no longer describe the cart.
  const clearResult = () => {
    createOrder.reset();
    setPlacedOrder(null);
  };

  const handleAdd = (product: Product) => {
    clearResult();
    cart.addProduct(product);
  };

  const handleQuantityChange = (productId: string, quantity: number) => {
    clearResult();
    cart.setQuantity(productId, quantity);
  };

  const handleRemove = (productId: string) => {
    clearResult();
    cart.removeProduct(productId);
  };

  const handleSubmit = () => {
    setPlacedOrder(null);
    createOrder.mutate(toOrderPayload(lines), {
      onSuccess: (order) => {
        setPlacedOrder(order);
        cart.clear();
        showToast({
          tone: "success",
          title: "Order placed",
          description: `${order.order_reference} · ${formatMoney(order.total_amount)}`,
        });
      },
      onError: (error) => {
        showToast({
          tone: "error",
          title: "Order not placed",
          description: getErrorMessage(error),
        });
      },
    });
  };

  return (
    <>
      <PageHeader
        title="Create Order"
        description="Add products, check the total and place the order. Stock is reserved only when the order is placed."
      />

      {placedOrder ? (
        <Alert tone="success" title={`Order ${placedOrder.order_reference} placed.`}>
          <p>
            {placedOrder.item_count} items · {formatMoney(placedOrder.total_amount)}. Stock has been
            updated.
          </p>
          <div className="create-order-result-actions">
            <ButtonLink href={ROUTES.orderDetail(placedOrder.id)} size="sm">
              View order
            </ButtonLink>
            <ButtonLink href={ROUTES.orders} size="sm" variant="secondary">
              All orders
            </ButtonLink>
          </div>
        </Alert>
      ) : null}

      {stockLimitMessages.length > 0 ? (
        <Alert tone="warning" title="Stock limit reached" items={stockLimitMessages}>
          <p>No more units can be added until the product is restocked.</p>
        </Alert>
      ) : null}

      {createOrder.isError ? (
        <Alert
          tone="error"
          title={`Order not placed: ${getErrorMessage(createOrder.error)}`}
          items={getErrorDetails(createOrder.error).map((detail) => detail.message)}
        >
          <p>Nothing was ordered and no stock was changed.</p>
        </Alert>
      ) : null}

      {products.isError ? (
        <Card>
          <EmptyState
            icon={ServerCrash}
            tone="error"
            title="Could not load the catalogue"
            description={getErrorMessage(products.error)}
            action={
              <Button
                variant="secondary"
                onClick={() => products.refetch()}
                loading={products.isRefetching}
              >
                Try again
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="create-order-layout">
          <ProductPicker
            products={products.data?.items}
            quantities={cart.quantities}
            onAdd={handleAdd}
          />
          <CartPanel
            lines={lines}
            lineErrors={lineErrors}
            submitting={createOrder.isPending}
            onQuantityChange={handleQuantityChange}
            onRemove={handleRemove}
            onSubmit={handleSubmit}
          />
        </div>
      )}
    </>
  );
}
