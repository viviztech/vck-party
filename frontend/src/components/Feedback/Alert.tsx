import React from 'react';
import { cn } from '@/utils/helpers';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

export type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  variant: AlertVariant;
  title?: string;
  children: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

const variantStyles: Record<AlertVariant, { bg: string; border: string; text: string; icon: React.ReactNode }> = {
  success: {
    bg: 'bg-success-50',
    border: 'border-success-200',
    text: 'text-success-800',
    icon: <CheckCircle className="text-success-500" size={20} />,
  },
  error: {
    bg: 'bg-error-50',
    border: 'border-error-200',
    text: 'text-error-800',
    icon: <AlertCircle className="text-error-500" size={20} />,
  },
  warning: {
    bg: 'bg-warning-50',
    border: 'border-warning-200',
    text: 'text-warning-800',
    icon: <AlertTriangle className="text-warning-500" size={20} />,
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    icon: <Info className="text-blue-500" size={20} />,
  },
};

export function Alert({
  variant,
  title,
  children,
  dismissible = false,
  onDismiss,
  className,
}: AlertProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        styles.bg,
        styles.border,
        className
      )}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">{styles.icon}</div>
        <div className="ml-3 flex-1">
          {title && <h3 className={cn('text-sm font-medium', styles.text)}>{title}</h3>}
          <div className={cn('text-sm', title && 'mt-1', styles.text)}>
            {children}
          </div>
        </div>
        {dismissible && onDismiss && (
          <div className="ml-auto pl-3">
            <button
              onClick={onDismiss}
              className={cn(
                'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                styles.text,
                'hover:bg-white/50'
              )}
              aria-label="Dismiss"
            >
              <X size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
