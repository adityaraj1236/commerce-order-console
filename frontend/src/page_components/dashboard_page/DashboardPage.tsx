"use client";

import { Plus, ServerCrash } from "lucide-react";

import { StatusBadge, StockBadge } from "@/components/base_components/Badge";
import { Button, ButtonLink } from "@/components/base_components/Button";
import { Card } from "@/components/base_components/Card";
import { EmptyState } from "@/components/base_components/EmptyState";
import { PageHeader } from "@/components/global_components/PageHeader";
import { ROUTES } from "@/components/global_components/navigation";
import { useDashboardSummary } from "@/hooks/useDashboardSummary";
import type { OrderStatus } from "@/types/order";
import { getErrorMessage } from "@/utils/apiErrors";

import { MetricCard } from "./MetricCard";
import "./dashboard.css";

/** What each status means for the team's day-to-day work. */
const STATUS_HINT: Record<OrderStatus, string> = {
  PLACED: "Waiting to be packed",
  PACKED: "Ready to ship",
  SHIPPED: "With the courier",
  CANCELLED: "Stock returned",
};

const STATUS_ORDER: OrderStatus[] = ["PLACED", "PACKED", "SHIPPED", "CANCELLED"];

export function DashboardPage() {
  const { data, isError, error, refetch, isRefetching } = useDashboardSummary();

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Where every order stands and which products need attention."
        actions={
          <ButtonLink
            href={ROUTES.createOrder}
            icon={<Plus className="icon-sm" aria-hidden="true" />}
          >
            Create order
          </ButtonLink>
        }
      />

      {isError ? (
        <Card>
          <EmptyState
            icon={ServerCrash}
            tone="error"
            title="Could not load the dashboard"
            description={getErrorMessage(error)}
            action={
              <Button variant="secondary" onClick={() => refetch()} loading={isRefetching}>
                Try again
              </Button>
            }
          />
        </Card>
      ) : (
        <>
          <section className="dashboard-section" aria-labelledby="dashboard-orders">
            <h2 id="dashboard-orders" className="dashboard-section-title">
              Orders
            </h2>
            <div className="dashboard-grid">
              <MetricCard
                label="Total orders"
                value={data?.orders.total}
                hint="All time"
                href={ROUTES.orders}
              />
              {STATUS_ORDER.map((status) => (
                <MetricCard
                  key={status}
                  label={<StatusBadge status={status} />}
                  value={data?.orders.by_status[status]}
                  hint={STATUS_HINT[status]}
                  href={ROUTES.ordersWithStatus(status)}
                />
              ))}
            </div>
          </section>

          <section className="dashboard-section" aria-labelledby="dashboard-inventory">
            <h2 id="dashboard-inventory" className="dashboard-section-title">
              Inventory
            </h2>
            <div className="dashboard-grid">
              <MetricCard
                label="Total products"
                value={data?.products.total}
                hint="In the catalogue"
                href={ROUTES.products}
              />
              <MetricCard
                label={<StockBadge level="low_stock" />}
                value={data?.products.low_stock}
                hint={
                  data ? `${data.products.low_stock_threshold} or fewer units left` : "Running low"
                }
                href={ROUTES.products}
              />
              <MetricCard
                label={<StockBadge level="out_of_stock" />}
                value={data?.products.out_of_stock}
                hint="Cannot be ordered"
                href={ROUTES.products}
              />
            </div>
          </section>
        </>
      )}
    </>
  );
}
