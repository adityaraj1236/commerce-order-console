import { LayoutDashboard, type LucideIcon, Package, PlusCircle, ReceiptText } from "lucide-react";

import type { OrderStatus } from "@/types/order";

export interface NavigationItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Decides whether this item is highlighted for the current path. */
  isActive: (pathname: string) => boolean;
}

export const ROUTES = {
  dashboard: "/dashboard",
  products: "/products",
  orders: "/orders",
  createOrder: "/orders/new",
  orderDetail: (orderId: string) => `/orders/${orderId}`,
  ordersWithStatus: (status: OrderStatus) => `/orders?status=${status}`,
} as const;

/** The single list of main navigation entries, in display order. */
export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    href: ROUTES.dashboard,
    label: "Dashboard",
    icon: LayoutDashboard,
    isActive: (pathname) => pathname === ROUTES.dashboard,
  },
  {
    href: ROUTES.products,
    label: "Products",
    icon: Package,
    isActive: (pathname) => pathname.startsWith(ROUTES.products),
  },
  {
    href: ROUTES.orders,
    label: "Orders",
    icon: ReceiptText,
    // Order list and order detail pages, but not the separate Create Order page.
    isActive: (pathname) => pathname.startsWith(ROUTES.orders) && pathname !== ROUTES.createOrder,
  },
  {
    href: ROUTES.createOrder,
    label: "Create Order",
    icon: PlusCircle,
    isActive: (pathname) => pathname === ROUTES.createOrder,
  },
];
