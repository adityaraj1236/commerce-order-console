"use client";

import { CircleAlert, CircleCheck, X } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import "./base_components.css";

const TOAST_DURATION_MS = 5000;

type ToastTone = "success" | "error";

interface ToastInput {
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastItem extends ToastInput {
  id: number;
}

interface ToastContextValue {
  showToast: (toast: ToastInput) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_ICON = { success: CircleCheck, error: CircleAlert } as const;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (toast: ToastInput) => {
      const id = Date.now() + Math.random();
      setToasts((current) => [...current, { ...toast, id }]);
      window.setTimeout(() => dismiss(id), TOAST_DURATION_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" aria-live="polite">
        {toasts.map((toast) => {
          const Icon = TOAST_ICON[toast.tone];
          return (
            <div
              key={toast.id}
              className={`toast toast-${toast.tone}`}
              role={toast.tone === "error" ? "alert" : "status"}
            >
              <Icon className="toast-icon icon-md" aria-hidden="true" />
              <div className="toast-message">
                <p className="toast-title">{toast.title}</p>
                {toast.description ? (
                  <p className="toast-description">{toast.description}</p>
                ) : null}
              </div>
              <button
                type="button"
                className="button button-ghost button-sm button-icon-only"
                onClick={() => dismiss(toast.id)}
                aria-label="Dismiss notification"
              >
                <X className="icon-sm" aria-hidden="true" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

/** showToast({ tone: "success", title: "Order placed" }) from any client component. */
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }
  return context;
}
