import React from 'react';
import { cn } from '@/utils/helpers';

export type RadioOption = {
  value: string | number;
  label: string;
  disabled?: boolean;
};

interface RadioGroupProps {
  label?: string;
  name: string;
  options: RadioOption[];
  value: string | number;
  onChange: (value: string | number) => void;
  error?: string;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

interface RadioProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  label,
  name,
  options,
  value,
  onChange,
  error,
  className,
  orientation = 'vertical',
}) => {
  const isHorizontal = orientation === 'horizontal';

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <div className={cn('flex', isHorizontal ? 'space-x-4' : 'flex-col space-y-2')}>
        {options.map((option) => (
          <label
            key={option.value}
            className={cn(
              'flex items-center cursor-pointer',
              isHorizontal && 'flex-shrink-0'
            )}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange(e.target.value)}
              disabled={option.disabled}
              className={cn(
                'h-4 w-4 border-gray-300 text-primary-600',
                'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                'cursor-pointer'
              )}
            />
            <span className="ml-2 text-sm text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>
      {error && <p className="text-sm text-error-600">{error}</p>}
    </div>
  );
};

export const Radio: React.FC<RadioProps> = ({ label, ...props }) => {
  return (
    <label className="flex items-center cursor-pointer">
      <input
        type="radio"
        className={cn(
          'h-4 w-4 border-gray-300 text-primary-600',
          'focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'cursor-pointer'
        )}
        {...props}
      />
      <span className="ml-2 text-sm text-gray-700">{label}</span>
    </label>
  );
};
