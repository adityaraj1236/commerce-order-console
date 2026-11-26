import { redirect } from "next/navigation";

import { ROUTES } from "@/components/global_components/navigation";

/** The console opens on the dashboard. */
export default function HomePage() {
  redirect(ROUTES.dashboard);
}
