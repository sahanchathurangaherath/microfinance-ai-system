"use client";

import { useState, useEffect } from "react";
import { create } from "zustand";
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (type: ToastType, message: string) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (type, message) => {
    const id = Date.now().toString() + Math.random().toString(36).slice(2);
    set((state) => ({
      toasts: [...state.toasts, { id, type, message }],
    }));
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 4000);
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
}));

export function useToast() {
  const addToast = useToastStore((s) => s.addToast);
  return {
    success: (msg: string) => addToast("success", msg),
    error: (msg: string) => addToast("error", msg),
    warning: (msg: string) => addToast("warning", msg),
    info: (msg: string) => addToast("info", msg),
  };
}

const icons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="h-5 w-5 text-emerald-600" />,
  error: <AlertCircle className="h-5 w-5 text-red-600" />,
  warning: <AlertTriangle className="h-5 w-5 text-amber-600" />,
  info: <Info className="h-5 w-5 text-blue-600" />,
};

function ToastItem({ toast }: { toast: Toast }) {
  const removeToast = useToastStore((s) => s.removeToast);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsClosing(true);
      setTimeout(() => removeToast(toast.id), 300);
    }, 3700);
    return () => clearTimeout(timer);
  }, [toast.id, removeToast]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => removeToast(toast.id), 300);
  };

  return (
    <div className={cn(
      "toast relative overflow-hidden transition-all duration-300 ease-in-out",
      `toast-${toast.type}`,
      isClosing ? "opacity-0 translate-x-4 scale-95" : "opacity-100 translate-x-0 scale-100 animate-slideIn"
    )}>
      {icons[toast.type]}
      <span className="flex-1 text-[13px] font-medium">{toast.message}</span>
      <button
        onClick={handleClose}
        className="opacity-50 hover:opacity-100 transition-opacity ml-2 p-1 rounded-md hover:bg-black/5"
      >
        <X className="h-4 w-4" />
      </button>
      <div 
        className="absolute bottom-0 left-0 h-1 bg-black/10 origin-left"
        style={{ 
          width: '100%',
          animation: 'toast-progress 3.7s linear forwards' 
        }} 
      />
    </div>
  );
}

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);
  if (!mounted || toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
