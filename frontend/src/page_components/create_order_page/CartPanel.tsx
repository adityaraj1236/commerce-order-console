"use client";

import { ShoppingCart, Trash2 } from "lucide-react";

import { Alert } from "@/components/base_components/Alert";
import { Button } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { QuantityStepper } from "@/components/base_components/QuantityStepper";
import { SummaryList } from "@/components/base_components/SummaryList";
import { ProductIdentity } from "@/components/global_components/ProductIdentity";
import { formatMoney, formatPaise } from "@/utils/money";

import type { CartLine } from "./cartLines";

interface CartPanelProps {
  lines: CartLine[];
  /** Messages from the server for specific lines (409 / 404), keyed by product id. */
  lineErrors: Record<string, string>;
  submitting: boolean;
  onQuantityChange: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
  onSubmit: () => void;
}

export function CartPanel({
  lines,
  lineErrors,
  submitting,
  onQuantityChange,
  onRemove,
  onSubmit,
}: CartPanelProps) {
  const totalPaise = lines.reduce((sum, line) => sum + line.lineTotalPaise, 0);
  const totalUnits = lines.reduce((sum, line) => sum + line.quantity, 0);
  const hasIssues = lines.some((line) => line.issue !== null);

  return (
    <Card
      title="Order summary"
      className="cart-panel"
      actions={<span className="cart-count">{totalUnits} items</span>}
    >
      {lines.length === 0 ? (
        <EmptyState
          icon={ShoppingCart}
          title="Cart is empty"
          description="Add products from the catalogue to start an order."
        />
      ) : (
        <div className="cart-content">
          <ul className="cart-lines">
            {lines.map((line) => (
              <CartLineItem
                key={line.product.id}
                line={line}
                serverError={lineErrors[line.product.id]}
                disabled={submitting}
                onQuantityChange={onQuantityChange}
                onRemove={onRemove}
              />
            ))}
          </ul>

          <SummaryList
            items={[
              { label: "Items", value: totalUnits },
              { label: "Total", value: formatPaise(totalPaise), emphasis: true },
            ]}
          />

          {hasIssues ? (
            <Alert tone="error" title="Fix the highlighted items to place the order." />
          ) : null}

          <Button fullWidth onClick={onSubmit} loading={submitting} disabled={hasIssues}>
            Place order
          </Button>
          <p className="cart-note">Prices and stock are confirmed by the server when you order.</p>
        </div>
      )}
    </Card>
  );
}

interface CartLineItemProps {
  line: CartLine;
  serverError: string | undefined;
  disabled: boolean;
  onQuantityChange: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
}

function CartLineItem({
  line,
  serverError,
  disabled,
  onQuantityChange,
  onRemove,
}: CartLineItemProps) {
  const { product, quantity, lineTotalPaise, issue, atStockLimit } = line;
  const message = issue ?? serverError;

  return (
    <li className="cart-line">
      <div className="cart-line-header">
        <ProductIdentity name={product.name} sku={product.sku} />
        <Button
          variant="ghost"
          size="sm"
          iconOnly
          icon={<Trash2 className="icon-sm" aria-hidden="true" />}
          onClick={() => onRemove(product.id)}
          disabled={disabled}
          aria-label={`Remove ${product.name} from the order`}
        />
      </div>
      <div className="cart-line-controls">
        <QuantityStepper
          value={quantity}
          onChange={(next) => onQuantityChange(product.id, next)}
          max={Math.max(product.stock_quantity, 1)}
          disabled={disabled || product.stock_quantity === 0}
          label={`Quantity for ${product.name}`}
        />
        <span className="cart-line-price">× {formatMoney(product.price)}</span>
        <span className="cart-line-total">{formatPaise(lineTotalPaise)}</span>
      </div>
      {message ? (
        <p className="cart-line-issue" role="alert">
          {message}
        </p>
      ) : atStockLimit ? (
        <p className="cart-line-limit">Maximum available quantity added.</p>
      ) : null}
    </li>
  );
}
