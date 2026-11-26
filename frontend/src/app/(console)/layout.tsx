import type { ReactNode } from "react";

import { AppShell } from "@/components/global_components/AppShell";

/** Every console page (dashboard, products, orders) renders inside the sidebar shell. */
export default function ConsoleLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
