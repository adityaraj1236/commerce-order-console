"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

import "./base_components.css";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  /** Buttons rendered bottom-right. */
  actions: ReactNode;
  children?: ReactNode;
}

/**
 * Native <dialog>: the browser handles focus trapping, Escape to close and the
 * backdrop, so no extra library is needed.
 */
export function Modal({ open, onClose, title, description, actions, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  // Syncing React state to the imperative dialog API is what useEffect is for.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className="modal"
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onClose={onClose}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <div className="modal-content">
        <h2 id={titleId} className="modal-title">
          {title}
        </h2>
        {description ? (
          <p id={descriptionId} className="modal-description">
            {description}
          </p>
        ) : null}
        {children}
        <div className="modal-actions">{actions}</div>
      </div>
    </dialog>
  );
}
