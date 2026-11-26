import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import "./global_components.css";

interface PageHeaderProps {
  title: ReactNode;
  description?: string;
  /** Buttons on the right, e.g. "Create order". */
  actions?: ReactNode;
  /** Back link above the title, e.g. from an order detail to the order list. */
  backLink?: { href: string; label: string };
}

/** The top of every page: one h1 per page, same spacing everywhere. */
export function PageHeader({ title, description, actions, backLink }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header-text">
        {backLink ? (
          <Link href={backLink.href} className="page-header-back">
            <ArrowLeft className="icon-sm" aria-hidden="true" />
            {backLink.label}
          </Link>
        ) : null}
        <h1>{title}</h1>
        {description ? <p className="page-header-description">{description}</p> : null}
      </div>
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </header>
  );
}
