import type { ReactNode } from "react";

import { Sidebar } from "./Sidebar";
import "./global_components.css";

/** Sidebar + scrollable content area shared by every console page. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="app-content">{children}</div>
      </main>
    </div>
  );
}
