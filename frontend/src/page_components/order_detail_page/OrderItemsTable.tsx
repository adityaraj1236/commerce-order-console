import { Table, TableCell, TableHeaderCell, TableRow } from "@/components/base_components/Table";
import type { Order } from "@/types/order";
import { formatMoney } from "@/utils/money";

/** Lines of an order. Names and unit prices are the snapshots taken at order time. */
export function OrderItemsTable({ order }: { order: Order }) {
  return (
    <Table caption={`Items in order ${order.order_reference}`}>
      <thead>
        <tr>
          <TableHeaderCell>Product</TableHeaderCell>
          <TableHeaderCell numeric>Unit price</TableHeaderCell>
          <TableHeaderCell numeric>Quantity</TableHeaderCell>
          <TableHeaderCell numeric>Line total</TableHeaderCell>
        </tr>
      </thead>
      <tbody>
        {order.items.map((item) => (
          <TableRow key={item.product_id}>
            <TableCell className="order-item-name">{item.product_name}</TableCell>
            <TableCell numeric muted>
              {formatMoney(item.unit_price)}
            </TableCell>
            <TableCell numeric>{item.quantity}</TableCell>
            <TableCell numeric>{formatMoney(item.line_total)}</TableCell>
          </TableRow>
        ))}
        <TableRow className="order-items-total-row">
          <TableCell colSpan={3}>Grand total</TableCell>
          <TableCell numeric>{formatMoney(order.total_amount)}</TableCell>
        </TableRow>
      </tbody>
    </Table>
  );
}
