"use client";

import { PackageSearch, Plus, Search, ServerCrash } from "lucide-react";
import { useState } from "react";

import { Alert } from "@/components/base_components/Alert";
import { StatusBadge, StockBadge } from "@/components/base_components/Badge";
import { Button } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { ConfirmDialog } from "@/components/base_components/ConfirmDialog";
import { EmptyState } from "@/components/base_components/EmptyState";
import { FormField } from "@/components/base_components/FormField";
import { Input } from "@/components/base_components/Input";
import { QuantityStepper } from "@/components/base_components/QuantityStepper";
import { Select } from "@/components/base_components/Select";
import { Skeleton } from "@/components/base_components/Skeleton";
import { Spinner } from "@/components/base_components/Spinner";
import { Table, TableCell, TableHeaderCell, TableRow } from "@/components/base_components/Table";
import { useToast } from "@/components/base_components/Toast";
import { ORDER_STATUSES, type OrderStatus } from "@/types/order";
import type { StockLevel } from "@/types/product";
import { ORDER_STATUS_LABEL } from "@/utils/labels";
import { formatMoney, formatPaise, multiplyPaise } from "@/utils/money";

import "./components_preview.css";

const STOCK_LEVELS: StockLevel[] = ["in_stock", "low_stock", "out_of_stock"];

const SAMPLE_LINES = [
  { name: "Mechanical Keyboard (TKL)", unitPrice: "4499.00", quantity: 2 },
  { name: "Wireless Ergonomic Mouse", unitPrice: "1899.00", quantity: 1 },
];

const STATUS_FILTER_OPTIONS = [
  { value: "ALL" as const, label: "All statuses" },
  ...ORDER_STATUSES.map((status) => ({ value: status, label: ORDER_STATUS_LABEL[status] })),
];

export function ComponentsPreview() {
  const { showToast } = useToast();
  const [quantity, setQuantity] = useState(2);
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "ALL">("ALL");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const totalPaise = SAMPLE_LINES.reduce(
    (sum, line) => sum + multiplyPaise(line.unitPrice, line.quantity),
    0,
  );

  return (
    <main className="preview-page">
      <div className="preview-intro">
        <h1>Component preview</h1>
        <p className="preview-intro-text">
          Every base component, styled only from theme.css tokens. Temporary page for review.
        </p>
      </div>

      <Card title="Buttons">
        <div className="preview-row">
          <Button icon={<Plus className="icon-sm" aria-hidden="true" />}>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Cancel order</Button>
          <Button loading>Saving</Button>
          <Button disabled>Disabled</Button>
          <Button size="sm" variant="secondary">
            Small
          </Button>
        </div>
      </Card>

      <Card title="Status and stock badges">
        <div className="preview-stack">
          <div className="preview-row">
            {ORDER_STATUSES.map((status) => (
              <StatusBadge key={status} status={status} />
            ))}
          </div>
          <div className="preview-row">
            {STOCK_LEVELS.map((level) => (
              <StockBadge key={level} level={level} />
            ))}
          </div>
        </div>
      </Card>

      <Card title="Form controls">
        <div className="preview-form-grid">
          <FormField htmlFor="preview-search" label="Search by order reference">
            <Input
              id="preview-search"
              placeholder="e.g. ORD-20261125"
              icon={<Search className="icon-sm" />}
            />
          </FormField>
          <FormField htmlFor="preview-status" label="Status">
            <Select
              id="preview-status"
              options={STATUS_FILTER_OPTIONS}
              value={statusFilter}
              onValueChange={setStatusFilter}
            />
          </FormField>
          <FormField
            htmlFor="preview-invalid"
            label="Invalid field"
            error="Order reference can be at most 32 characters."
          >
            <Input id="preview-invalid" defaultValue="ORD-TOO-LONG" invalid />
          </FormField>
          <FormField htmlFor="preview-quantity" label="Quantity" hint="Available: 5">
            <QuantityStepper
              value={quantity}
              onChange={setQuantity}
              max={5}
              label="Quantity for Mechanical Keyboard"
            />
          </FormField>
        </div>
      </Card>

      <Card title="Table" flush>
        <Table caption="Sample order lines">
          <thead>
            <tr>
              <TableHeaderCell>Product</TableHeaderCell>
              <TableHeaderCell numeric>Unit price</TableHeaderCell>
              <TableHeaderCell numeric>Qty</TableHeaderCell>
              <TableHeaderCell numeric>Line total</TableHeaderCell>
            </tr>
          </thead>
          <tbody>
            {SAMPLE_LINES.map((line) => (
              <TableRow key={line.name} interactive>
                <TableCell>{line.name}</TableCell>
                <TableCell numeric muted>
                  {formatMoney(line.unitPrice)}
                </TableCell>
                <TableCell numeric>{line.quantity}</TableCell>
                <TableCell numeric>
                  {formatPaise(multiplyPaise(line.unitPrice, line.quantity))}
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={3}>Total</TableCell>
              <TableCell numeric>{formatPaise(totalPaise)}</TableCell>
            </TableRow>
          </tbody>
        </Table>
      </Card>

      <Card title="Alerts">
        <div className="preview-stack">
          <Alert
            tone="error"
            title="Insufficient stock. Nothing was ordered."
            items={["Noise-Cancelling Headset: requested 1, available 0."]}
          />
          <Alert tone="success" title="Order ORD-20261125-5CQCKL placed." />
          <Alert tone="info" title="Prices are confirmed by the server when you place the order." />
        </div>
      </Card>

      <Card title="Loading states">
        <div className="preview-row">
          <Spinner size="md" />
          <div className="preview-skeleton-list">
            <Skeleton variant="heading" />
            <Skeleton />
            <Skeleton />
          </div>
        </div>
      </Card>

      <Card title="Empty and error states">
        <div className="preview-form-grid">
          <EmptyState
            icon={PackageSearch}
            title="No orders match your search"
            description="Try a different reference or clear the status filter."
            action={<Button variant="secondary">Clear filters</Button>}
          />
          <EmptyState
            icon={ServerCrash}
            tone="error"
            title="Could not load orders"
            description="Cannot reach the server. Check that the backend is running and try again."
            action={<Button variant="secondary">Try again</Button>}
          />
        </div>
      </Card>

      <Card title="Dialog and toasts">
        <div className="preview-row">
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            Open cancel dialog
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              showToast({
                tone: "success",
                title: "Order placed",
                description: "ORD-20261125-5CQCKL",
              })
            }
          >
            Success toast
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              showToast({
                tone: "error",
                title: "Could not cancel order",
                description: "SHIPPED is a final status; no further changes are allowed.",
              })
            }
          >
            Error toast
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        title="Cancel order ORD-20261125-5CQCKL?"
        description="The order will be cancelled and its items returned to stock. This cannot be undone."
        confirmLabel="Cancel order"
        cancelLabel="Keep order"
        destructive
        onConfirm={() => setConfirmOpen(false)}
        onCancel={() => setConfirmOpen(false)}
      />
    </main>
  );
}
