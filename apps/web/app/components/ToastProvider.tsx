"use client";

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

/* ------------------------------------------------------------------ */
/*  Types                                                               */
/* ------------------------------------------------------------------ */

export type ToastTone = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  tone: ToastTone;
  duration?: number; // ms, default 4000
}

interface ToastCtx {
  toasts: Toast[];
  addToast: (message: string, tone?: ToastTone, duration?: number) => void;
  removeToast: (id: string) => void;
  success: (msg: string, duration?: number) => void;
  error: (msg: string, duration?: number) => void;
  warning: (msg: string, duration?: number) => void;
  info: (msg: string, duration?: number) => void;
}

/* ------------------------------------------------------------------ */
/*  Context                                                             */
/* ------------------------------------------------------------------ */

const ToastContext = createContext<ToastCtx | null>(null);

export function useToast(): ToastCtx {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast muss innerhalb von ToastProvider verwendet werden.");
  return ctx;
}

/* ------------------------------------------------------------------ */
/*  Icons                                                               */
/* ------------------------------------------------------------------ */

function IconSuccess() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function IconError() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  );
}

function IconWarning() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function IconInfo() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function IconClose() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Single Toast Item                                                    */
/* ------------------------------------------------------------------ */

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    // Einblend-Animation anstoßen
    requestAnimationFrame(() => setVisible(true));

    timerRef.current = setTimeout(() => {
      setExiting(true);
      setTimeout(onRemove, 300);
    }, toast.duration ?? 4000);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [toast.duration, onRemove]);

  const handleClose = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setExiting(true);
    setTimeout(onRemove, 300);
  };

  const icons: Record<ToastTone, React.ReactNode> = {
    success: <IconSuccess />,
    error: <IconError />,
    warning: <IconWarning />,
    info: <IconInfo />,
  };

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`toastItem toastItem--${toast.tone} ${visible && !exiting ? "toastItem--visible" : ""} ${exiting ? "toastItem--exit" : ""}`}
    >
      <span className={`toastIcon toastIcon--${toast.tone}`}>{icons[toast.tone]}</span>
      <span className="toastMessage">{toast.message}</span>
      <button className="toastClose" onClick={handleClose} aria-label="Benachrichtigung schließen">
        <IconClose />
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Provider                                                            */
/* ------------------------------------------------------------------ */

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, tone: ToastTone = "info", duration?: number) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev.slice(-4), { id, message, tone, duration }]);
    },
    []
  );

  const success = useCallback((msg: string, dur?: number) => addToast(msg, "success", dur), [addToast]);
  const error = useCallback((msg: string, dur?: number) => addToast(msg, "error", dur ?? 6000), [addToast]);
  const warning = useCallback((msg: string, dur?: number) => addToast(msg, "warning", dur), [addToast]);
  const info = useCallback((msg: string, dur?: number) => addToast(msg, "info", dur), [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      {/* Toast-Container – oben rechts, über allem */}
      <div className="toastContainer" aria-label="Benachrichtigungen">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
