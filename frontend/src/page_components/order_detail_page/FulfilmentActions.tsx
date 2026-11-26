"use client";

import { useState } from "react";

import { Button } from "@/components/base_components/Button";
import { ConfirmDialog } from "@/components/base_components/ConfirmDialog";
import { useToast } from "@/components/base_components/Toast";
import { useUpdateOrderStatus } from "@/hooks/useOrders";
import type { Order, OrderStatus } from "@/types/order";
import { getErrorMessage } from "@/utils/apiErrors";
import { ORDER_STATUS_LABEL, STATUS_ACTION_LABEL } from "@/utils/labels";

/**
 * Shows only the actions the backend allows next (`allowed_transitions`).
 * The backend still validates every change, so a stale page can never skip a step.
 */
export function FulfilmentActions({ order }: { order: Order }) {
  const updateStatus = useUpdateOrderStatus(order.id);
  const { showToast } = useToast();
  const [confirmingCancel, setConfirmingCancel] = useState(false);

  const changeStatus = (target: OrderStatus) => {
    updateStatus.mutate(target, {
      onSuccess: (updated) => {
        setConfirmingCancel(false);
        showToast({
          tone: "success",
          title: `Order ${ORDER_STATUS_LABEL[updated.status].toLowerCase()}`,
          description:
            updated.status === "CANCELLED"
              ? `${updated.order_reference}: ${updated.item_count} items returned to stock.`
              : updated.order_reference,
        });
      },
      onError: (error) => {
        setConfirmingCancel(false);
        showToast({
          tone: "error",
          title: "Status not changed",
          description: getErrorMessage(error),
        });
      },
    });
  };

  if (order.allowed_transitions.length === 0) {
    return (
      <p className="fulfilment-final">
        {ORDER_STATUS_LABEL[order.status]} is a final status. No further actions.
      </p>
    );
  }

  const pendingTarget = updateStatus.isPending ? updateStatus.variables : undefined;

  return (
    <div className="fulfilment-actions">
      {order.allowed_transitions.map((target) =>
        target === "CANCELLED" ? (
          <Button
            key={target}
            variant="danger"
            onClick={() => setConfirmingCancel(true)}
            disabled={updateStatus.isPending}
          >
            {STATUS_ACTION_LABEL[target]}
          </Button>
        ) : (
          <Button
            key={target}
            onClick={() => changeStatus(target)}
            loading={pendingTarget === target}
            disabled={updateStatus.isPending}
          >
            {STATUS_ACTION_LABEL[target]}
          </Button>
        ),
      )}

      <ConfirmDialog
        open={confirmingCancel}
        title={`Cancel order ${order.order_reference}?`}
        description={`The order will be cancelled and its ${order.item_count} items returned to stock. This cannot be undone.`}
        confirmLabel="Cancel order"
        cancelLabel="Keep order"
        destructive
        loading={pendingTarget === "CANCELLED"}
        onConfirm={() => changeStatus("CANCELLED")}
        onCancel={() => setConfirmingCancel(false)}
      />
    </div>
  );
}
