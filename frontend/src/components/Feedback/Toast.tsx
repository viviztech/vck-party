import React, { useState, useEffect } from 'react';
import { cn } from '@/utils/helpers';
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  id: string;
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number;
  onClose: (id: string) => void;
}

const variantStyles: Record<ToastVariant, { bg: string; border: string; icon: React.ReactNode }> = {
  success: {
    bg: 'bg-white border-success-200',
    border: 'border-l-4 border-l-success-500',
    icon: <CheckCircle className="text-success-500" size={20} />,
  },
  error: {
    bg: 'bg-white border-error-200',
    border: 'border-l-4 border-l-error-500',
    icon: <AlertCircle className="text-error-500" size={20} />,
  },
  warning: {
    bg: 'bg-white border-warning-200',
    border: 'border-l-4 border-l-warning-500',
    icon: <AlertTriangle className="text-warning-500" size={20} />,
  },
  info: {
    bg: 'bg-white border-blue-200',
    border: 'border-l-4 border-l-blue-500',
    icon: <Info className="text-blue-500" size={20} />,
  },
};

export function Toast({
  id,
  variant,
  title,
  message,
  duration = 5000,
  onClose,
}: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  const styles = variantStyles[variant];

  return (
    <div
      className={cn(
        'flex items-start p-4 rounded-lg shadow-lg animate-slide-up',
        styles.bg,
        styles.border,
        'max-w-sm'
      )}
    >
      <div className="flex-shrink-0">{styles.icon}</div>
      <div className="ml-3 flex-1">
        <p className="text-sm font-medium text-gray-900">{title}</p>
        {message && <p className="mt-1 text-sm text-gray-500">{message}</p>}
      </div>
      <button
        onClick={() => onClose(id)}
        className="ml-4 inline-flex flex-shrink-0 text-gray-400 hover:text-gray-600"
      >
        <X size={18} />
      </button>
    </div>
  );
}

interface ToastContextType {
  toasts: Array<{ id: string; variant: ToastVariant; title: string; message?: string }>;
  addToast: (toast: { variant: ToastVariant; title: string; message?: string }) => void;
  removeToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Array<{ id: string; variant: ToastVariant; title: string; message?: string }>>([]);

  const addToast = (toast: { variant: ToastVariant; title: string; message?: string }) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
          {toasts.map((toast) => (
            <Toast key={toast.id} {...toast} onClose={removeToast} />
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
