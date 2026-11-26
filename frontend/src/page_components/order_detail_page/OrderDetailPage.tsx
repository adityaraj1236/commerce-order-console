"use client";

import { FileQuestion, ServerCrash } from "lucide-react";

import { StatusBadge } from "@/components/base_components/Badge";
import { Button, ButtonLink } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { Skeleton } from "@/components/base_components/Skeleton";
import { SummaryList } from "@/components/base_components/SummaryList";
import { PageHeader } from "@/components/global_components/PageHeader";
import { ROUTES } from "@/components/global_components/navigation";
import { useOrder } from "@/hooks/useOrders";
import { ApiError } from "@/lib/api/apiClient";
import type { Order } from "@/types/order";
import { getErrorMessage } from "@/utils/apiErrors";
import { formatDateTime } from "@/utils/dateUtils";
import { formatMoney } from "@/utils/money";

import { FulfilmentActions } from "./FulfilmentActions";
import { OrderItemsTable } from "./OrderItemsTable";
import "./order_detail.css";

const BACK_TO_ORDERS = { href: ROUTES.orders, label: "All orders" };

export function OrderDetailPage({ orderId }: { orderId: string }) {
  const { data: order, isPending, isError, error, refetch, isRefetching } = useOrder(orderId);

  if (isPending) {
    return <OrderDetailSkeleton />;
  }

  if (isError) {
    // 404 (unknown id) and 422 (not a valid id) both mean "no such order" to staff.
    const notFound = error instanceof ApiError && (error.status === 404 || error.status === 422);
    return (
      <>
        <PageHeader title="Order" backLink={BACK_TO_ORDERS} />
        <Card>
          {notFound ? (
            <EmptyState
              icon={FileQuestion}
              title="Order not found"
              description="This order does not exist. Check the link or search for it by reference."
              action={<ButtonLink href={ROUTES.orders}>Go to orders</ButtonLink>}
            />
          ) : (
            <EmptyState
              icon={ServerCrash}
              tone="error"
              title="Could not load this order"
              description={getErrorMessage(error)}
              action={
                <Button variant="secondary" onClick={() => refetch()} loading={isRefetching}>
                  Try again
                </Button>
              }
            />
          )}
        </Card>
      </>
    );
  }

  return <OrderDetail order={order} />;
}

function OrderDetail({ order }: { order: Order }) {
  return (
    <>
      <PageHeader
        title={
          <span className="order-detail-title">
            {order.order_reference}
            <StatusBadge status={order.status} />
          </span>
        }
        description={`Placed ${formatDateTime(order.created_at)}`}
        backLink={BACK_TO_ORDERS}
        actions={<FulfilmentActions order={order} />}
      />

      <div className="order-detail-layout">
        <Card title="Items" flush>
          <OrderItemsTable order={order} />
        </Card>

        <Card title="Summary">
          <SummaryList
            items={[
              { label: "Status", value: <StatusBadge status={order.status} /> },
              { label: "Created", value: formatDateTime(order.created_at) },
              { label: "Last updated", value: formatDateTime(order.updated_at) },
              { label: "Products", value: order.items.length },
              { label: "Items", value: order.item_count },
              { label: "Grand total", value: formatMoney(order.total_amount), emphasis: true },
            ]}
          />
        </Card>
      </div>
    </>
  );
}

function OrderDetailSkeleton() {
  return (
    <>
      <PageHeader title={<Skeleton variant="heading" />} backLink={BACK_TO_ORDERS} />
      <div className="order-detail-layout">
        <Card title="Items">
          <div className="order-detail-skeleton">
            <Skeleton />
            <Skeleton />
            <Skeleton />
          </div>
        </Card>
        <Card title="Summary">
          <div className="order-detail-skeleton">
            <Skeleton />
            <Skeleton />
            <Skeleton variant="display" />
          </div>
        </Card>
      </div>
    </>
  );
}
