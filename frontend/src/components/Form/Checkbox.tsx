import React from 'react';
import { cn } from '@/utils/helpers';

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="flex items-start">
        <div className="flex items-center h-5">
          <input
            ref={ref}
            id={checkboxId}
            type="checkbox"
            className={cn(
              'h-4 w-4 rounded border-gray-300 text-primary-600',
              'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              'cursor-pointer',
              error && 'border-error-300',
              className
            )}
            {...props}
          />
        </div>
        {label && (
          <div className="ml-2">
            <label
              htmlFor={checkboxId}
              className="text-sm font-medium text-gray-700 cursor-pointer"
            >
              {label}
            </label>
          </div>
        )}
        {error && (
          <p className="ml-2 text-sm text-error-600">{error}</p>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';
