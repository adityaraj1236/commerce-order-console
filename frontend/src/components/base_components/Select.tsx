import type { SelectHTMLAttributes } from "react";

import { cx } from "@/utils/classNames";

import "./base_components.css";

export interface SelectOption<TValue extends string> {
  value: TValue;
  label: string;
}

export interface SelectProps<TValue extends string>
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "value" | "onChange"> {
  options: ReadonlyArray<SelectOption<TValue>>;
  value: TValue;
  onValueChange: (value: TValue) => void;
}

export function Select<TValue extends string>({
  options,
  value,
  onValueChange,
  className,
  ...rest
}: SelectProps<TValue>) {
  return (
    <select
      className={cx("control", "control-select", className)}
      value={value}
      onChange={(event) => onValueChange(event.target.value as TValue)}
      {...rest}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
