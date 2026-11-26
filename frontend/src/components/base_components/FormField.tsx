import type { ReactNode } from "react";

import "./base_components.css";

interface FormFieldProps {
  /** Must match the id of the control inside. */
  htmlFor: string;
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

/** Label + control + hint/error. The control should set aria-describedby to `${htmlFor}-message`. */
export function FormField({ htmlFor, label, hint, error, children }: FormFieldProps) {
  const message = error ?? hint;
  return (
    <div className="form-field">
      <label className="form-field-label" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {message ? (
        <p
          id={`${htmlFor}-message`}
          className={error ? "form-field-error" : "form-field-hint"}
          role={error ? "alert" : undefined}
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
