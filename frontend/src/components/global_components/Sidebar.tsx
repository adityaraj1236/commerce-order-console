"use client";

import { Boxes } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cx } from "@/utils/classNames";

import { NAVIGATION_ITEMS, ROUTES } from "./navigation";
import "./global_components.css";

/** Left sidebar on desktop; a top navigation bar on smaller screens (pure CSS). */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <Link href={ROUTES.dashboard} className="sidebar-brand">
        <Boxes className="icon-md" aria-hidden="true" />
        <span className="sidebar-brand-name">Order Console</span>
      </Link>
      <nav className="sidebar-nav" aria-label="Main navigation">
        <ul className="sidebar-nav-list">
          {NAVIGATION_ITEMS.map(({ href, label, icon: Icon, isActive }) => {
            const active = isActive(pathname);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cx("sidebar-link", active && "sidebar-link-active")}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="icon-md" aria-hidden="true" />
                  <span>{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
