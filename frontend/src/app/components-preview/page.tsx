import type { Metadata } from "next";

import { ComponentsPreview } from "@/page_components/components_preview/ComponentsPreview";

export const metadata: Metadata = { title: "Component preview · Commerce Order Console" };

export default function ComponentsPreviewPage() {
  return <ComponentsPreview />;
}
