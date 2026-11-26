import { LoaderCircle } from "lucide-react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  label?: string;
}

export function Spinner({ size = "sm", label = "Loading" }: SpinnerProps) {
  return (
    <span role="status">
      <LoaderCircle className={cx("spinner", `icon-${size}`)} aria-hidden="true" />
      <span className="visually-hidden">{label}</span>
    </span>
  );
}
