"use client";

import { Plus, ReceiptText, Search, SearchX, ServerCrash } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { StatusBadge } from "@/components/base_components/Badge";
import { Button, ButtonLink } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { FormField } from "@/components/base_components/FormField";
import { Input } from "@/components/base_components/Input";
import { Pagination } from "@/components/base_components/Pagination";
import { Select, type SelectOption } from "@/components/base_components/Select";
import {
  Table,
  TableCell,
  TableHeaderCell,
  TableRow,
  TableSkeleton,
} from "@/components/base_components/Table";
import { PageHeader } from "@/components/global_components/PageHeader";
import { ROUTES } from "@/components/global_components/navigation";
import { useOrders } from "@/hooks/useOrders";
import { ORDER_STATUSES, type OrderStatus, type OrderSummary } from "@/types/order";
import { getErrorMessage } from "@/utils/apiErrors";
import { formatDateTime } from "@/utils/dateUtils";
import { ORDER_STATUS_LABEL } from "@/utils/labels";
import { formatMoney } from "@/utils/money";

import { ORDERS_PAGE_SIZE, useOrderFilters } from "./useOrderFilters";
import "./orders.css";

const SEARCH_DEBOUNCE_MS = 300;
const COLUMN_COUNT = 5;
const ALL_STATUSES = "ALL";
type StatusFilterValue = OrderStatus | typeof ALL_STATUSES;

const STATUS_OPTIONS: SelectOption<StatusFilterValue>[] = [
  { value: ALL_STATUSES, label: "All statuses" },
  ...ORDER_STATUSES.map((status) => ({ value: status, label: ORDER_STATUS_LABEL[status] })),
];

export function OrdersPage() {
  const filters = useOrderFilters();
  const orders = useOrders({
    reference: filters.reference,
    status: filters.status,
    page: filters.page,
    pageSize: ORDERS_PAGE_SIZE,
  });

  // The search box updates instantly; the URL (and the API call) follows after a pause.
  const [searchInput, setSearchInput] = useState(filters.reference);
  const searchTimer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(searchTimer.current), []);

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    window.clearTimeout(searchTimer.current);
    searchTimer.current = window.setTimeout(
      () => filters.update({ reference: value, page: 1 }),
      SEARCH_DEBOUNCE_MS,
    );
  };

  const clearFilters = () => {
    window.clearTimeout(searchTimer.current);
    setSearchInput("");
    filters.update({ reference: "", status: null, page: 1 });
  };

  return (
    <>
      <PageHeader
        title="Orders"
        description="Search by reference, filter by status and open an order to manage it."
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
        <div className="orders-toolbar">
          <div className="orders-toolbar-search">
            <FormField htmlFor="order-search" label="Order reference">
              <Input
                id="order-search"
                type="search"
                placeholder="e.g. ORD-20261125 or 5CQCKL"
                value={searchInput}
                maxLength={32}
                onChange={(event) => handleSearchChange(event.target.value)}
                icon={<Search className="icon-sm" />}
              />
            </FormField>
          </div>
          <div className="orders-toolbar-status">
            <FormField htmlFor="order-status" label="Status">
              <Select<StatusFilterValue>
                id="order-status"
                options={STATUS_OPTIONS}
                value={filters.status ?? ALL_STATUSES}
                onValueChange={(value) =>
                  filters.update({ status: value === ALL_STATUSES ? null : value, page: 1 })
                }
              />
            </FormField>
          </div>
          {filters.hasFilters ? (
            <Button variant="ghost" onClick={clearFilters}>
              Clear filters
            </Button>
          ) : null}
        </div>

        <OrdersTableContent
          orders={orders}
          hasFilters={filters.hasFilters}
          onClearFilters={clearFilters}
          onPageChange={(page) => filters.update({ page })}
        />
      </Card>
    </>
  );
}

interface OrdersTableContentProps {
  orders: ReturnType<typeof useOrders>;
  hasFilters: boolean;
  onClearFilters: () => void;
  onPageChange: (page: number) => void;
}

function OrdersTableContent({
  orders,
  hasFilters,
  onClearFilters,
  onPageChange,
}: OrdersTableContentProps) {
  const { data, isPending, isError, error, refetch, isRefetching, isPlaceholderData } = orders;

  if (isError) {
    return (
      <EmptyState
        icon={ServerCrash}
        tone="error"
        title="Could not load orders"
        description={getErrorMessage(error)}
        action={
          <Button variant="secondary" onClick={() => refetch()} loading={isRefetching}>
            Try again
          </Button>
        }
      />
    );
  }

  if (data && data.total === 0) {
    return hasFilters ? (
      <EmptyState
        icon={SearchX}
        title="No orders match your filters"
        description="Try a different reference, or clear the filters to see every order."
        action={
          <Button variant="secondary" onClick={onClearFilters}>
            Clear filters
          </Button>
        }
      />
    ) : (
      <EmptyState
        icon={ReceiptText}
        title="No orders yet"
        description="Orders placed from the Create Order page will appear here."
        action={<ButtonLink href={ROUTES.createOrder}>Create the first order</ButtonLink>}
      />
    );
  }

  if (data && data.items.length === 0) {
    return (
      <EmptyState
        icon={SearchX}
        title="This page is empty"
        description={`There are only ${data.total_pages} pages of results.`}
        action={
          <Button variant="secondary" onClick={() => onPageChange(1)}>
            Go to the first page
          </Button>
        }
      />
    );
  }

  return (
    <>
      <Table caption="Orders, newest first">
        <thead>
          <tr>
            <TableHeaderCell>Reference</TableHeaderCell>
            <TableHeaderCell>Created</TableHeaderCell>
            <TableHeaderCell numeric>Items</TableHeaderCell>
            <TableHeaderCell numeric>Total</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </tr>
        </thead>
        {isPending ? (
          <TableSkeleton rows={ORDERS_PAGE_SIZE} columns={COLUMN_COUNT} />
        ) : (
          <tbody className={isPlaceholderData ? "orders-table-stale" : undefined}>
            {data.items.map((order) => (
              <OrderRow key={order.id} order={order} />
            ))}
          </tbody>
        )}
      </Table>
      {data ? (
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          totalItems={data.total}
          itemLabel={data.total === 1 ? "order" : "orders"}
          onPageChange={onPageChange}
          busy={isPlaceholderData}
        />
      ) : null}
    </>
  );
}

function OrderRow({ order }: { order: OrderSummary }) {
  const router = useRouter();
  const href = ROUTES.orderDetail(order.id);

  return (
    <TableRow interactive onClick={() => router.push(href)}>
      <TableCell>
        {/* A real link too, for keyboard users, middle-click and screen readers. */}
        <Link
          href={href}
          className="orders-reference-link"
          onClick={(event) => event.stopPropagation()}
        >
          {order.order_reference}
        </Link>
      </TableCell>
      <TableCell muted>{formatDateTime(order.created_at)}</TableCell>
      <TableCell numeric>{order.item_count}</TableCell>
      <TableCell numeric>{formatMoney(order.total_amount)}</TableCell>
      <TableCell>
        <StatusBadge status={order.status} />
      </TableCell>
    </TableRow>
  );
}
