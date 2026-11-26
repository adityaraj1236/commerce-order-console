"use client";

import { Minus, Plus } from "lucide-react";

import "./base_components.css";

interface QuantityStepperProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  /** Usually the product's available stock. */
  max: number;
  /** Accessible name, e.g. "Quantity for Mechanical Keyboard". */
  label: string;
  disabled?: boolean;
}

/** [-] [ 2 ] [+]. Keeps the value a whole number within min..max. */
export function QuantityStepper({
  value,
  onChange,
  min = 1,
  max,
  label,
  disabled = false,
}: QuantityStepperProps) {
  const clamp = (next: number) => Math.min(Math.max(Math.trunc(next), min), max);

  return (
    <div className="quantity-stepper" role="group" aria-label={label}>
      <button
        type="button"
        className="quantity-stepper-button"
        onClick={() => onChange(clamp(value - 1))}
        disabled={disabled || value <= min}
        aria-label="Decrease quantity"
      >
        <Minus className="icon-sm" aria-hidden="true" />
      </button>
      <input
        className="quantity-stepper-input"
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        step={1}
        value={value}
        disabled={disabled}
        aria-label={label}
        onChange={(event) => {
          const next = Number(event.target.value);
          if (Number.isFinite(next)) {
            onChange(clamp(next));
          }
        }}
      />
      <button
        type="button"
        className="quantity-stepper-button"
        onClick={() => onChange(clamp(value + 1))}
        disabled={disabled || value >= max}
        aria-label="Increase quantity"
      >
        <Plus className="icon-sm" aria-hidden="true" />
      </button>
    </div>
  );
}
