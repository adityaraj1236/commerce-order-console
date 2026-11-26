import type { InputHTMLAttributes, ReactNode } from "react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Leading icon, e.g. a search glass. */
  icon?: ReactNode;
  invalid?: boolean;
}

export function Input({ icon, invalid = false, className, ...rest }: InputProps) {
  const input = (
    <input className={cx("control", className)} aria-invalid={invalid || undefined} {...rest} />
  );
  if (!icon) {
    return input;
  }
  return (
    <div className="control-with-icon">
      <span className="control-icon" aria-hidden="true">
        {icon}
      </span>
      {input}
    </div>
  );
}
